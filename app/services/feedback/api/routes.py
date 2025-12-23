from flask import Blueprint, jsonify, request
import logging
from app.auth.decorators import login_required, get_current_user_id
from app.auth.user_service import UserService
from app.services.jira_token_manager import JiraTokenManager
from app.backend.jira.connection import JiraConnection
from app.services.feedback_service import FeedbackService
from app.utils.decorators import handle_errors

logger = logging.getLogger(__name__)

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

@feedback_bp.route('/validate-project', methods=['POST'])
@login_required
@handle_errors("Error al validar proyecto", status_code=500)
def feedback_validate_project():
    try:
        from app.core.dependencies import get_user_service, get_jira_token_manager, get_feedback_service
        data = request.get_json()
        project_key = data.get('project_key', '').strip()
        if not project_key: return jsonify({"success": False, "error": "Falta project_key"}), 400
        
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(jira_config.base_url, jira_config.email, jira_config.token)
        
        valid = get_feedback_service(connection).validate_project(project_key)
        return jsonify({"success": True, "valid": valid})
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@feedback_bp.route('/submit', methods=['POST'])
@login_required
@handle_errors("Error al enviar feedback", status_code=500)
def feedback_submit():
    try:
        from app.core.dependencies import get_user_service, get_jira_token_manager, get_feedback_service
        data = request.get_json()
        project_key, issue_type, summary, description = data.get('project_key'), data.get('issue_type'), data.get('summary'), data.get('description')
        if not all([project_key, issue_type, summary, description]): return jsonify({"success": False, "error": "Datos incompletos"}), 400
        
        user = get_user_service().get_user_by_id(get_current_user_id())
        jira_config = get_jira_token_manager().get_token_for_user(user, project_key)
        connection = JiraConnection(jira_config.base_url, jira_config.email, jira_config.token)
        
        result = get_feedback_service(connection).create_feedback_issue(project_key, issue_type, summary, description, user.email)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
