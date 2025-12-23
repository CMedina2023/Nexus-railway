from __future__ import annotations
"""
Módulo para gestión de dependencias (DIP)
Proporciona instancias de servicios con sus dependencias inyectadas
"""
from app.auth.user_service import UserService
from app.auth.password_service import PasswordService
from app.auth.encryption_service import EncryptionService
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.project_config_repository import ProjectConfigRepository
from app.database.repositories.user_jira_config_repository import UserJiraConfigRepository
from app.services.jira_token_manager import JiraTokenManager
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_service import IssueService
from app.backend.jira.metrics_calculator import MetricsCalculator
from app.backend.jira.jira_client_wrapper import JiraClient
from app.services.file_manager import FileManager
from app.services.data_transformer import DataTransformer
from app.services.text_processor import TextProcessor
from app.services.validator import Validator
from app.services.file_generator import FileGenerator
from app.services.generation_orchestrator import GenerationOrchestrator
from app.services.feedback_service import FeedbackService
from app.services.pdf.infrastructure.playwright_generator import PlaywrightPdfGenerator
from app.services.pdf.infrastructure.weasyprint_generator import WeasyPrintPdfGenerator
from app.services.pdf.application.pdf_service import PdfService

def get_user_service() -> UserService:
    """Retorna una instancia de UserService con sus dependencias"""
    return UserService(UserRepository(), PasswordService())

def get_jira_token_manager() -> JiraTokenManager:
    """Retorna una instancia de JiraTokenManager con sus dependencias"""
    return JiraTokenManager(
        EncryptionService(),
        ProjectConfigRepository(),
        UserJiraConfigRepository()
    )

def get_encryption_service() -> EncryptionService:
    """Retorna una instancia de EncryptionService"""
    return EncryptionService()

def get_jira_client(base_url=None, email=None, api_token=None) -> JiraClient:
    """Retorna una instancia de JiraClient con sus dependencias"""
    connection = JiraConnection(base_url, email, api_token)
    project_service = ProjectService(connection)
    issue_service = IssueService(connection, project_service)
    metrics_calculator = MetricsCalculator()
    
    return JiraClient(
        connection=connection,
        project_service=project_service,
        issue_service=issue_service,
        metrics_calculator=metrics_calculator
    )

def get_feedback_service(connection: JiraConnection) -> FeedbackService:
    """Retorna una instancia de FeedbackService con sus dependencias"""
    project_service = ProjectService(connection)
    issue_service = IssueService(connection, project_service)
    return FeedbackService(connection, project_service, issue_service)

def get_pdf_service() -> PdfService:
    """Retorna una instancia de PdfService con sus dependencias"""
    return PdfService(PlaywrightPdfGenerator(), WeasyPrintPdfGenerator())

def get_file_manager(upload_folder: str) -> FileManager:
    """Retorna una instancia de FileManager"""
    return FileManager(upload_folder)

def get_data_transformer() -> DataTransformer:
    """Retorna una instancia de DataTransformer con su procesador de texto"""
    return DataTransformer(TextProcessor())

def get_validator() -> Validator:
    """Retorna una instancia de Validator"""
    return Validator()

def get_file_generator() -> FileGenerator:
    """Retorna una instancia de FileGenerator"""
    return FileGenerator()

def get_generation_orchestrator(file_manager: FileManager) -> GenerationOrchestrator:
    """Retorna una instancia de GenerationOrchestrator con sus dependencias"""
    return GenerationOrchestrator(
        file_manager=file_manager,
        data_transformer=get_data_transformer(),
        validator=get_validator(),
        file_generator=get_file_generator()
    )
