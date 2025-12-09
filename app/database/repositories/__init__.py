"""
Repositorios para acceso a datos
Responsabilidad única: Abstracción de acceso a base de datos (DIP)
"""
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.project_config_repository import ProjectConfigRepository
from app.database.repositories.user_jira_config_repository import UserJiraConfigRepository
from app.database.repositories.user_story_repository import UserStoryRepository
from app.database.repositories.test_case_repository import TestCaseRepository
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.database.repositories.bulk_upload_repository import BulkUploadRepository

__all__ = [
    'UserRepository',
    'ProjectConfigRepository',
    'UserJiraConfigRepository',
    'UserStoryRepository',
    'TestCaseRepository',
    'JiraReportRepository',
    'BulkUploadRepository'
]



