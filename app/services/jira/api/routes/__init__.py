from flask import Blueprint
import logging

# Import sub-blueprints using relative imports
from .jira_connection import jira_conn_bp
from .jira_fields import jira_fields_bp
from .jira_upload import jira_upload_bp
from .jira_reports import jira_reports_bp
from .jira_validation import jira_validation_bp

logger = logging.getLogger(__name__)

# Main Blueprint for Jira Services
# This is what's imported by app/core/app.py via 'from app.services.jira.api.routes import jira_bp'
jira_bp = Blueprint('jira', __name__, url_prefix='/api/jira')

# Register sub-blueprints
jira_bp.register_blueprint(jira_conn_bp)
jira_bp.register_blueprint(jira_fields_bp)
jira_bp.register_blueprint(jira_upload_bp)
jira_bp.register_blueprint(jira_reports_bp)
jira_bp.register_blueprint(jira_validation_bp)

__all__ = ['jira_bp']
