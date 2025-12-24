from flask import Blueprint, jsonify
import json
import logging
from collections import defaultdict
from app.auth.decorators import login_required, get_current_user_id
from app.database.repositories.user_story_repository import UserStoryRepository
from app.database.repositories.test_case_repository import TestCaseRepository
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.database.repositories.bulk_upload_repository import BulkUploadRepository

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/metrics', methods=['GET'])
@login_required
def get_dashboard_metrics():
    """
    Obtiene métricas del dashboard para el usuario actual
    
    Retorna:
        - generator_metrics: Métricas del generador (historias y casos de prueba)
        - jira_metrics: Métricas de Jira (reportes y cargas masivas)
    """
    try:
        user_id = get_current_user_id()
        
        # Repositorios
        story_repo = UserStoryRepository()
        test_case_repo = TestCaseRepository()
        report_repo = JiraReportRepository()
        upload_repo = BulkUploadRepository()
        
        # ===== MÉTRICAS DEL GENERADOR =====
        # Obtener historias y casos de prueba del usuario
        stories = story_repo.get_by_user_id(user_id)
        test_cases = test_case_repo.get_by_user_id(user_id)
        
        # Contar totales
        total_stories = story_repo.count_by_user(user_id)
        total_test_cases = test_case_repo.count_by_user(user_id)
        
        # Construir historial de generaciones
        history = []
        
        # Agregar historias al historial
        for story in stories:
            try:
                story_content = json.loads(story.story_content) if isinstance(story.story_content, str) else story.story_content
                count = len(story_content) if isinstance(story_content, list) else 1
                history.append({
                    'type': 'stories',
                    'count': count,
                    'area': story.area or 'Sin área',
                    'date': story.created_at.isoformat() if story.created_at else None
                })
            except:
                history.append({
                    'type': 'stories',
                    'count': 1,
                    'area': story.area or 'Sin área',
                    'date': story.created_at.isoformat() if story.created_at else None
                })
        
        # Agregar casos de prueba al historial
        for test_case in test_cases:
            try:
                tc_content = json.loads(test_case.test_case_content) if isinstance(test_case.test_case_content, str) else test_case.test_case_content
                count = len(tc_content) if isinstance(tc_content, list) else 1
                history.append({
                    'type': 'testCases',
                    'count': count,
                    'area': test_case.area or 'Sin área',
                    'date': test_case.created_at.isoformat() if test_case.created_at else None
                })
            except:
                history.append({
                    'type': 'testCases',
                    'count': 1,
                    'area': test_case.area or 'Sin área',
                    'date': test_case.created_at.isoformat() if test_case.created_at else None
                })
        
        # Ordenar historial por fecha (más reciente primero)
        history.sort(key=lambda x: x['date'] or '', reverse=True)
        
        generator_metrics = {
            'stories': total_stories,
            'testCases': total_test_cases,
            'history': history
        }
        
        # ===== MÉTRICAS DE JIRA =====
        # Obtener reportes del usuario
        reports_all = report_repo.get_by_user_id(user_id)
        # Filtrar reportes de tipo 'metrics' que son logs internos automáticos
        reports = [r for r in reports_all if r.report_type != 'metrics']
        
        # Agrupar reportes por proyecto y construir historial
        reports_by_project = defaultdict(lambda: {'count': 0, 'name': '', 'lastDate': None})
        reports_history = []
        
        for report in reports:
            key = report.project_key
            reports_by_project[key]['count'] += 1
            reports_by_project[key]['name'] = report.project_key
            
            # Actualizar última fecha
            if report.created_at:
                current_last = reports_by_project[key]['lastDate']
                if not current_last or report.created_at.isoformat() > current_last:
                    reports_by_project[key]['lastDate'] = report.created_at.strftime('%Y-%m-%d')
                
                # Agregar al historial
                reports_history.append({
                    'project_key': report.project_key,
                    'created_at': report.created_at.isoformat(),
                    'timestamp': report.created_at.timestamp() * 1000
                })
        
        # Ordenar historial por fecha (más reciente primero)
        reports_history.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Última fecha de reporte
        last_report_date = None
        if reports:
            last_report_date = max(r.created_at for r in reports if r.created_at)
            last_report_date = last_report_date.strftime('%Y-%m-%d') if last_report_date else None
        
        # Obtener cargas masivas del usuario
        uploads = upload_repo.get_by_user_id(user_id)
        
        # Calcular totales de items cargados
        total_items_uploaded = sum(u.successful_items or 0 for u in uploads)
        
        # Agrupar cargas por proyecto y construir historial
        uploads_by_project = defaultdict(lambda: {'count': 0, 'name': '', 'itemsCount': 0, 'lastDate': None, 'issueTypesDistribution': {}})
        issue_types_distribution = defaultdict(int)
        uploads_history = []
        
        for upload in uploads:
            key = upload.project_key
            uploads_by_project[key]['count'] += 1
            uploads_by_project[key]['name'] = upload.project_key
            uploads_by_project[key]['itemsCount'] += upload.successful_items or 0
            
            if upload.created_at:
                current_last = uploads_by_project[key]['lastDate']
                if not current_last or upload.created_at.isoformat() > current_last:
                    uploads_by_project[key]['lastDate'] = upload.created_at.strftime('%Y-%m-%d')
            
            # Procesar distribución de tipos de issue
            try:
                details = json.loads(upload.upload_details) if isinstance(upload.upload_details, str) else upload.upload_details
                if details and 'issue_types_distribution' in details:
                    for issue_type, count in details['issue_types_distribution'].items():
                        issue_types_distribution[issue_type] += count
                        uploads_by_project[key]['issueTypesDistribution'][issue_type] = \
                            uploads_by_project[key]['issueTypesDistribution'].get(issue_type, 0) + count
            except:
                details = {}

            # Agregar al historial
            if upload.created_at:
                uploads_history.append({
                    'project_key': upload.project_key,
                    'itemsCount': upload.successful_items or 0,
                    'created_at': upload.created_at.isoformat(),
                    'timestamp': upload.created_at.timestamp() * 1000,
                    'upload_details': details
                })
        
        # Ordenar historial por fecha (más reciente primero)
        uploads_history.sort(key=lambda x: x['created_at'], reverse=True)
        
        jira_metrics = {
            'reports': {
                'count': len(reports),
                'byProject': dict(reports_by_project),
                'lastDate': last_report_date,
                'history': reports_history
            },
            'uploads': {
                'count': len(uploads),
                'itemsCount': total_items_uploaded,
                'byProject': dict(uploads_by_project),
                'issueTypesDistribution': dict(issue_types_distribution),
                'history': uploads_history
            }
        }
        
        return jsonify({
            'success': True,
            'generator_metrics': generator_metrics,
            'jira_metrics': jira_metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener métricas del dashboard: {e}", exc_info=True)

@dashboard_bp.route('/clear-metrics', methods=['DELETE'])
@login_required
def clear_all_metrics():
    """
    Limpia todas las métricas del dashboard (historias, casos de prueba, reportes y cargas masivas)
    
    ✅ Solo Admin puede ejecutar esta acción
    ❌ Analista QA y Usuario NO tienen acceso
    """
    try:
        user_id = get_current_user_id()
        # Se requiere importar get_user_service y UserService si no estan disponibles
        # Asumimos que get_current_user_id funciona
        # Necesitamos verificar el rol del usuario. 
        # En la arquitectura actual, parece que podemos usar un repositorio o servicio.
        
        # Como no tenemos acceso facil a UserService aqui (no esta importado), 
        # vamos a obtener el usuario a través de un repositorio o inyección si es posible.
        # Revisando importaciones: from app.auth.decorators import login_required, get_current_user_id
        
        # Vamos a importar UserService localmente para evitar dependencias circulares si las hubiera, 
        # o agregarlo arriba. Mejor agregarlo arriba si es posible, pero voy a usar import local para ser seguro.
        from app.auth.user_service import UserService
        from app.core.dependencies import get_user_service

        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Verificar que sea admin
        if user.role != 'admin':
            logger.warning(f"Intento no autorizado de limpiar métricas por usuario {user.email} (rol: {user.role})")
            return jsonify({"error": "No autorizado. Solo Admin puede limpiar métricas"}), 403
        
        # Limpiar todas las tablas de métricas
        story_repo = UserStoryRepository()
        test_case_repo = TestCaseRepository()
        report_repo = JiraReportRepository()
        upload_repo = BulkUploadRepository()
        
        # Contar antes de limpiar para el log
        stories_count = story_repo.count_all()
        test_cases_count = test_case_repo.count_all()
        reports_count = report_repo.count_all()
        uploads_count = upload_repo.count_all()
        
        # Limpiar todas las tablas
        story_repo.delete_all()
        test_case_repo.delete_all()
        report_repo.delete_all()
        upload_repo.delete_all()
        
        logger.info(f"Admin {user.email} limpió todas las métricas: {stories_count} historias, {test_cases_count} casos de prueba, {reports_count} reportes, {uploads_count} cargas masivas")
        
        return jsonify({
            "success": True,
            "message": "Todas las métricas han sido limpiadas exitosamente",
            "deleted": {
                "stories": stories_count,
                "test_cases": test_cases_count,
                "reports": reports_count,
                "bulk_uploads": uploads_count
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error al limpiar métricas: {e}", exc_info=True)
        return jsonify({"error": "Error al limpiar métricas"}), 500

