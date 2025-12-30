from flask import Blueprint, jsonify, request
import logging
from app.auth.decorators import login_required, get_current_user_id
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.core.dependencies import get_user_service, get_jira_token_manager, get_jira_client
from app.services.jira.utils.text_normalizer import normalize

logger = logging.getLogger(__name__)

jira_fields_bp = Blueprint('jira_fields', __name__)

@jira_fields_bp.route('/project/<project_key>/filter-fields', methods=['GET'])
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

@jira_fields_bp.route('/project/<project_key>/metrics', methods=['GET'])
@login_required
def jira_get_project_metrics(project_key):
    from app.auth.metrics_routes import get_project_metrics
    return get_project_metrics(project_key)

@jira_fields_bp.route('/project/<project_key>/fields', methods=['GET'])
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

@jira_fields_bp.route('/validate-csv-fields', methods=['POST'])
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

@jira_fields_bp.route('/validate-test-case-fields', methods=['POST'])
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

@jira_fields_bp.route('/get-test-case-field-values', methods=['POST'])
@login_required
def get_test_case_field_values():
    try:
        data = request.get_json()
        project_key = data.get('project_key', '').strip()
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(jira_config.base_url, jira_config.email, jira_config.token)
        fields_info = ProjectService(connection).get_project_fields_for_creation(project_key, 'Test Case')
        
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
