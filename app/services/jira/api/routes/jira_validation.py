from flask import Blueprint, jsonify, request
import logging
from app.auth.decorators import login_required, get_current_user_id
from app.backend.jira.connection import JiraConnection
from app.backend.jira.issue_service import IssueService
from app.database.repositories.project_config_repository import ProjectConfigRepository
from app.core.config import Config
from app.core.dependencies import get_user_service, get_jira_token_manager

logger = logging.getLogger(__name__)

jira_validation_bp = Blueprint('jira_validation', __name__)

@jira_validation_bp.route('/validate-user', methods=['POST'])
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
