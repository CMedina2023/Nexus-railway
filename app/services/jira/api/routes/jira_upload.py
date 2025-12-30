from flask import Blueprint, jsonify, request
import logging
import json
import io
import csv
import base64
from datetime import datetime
from app.auth.decorators import login_required, get_current_user_id
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_service import IssueService
from app.database.repositories.bulk_upload_repository import BulkUploadRepository
from app.models.bulk_upload import BulkUpload
from app.core.dependencies import get_user_service, get_jira_token_manager, get_jira_client
from app.services.jira.api.helpers import (
    generate_upload_summary_txt, 
    generate_stories_upload_summary_txt, 
    generate_test_cases_upload_summary_txt
)
from app.services.jira.utils.text_normalizer import normalize

logger = logging.getLogger(__name__)

jira_upload_bp = Blueprint('jira_upload', __name__)

@jira_upload_bp.route('/stories/upload-to-jira', methods=['POST'])
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

@jira_upload_bp.route('/tests/upload-to-jira', methods=['POST'])
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
        
        fields_info = project_service.get_project_fields_for_creation(project_key, 'Test Case')
        all_fields = fields_info.get('required_fields', []) + fields_info.get('optional_fields', [])
        
        jira_field_map = _get_jira_field_map(all_fields)
        logger.info(f"Mapeo de campos detectado: {jira_field_map}")
        
        csv_data = _prepare_test_case_csv_data(
            test_cases, jira_field_map, assignee_email, 
            tipo_prueba, nivel_prueba, ambiente, tipo_ejecucion, ciclo
        )
        
        field_mappings = _get_test_case_field_mappings(jira_field_map, assignee_email)

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

def _get_jira_field_map(all_fields):
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
    jira_field_map = {}
    for internal_key, aliases in field_aliases.items():
        for f in all_fields:
            if any(normalize(alias) == normalize(f['name']) for alias in aliases):
                jira_field_map[internal_key] = f['id']
                break
    return jira_field_map

def _prepare_test_case_csv_data(test_cases, jira_field_map, assignee_email, tipo_prueba, nivel_prueba, ambiente, tipo_ejecucion, ciclo):
    csv_data = []
    default_test_type = 'Test Case'
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

        if 'pasos' in jira_field_map:
            pasos_content = '\n'.join(raw.get('Pasos', raw.get('pasos', [])))
            csv_row['Pasos'] = pasos_content
        
        if 'resultado_esperado' in jira_field_map:
            res_content = '\n'.join(raw.get('Resultado_esperado', []))
            csv_row['Resultado Esperado'] = res_content
            
        if 'precondiciones' in jira_field_map:
            pre_content = raw.get('Precondiciones', tc.get('preconditions', ''))
            csv_row['Precondiciones'] = pre_content

        if tipo_prueba and 'tipo_prueba' in jira_field_map: csv_row['Tipo de Prueba'] = tipo_prueba
        if nivel_prueba and 'nivel_prueba' in jira_field_map: csv_row['Nivel de Prueba'] = nivel_prueba
        if ambiente and 'ambiente' in jira_field_map: csv_row['Ambiente'] = ambiente
        if tipo_ejecucion and 'tipo_ejecucion' in jira_field_map: csv_row['Tipo de Ejecución'] = tipo_ejecucion
        if ciclo and 'ciclo' in jira_field_map: csv_row['Ciclo'] = ciclo
            
        if assignee_email:
            csv_row['Asignado'] = assignee_email
        
        csv_data.append(csv_row)
    return csv_data

def _get_test_case_field_mappings(jira_field_map, assignee_email):
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
    return field_mappings

@jira_upload_bp.route('/upload-csv', methods=['POST'])
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
        
        # Leer el CSV con detección de encoding
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
