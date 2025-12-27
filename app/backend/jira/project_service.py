"""
Servicio para operaciones relacionadas con proyectos de Jira
Responsabilidad única: Gestionar información y configuración de proyectos
Refactorizado para delegar en ProjectFetcher, ProjectValidator y ProjectCache.
"""
import logging
from typing import Dict, List, Optional

from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_fetcher import ProjectFetcher
from app.backend.jira.project_validator import ProjectValidator
from app.backend.jira.project_cache import ProjectCache

logger = logging.getLogger(__name__)


class ProjectService:
    """Servicio para operaciones relacionadas con proyectos de Jira"""
    
    def __init__(self, connection: JiraConnection):
        """
        Inicializa el servicio de proyectos
        
        Args:
            connection: Conexión con Jira (inyección de dependencias)
        """
        self._connection = connection
        
        # Inicializar componentes
        self.fetcher = ProjectFetcher(connection)
        self.validator = ProjectValidator(self.fetcher)
        self.cache = ProjectCache(self.fetcher, self.validator)
    
    def get_projects(self) -> List[Dict]:
        """
        Obtiene la lista de proyectos de Jira
        
        Returns:
            List[Dict]: Lista de proyectos formateados
        """
        return self.cache.get_projects()
    
    def get_issue_types(self, project_key: str, use_createmeta: bool = False, filter_types: bool = True) -> List[Dict]:
        """
        Obtiene los tipos de issue disponibles para un proyecto
        
        Args:
            project_key: Clave del proyecto
            use_createmeta: Si es True, usa createmeta API (más lento pero obtiene todos los issuetypes)
            filter_types: Si es True, filtra solo tests Cases y Bugs. Si es False, retorna todos los tipos.
            
        Returns:
            List[Dict]: Lista de tipos de issue
        """
        return self.cache.get_issue_types(project_key, use_createmeta, filter_types)
    
    def get_filter_fields(self, project_key: str, issuetype: str = None, include_all_fields: bool = False) -> Dict:
        """
        Obtiene los campos disponibles para filtros y sus valores
        
        Args:
            project_key: Clave del proyecto
            issuetype: Tipo de issue opcional para filtrar campos específicos
            include_all_fields: Si es True, incluye todos los campos incluso sin valores permitidos
            
        Returns:
            Dict: Campos disponibles para filtros
        """
        return self.cache.get_filter_fields(project_key, issuetype, include_all_fields)
    
    def get_project_fields_for_creation(self, project_key: str, issue_type: str = None, combine_test_cases_and_stories: bool = False) -> Dict:
        """
        Obtiene los campos disponibles para crear un issue en un proyecto
        
        Args:
            project_key: Clave del proyecto
            issue_type: Tipo de issue (opcional)
            combine_test_cases_and_stories: Si es True y issue_type es None, combina campos de tests Cases y Stories
            
        Returns:
            Dict: Campos disponibles para creación
        """
        return self.cache.get_project_fields_for_creation(project_key, issue_type, combine_test_cases_and_stories)

    def check_user_membership(self, project_key: str, user_email: str) -> Dict:
        """
        Valida si un usuario es asignable (miembro) en un proyecto Jira.
        """
        return self.validator.check_user_membership(project_key, user_email)
