import logging
from typing import Dict, List, Optional
from app.backend.jira.connection import JiraConnection
from app.backend.jira.cache_manager import FieldMetadataCache
from app.core.config import Config

logger = logging.getLogger(__name__)

# Variaciones comunes de nombres para tipos de issues
TEST_CASE_VARIATIONS = [
    'tests Case', 'tests case', 'test case', 'TestCase', 'Testcase',
    'Caso de Prueba', 'Caso de prueba', 'Caso De Prueba', 'TEST CASE'
]

BUG_VARIATIONS = [
    'Bug', 'bug', 'BUG', 'Error', 'error', 'Defect', 'defect'
]

STORY_VARIATIONS = [
    'Story', 'story', 'STORY', 'Historia', 'historia',
    'User Story', 'user story', 'USER STORY'
]

def build_issuetype_jql(issue_type: str, project_key: str) -> str:
    """
    Construye un JQL que busca un tipo de issue considerando todas sus variaciones posibles
    """
    issue_type_lower = issue_type.lower()
    
    if 'test' in issue_type_lower and 'case' in issue_type_lower:
        variations = TEST_CASE_VARIATIONS
    elif 'bug' in issue_type_lower or issue_type_lower == 'error' or issue_type_lower == 'defect':
        variations = BUG_VARIATIONS
    else:
        variations = [issue_type]
    
    issuetype_conditions = ' OR '.join([f'issuetype = "{var}"' for var in variations])
    jql = f'project = {project_key} AND ({issuetype_conditions})'
    
    logger.info(f"JQL generado con variaciones para '{issue_type}': {jql}")
    return jql

class IssueFetcher:
    """Clase encargada de la consulta de issues en Jira"""

    def __init__(self, connection: JiraConnection, cache: FieldMetadataCache = None):
        self._connection = connection
        self._field_metadata_cache = cache or FieldMetadataCache()

    def get_issues_by_type(self, project_key: str, issue_type: str, max_results: int = None) -> List[Dict]:
        """
        Obtiene issues de un tipo específico para un proyecto
        """
        if max_results is None:
            max_results = 1000
        
        all_issues = []
        start_at = 0
        
        try:
            jql = build_issuetype_jql(issue_type, project_key)
            url = f"{self._connection.base_url}/rest/api/3/search/jql"
            
            while True:
                params = {
                    'jql': jql,
                    'startAt': start_at,
                    'maxResults': max_results,
                    'fields': 'summary,status,assignee,created,updated,priority,resolution,issuetype'
                }
                
                response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_LONG)
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    total = data.get('total', 0)
                    
                    all_issues.extend(issues)
                    logger.info(f"Obtenidos {len(issues)} {issue_type} (total acumulado: {len(all_issues)}/{total})")
                    
                    if len(all_issues) >= total or len(issues) == 0:
                        break
                    start_at += len(issues)
                else:
                    logger.error(f"Error al obtener {issue_type}: {response.status_code} - {response.text}")
                    break
                    
            logger.info(f"Total de {issue_type} obtenidos: {len(all_issues)}")
            return all_issues
            
        except Exception as e:
            logger.error(f"Error al obtener {issue_type} para {project_key}: {str(e)}")
            return all_issues

    def get_all_issues(self, project_key: str, max_results: int = None) -> List[Dict]:
        """Obtiene todas las issues de un proyecto"""
        if max_results is None:
            max_results = 1000
        
        all_issues = []
        start_at = 0
        
        try:
            jql = f'project = {project_key}'
            url = f"{self._connection.base_url}/rest/api/3/search/jql"
            
            while True:
                params = {
                    'jql': jql,
                    'startAt': start_at,
                    'maxResults': max_results,
                    'fields': 'summary,status,issuetype'
                }
                
                response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_LONG)
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    total = data.get('total', 0)
                    
                    all_issues.extend(issues)
                    logger.info(f"Obtenidas {len(issues)} issues (total acumulado: {len(all_issues)}/{total})")
                    
                    if len(all_issues) >= total or len(issues) == 0:
                        break
                    start_at += len(issues)
                else:
                    logger.error(f"Error al obtener todas las issues: {response.status_code} - {response.text}")
                    break
                    
            logger.info(f"Total de issues obtenidas: {len(all_issues)}")
            return all_issues
            
        except Exception as e:
            logger.error(f"Error al obtener todas las issues para {project_key}: {str(e)}")
            return all_issues

    def get_issues_by_assignee(self, project_key: str, assignee_email: str, max_results: int = None) -> List[Dict]:
        """Obtiene issues asignadas a un usuario específico"""
        if max_results is None:
            max_results = 1000
        
        all_issues = []
        start_at = 0
        
        try:
            jql = f'project = {project_key} AND assignee = "{assignee_email}"'
            url = f"{self._connection.base_url}/rest/api/3/search/jql"
            
            while True:
                params = {
                    'jql': jql,
                    'startAt': start_at,
                    'maxResults': max_results,
                    'fields': 'summary,status,issuetype,assignee'
                }
                
                response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_LONG)
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    total = data.get('total', 0)
                    
                    all_issues.extend(issues)
                    logger.info(f"Obtenidas {len(issues)} issues para {assignee_email} (total acumulado: {len(all_issues)}/{total})")
                    
                    if len(all_issues) >= total or len(issues) == 0:
                        break
                    start_at += len(issues)
                else:
                    logger.error(f"Error al obtener issues por assignee: {response.status_code} - {response.text}")
                    break
                    
            logger.info(f"Total de issues obtenidas para {assignee_email}: {len(all_issues)}")
            return all_issues
            
        except Exception as e:
            logger.error(f"Error al obtener issues por assignee para {project_key}: {str(e)}")
            return all_issues

    def get_user_account_id_by_email(self, email: str) -> Optional[str]:
        """Busca el accountId de un usuario por su email en Jira"""
        try:
            if not email or not email.strip():
                return None
            
            email = email.strip()
            url = f"{self._connection.base_url}/rest/api/3/user/search"
            params = {'query': email, 'maxResults': 1}
            
            response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                users = response.json()
                # Buscar coincidencia exacta
                for user in users:
                    user_email = user.get('emailAddress', '')
                    if user_email.lower() == email.lower():
                        account_id = user.get('accountId')
                        if account_id:
                            logger.info(f"Usuario encontrado: {email} -> accountId: {account_id}")
                            return account_id
                
                # Usar primer resultado si no hay exacta
                if users and len(users) > 0:
                    account_id = users[0].get('accountId')
                    if account_id:
                        logger.warning(f"Usuario no encontrado exactamente por email {email}, usando primer resultado: {account_id}")
                        return account_id
                
                logger.warning(f"Usuario no encontrado para email: {email}")
                return None
            else:
                logger.error(f"Error al buscar usuario por email {email}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error al buscar usuario por email {email}: {str(e)}")
            return None

    def get_available_fields_metadata(self, project_key: str, issue_type: str, use_cache: bool = True) -> Optional[Dict]:
        """Obtiene metadata de campos disponibles para un tipo de issue"""
        cache_key = f"{project_key}:{issue_type}"
        
        if use_cache:
            cached_data = self._field_metadata_cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            logger.info(f"Obteniendo metadata de campos para {cache_key} desde Jira API...")
            url = f"{self._connection.base_url}/rest/api/3/issue/createmeta"
            params = {
                'projectKeys': project_key,
                'issuetypeNames': issue_type,
                'expand': 'projects.issuetypes.fields'
            }
            
            response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                metadata = response.json()
                projects = metadata.get('projects', [])
                
                if projects and projects[0].get('issuetypes'):
                    for it in projects[0]['issuetypes']:
                        if it.get('name', '').lower() == issue_type.lower():
                            fields = it.get('fields', {})
                            
                            available_fields = {}
                            for field_id, field_info in fields.items():
                                available_fields[field_id] = {
                                    'name': field_info.get('name', ''),
                                    'required': field_info.get('required', False),
                                    'schema': field_info.get('schema', {}),
                                    'operations': field_info.get('operations', []),
                                    'allowedValues': field_info.get('allowedValues', [])
                                }
                            
                            self._field_metadata_cache.set(cache_key, available_fields)
                            logger.info(f"Metadata obtenida para {cache_key}: {len(available_fields)} campos disponibles")
                            return available_fields
                
                logger.warning(f"No se encontró metadata para {cache_key} en la respuesta de Jira")
                return None
            else:
                logger.error(f"Error al obtener metadata para {cache_key}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Excepción al obtener metadata para {cache_key}: {str(e)}", exc_info=True)
            return None
            
    def invalidate_metadata_cache(self, cache_key: str):
         self._field_metadata_cache.invalidate(cache_key)
