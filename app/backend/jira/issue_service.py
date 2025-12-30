"""
Servicio para operaciones relacionadas con issues de Jira
Responsabilidad única: Fachada para gestión de issues (creación y consulta)
Refactorizado para delegar en:
- issue_creator.py
- issue_fetcher.py
- field_validator.py
- cache_manager.py
"""
import logging
from typing import Dict, List, Optional
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_fetcher import IssueFetcher, build_issuetype_jql, TEST_CASE_VARIATIONS, BUG_VARIATIONS, STORY_VARIATIONS
from app.backend.jira.issue_creator import IssueCreator
from app.backend.jira.rate_limiter import IssueCreationRateLimiter
from app.backend.jira.csv_issue_processor import CSVIssueProcessor
from app.backend.jira.field_validator import FieldValidator
from app.backend.jira.cache_manager import FieldMetadataCache

logger = logging.getLogger(__name__)

# Re-exportar constantes y clases auxiliares por compatibilidad
TEST_CASE_VARIATIONS = TEST_CASE_VARIATIONS
BUG_VARIATIONS = BUG_VARIATIONS
STORY_VARIATIONS = STORY_VARIATIONS
build_issuetype_jql = build_issuetype_jql
FieldMetadataCache = FieldMetadataCache
IssueCreationRateLimiter = IssueCreationRateLimiter

class IssueService:
    """Servicio para operaciones relacionadas con issues de Jira (Fachada)"""
    
    def __init__(self, connection: JiraConnection, project_service: ProjectService):
        """
        Inicializa el servicio de issues
        
        Args:
            connection: Conexión con Jira (inyección de dependencias)
            project_service: Servicio de proyectos (inyección de dependencias)
        """
        self._connection = connection
        self._project_service = project_service
        
        # Inicializar componentes
        # Fetcher maneja la caché de metadata internamente
        self._fetcher = IssueFetcher(connection)
        
        # Creator usa el fetcher para validaciones
        self._creator = IssueCreator(connection, project_service, self._fetcher)
        
        # Processor para carga masiva (delegación)
        self._csv_processor = CSVIssueProcessor(connection, project_service, self._fetcher, self._creator)
        
        # Exponer componentes internos si es necesario (preferiblemente no usar directamente)
        self._field_metadata_cache = self._fetcher._field_metadata_cache 
        self._rate_limiter = self._creator._rate_limiter

    def get_issues_by_type(self, project_key: str, issue_type: str, max_results: int = None) -> List[Dict]:
        """Obtiene issues de un tipo específico para un proyecto"""
        return self._fetcher.get_issues_by_type(project_key, issue_type, max_results)
    
    def get_all_issues(self, project_key: str, max_results: int = None) -> List[Dict]:
        """Obtiene todas las issues de un proyecto"""
        return self._fetcher.get_all_issues(project_key, max_results)
    
    def get_issues_by_assignee(self, project_key: str, assignee_email: str, max_results: int = None) -> List[Dict]:
        """Obtiene issues asignadas a un usuario específico"""
        return self._fetcher.get_issues_by_assignee(project_key, assignee_email, max_results)
    
    def get_user_account_id_by_email(self, email: str) -> Optional[str]:
        """Busca el accountId de un usuario por su email en Jira"""
        return self._fetcher.get_user_account_id_by_email(email)
    
    def create_issue(self, project_key: str, issue_type: str, summary: str, description: str = None,
                     assignee: str = None, priority: str = None, labels: List[str] = None,
                     custom_fields: Dict = None, field_schemas: Dict = None) -> Dict:
        """Crea un issue en Jira"""
        return self._creator.create_issue(
            project_key, issue_type, summary, description, assignee, priority, labels, 
            custom_fields, field_schemas
        )
    
    def create_issues_from_csv(self, csv_data: List[Dict], project_key: str, 
                               field_mappings: Dict = None, default_values: Dict = None,
                               filter_issue_types: bool = True) -> Dict:
        """Crea múltiples issues en Jira desde datos CSV"""
        return self._csv_processor.create_issues_from_csv(
            csv_data, project_key, field_mappings, default_values, filter_issue_types
        )
        
    def normalize_issue_type(self, csv_type: str, available_types: List[Dict]) -> Optional[str]:
        """Normaliza el nombre del tipo de issue"""
        return FieldValidator.normalize_issue_type(csv_type, available_types)
    
    def _get_available_fields_metadata(self, project_key: str, issue_type: str, use_cache: bool = True) -> Optional[Dict]:
        """Wrapper para obtener metadata de campos (método privado legado)"""
        return self._fetcher.get_available_fields_metadata(project_key, issue_type, use_cache)

    def _format_field_value_by_type(self, field_id: str, field_value: str, field_schema: Dict = None, allowed_values: List = None):
        """Wrapper legado"""
        return FieldValidator.format_field_value_by_type(field_id, field_value, field_schema, allowed_values)

    def _format_description_to_adf(self, description: str) -> Dict:
        """Wrapper legado"""
        return FieldValidator.format_description_to_adf(description)

    def _validate_and_filter_custom_fields(self, custom_fields: Dict, available_fields_metadata: Dict, row_idx: int):
        """Wrapper legado"""
        return FieldValidator.validate_and_filter_custom_fields(custom_fields, available_fields_metadata, row_idx)
