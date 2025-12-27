"""
Componente para realizar peticiones HTTP a Jira relacionadas con proyectos
"""
import logging
from typing import Dict, List, Optional
from app.backend.jira.connection import JiraConnection
from app.core.config import Config

logger = logging.getLogger(__name__)

class ProjectFetcher:
    """Componente responsable de las peticiones a la API de Jira"""
    
    def __init__(self, connection: JiraConnection):
        self._connection = connection

    def fetch_projects(self) -> Optional[List[Dict]]:
        """Obtiene la lista cruda de proyectos"""
        try:
            url = f"{self._connection.base_url}/rest/api/3/project"
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error al obtener proyectos: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error al obtener proyectos: {str(e)}")
            return None

    def fetch_global_issue_types(self) -> Optional[List[Dict]]:
        """Obtiene issuetypes del endpoint global"""
        try:
            url = f"{self._connection.base_url}/rest/api/3/issuetype"
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Error al obtener issuetypes globales: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.warning(f"Error al obtener issuetypes globales: {str(e)}")
            return None

    def fetch_project_issue_types(self, project_key: str) -> Optional[List[Dict]]:
        """Obtiene proyecto y sus issuetypes"""
        try:
            url = f"{self._connection.base_url}/rest/api/3/project/{project_key}"
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error al obtener tipos de issue: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error al obtener tipos de issue para {project_key}: {str(e)}")
            return None

    def fetch_project_statuses(self, project_key: str) -> Optional[List[Dict]]:
        """Obtiene estados del proyecto"""
        try:
            status_url = f"{self._connection.base_url}/rest/api/3/project/{project_key}/statuses"
            response = self._connection.session.get(status_url, timeout=Config.JIRA_TIMEOUT_SHORT)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Error al obtener estados: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.warning(f"Error al obtener estados: {str(e)}")
            return None

    def fetch_priorities(self) -> Optional[List[Dict]]:
        """Obtiene prioridades globales"""
        try:
            priority_url = f"{self._connection.base_url}/rest/api/3/priority"
            response = self._connection.session.get(priority_url, timeout=Config.JIRA_TIMEOUT_SHORT)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Error al obtener prioridades: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.warning(f"Error al obtener prioridades: {str(e)}")
            return None

    def fetch_project_versions(self, project_key: str) -> Optional[List[Dict]]:
        """Obtiene versiones del proyecto"""
        try:
            versions_url = f"{self._connection.base_url}/rest/api/3/project/{project_key}/versions"
            response = self._connection.session.get(versions_url, timeout=Config.JIRA_TIMEOUT_SHORT)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Error al obtener versiones del proyecto: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error al obtener versiones del proyecto: {str(e)}", exc_info=True)
            return None

    def fetch_all_fields(self) -> Optional[List[Dict]]:
        """Obtiene todos los campos del sistema"""
        try:
            fields_url = f"{self._connection.base_url}/rest/api/3/field"
            response = self._connection.session.get(fields_url, timeout=Config.JIRA_TIMEOUT_SHORT)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Error al obtener todos los campos: {response.status_code}")
            return None
        except Exception as e:
            logger.warning(f"Error al obtener todos los campos: {str(e)}")
            return None

    def fetch_createmeta(self, project_key: str, issue_type_names: Optional[str] = None) -> Optional[Dict]:
        """Obtiene metadatos de creación (createmeta)"""
        try:
            url = f"{self._connection.base_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes.fields"
            if issue_type_names:
                url += f"&issuetypeNames={issue_type_names}"
            
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_LONG)
            if response.status_code == 200:
                return response.json()
            
            # Nota: El servicio original retorna estructura de error en algunos casos o None en otros
            # Aquí retornamos None para indicar fallo de red/http, el consumidor manejará errores
            logger.warning(f"Error en createmeta: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.warning(f"Error al obtener valores de campos desde createmeta: {str(e)}")
            return None

    def search_assignable_users(self, project_key: str, query: str) -> Optional[List[Dict]]:
        """Busca usuarios asignables en un proyecto"""
        try:
            url = f"{self._connection.base_url}/rest/api/3/user/assignable/search"
            params = {
                'project': project_key,
                'query': query,
                'maxResults': 200
            }
            response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_SHORT)
            if response.status_code == 200:
                return response.json()
            logger.error(f"Error al validar membresía en {project_key}: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error al validar membresía en proyecto {project_key}: {e}", exc_info=True)
            return None
