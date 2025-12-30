from flask import Blueprint, jsonify, request
import logging
from app.auth.decorators import login_required, get_current_user_id
from app.auth.session_service import SessionService
from app.services.jira_token_manager import JiraTokenManager
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.core.config import Config
from app.utils.decorators import handle_errors
from app.core.dependencies import get_user_service, get_jira_token_manager, get_jira_client

logger = logging.getLogger(__name__)

jira_conn_bp = Blueprint('jira_connection', __name__)

@jira_conn_bp.route('/test-connection', methods=['GET'])
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

@jira_conn_bp.route('/projects', methods=['GET'])
@login_required
def jira_get_projects():
    """Obtiene la lista de proyectos de Jira"""
    try:
        user_id = get_current_user_id()
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado", "projects": []}), 401
        
        from app.database.repositories.project_config_repository import ProjectConfigRepository
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

@jira_conn_bp.route('/validate-project-access', methods=['POST'])
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
