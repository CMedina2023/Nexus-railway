"""
Modelos de datos del sistema
Responsabilidad única: Definir estructuras de datos
"""
from app.models.user import User
from app.models.project_config import ProjectConfig
from app.models.user_jira_config import UserJiraConfig
from app.models.user_story import UserStory
from app.models.test_case import TestCase
from app.models.jira_report import JiraReport
from app.models.bulk_upload import BulkUpload
from app.models.project_context import ProjectContext
from app.models.project_document import ProjectDocument
from app.models.requirement import Requirement
from app.models.requirement_coverage import RequirementCoverage
from app.models.traceability_link import TraceabilityLink

__all__ = [
    'User',
    'ProjectConfig',
    'UserJiraConfig',
    'UserStory',
    'TestCase',
    'JiraReport',
    'BulkUpload',
    'ProjectContext',
    'ProjectDocument',
    'Requirement',
    'RequirementCoverage',
    'TraceabilityLink'
]
