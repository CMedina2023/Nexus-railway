from flask import Blueprint, jsonify, request, send_file, Response, render_template
from datetime import datetime
import json
import logging
import io
import csv
import base64
from typing import Dict

from app.auth.decorators import login_required, get_current_user_id
from app.auth.session_service import SessionService
from app.auth.user_service import UserService
from app.services.jira_token_manager import JiraTokenManager
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_service import IssueService
from app.backend.jira_backend import JiraClient
from app.database.repositories.project_config_repository import ProjectConfigRepository
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.database.repositories.bulk_upload_repository import BulkUploadRepository
from app.models.jira_report import JiraReport
from app.models.bulk_upload import BulkUpload
from app.core.config import Config
from app.backend import jira_backend
from app.utils.decorators import handle_errors
from app.services.pdf.application.pdf_service import PdfService
from app.core.dependencies import get_user_service, get_jira_token_manager, get_jira_client, get_pdf_service
from app.services.jira.api.helpers import (
    generate_upload_summary_txt, 
    generate_stories_upload_summary_txt, 
    generate_test_cases_upload_summary_txt
)

logger = logging.getLogger(__name__)

jira_bp = Blueprint('jira', __name__, url_prefix='/api/jira')
# pdf_service será obtenido vía dependencia en la ruta
# pdf_service = PdfService()

@jira_bp.route('/test-connection', methods=['GET'])
@login_required
@handle_errors("Error al probar conexión con Jira", status_code=500)
def jira_test_connection():
    """Prueba la conexión con Jira"""
    try:
        client = get_jira_client()
        result = client.test_connection()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error al probar conexión con Jira: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/projects', methods=['GET'])
@login_required
def jira_get_projects():
    """Obtiene la lista de proyectos de Jira"""
    try:
        user_id = get_current_user_id()
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado", "projects": []}), 401
        
        project_config_repo = ProjectConfigRepository()
        all_configs = project_config_repo.get_all(active_only=True)
        
        if not all_configs:
            if Config.JIRA_BASE_URL and Config.JIRA_EMAIL and Config.JIRA_API_TOKEN:
                connection = JiraConnection(base_url=Config.JIRA_BASE_URL, email=Config.JIRA_EMAIL, api_token=Config.JIRA_API_TOKEN)
                projects = ProjectService(connection).get_projects()
                return jsonify({"success": True, "projects": projects})
            return jsonify({"success": False, "error": "No hay configuración de Jira disponible", "projects": []}), 400
        
        token_manager = get_jira_token_manager()
        jira_config = token_manager.get_token_for_user(user, all_configs[0].project_key)
        connection = JiraConnection(base_url=jira_config.base_url, email=jira_config.email, api_token=jira_config.token)
        projects = ProjectService(connection).get_projects()
        return jsonify({"success": True, "projects": projects})
    except Exception as e:
        logger.error(f"Error al obtener proyectos de Jira: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e), "projects": []}), 500

@jira_bp.route('/validate-project-access', methods=['POST'])
@login_required
def jira_validate_project_access():
    try:
        data = request.get_json() or {}
        project_key = (data.get('project_key') or data.get('projectKey') or '').strip()
        requested_email = (data.get('email') or '').strip()
        role = SessionService.get_current_user_role() or 'usuario'
        session_email = SessionService.get_current_user_email() or ''

        if not project_key:
            return jsonify({'hasAccess': False, 'message': 'project_key es requerido'}), 400

        if role in ['admin', 'analista_qa']:
            return jsonify({'hasAccess': True, 'message': 'Acceso permitido por rol'}), 200

        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        target_email = session_email if session_email else requested_email

        connection = JiraConnection(base_url=jira_config.base_url, email=jira_config.email, api_token=jira_config.token)
        membership = ProjectService(connection).check_user_membership(project_key, target_email)
        return jsonify(membership), 200
    except Exception as e:
        logger.error(f"Error al validar acceso a proyecto Jira: {e}", exc_info=True)
        return jsonify({'hasAccess': False, 'message': f'Error al validar permisos: {str(e)}'}), 500

@jira_bp.route('/project/<project_key>/filter-fields', methods=['GET'])
@login_required
def jira_get_filter_fields(project_key):
    try:
        issuetype = request.args.get('issuetype', None)
        include_all_fields = request.args.get('include_all_fields', 'false').lower() == 'true'
        jira = get_jira_client()
        result = jira.get_filter_fields(project_key, issuetype=issuetype, include_all_fields=include_all_fields)
        available_fields = []
        field_values = {}
        custom_field_values = result.get('custom_field_values', {})
        
        if result.get('status'):
            available_fields.append({'id': 'status', 'name': 'Estado', 'type': 'select', 'custom': False})
            field_values['status'] = result.get('status', [])
        if result.get('priority'):
            available_fields.append({'id': 'priority', 'name': 'Prioridad', 'type': 'select', 'custom': False})
            field_values['priority'] = result.get('priority', [])
        available_fields.append({'id': 'assignee', 'name': 'Asignado', 'type': 'text', 'custom': False})
        field_values['assignee'] = result.get('assignee', [])
        available_fields.append({'id': 'labels', 'name': 'Etiqueta', 'type': 'text', 'custom': False})
        field_values['labels'] = []
        
        standard_fields = [
            {'id': 'reporter', 'name': 'Reportado por', 'type': 'text'},
            {'id': 'fixVersions', 'name': 'Versión de Corrección', 'type': 'select'},
            {'id': 'affectsVersions', 'name': 'Affects Version', 'type': 'select'},
            {'id': 'components', 'name': 'Componentes', 'type': 'select'},
            {'id': 'created', 'name': 'Fecha de Creación', 'type': 'date'},
            {'id': 'updated', 'name': 'Fecha de Actualización', 'type': 'date'},
            {'id': 'resolution', 'name': 'Resolución', 'type': 'select'}
        ]
        all_fields = result.get('all_fields', [])
        for field_info in standard_fields:
            field_id = field_info['id']
            field_vals = custom_field_values.get(field_id, [])
            if any(f.get('id') == field_id for f in all_fields) or (field_id == 'affectsVersions' and field_vals):
                if field_info['type'] in ['text', 'date'] or field_vals:
                    available_fields.append({'id': field_id, 'name': field_info['name'], 'type': field_info['type'], 'custom': False})
                    field_values[field_id] = field_vals if field_vals else []
                    
        for cf in result.get('custom_fields', []):
            field_id, field_name, field_type = cf.get('id'), cf.get('name'), cf.get('type', 'string')
            allowed_values = cf.get('allowedValues') or custom_field_values.get(field_id, [])
            if not include_all_fields and not allowed_values: continue
            input_type = 'select' if allowed_values else ('date' if field_type in ['date','datetime'] else 'number' if field_type in ['number','integer','float'] else 'text')
            available_fields.append({'id': field_id, 'name': field_name, 'type': input_type, 'custom': True})
            field_values[field_id] = allowed_values
            
        return jsonify({'success': True, 'fields': {'available_fields': available_fields, 'field_values': field_values}})
    except Exception as e:
        logger.error(f"Error al obtener campos de filtros: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@jira_bp.route('/project/<project_key>/metrics', methods=['GET'])
@login_required
def jira_get_project_metrics(project_key):
    from app.auth.metrics_routes import get_project_metrics
    return get_project_metrics(project_key)

@jira_bp.route('/project/<project_key>/fields', methods=['GET'])
@login_required
def jira_get_project_fields(project_key):
    try:
        issue_type = request.args.get('issue_type')
        fields_info = get_jira_client().get_project_fields_for_creation(project_key, issue_type)
        if fields_info.get('success'):
            return jsonify({"success": True, "required_fields": fields_info.get('required_fields', []), "optional_fields": fields_info.get('optional_fields', []), "issue_type": fields_info.get('issue_type', '')})
        return jsonify({"success": False, "error": fields_info.get('error', 'Error al obtener campos')}), 400
    except Exception as e:
        logger.error(f"Error al obtener campos del proyecto: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/validate-csv-fields', methods=['POST'])
@login_required
def jira_validate_csv_fields():
    try:
        data = request.get_json()
        csv_columns, project_key, issue_type = data.get('csv_columns', []), data.get('project_key'), data.get('issue_type')
        if not project_key or not csv_columns: return jsonify({"success": False, "error": "Datos incompletos"}), 400
        return jsonify(get_jira_client().validate_csv_fields(csv_columns, project_key, issue_type))
    except Exception as e:
        logger.error(f"Error al validar campos CSV: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/validate-test-case-fields', methods=['POST'])
@login_required
def jira_validate_test_case_fields():
    try:
        data = request.get_json()
        project_key = data.get('project_key', '').strip()
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(jira_config.base_url, jira_config.email, jira_config.token)
        fields_info = ProjectService(connection).get_project_fields_for_creation(project_key, 'Test Case')
        if not fields_info.get('success', True): return jsonify({"success": False, "error": fields_info.get('error')}), 400
        
        required_fields = {
            'summary': ['summary', 'Summary', 'Resumen'],
            'description': ['description', 'Description'],
            'pasos': ['pasos', 'tests Steps', 'Steps'],
            'resultado_esperado': ['resultado esperado', 'Expected Result'],
            'tipo_prueba': ['tipo de prueba', 'tests Type'],
            'nivel_prueba': ['nivel de prueba', 'tests Level'],
            'ambiente': ['ambiente', 'Environment'],
            'tipo_ejecucion': ['tipo de ejecución', 'Execution Type']
        }
        
        def normalize(n):
            import unicodedata, re
            return re.sub(r'[^a-z0-9\s]', '', unicodedata.normalize('NFD', n.lower()).encode('ascii', 'ignore').decode()).strip()
            
        all_fs = fields_info.get('required_fields', []) + fields_info.get('optional_fields', [])
        avail = {normalize(f['name']): f for f in all_fs}
        missing = []
        found = {}
        for k, names in required_fields.items():
            f_found = False
            for n in names:
                if normalize(n) in avail:
                    found[k] = avail[normalize(n)]['name']
                    f_found = True
                    break
            if not f_found: 
                missing.append({
                    "field": k,
                    "possible_names": names
                })
            
        if missing: return jsonify({"success": False, "missing_fields": missing}), 400
        return jsonify({"success": True, "found_fields": found}), 200
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/get-test-case-field-values', methods=['POST'])
@login_required
def get_test_case_field_values():
    try:
        data = request.get_json()
        project_key = data.get('project_key', '').strip()
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(jira_config.base_url, jira_config.email, jira_config.token)
        fields_info = ProjectService(connection).get_project_fields_for_creation(project_key, 'Test Case')
        
        def normalize(n):
            import unicodedata, re
            return re.sub(r'[^a-z0-9\s]', '', unicodedata.normalize('NFD', n.lower()).encode('ascii', 'ignore').decode()).strip()
            
        selects = {
            'tipo_prueba': ['tipo de prueba', 'tipo prueba', 'test type', 'type of test', 'test_type'],
            'nivel_prueba': ['nivel de prueba', 'nivel prueba', 'test level', 'level', 'test_level'],
            'tipo_ejecucion': ['tipo de ejecución', 'tipo de ejecucion', 'execution type', 'execution', 'execution_type'],
            'ambiente': ['ambiente', 'environment', 'env', 'entorno'],
            'ciclo': ['ciclo', 'cycle']
        }
        all_fs = fields_info.get('required_fields', []) + fields_info.get('optional_fields', [])
        
        # Log para depuración
        logger.info(f"Campos disponibles en Jira para Test Case: {[f['name'] for f in all_fs]}")
        
        res = {}
        for k, names in selects.items():
            f_info = {'exists': False, 'values': []}
            for f in all_fs:
                # Normalización robusta
                normalized_fname = normalize(f['name'])
                if any(normalize(n) == normalized_fname for n in names):
                    # Extracción mejorada de valores: Priorizar 'value' sobre 'name' para custom options
                    values_list = []
                    for v in f.get('allowedValues', []):
                        if isinstance(v, dict):
                            val = str(v.get('value', v.get('name', '')))
                            if val:
                                values_list.append({'value': val, 'name': val})
                    
                    f_info = {
                        'exists': True, 
                        'has_values': len(values_list) > 0,
                        'field_name': f['name'], 
                        'field_id': f['id'], 
                        'values': values_list
                    }
                    logger.info(f"Campo encontrado: {k} -> {f['name']} (ID: {f['id']}) - Valores: {len(values_list)}")
                    break
            if not f_info['exists']:
                logger.warning(f"Campo NO encontrado: {k}. Buscado como: {names}")
            res[k] = f_info
        return jsonify({"success": True, "field_values": res}), 200
    except Exception as e: return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/stories/upload-to-jira', methods=['POST'])
@login_required
def upload_stories_to_jira():
    """Sube historias de usuario directamente a Jira"""
    try:
        data = request.get_json()
        stories = data.get('stories', [])
        project_key = data.get('project_key', '').strip()
        assignee_email = data.get('assignee_email', '').strip() or None
        
        if not stories:
            return jsonify({"success": False, "error": "No se proporcionaron historias"}), 400
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(base_url=jira_config.base_url, email=jira_config.email, api_token=jira_config.token)
        issue_service = IssueService(connection, ProjectService(connection))
        
        assignee_account_id = None
        if assignee_email:
            assignee_account_id = issue_service.get_user_account_id_by_email(assignee_email)
            if not assignee_account_id:
                return jsonify({"success": False, "error": f"El correo {assignee_email} no tiene cuenta en Jira"}), 400
        
        csv_data = []
        for story in stories:
            csv_row = {
                'Summary': story.get('summary', 'Sin título'),
                'Description': story.get('description', ''),
                'Issuetype': story.get('issuetype', 'Story'),
                'Priority': story.get('priority', 'Medium')
            }
            if assignee_email:
                csv_row['Asignado'] = assignee_email
            csv_data.append(csv_row)
        
        field_mappings = {
            'Summary': 'summary',
            'Description': 'description',
            'Issuetype': 'issuetype',
            'Priority': 'priority'
        }
        if assignee_email:
            field_mappings['Asignado'] = 'assignee'
        
        results = issue_service.create_issues_from_csv(
            csv_data=csv_data,
            project_key=project_key,
            field_mappings=field_mappings,
            default_values={},
            filter_issue_types=False
        )
        
        txt_content = generate_stories_upload_summary_txt(results, project_key, len(stories))
        txt_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
        
        return jsonify({
            "success": results['success_count'] > 0,
            "message": f"Se crearon {results['success_count']} historias",
            "results": results,
            "txt_content": txt_base64,
            "txt_filename": f"stories_upload_{project_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        })
    except Exception as e:
        logger.error(f"Error al subir historias: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/tests/upload-to-jira', methods=['POST'])
@login_required
def upload_test_cases_to_jira():
    """Sube casos de prueba directamente a Jira"""
    try:
        data = request.get_json()
        test_cases = data.get('test_cases', [])
        project_key = data.get('project_key', '').strip()
        assignee_email = data.get('assignee_email', '').strip() or None
        
        # Valores de campos select desde el modal
        custom_fields_data = data.get('custom_fields', {})
        # Mantener retrocompatibilidad o buscar en custom_fields
        tipo_prueba = custom_fields_data.get('tipo_prueba') or data.get('tipo_prueba', '')
        nivel_prueba = custom_fields_data.get('nivel_prueba') or data.get('nivel_prueba', '')
        tipo_ejecucion = custom_fields_data.get('tipo_ejecucion') or data.get('tipo_ejecucion', '')
        ambiente = custom_fields_data.get('ambiente') or data.get('ambiente', '')
        ciclo = custom_fields_data.get('ciclo') or data.get('ciclo', '')
        
        if not test_cases:
            return jsonify({"success": False, "error": "No se proporcionaron casos de prueba"}), 400
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(base_url=jira_config.base_url, email=jira_config.email, api_token=jira_config.token)
        project_service = ProjectService(connection)
        issue_service = IssueService(connection, project_service)
        
        if assignee_email:
            if not issue_service.get_user_account_id_by_email(assignee_email):
                return jsonify({"success": False, "error": f"Email {assignee_email} no encontrado"}), 400
        
        # Determinar el tipo de issue para casos de prueba
        # 1. Intentar usar lo que venga en el test case individual
        # 2. Si no, buscar un nombre común válido en la lista de tipos del proyecto (si pudiéramos acceder a ella aquí fácilmente, pero para mantenerlo simple usaremos una lista de fallbacks comunes)
        
        default_test_type = 'Test Case'
        
        # Lista de nombres comunes para tipos de issue de prueba
        test_type_candidates = ['Test Case', 'Test', 'QA Task', 'Prueba', 'Caso de Prueba']
        
        # Obtener metadata de campos para mapeo dinámico
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(jira_config.base_url, jira_config.email, jira_config.token)
        
        # Validar issue type para obtener campos
        fields_info = ProjectService(connection).get_project_fields_for_creation(project_key, 'Test Case')
        all_fields = fields_info.get('required_fields', []) + fields_info.get('optional_fields', [])
        
        def normalize(n):
            import unicodedata, re
            return re.sub(r'[^a-z0-9\s]', '', unicodedata.normalize('NFD', n.lower()).encode('ascii', 'ignore').decode()).strip()

        # Diccionario de alias para búsqueda de campos
        field_aliases = {
            'tipo_prueba': ['tipo de prueba', 'test type', 'type of test'],
            'nivel_prueba': ['nivel de prueba', 'test level', 'level'],
            'tipo_ejecucion': ['tipo de ejecución', 'execution type', 'execution'],
            'ambiente': ['ambiente', 'environment', 'env', 'entorno'],
            'pasos': ['pasos', 'steps', 'test steps', 'action', 'pasos de prueba'],
            'resultado_esperado': ['resultado esperado', 'expected result', 'expected results', 'test result'],
            'precondiciones': ['precondiciones', 'preconditions', 'pre-requisites', 'prerrequisitos'],
            'ciclo': ['ciclo', 'cycle']
        }

        # Mapear nombres internos a IDs de Jira encontrados
        jira_field_map = {}
        for internal_key, aliases in field_aliases.items():
            for f in all_fields:
                if any(normalize(alias) == normalize(f['name']) for alias in aliases):
                    jira_field_map[internal_key] = f['id'] # Guardamos ID del campo (customfield_XXXX)
                    break

        logger.info(f"Mapeo de campos detectado: {jira_field_map}")
        
        csv_data = []
        for tc in test_cases:
            raw = tc.get('raw_data', {})
            
            issue_type = tc.get('issuetype')
            if issue_type == 'tests Case':
                issue_type = 'Test Case'
            elif not issue_type:
                issue_type = default_test_type

            csv_row = {
                'Summary': tc.get('summary', 'Sin título'),
                'Description': raw.get('Descripcion', tc.get('description', '')),
                'Issuetype': issue_type,
                'Priority': tc.get('priority', 'Medium')
            }

            # Agregar campos mapeados si existen en Jira
            if 'pasos' in jira_field_map:
                pasos_content = '\n'.join(raw.get('Pasos', raw.get('pasos', [])))
                csv_row['Pasos'] = pasos_content
            
            if 'resultado_esperado' in jira_field_map:
                res_content = '\n'.join(raw.get('Resultado_esperado', []))
                csv_row['Resultado Esperado'] = res_content
                
            if 'precondiciones' in jira_field_map:
                pre_content = raw.get('Precondiciones', tc.get('preconditions', ''))
                csv_row['Precondiciones'] = pre_content

            # Campos de configuración manual (SELECTS)
            if tipo_prueba and 'tipo_prueba' in jira_field_map:
                csv_row['Tipo de Prueba'] = tipo_prueba
            if nivel_prueba and 'nivel_prueba' in jira_field_map:
                csv_row['Nivel de Prueba'] = nivel_prueba
            if ambiente and 'ambiente' in jira_field_map:
                csv_row['Ambiente'] = ambiente
            if tipo_ejecucion and 'tipo_ejecucion' in jira_field_map:
                csv_row['Tipo de Ejecución'] = tipo_ejecucion
            if ciclo and 'ciclo' in jira_field_map:
                csv_row['Ciclo'] = ciclo
                
            if assignee_email:
                csv_row['Asignado'] = assignee_email
            
            csv_data.append(csv_row)
        
        # Construir mappings para issue_service
        field_mappings = {
            'Summary': 'summary',
            'Description': 'description',
            'Issuetype': 'issuetype',
            'Priority': 'priority'
        }
        
        if 'pasos' in jira_field_map: field_mappings['Pasos'] = jira_field_map['pasos']
        if 'resultado_esperado' in jira_field_map: field_mappings['Resultado Esperado'] = jira_field_map['resultado_esperado']
        if 'precondiciones' in jira_field_map: field_mappings['Precondiciones'] = jira_field_map['precondiciones']
        
        if 'tipo_prueba' in jira_field_map: field_mappings['Tipo de Prueba'] = jira_field_map['tipo_prueba']
        if 'nivel_prueba' in jira_field_map: field_mappings['Nivel de Prueba'] = jira_field_map['nivel_prueba']
        if 'ambiente' in jira_field_map: field_mappings['Ambiente'] = jira_field_map['ambiente']
        if 'tipo_ejecucion' in jira_field_map: field_mappings['Tipo de Ejecución'] = jira_field_map['tipo_ejecucion']
        if 'ciclo' in jira_field_map: field_mappings['Ciclo'] = jira_field_map['ciclo']
            
        if assignee_email:
            field_mappings['Asignado'] = 'assignee'

        results = issue_service.create_issues_from_csv(
            csv_data=csv_data,
            project_key=project_key,
            field_mappings=field_mappings,
            default_values={},
            filter_issue_types=False
        )
        txt_content = generate_test_cases_upload_summary_txt(results, project_key, len(test_cases))
        txt_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
        
        return jsonify({
            "success": results['success_count'] > 0,
            "results": results,
            "txt_content": txt_base64,
            "txt_filename": f"test_cases_upload_{project_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        })
    except Exception as e:
        logger.error(f"Error al subir casos de prueba: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/validate-user', methods=['POST'])
@login_required
def jira_validate_user():
    try:
        email = request.get_json().get('email', '').strip()
        if not email: return jsonify({"valid": False}), 400
        
        user = get_user_service().get_user_by_id(get_current_user_id())
        
        # Obtener configuración de Jira (con validación)
        configs = ProjectConfigRepository().get_all(active_only=True)
        
        if configs:
            # Usar la primera configuración activa de la BD
            config = configs[0]
            jira_config = get_jira_token_manager().get_token_for_user(user, config.project_key)
            connection = JiraConnection(jira_config.base_url, jira_config.email, jira_config.token)
        elif Config.JIRA_BASE_URL and Config.JIRA_EMAIL and Config.JIRA_API_TOKEN:
            # Fallback: usar configuración del .env si no hay en BD
            connection = JiraConnection(
                base_url=Config.JIRA_BASE_URL,
                email=Config.JIRA_EMAIL,
                api_token=Config.JIRA_API_TOKEN
            )
        else:
            return jsonify({
                "valid": False, 
                "error": "No hay configuración de Jira disponible. Configura Jira en el sistema."
            }), 400
        
        acc_id = IssueService(connection, None).get_user_account_id_by_email(email)
        return jsonify({"valid": bool(acc_id), "accountId": acc_id, "email": email}), 200
    except Exception as e: 
        logger.error(f"Error al validar usuario en Jira: {e}", exc_info=True)
        return jsonify({"valid": False, "error": str(e)}), 500

@jira_bp.route('/upload-csv', methods=['POST'])
@login_required
def jira_upload_csv():
    """Procesa un archivo CSV y crea issues en Jira"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No se proporcionó ningún archivo"}), 400
        
        file = request.files['file']
        project_key = request.form.get('project_key')
        field_mappings_raw = request.form.get('field_mappings')
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        
        # Leer el CSV con detección de encoding (versión robusta)
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
        csv_data = None
        for enc in encodings:
            try:
                file.stream.seek(0)
                stream = io.TextIOWrapper(file.stream, encoding=enc, errors='replace')
                csv_data = list(csv.DictReader(stream))
                if csv_data: break
            except: continue
            
        if not csv_data:
            return jsonify({"success": False, "error": "No se pudo leer el CSV"}), 400
        
        field_mappings = {}
        if field_mappings_raw:
            raw_map = json.loads(field_mappings_raw)
            for k, v in raw_map.items():
                if isinstance(v, dict): field_mappings[k] = v.get('jira_field_id')
                else: field_mappings[k] = v
        
        client = get_jira_client(base_url=jira_config.base_url, email=jira_config.email, api_token=jira_config.token)
        results = client.create_issues_from_csv(csv_data, project_key, field_mappings, filter_issue_types=False)
        
        # Métricas y resumen
        issue_types_distribution = {}
        for created in results.get('created', []):
            it = created.get('issue_type', 'Unknown')
            issue_types_distribution[it] = issue_types_distribution.get(it, 0) + 1
        results['issue_types_distribution'] = issue_types_distribution
        
        txt_content = generate_upload_summary_txt(file.filename, results, project_key)
        txt_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
        
        # Guardar en base de datos local
        try:
            upload_repo = BulkUploadRepository()
            upload_repo.create(BulkUpload(
                user_id=get_current_user_id(),
                project_key=project_key,
                upload_type='csv_upload',
                total_items=results['total'],
                successful_items=results['success_count'],
                failed_items=results['error_count'],
                upload_details=json.dumps({'filename': file.filename, 'issue_types_distribution': issue_types_distribution})
            ))
        except Exception as e:
            logger.error(f"Error al guardar historial local: {e}")
            
        return jsonify({
            "success": results['success_count'] > 0,
            "results": results,
            "txt_content": txt_base64,
            "txt_filename": file.filename.replace('.csv', '') + '.txt'
        })
    except Exception as e:
        logger.error(f"Error en upload_csv: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/download-report', methods=['POST'])
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
            
        # Procesar datos de tablas y calcular totales
        test_cases_all = table_data.get('test_cases_by_person', [])
        defects_all = table_data.get('defects_by_person', [])
        
        # Calcular totales para casos de prueba
        test_cases_totals = {
            'exitoso': sum(item.get('exitoso', 0) for item in test_cases_all),
            'en_progreso': sum(item.get('en_progreso', 0) for item in test_cases_all),
            'fallado': sum(item.get('fallado', 0) for item in test_cases_all),
            'total': sum(item.get('total', 0) for item in test_cases_all)
        }
        
        items_per_page = 20
        test_cases_paginated = test_cases_all[:items_per_page]
        defects_paginated = defects_all[:items_per_page]
        
        # Preparar objetos de paginación para el template
        test_cases_pagination = {
            'current_page': 1,
            'total_pages': (len(test_cases_all) + items_per_page - 1) // items_per_page if test_cases_all else 1,
            'total_items': len(test_cases_all),
            'start_item': 1 if test_cases_all else 0,
            'end_item': len(test_cases_paginated)
        }
        
        defects_pagination = {
            'current_page': 1,
            'total_pages': (len(defects_all) + items_per_page - 1) // items_per_page if defects_all else 1,
            'total_items': len(defects_all),
            'start_item': 1 if defects_all else 0,
            'end_item': len(defects_paginated)
        }
        
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
        
        # Guardar historial local
        try:
            JiraReportRepository().create(JiraReport(
                user_id=get_current_user_id(),
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
            
        return Response(
            pdf_buffer,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=reporte_{project_key}_{datetime.now().strftime("%Y%m%d")}.pdf'}
        )
    except Exception as e:
        logger.error(f"Error al generar reporte: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@jira_bp.route('/download-template', methods=['GET'])
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
