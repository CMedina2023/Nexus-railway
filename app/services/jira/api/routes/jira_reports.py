import logging
import json
from datetime import datetime
from app.auth.decorators import login_required, get_current_user_id, get_current_user_role
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.models.jira_report import JiraReport
from app.core.dependencies import get_pdf_service
from app.core.dependencies import get_jira_client
import io
import csv
from flask import Blueprint, jsonify, request, Response, render_template, send_file

logger = logging.getLogger(__name__)

jira_reports_bp = Blueprint('jira_reports', __name__)

@jira_reports_bp.route('/reports/save', methods=['POST'])
@login_required
def save_report():
    """Guarda un reporte generado"""
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        
        if not data.get('project_key') or not data.get('report_content'):
             return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400

        # Asegurar que content sea string JSON
        content = data['report_content']
        if not isinstance(content, str):
            content = json.dumps(content)

        report = JiraReport(
            user_id=user_id,
            project_key=data['project_key'],
            report_type=data.get('report_type', 'web_report'),
            report_title=data.get('title', 'Sin título'),
            report_content=content,
            jira_issue_key=data.get('jira_issue_key', 'LOCAL')
        )
        
        repo = JiraReportRepository()
        saved = repo.create(report)
        
        return jsonify({'success': True, 'report_id': saved.id})
    except Exception as e:
        logger.error(f"Error saving report: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@jira_reports_bp.route('/reports/list', methods=['GET'])
@login_required
def list_reports():
    """Lista reportes con paginación y reglas de visibilidad"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Validar límites
        per_page = min(per_page, 50)
        
        user_id = get_current_user_id()
        role = get_current_user_role()
        
        repo = JiraReportRepository()
        
        if role == 'admin':
            result = repo.get_paginated_all(page, per_page)
        else:
            result = repo.get_paginated_by_user(user_id, page, per_page)
            
        # Convertir objetos a dicts
        result['items'] = [item.to_dict() for item in result['items']]
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@jira_reports_bp.route('/reports/<int:report_id>', methods=['GET'])
@login_required
def get_report_detail(report_id):
    """Obtiene el detalle de un reporte"""
    try:
        repo = JiraReportRepository()
        report = repo.get_by_id(report_id)
        
        if not report:
            return jsonify({'success': False, 'error': 'Reporte no encontrado'}), 404
            
        # Validar acceso
        user_id = get_current_user_id()
        role = get_current_user_role()
        
        if role != 'admin' and report.user_id != user_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
            
        return jsonify({'success': True, 'data': report.to_dict()})
    except Exception as e:
        logger.error(f"Error getting report detail: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@jira_reports_bp.route('/reports/<int:report_id>', methods=['PUT'])
@login_required
def update_report(report_id):
    """Actualiza un reporte existente (ej. tras refrescar datos)"""
    try:
        data = request.get_json()
        repo = JiraReportRepository()
        report = repo.get_by_id(report_id)
        
        if not report:
            return jsonify({'success': False, 'error': 'Reporte no encontrado'}), 404
            
        user_id = get_current_user_id()
        role = get_current_user_role()
        
        if role != 'admin' and report.user_id != user_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
            
        # Actualizar campos permitidos
        if 'title' in data:
            report.report_title = data['title']
        if 'report_content' in data:
            content = data['report_content']
            report.report_content = json.dumps(content) if not isinstance(content, str) else content
            
        repo.update(report)
        
        return jsonify({'success': True, 'data': report.to_dict()})
    except Exception as e:
        logger.error(f"Error updating report: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@jira_reports_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """Elimina un reporte"""
    try:
        repo = JiraReportRepository()
        report = repo.get_by_id(report_id)
        
        if not report:
            return jsonify({'success': False, 'error': 'Reporte no encontrado'}), 404
            
        user_id = get_current_user_id()
        role = get_current_user_role()
        
        if role != 'admin' and report.user_id != user_id:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
            
        repo.delete(report_id)
        
        return jsonify({'success': True, 'message': 'Reporte eliminado'})
    except Exception as e:
        logger.error(f"Error deleting report: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@jira_reports_bp.route('/download-report', methods=['POST'])
@login_required
def jira_download_report():
    """Genera y descarga un reporte de Jira en formato PDF"""
    try:
        data = request.get_json()
        project_key = data.get('project_key')
        report = data.get('general_report', {})
        chart_images = data.get('chart_images', {})
        table_data = data.get('table_data', {})
        active_widgets = data.get('active_widgets', [])
        widget_chart_images = data.get('widget_chart_images', {})
        widget_data = data.get('widget_data', {})
        
        if not project_key:
            return jsonify({"success": False, "error": "Falta project_key"}), 400
            
        # Preparar datos para el template
        test_cases_all = table_data.get('test_cases_by_person', [])
        defects_all = table_data.get('defects_by_person', [])
        
        test_cases_totals = _calculate_test_cases_totals(test_cases_all)
        
        items_per_page = 20
        test_cases_paginated = test_cases_all[:items_per_page]
        defects_paginated = defects_all[:items_per_page]
        
        test_cases_pagination = _get_pagination_data(test_cases_all, test_cases_paginated, items_per_page)
        defects_pagination = _get_pagination_data(defects_all, defects_paginated, items_per_page)
        
        html_content = render_template('jira_report.html', 
                                     project_key=project_key,
                                     report=report,
                                     chart_images=chart_images,
                                     test_cases_data=test_cases_paginated,
                                     test_cases_totals=test_cases_totals,
                                     test_cases_pagination=test_cases_pagination,
                                     defects_data=defects_paginated,
                                     defects_pagination=defects_pagination,
                                     active_widgets=active_widgets,
                                     widget_chart_images=widget_chart_images,
                                     widget_data=widget_data,
                                     date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        pdf_buffer = get_pdf_service().generate_pdf(html_content)
        
        _save_report_history(get_current_user_id(), project_key, report)
            
        return Response(
            pdf_buffer,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=reporte_{project_key}_{datetime.now().strftime("%Y%m%d")}.pdf'}
        )
    except Exception as e:
        logger.error(f"Error al generar reporte: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

def _calculate_test_cases_totals(test_cases_all):
    return {
        'exitoso': sum(item.get('exitoso', 0) for item in test_cases_all),
        'en_progreso': sum(item.get('en_progreso', 0) for item in test_cases_all),
        'fallado': sum(item.get('fallado', 0) for item in test_cases_all),
        'total': sum(item.get('total', 0) for item in test_cases_all)
    }

def _get_pagination_data(items_all, items_paginated, items_per_page):
    return {
        'current_page': 1,
        'total_pages': (len(items_all) + items_per_page - 1) // items_per_page if items_all else 1,
        'total_items': len(items_all),
        'start_item': 1 if items_all else 0,
        'end_item': len(items_paginated)
    }

def _save_report_history(user_id, project_key, report):
    try:
        JiraReportRepository().create(JiraReport(
            user_id=user_id,
            project_key=project_key,
            report_type='pdf_report',
            report_title=f"Reporte PDF - {project_key}",
            report_content=json.dumps({
                'total_test_cases': report.get('total_test_cases', 0),
                'total_defects': report.get('total_defects', 0),
                'generated_at': datetime.now().isoformat()
            }),
            jira_issue_key='N/A'
        ))
    except Exception as e:
        logger.error(f"Error al guardar reporte en historial: {e}")

@jira_reports_bp.route('/download-template', methods=['GET'])
@login_required
def jira_download_template():
    """Descarga una plantilla CSV para Jira"""
    try:
        project_key = request.args.get('project_key')
        story_type, test_case_type, bug_type = 'Story', 'Test Case', 'Bug'
        
        if project_key:
            try:
                itypes = get_jira_client().get_issue_types(project_key)
                names = [it.get('name', '').lower() for it in itypes]
                for n in names:
                    if 'story' in n: story_type = n
                    if 'test' in n and 'case' in n: test_case_type = n
                    if 'bug' in n: bug_type = n
            except: pass
            
        output = io.StringIO()
        fieldnames = ['Tipo de Issue', 'Resumen', 'Descripción', 'Prioridad', 'Labels']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'Tipo de Issue': story_type, 'Resumen': 'Ejemplo de historia', 'Descripción': 'Descripción de ejemplo', 'Prioridad': 'High', 'Labels': 'nexus_ai'})
        writer.writerow({'Tipo de Issue': test_case_type, 'Resumen': 'Ejemplo de caso de prueba', 'Descripción': 'Pasos: 1. Login', 'Prioridad': 'Medium', 'Labels': 'nexus_ai'})
        
        csv_bytes = output.getvalue().encode('utf-8-sig')
        return send_file(io.BytesIO(csv_bytes), mimetype='text/csv', as_attachment=True, download_name='plantilla_jira.csv')
    except Exception as e:
        logger.error(f"Error al descargar plantilla: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
