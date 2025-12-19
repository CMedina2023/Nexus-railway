"""
Servicio para operaciones relacionadas con issues de Jira
Responsabilidad única: Gestionar creación y consulta de issues
"""
import logging
import json
import unicodedata
import re
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.core.config import Config

logger = logging.getLogger(__name__)


# ============================================================================
# Cache con TTL para metadata de campos
# ============================================================================
class FieldMetadataCache:
    """
    Cache con TTL (Time-To-Live) para metadata de campos de Jira
    Permite invalidación manual en caso de errores
    """
    
    def __init__(self, ttl_seconds: int = None):
        """
        Inicializa el cache con TTL
        
        Args:
            ttl_seconds: Tiempo de vida del cache en segundos (default: Config.JIRA_FIELD_METADATA_CACHE_TTL_SECONDS)
        """
        self._cache = {}  # {cache_key: {'data': ..., 'timestamp': ...}}
        self._ttl_seconds = ttl_seconds or Config.JIRA_FIELD_METADATA_CACHE_TTL_SECONDS
        logger.info(f"FieldMetadataCache inicializado con TTL de {self._ttl_seconds} segundos")
    
    def get(self, cache_key: str) -> Optional[Dict]:
        """
        Obtiene datos del cache si existen y no han expirado
        
        Args:
            cache_key: Clave del cache (ej: "RB:tests Case")
            
        Returns:
            Dict con metadata si existe y es válido, None si no existe o expiró
        """
        if cache_key not in self._cache:
            return None
        
        cached_item = self._cache[cache_key]
        timestamp = cached_item.get('timestamp')
        data = cached_item.get('data')
        
        # Verificar si el cache ha expirado
        if timestamp and datetime.now() - timestamp > timedelta(seconds=self._ttl_seconds):
            logger.debug(f"Cache expirado para '{cache_key}', eliminando...")
            del self._cache[cache_key]
            return None
        
        logger.debug(f"Cache hit para '{cache_key}'")
        return data
    
    def set(self, cache_key: str, data: Dict) -> None:
        """
        Guarda datos en el cache con timestamp actual
        
        Args:
            cache_key: Clave del cache
            data: Datos a guardar
        """
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cache actualizado para '{cache_key}'")
    
    def invalidate(self, cache_key: str) -> None:
        """
        Invalida (elimina) una entrada del cache
        
        Args:
            cache_key: Clave del cache a invalidar
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info(f"Cache invalidado para '{cache_key}'")
    
    def clear(self) -> None:
        """Limpia todo el cache"""
        self._cache.clear()
        logger.info("Cache completamente limpiado")


# ============================================================================
# Rate Limiter para creación de issues
# ============================================================================
class IssueCreationRateLimiter:
    """
    Rate limiter con backoff exponencial para creación de issues
    Previene throttling de Jira API
    """
    
    def __init__(self, base_delay: float = None, backoff_multiplier: float = None, max_delay: float = None):
        """
        Inicializa el rate limiter
        
        Args:
            base_delay: Delay base entre requests en segundos
            backoff_multiplier: Multiplicador para backoff exponencial
            max_delay: Delay máximo en segundos
        """
        self._base_delay = base_delay or Config.JIRA_CREATE_ISSUE_DELAY_SECONDS
        self._backoff_multiplier = backoff_multiplier or Config.JIRA_CREATE_ISSUE_BACKOFF_MULTIPLIER
        self._max_delay = max_delay or Config.JIRA_CREATE_ISSUE_MAX_DELAY_SECONDS
        self._current_delay = self._base_delay
        self._consecutive_errors = 0
        self._last_request_time = None
        logger.info(f"RateLimiter inicializado: base_delay={self._base_delay}s, backoff={self._backoff_multiplier}x, max={self._max_delay}s")
    
    def wait(self) -> None:
        """
        Espera el tiempo necesario antes del siguiente request
        Implementa backoff exponencial si hay errores consecutivos
        """
        if self._last_request_time is None:
            self._last_request_time = time.time()
            return
        
        # Calcular tiempo transcurrido desde el último request
        elapsed = time.time() - self._last_request_time
        
        # Calcular delay necesario (con backoff si hay errores)
        required_delay = self._current_delay
        
        # Si no ha pasado suficiente tiempo, esperar
        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            logger.debug(f"Rate limiting: esperando {wait_time:.2f}s (delay actual: {self._current_delay:.2f}s)")
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def report_success(self) -> None:
        """
        Reporta un request exitoso
        Resetea el backoff exponencial
        """
        if self._consecutive_errors > 0:
            logger.info(f"Request exitoso después de {self._consecutive_errors} errores, reseteando backoff")
        self._consecutive_errors = 0
        self._current_delay = self._base_delay
    
    def report_error(self) -> None:
        """
        Reporta un request fallido
        Incrementa el backoff exponencial
        """
        self._consecutive_errors += 1
        old_delay = self._current_delay
        self._current_delay = min(
            self._current_delay * self._backoff_multiplier,
            self._max_delay
        )
        logger.warning(
            f"Error #{self._consecutive_errors} detectado, "
            f"incrementando delay: {old_delay:.2f}s → {self._current_delay:.2f}s"
        )


# Variaciones comunes de nombres para tipos de issues
TEST_CASE_VARIATIONS = [
    'tests Case',
    'tests case',
    'test case',
    'TestCase',
    'Testcase',
    'Caso de Prueba',
    'Caso de prueba',
    'Caso De Prueba',
    'TEST CASE'
]

BUG_VARIATIONS = [
    'Bug',
    'bug',
    'BUG',
    'Error',
    'error',
    'Defect',
    'defect'
]

STORY_VARIATIONS = [
    'Story',
    'story',
    'STORY',
    'Historia',
    'historia',
    'User Story',
    'user story',
    'USER STORY'
]


def build_issuetype_jql(issue_type: str, project_key: str) -> str:
    """
    Construye un JQL que busca un tipo de issue considerando todas sus variaciones posibles
    
    Args:
        issue_type: Tipo de issue a buscar (ej: "tests Case", "Bug")
        project_key: Clave del proyecto
        
    Returns:
        str: JQL query con OR para todas las variaciones
    """
    issue_type_lower = issue_type.lower()
    
    # Determinar qué variaciones usar
    if 'test' in issue_type_lower and 'case' in issue_type_lower:
        variations = TEST_CASE_VARIATIONS
    elif 'bug' in issue_type_lower or issue_type_lower == 'error' or issue_type_lower == 'defect':
        variations = BUG_VARIATIONS
    else:
        # Si no es un tipo conocido, usar solo el nombre proporcionado
        variations = [issue_type]
    
    # Construir JQL con OR para todas las variaciones
    issuetype_conditions = ' OR '.join([f'issuetype = "{var}"' for var in variations])
    jql = f'project = {project_key} AND ({issuetype_conditions})'
    
    logger.info(f"JQL generado con variaciones para '{issue_type}': {jql}")
    return jql


class IssueService:
    """Servicio para operaciones relacionadas con issues de Jira"""
    
    def __init__(self, connection: JiraConnection, project_service: ProjectService):
        """
        Inicializa el servicio de issues
        
        Args:
            connection: Conexión con Jira (inyección de dependencias)
            project_service: Servicio de proyectos (inyección de dependencias)
        """
        self._connection = connection
        self._project_service = project_service
        
        # Inicializar cache con TTL y rate limiter
        self._field_metadata_cache = FieldMetadataCache()
        self._rate_limiter = IssueCreationRateLimiter()
    
    def get_issues_by_type(self, project_key: str, issue_type: str, max_results: int = None) -> List[Dict]:
        """
        Obtiene issues de un tipo específico para un proyecto
        Implementa paginación automática para obtener TODOS los resultados
        
        Args:
            project_key: Clave del proyecto
            issue_type: Tipo de issue a buscar
            max_results: Número máximo de resultados por página (default: Config.JIRA_MAX_RESULTS)
                        Si es None, obtiene TODOS los resultados sin límite
            
        Returns:
            List[Dict]: Lista de issues encontradas (TODAS, sin límite)
        """
        # Usar límite de 100 por página (paginación automática obtendrá TODOS los resultados sin límite)
        if max_results is None:
            max_results = 1000  # Máximo permitido por Jira API
        
        all_issues = []
        start_at = 0
        
        try:
            # JQL query para obtener issues del proyecto y tipo específico
            # Usa variaciones del nombre para mayor compatibilidad
            jql = build_issuetype_jql(issue_type, project_key)
            
            # Usar /rest/api/3/search/jql según documentación oficial (CHANGE-2046)
            # El endpoint /rest/api/3/search fue removido, ahora se usa /rest/api/3/search/jql
            url = f"{self._connection.base_url}/rest/api/3/search/jql"
            
            while True:
                # GET con parámetros de query según nueva API
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
                    
                    # Si ya obtuvimos todos los resultados, salir del loop
                    if len(all_issues) >= total or len(issues) == 0:
                        break
                    
                    # Avanzar al siguiente lote
                    start_at += len(issues)
                else:
                    logger.error(f"Error al obtener {issue_type}: {response.status_code} - {response.text}")
                    break
                    
            logger.info(f"Total de {issue_type} obtenidos: {len(all_issues)}")
            return all_issues
            
        except Exception as e:
            logger.error(f"Error al obtener {issue_type} para {project_key}: {str(e)}")
            return all_issues  # Retornar lo que se haya obtenido hasta el momento
    
    def get_all_issues(self, project_key: str, max_results: int = None) -> List[Dict]:
        """
        Obtiene todas las issues de un proyecto
        Implementa paginación automática para obtener TODOS los resultados
        
        Args:
            project_key: Clave del proyecto
            max_results: Número máximo de resultados por página (default: Config.JIRA_MAX_RESULTS)
                        Si es None, obtiene TODOS los resultados sin límite
            
        Returns:
            List[Dict]: Lista de todas las issues (TODAS, sin límite)
        """
        # Usar límite de 100 por página (paginación automática obtendrá TODOS los resultados sin límite)
        if max_results is None:
            max_results = 1000  # Máximo permitido por Jira API
        
        all_issues = []
        start_at = 0
        
        try:
            jql = f'project = {project_key}'
            
            # Usar /rest/api/3/search/jql según documentación oficial (CHANGE-2046)
            # El endpoint /rest/api/3/search fue removido, ahora se usa /rest/api/3/search/jql
            url = f"{self._connection.base_url}/rest/api/3/search/jql"
            
            while True:
                # GET con parámetros de query según nueva API
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
                    
                    # Si ya obtuvimos todos los resultados, salir del loop
                    if len(all_issues) >= total or len(issues) == 0:
                        break
                    
                    # Avanzar al siguiente lote
                    start_at += len(issues)
                else:
                    logger.error(f"Error al obtener todas las issues: {response.status_code} - {response.text}")
                    break
                    
            logger.info(f"Total de issues obtenidas: {len(all_issues)}")
            return all_issues
            
        except Exception as e:
            logger.error(f"Error al obtener todas las issues para {project_key}: {str(e)}")
            return all_issues  # Retornar lo que se haya obtenido hasta el momento
    
    def get_issues_by_assignee(self, project_key: str, assignee_email: str, max_results: int = None) -> List[Dict]:
        """
        Obtiene issues asignadas a un usuario específico
        Implementa paginación automática para obtener TODOS los resultados
        
        Args:
            project_key: Clave del proyecto
            assignee_email: Email del usuario asignado
            max_results: Número máximo de resultados por página (default: Config.JIRA_MAX_RESULTS)
                        Si es None, obtiene TODOS los resultados sin límite
            
        Returns:
            List[Dict]: Lista de issues asignadas al usuario (TODAS, sin límite)
        """
        # Usar límite de 100 por página (paginación automática obtendrá TODOS los resultados sin límite)
        if max_results is None:
            max_results = 1000  # Máximo permitido por Jira API
        
        all_issues = []
        start_at = 0
        
        try:
            # JQL query para obtener issues del proyecto asignadas al usuario
            # Escapar email por si contiene caracteres especiales
            jql = f'project = {project_key} AND assignee = "{assignee_email}"'
            
            # Usar /rest/api/3/search/jql según documentación oficial (CHANGE-2046)
            # El endpoint /rest/api/3/search fue removido, ahora se usa /rest/api/3/search/jql
            url = f"{self._connection.base_url}/rest/api/3/search/jql"
            
            while True:
                # GET con parámetros de query según nueva API
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
                    
                    # Si ya obtuvimos todos los resultados, salir del loop
                    if len(all_issues) >= total or len(issues) == 0:
                        break
                    
                    # Avanzar al siguiente lote
                    start_at += len(issues)
                else:
                    logger.error(f"Error al obtener issues por assignee: {response.status_code} - {response.text}")
                    break
                    
            logger.info(f"Total de issues obtenidas para {assignee_email}: {len(all_issues)}")
            return all_issues
            
        except Exception as e:
            logger.error(f"Error al obtener issues por assignee para {project_key}: {str(e)}")
            return all_issues  # Retornar lo que se haya obtenido hasta el momento
    
    def get_user_account_id_by_email(self, email: str) -> Optional[str]:
        """
        Busca el accountId de un usuario por su email en Jira
        
        Args:
            email: Email del usuario a buscar
            
        Returns:
            str: accountId del usuario si se encuentra, None si no se encuentra
        """
        try:
            if not email or not email.strip():
                return None
            
            email = email.strip()
            url = f"{self._connection.base_url}/rest/api/3/user/search"
            
            # Buscar usuario por query (puede ser email o nombre)
            params = {
                'query': email,
                'maxResults': 1
            }
            
            response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                users = response.json()
                # Buscar el usuario que coincida exactamente con el email
                for user in users:
                    user_email = user.get('emailAddress', '')
                    if user_email.lower() == email.lower():
                        account_id = user.get('accountId')
                        if account_id:
                            logger.info(f"Usuario encontrado: {email} -> accountId: {account_id}")
                            return account_id
                
                # Si no se encontró por email exacto, intentar con el primer resultado si hay uno
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
    
    def _format_field_value_by_type(self, field_id: str, field_value: str, field_schema: Dict = None, allowed_values: List = None) -> any:
        """
        Formatea un valor de campo según su tipo de schema en Jira
        
        Args:
            field_id: ID del campo en Jira
            field_value: Valor del campo (string del CSV)
            field_schema: Schema del campo obtenido de Jira (opcional)
            allowed_values: Lista de valores permitidos para campos option (opcional)
            
        Returns:
            Valor formateado según el tipo de campo
        """
        if not field_value or not field_value.strip():
            return None
        
        field_value = field_value.strip()
        
        # Si no hay schema, intentar detectar por el nombre del campo
        if not field_schema:
            # Campos conocidos que requieren formato de objeto
            if field_id == 'parent' or field_id.lower() in ['parent', 'epic link', 'epiclink']:
                # Formato para parent: {"key": "NA-25"}
                return {"key": field_value}
            # Campo environment siempre requiere ADF
            if field_id.lower() == 'environment':
                return self._format_description_to_adf(field_value)
            return field_value
        
        schema_type = field_schema.get('type', 'string')
        schema_items = field_schema.get('items', {})
        schema_custom = field_schema.get('custom', '')
        
        # Campo de tipo "string" con schema custom que requiere ADF
        # Algunos campos personalizados de texto largo requieren formato ADF
        if schema_type == 'string' and schema_custom:
            # Verificar si el campo es de tipo texto largo que requiere ADF
            # Los campos que requieren ADF generalmente tienen schema custom como:
            # - com.atlassian.jira.plugin.system.customfieldtypes:textarea
            # - com.atlassian.jira.plugin.system.customfieldtypes:readonlyfield
            # Pero algunos campos personalizados también pueden requerirlo
            # Intentar convertir a ADF si el valor parece ser texto largo
            if len(field_value) > 50 or '\n' in field_value or '\t' in field_value:
                # Convertir a ADF para campos de texto largo
                has_newlines = '\n' in field_value
                logger.debug(f"Campo '{field_id}' detectado como requeridor de ADF (longitud: {len(field_value)}, tiene saltos de línea: {has_newlines})")
                return self._format_description_to_adf(field_value)
        
        # Campo de tipo "option" (select/dropdown) - requiere formato {"name": "valor"} o {"id": "id"}
        if schema_type == 'option':
            # Valores por defecto hardcodeados para campos comunes
            default_values_map = {
                'tipo de prueba': 'Funcional',
                'tipo_prueba': 'Funcional',
                'test type': 'Funcional',
                'nivel de prueba': 'UAT',
                'nivel_prueba': 'UAT',
                'test level': 'UAT',
                'environment': 'QA',
                'ambiente': 'QA',
                'entorno': 'QA'
            }
            
            # Buscar el valor en allowedValues para obtener el formato correcto
            if allowed_values:
                # Primero intentar con el valor original
                for av in allowed_values:
                    if isinstance(av, dict):
                        av_name = av.get('value', av.get('name', ''))
                        av_id = av.get('id')
                        # Comparar por nombre (insensible a mayúsculas)
                        if av_name and av_name.lower() == field_value.lower():
                            # Retornar con id si está disponible, sino con name
                            if av_id:
                                return {"id": str(av_id)}
                            return {"name": av_name}
                    elif isinstance(av, str):
                        if av.lower() == field_value.lower():
                            return {"name": av}
                
                # Si no se encuentra, intentar con valores por defecto según el nombre del campo
                field_id_lower = field_id.lower()
                default_value = None
                for key, default in default_values_map.items():
                    if key in field_id_lower:
                        default_value = default
                        break
                
                if default_value:
                    # Buscar el valor por defecto en allowedValues
                    logger.info(f"Valor '{field_value}' no encontrado para campo '{field_id}', intentando con valor por defecto '{default_value}'")
                    for av in allowed_values:
                        if isinstance(av, dict):
                            av_name = av.get('value', av.get('name', ''))
                            av_id = av.get('id')
                            if av_name and av_name.lower() == default_value.lower():
                                if av_id:
                                    return {"id": str(av_id)}
                                return {"name": av_name}
                        elif isinstance(av, str):
                            if av.lower() == default_value.lower():
                                return {"name": av}
                
                # Si tampoco se encuentra el valor por defecto, loggear y retornar None
                logger.warning(f"Valor '{field_value}' y valor por defecto '{default_value}' no encontrados en allowedValues para campo '{field_id}'. Valores permitidos: {[av.get('name', av.get('value', str(av))) if isinstance(av, dict) else av for av in allowed_values[:5]]}")
                return None  # Omitir el campo si el valor no es válido
            
            # Si no hay allowedValues, usar el valor tal cual con formato name
            return {"name": field_value}
        
        # Array de options - requiere formato [{"name": "valor"}]
        if schema_type == 'array' and schema_items.get('type') == 'option':
            # Si el valor contiene comas, separar en múltiples opciones
            if ',' in field_value:
                values = [v.strip() for v in field_value.split(',')]
                formatted_values = []
                for val in values:
                    if val:
                        # Buscar en allowedValues
                        found = False
                        if allowed_values:
                            for av in allowed_values:
                                if isinstance(av, dict):
                                    av_name = av.get('value', av.get('name', ''))
                                    av_id = av.get('id')
                                    if av_name and av_name.lower() == val.lower():
                                        if av_id:
                                            formatted_values.append({"id": str(av_id)})
                                        else:
                                            formatted_values.append({"name": av_name})
                                        found = True
                                        break
                                elif isinstance(av, str):
                                    if av.lower() == val.lower():
                                        formatted_values.append({"name": av})
                                        found = True
                                        break
                        if not found:
                            formatted_values.append({"name": val})
                return formatted_values
            else:
                # Valor único
                if allowed_values:
                    for av in allowed_values:
                        if isinstance(av, dict):
                            av_name = av.get('value', av.get('name', ''))
                            av_id = av.get('id')
                            if av_name and av_name.lower() == field_value.lower():
                                if av_id:
                                    return [{"id": str(av_id)}]
                                return [{"name": av_name}]
                        elif isinstance(av, str):
                            if av.lower() == field_value.lower():
                                return [{"name": av}]
                return [{"name": field_value}]
        
        # Campo de tipo "issue" - requiere formato {"key": "NA-25"}
        if schema_type == 'issue':
            return {"key": field_value}
        
        # Campo de tipo "issuelink" - también requiere formato {"key": "NA-25"}
        if schema_type == 'issuelink':
            return {"key": field_value}
        
        # Array de issues - requiere formato [{"key": "NA-25"}, {"key": "NA-26"}]
        if schema_type == 'array' and schema_items.get('type') == 'issue':
            # Si el valor contiene comas, separar en múltiples issues
            if ',' in field_value:
                keys = [k.strip() for k in field_value.split(',')]
                return [{"key": key} for key in keys if key]
            else:
                return [{"key": field_value}]
        
        # Array de issuelinks
        if schema_type == 'array' and schema_items.get('type') == 'issuelink':
            if ',' in field_value:
                keys = [k.strip() for k in field_value.split(',')]
                return [{"key": key} for key in keys if key]
            else:
                return [{"key": field_value}]
        
        # Para otros tipos, retornar el valor tal cual
        return field_value
    
    def _format_description_to_adf(self, description: str) -> Dict:
        """
        Convierte una descripción con formato markdown simple a formato ADF de Jira.
        
        Formato esperado:
        * COMO: texto
        * QUIERO: texto
        * PARA: texto
        * Prioridad: texto
        * Complejidad: texto
        * Reglas de Negocio Clave:
          • item1
          • item2
        
        Args:
            description: Texto con formato markdown simple
            
        Returns:
            Dict: Estructura ADF de Jira con negritas y saltos de línea
        """
        if not description:
            return {
                "type": "doc",
                "version": 1,
                "content": []
            }
        
        lines = description.split('\n')
        adf_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Línea vacía = párrafo vacío para salto de línea
                adf_content.append({
                    "type": "paragraph",
                    "content": []
                })
                continue
            
            # Detectar si es una línea con bullet (*) o bullet de segundo nivel (•)
            if line.startswith('* '):
                # Línea con bullet principal
                text = line[2:].strip()  # Remover "* "
                
                # Detectar si tiene formato "LABEL: texto"
                if ':' in text:
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        label = parts[0].strip()
                        value = parts[1].strip()
                        
                        # Crear párrafo con bullet, label en negrita y valor normal
                        adf_content.append({
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "* ",
                                    "marks": []
                                },
                                {
                                    "type": "text",
                                    "text": f"{label}:",
                                    "marks": [{"type": "strong"}]
                                },
                                {
                                    "type": "text",
                                    "text": f" {value}",
                                    "marks": []
                                }
                            ]
                        })
                    else:
                        # Solo label sin valor
                        adf_content.append({
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"* {text}",
                                    "marks": []
                                }
                            ]
                        })
                else:
                    # Texto simple con bullet
                    adf_content.append({
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"* {text}",
                                "marks": []
                            }
                        ]
                    })
            elif line.startswith('  • ') or line.startswith('• '):
                # Línea con bullet de segundo nivel
                text = line.replace('•', '').strip()
                adf_content.append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "  • ",
                            "marks": []
                        },
                        {
                            "type": "text",
                            "text": text,
                            "marks": []
                        }
                    ]
                })
            else:
                # Línea normal sin bullet
                adf_content.append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": line,
                            "marks": []
                        }
                    ]
                })
        
        return {
            "type": "doc",
            "version": 1,
            "content": adf_content
        }
    
    def create_issue(self, project_key: str, issue_type: str, summary: str, description: str = None,
                     assignee: str = None, priority: str = None, labels: List[str] = None,
                     custom_fields: Dict = None, field_schemas: Dict = None) -> Dict:
        """
        Crea un issue en Jira
        
        Args:
            project_key: Clave del proyecto
            issue_type: Tipo de issue
            summary: Resumen del issue
            description: Descripción del issue (opcional)
            assignee: Asignado (opcional)
            priority: Prioridad (opcional)
            labels: Etiquetas (opcional)
            custom_fields: Campos personalizados adicionales (opcional)
            field_schemas: Schemas de campos (opcional, para formateo)
            
        Returns:
            Dict: Resultado de la creación con 'success', 'key', 'id' o 'error'
        """
        # Aplicar rate limiting antes de hacer el request
        self._rate_limiter.wait()
        
        try:
            url = f"{self._connection.base_url}/rest/api/3/issue"
            
            # Construir el payload para crear el issue
            payload = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": summary,
                    "issuetype": {
                        "name": issue_type
                    }
                }
            }
            
            # Agregar descripción si se proporciona
            if description:
                payload["fields"]["description"] = self._format_description_to_adf(description)
            
            # Agregar asignado si se proporciona
            if assignee:
                assignee = assignee.strip()
                # Verificar si es un email (contiene @) o ya es un accountId
                if '@' in assignee:
                    # Es un email, buscar el accountId
                    account_id = self.get_user_account_id_by_email(assignee)
                    if account_id:
                        payload["fields"]["assignee"] = {
                            "accountId": account_id
                        }
                    else:
                        logger.warning(f"No se pudo encontrar accountId para el email: {assignee}. El issue se creará sin asignado.")
                        # No agregar assignee si no se encuentra el usuario
                else:
                    # Asumir que ya es un accountId
                    payload["fields"]["assignee"] = {
                        "accountId": assignee
                    }
            
            # Agregar prioridad si se proporciona
            # Jira API v3 requiere priority como objeto con "name" o "id"
            if priority:
                # Asegurar que priority sea un string válido
                priority_str = str(priority).strip() if priority else None
                if priority_str:
                    payload["fields"]["priority"] = {
                        "name": priority_str
                    }
            
            # Agregar labels si se proporcionan
            if labels:
                payload["fields"]["labels"] = labels
            
            # Agregar campos personalizados si se proporcionan
            # Excluir campos del sistema que ya se manejan por separado
            if custom_fields:
                filtered_custom_fields = {}
                for k, v in custom_fields.items():
                    # Excluir campos del sistema que ya se manejan por separado
                    # Estos campos deben manejarse con su formato específico, no desde custom_fields
                    if k in ['issuetype', 'summary', 'description', 'project', 'assignee', 'priority', 'labels']:
                        logger.warning(f"Campo del sistema '{k}' encontrado en custom_fields, será ignorado (ya se maneja por separado)")
                        continue
                    
                    # Formatear el valor según el tipo de campo si hay información de schema
                    if field_schemas and k in field_schemas:
                        field_info = field_schemas[k]
                        field_schema = field_info.get('schema', {})
                        allowed_values = field_info.get('allowedValues', [])
                        formatted_value = self._format_field_value_by_type(k, str(v) if v else '', field_schema, allowed_values)
                        filtered_custom_fields[k] = formatted_value
                        logger.debug(f"Campo '{k}' formateado: {v} -> {formatted_value}")
                    else:
                        # Si no hay schema, intentar formatear por nombre de campo conocido
                        formatted_value = self._format_field_value_by_type(k, str(v) if v else '', None, None)
                        filtered_custom_fields[k] = formatted_value
                
                if filtered_custom_fields:
                    payload["fields"].update(filtered_custom_fields)
            
            # Log del payload para debugging
            logger.debug(f"[DEBUG] Payload para crear issue: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = self._connection.session.post(url, json=payload, timeout=Config.JIRA_TIMEOUT_LONG)
            
            if response.status_code == 201:
                issue_data = response.json()
                # Reportar éxito al rate limiter
                self._rate_limiter.report_success()
                return {
                    'success': True,
                    'key': issue_data.get('key'),
                    'id': issue_data.get('id'),
                    'self': issue_data.get('self')
                }
            else:
                error_text = response.text
                error_json = {}
                errors = {}
                
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_json = response.json()
                        errors = error_json.get('errors', {})
                        error_messages = error_json.get('errorMessages', [])
                        
                        # Log detallado de errores
                        logger.error(f"Error al crear issue: {response.status_code}")
                        if error_messages:
                            logger.error(f"Mensajes de error: {error_messages}")
                        if errors:
                            logger.error(f"Errores por campo:")
                            for field_id, error_msg in errors.items():
                                logger.error(f"  - Campo '{field_id}': {error_msg}")
                except Exception as e:
                    logger.warning(f"No se pudo parsear la respuesta de error como JSON: {e}")
                
                # Detectar si hay campos que requieren ADF
                adf_fields = []
                for field_id, error_msg in errors.items():
                    if 'atlassian document' in str(error_msg).lower() or 'adf' in str(error_msg).lower():
                        adf_fields.append(field_id)
                        logger.warning(f"Campo '{field_id}' requiere formato ADF: {error_msg}")
                
                # Si hay campos que requieren ADF, reintentar convirtiéndolos
                if adf_fields and custom_fields:
                    logger.info(f"Detectados {len(adf_fields)} campo(s) que requieren ADF: {adf_fields}. Reintentando con formato ADF...")
                    # Convertir los campos problemáticos a ADF
                    for field_id in adf_fields:
                        if field_id in custom_fields:
                            original_value = custom_fields[field_id]
                            # Si el valor es un string, convertirlo a ADF
                            if isinstance(original_value, str):
                                custom_fields[field_id] = self._format_description_to_adf(original_value)
                                logger.debug(f"Campo '{field_id}' convertido a ADF (longitud original: {len(original_value)})")
                            # Si el valor ya es un dict (ADF), no hacer nada
                            elif isinstance(original_value, dict):
                                logger.debug(f"Campo '{field_id}' ya está en formato ADF")
                    
                    # Actualizar el payload con los campos convertidos
                    for field_id in adf_fields:
                        if field_id in custom_fields:
                            payload["fields"][field_id] = custom_fields[field_id]
                    
                    # Reintentar la creación
                    logger.info(f"Reintentando creación de issue con campos ADF corregidos...")
                    response = self._connection.session.post(url, json=payload, timeout=Config.JIRA_TIMEOUT_LONG)
                    
                    if response.status_code == 201:
                        issue_data = response.json()
                        logger.info(f"Issue creado exitosamente después de convertir campos a ADF: {issue_data.get('key')}")
                        # Reportar éxito al rate limiter
                        self._rate_limiter.report_success()
                        return {
                            'success': True,
                            'key': issue_data.get('key'),
                            'id': issue_data.get('id'),
                            'self': issue_data.get('self')
                        }
                    else:
                        # Si el reintento también falla, loguear el error y reportar error al rate limiter
                        retry_error_text = response.text
                        logger.error(f"Error al crear issue después de reintento con ADF: {response.status_code} - {retry_error_text}")
                        self._rate_limiter.report_error()
                        try:
                            retry_error_json = response.json()
                            retry_errors = retry_error_json.get('errors', {})
                            retry_error_messages = retry_error_json.get('errorMessages', [])
                            if retry_error_messages:
                                logger.error(f"Mensajes de error en reintento: {retry_error_messages}")
                            if retry_errors:
                                logger.error(f"Errores por campo en reintento:")
                                for field_id, error_msg in retry_errors.items():
                                    logger.error(f"  - Campo '{field_id}': {error_msg}")
                        except:
                            pass
                
                # Construir mensaje de error más claro
                error_summary = []
                if errors:
                    for field_id, error_msg in errors.items():
                        error_summary.append(f"Campo '{field_id}': {error_msg}")
                
                error_message = f"Error {response.status_code}"
                if error_summary:
                    error_message += f" - {'; '.join(error_summary)}"
                elif error_text:
                    error_message += f" - {error_text[:200]}"
                
                logger.error(f"Error final al crear issue: {error_message}")
                # Reportar error al rate limiter
                self._rate_limiter.report_error()
                return {
                    'success': False,
                    'error': error_message
                }
        except Exception as e:
            logger.error(f"Error al crear issue: {str(e)}")
            # Reportar error al rate limiter
            self._rate_limiter.report_error()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_available_fields_metadata(self, project_key: str, issue_type: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Obtiene metadata de campos disponibles para un tipo de issue
        Usa cache con TTL para optimizar performance
        
        Args:
            project_key: Clave del proyecto
            issue_type: Tipo de issue
            use_cache: Si es True, usa cache (default: True)
            
        Returns:
            Dict con metadata de campos disponibles, o None si falla
        """
        cache_key = f"{project_key}:{issue_type}"
        
        # Intentar obtener del cache si está habilitado
        if use_cache:
            cached_data = self._field_metadata_cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Si no está en cache o cache deshabilitado, obtener de Jira
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
                            
                            # Crear diccionario estructurado de campos disponibles
                            available_fields = {}
                            for field_id, field_info in fields.items():
                                available_fields[field_id] = {
                                    'name': field_info.get('name', ''),
                                    'required': field_info.get('required', False),
                                    'schema': field_info.get('schema', {}),
                                    'operations': field_info.get('operations', []),
                                    'allowedValues': field_info.get('allowedValues', [])
                                }
                            
                            # Guardar en cache
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
    
    def _validate_and_filter_custom_fields(
        self, 
        custom_fields: Dict, 
        available_fields_metadata: Dict,
        row_idx: int
    ) -> Tuple[Dict, List[str]]:
        """
        Valida campos personalizados contra metadata de Jira
        Filtra campos que no están disponibles o no son editables
        
        Args:
            custom_fields: Diccionario de campos personalizados a validar
            available_fields_metadata: Metadata de campos disponibles obtenida de Jira
            row_idx: Índice de la fila (para logging)
            
        Returns:
            Tuple[Dict, List[str]]: (campos_validos, campos_filtrados)
        """
        if not custom_fields:
            return {}, []
        
        if not available_fields_metadata:
            logger.warning(f"Fila {row_idx}: No hay metadata disponible, no se puede validar campos. Continuando sin validación.")
            return custom_fields, []
        
        valid_fields = {}
        filtered_fields = []
        
        for field_id, field_value in custom_fields.items():
            # Verificar si el campo existe en la metadata
            if field_id not in available_fields_metadata:
                logger.warning(
                    f"Fila {row_idx}: Campo '{field_id}' no está disponible en la pantalla de creación, será omitido"
                )
                filtered_fields.append(field_id)
                continue
            
            field_info = available_fields_metadata[field_id]
            
            # Verificar si el campo es editable (tiene operación 'set')
            operations = field_info.get('operations', [])
            if 'set' not in operations:
                logger.warning(
                    f"Fila {row_idx}: Campo '{field_id}' ({field_info.get('name', 'N/A')}) es read-only, será omitido"
                )
                filtered_fields.append(field_id)
                continue
            
            # Campo válido
            valid_fields[field_id] = field_value
        
        if filtered_fields:
            logger.info(
                f"Fila {row_idx}: {len(filtered_fields)} campo(s) filtrado(s) (no disponibles o read-only): {filtered_fields}"
            )
        
        return valid_fields, filtered_fields
    
    def normalize_issue_type(self, csv_type: str, available_types: List[Dict]) -> Optional[str]:
        """
        Normaliza el nombre del tipo de issue del CSV al nombre exacto que Jira espera.
        Busca coincidencias insensibles a mayúsculas/minúsculas y variaciones comunes.
        
        Args:
            csv_type: Tipo de issue del CSV
            available_types: Lista de tipos disponibles en Jira
            
        Returns:
            str: Nombre normalizado del tipo de issue o None si no se encuentra
        """
        if not csv_type or not available_types:
            logger.warning(f"Tipo de issue vacío o sin tipos disponibles. CSV type: '{csv_type}', Available: {len(available_types) if available_types else 0}")
            return None
        
        csv_type_clean = csv_type.strip()
        csv_type_lower = csv_type_clean.lower()
        
        logger.info(f"Normalizando tipo de issue: '{csv_type_clean}' (lowercase: '{csv_type_lower}')")
        logger.info(f"Tipos disponibles en Jira: {[it.get('name', '') for it in available_types]}")
        
        # Primero, buscar coincidencia exacta (insensible a mayúsculas)
        for issue_type in available_types:
            type_name = issue_type.get('name', '').strip()
            if type_name.lower() == csv_type_lower:
                logger.info(f"Coincidencia exacta encontrada: '{csv_type_clean}' -> '{type_name}'")
                return type_name
        
        # Segundo, buscar coincidencia parcial (palabras clave)
        # Para "tests Case" buscar tipos que contengan "test" y "case"
        if 'test' in csv_type_lower and 'case' in csv_type_lower:
            for issue_type in available_types:
                type_name = issue_type.get('name', '').strip()
                type_name_lower = type_name.lower()
                if 'test' in type_name_lower and 'case' in type_name_lower:
                    logger.info(f"Coincidencia por palabras clave (test+case): '{csv_type_clean}' -> '{type_name}'")
                    return type_name
        
        # Para "Story" buscar tipos que contengan "story" o "historia"
        if 'story' in csv_type_lower or 'historia' in csv_type_lower:
            for issue_type in available_types:
                type_name = issue_type.get('name', '').strip()
                type_name_lower = type_name.lower()
                if 'story' in type_name_lower or 'historia' in type_name_lower:
                    logger.info(f"Coincidencia por palabra clave (story/historia): '{csv_type_clean}' -> '{type_name}'")
                    return type_name
        
        # Para "Bug" buscar tipos que contengan "bug"
        if 'bug' in csv_type_lower:
            for issue_type in available_types:
                type_name = issue_type.get('name', '').strip()
                type_name_lower = type_name.lower()
                if 'bug' in type_name_lower:
                    logger.info(f"Coincidencia por palabra clave (bug): '{csv_type_clean}' -> '{type_name}'")
                    return type_name
        
        # Si no se encuentra, retornar None para que se reporte como error
        logger.warning(f"No se encontró coincidencia para '{csv_type_clean}'. Tipos disponibles: {[it.get('name', '') for it in available_types]}")
        return None
    
    def create_issues_from_csv(self, csv_data: List[Dict], project_key: str, 
                              field_mappings: Dict = None, default_values: Dict = None,
                              filter_issue_types: bool = True) -> Dict:
        """
        Crea múltiples issues en Jira desde datos CSV
        
        Args:
            csv_data: Lista de diccionarios con datos del CSV
            project_key: Clave del proyecto
            field_mappings: Mapeo de campos CSV a campos Jira
            default_values: Valores por defecto para campos
            filter_issue_types: Si es True, solo valida contra tests Cases y Bugs. Si es False, valida contra todos los tipos.
            
        Returns:
            Dict: Resultado con 'success', 'created', 'failed', 'total', etc.
        """
        results = {
            'success': True,
            'created': [],
            'failed': [],
            'total': len(csv_data),
            'success_count': 0,
            'error_count': 0
        }
        
        # Obtener tipos de issue disponibles del proyecto
        available_types = self._project_service.get_issue_types(project_key, filter_types=filter_issue_types)
        if not available_types:
            return {
                'success': False,
                'error': 'No se pudieron obtener los tipos de issue del proyecto',
                'created': [],
                'failed': [],
                'total': len(csv_data),
                'success_count': 0,
                'error_count': len(csv_data)
            }
        
        # Cache para schemas de campos por tipo de issue (legacy, ahora usa FieldMetadataCache)
        field_schemas_cache = {}
        
        # Cache para metadata de campos disponibles (con validación previa)
        available_fields_by_type = {}
        
        # Crear un diccionario de tipos disponibles para búsqueda rápida
        available_type_names = {issue_type.get('name', '').lower(): issue_type.get('name', '')
                                for issue_type in available_types}
        
        logger.info(f"Iniciando carga masiva de {len(csv_data)} issues al proyecto {project_key}")
        
        for idx, row in enumerate(csv_data, start=1):
            try:
                # Obtener campos del CSV - buscar en múltiples variaciones del nombre de columna
                # Primero verificar si hay un mapeo de issuetype
                mapped_issue_type = None
                if field_mappings:
                    for csv_field, jira_field in field_mappings.items():
                        if jira_field == 'issuetype' and csv_field in row and row[csv_field]:
                            mapped_issue_type = row[csv_field].strip()
                            logger.info(f"Fila {idx}: Tipo de issue encontrado en mapeo: '{mapped_issue_type}' desde columna '{csv_field}'")
                            break
                
                # Si no hay mapeo, leer directamente del CSV
                if not mapped_issue_type:
                    csv_issue_type_raw = (
                        row.get('Tipo de Issue') or
                        row.get('Tipo') or
                        row.get('tipo de issue') or
                        row.get('TIPO DE ISSUE') or
                        row.get('Issue Type') or
                        row.get('issue type') or
                        row.get('ISSUE TYPE') or
                        None
                    )
                    
                    if csv_issue_type_raw:
                        mapped_issue_type = csv_issue_type_raw.strip()
                        logger.info(f"Fila {idx}: Tipo de issue leído directamente del CSV: '{mapped_issue_type}'")
                
                # Si no se encuentra, usar 'Story' como valor por defecto
                if not mapped_issue_type:
                    logger.warning(f"Fila {idx}: No se encontró tipo de issue. Claves disponibles: {list(row.keys())}. Usando 'Story' por defecto.")
                    mapped_issue_type = 'Story'
                
                csv_issue_type = mapped_issue_type
                
                # Logging detallado para debug
                logger.info(f"Fila {idx}: Tipo procesado: '{csv_issue_type}'")
                logger.info(f"Fila {idx}: Todas las claves del row: {list(row.keys())}")
                
                # Obtener summary - PRIMERO desde field_mappings si existe
                summary = None
                if field_mappings:
                    for csv_field, jira_field in field_mappings.items():
                        if jira_field == 'summary' and csv_field in row:
                            summary = str(row[csv_field]).strip() if row[csv_field] else None
                            logger.info(f"Fila {idx}: Summary obtenido desde mapeo: '{csv_field}' -> '{summary[:50] if summary else 'VACÍO'}...'")
                            break
                
                # Si no se encontró en mapeos, buscar en campos estándar
                if not summary:
                    summary = row.get('Resumen', row.get('Summary', row.get('Título', ''))).strip()
                    logger.info(f"Fila {idx}: Summary obtenido desde campos estándar: '{summary[:50] if summary else 'VACÍO'}...'")
                
                description = row.get('Descripción', row.get('Description', '')).strip()
                assignee = row.get('Asignado', row.get('Assignee', '')).strip() or None
                priority = row.get('Prioridad', row.get('Priority', '')).strip() or None
                labels_str = row.get('Labels', row.get('Etiquetas', '')).strip()
                labels = [l.strip() for l in labels_str.split(',')] if labels_str else None
                
                logger.info(f"Procesando fila {idx}: Tipo CSV='{csv_issue_type}', Resumen='{summary[:50] if summary else 'VACÍO'}...'")
                
                # Validar campos requeridos
                if not summary:
                    error_msg = 'El campo "Resumen" o "Summary" es requerido. Verifica que el campo esté mapeado correctamente.'
                    logger.error(f"Fila {idx}: {error_msg}. Campos disponibles: {list(row.keys())}, Mapeos: {field_mappings}")
                    results['failed'].append({
                        'row': idx,
                        'error': error_msg
                    })
                    results['error_count'] += 1
                    continue
                
                # Normalizar el tipo de issue
                issue_type = self.normalize_issue_type(csv_issue_type, available_types)
                if not issue_type:
                    # Listar tipos disponibles para el mensaje de error
                    available_names = ', '.join([it.get('name', '') for it in available_types])
                    error_msg = f'Tipo de issue "{csv_issue_type}" no válido. Tipos disponibles: {available_names}'
                    logger.error(f"Fila {idx}: {error_msg}")
                    results['failed'].append({
                        'row': idx,
                        'error': error_msg,
                        'summary': summary
                    })
                    results['error_count'] += 1
                    continue
                
                logger.info(f"Fila {idx}: Tipo normalizado '{csv_issue_type}' -> '{issue_type}'")
                
                # Aplicar mapeos de campos si existen (excluyendo campos del sistema que ya se manejan)
                custom_fields = {}
                mapped_description = None
                mapped_priority = None
                if field_mappings:
                    for csv_field, jira_field in field_mappings.items():
                        if csv_field in row and row[csv_field]:
                            # Excluir campos del sistema que ya se manejan por separado
                            if jira_field == 'issuetype':
                                continue  # Ya se maneja arriba
                            elif jira_field == 'description':
                                mapped_description = row[csv_field]
                                logger.info(f"Fila {idx}: Descripción mapeada desde CSV: '{mapped_description[:50]}...'")
                            elif jira_field == 'priority':
                                mapped_priority = row[csv_field]
                                logger.info(f"Fila {idx}: Prioridad mapeada desde CSV: '{mapped_priority}'")
                            elif jira_field in ['summary', 'project', 'assignee', 'labels']:
                                # Estos campos se manejan por separado, no agregarlos a custom_fields
                                continue
                            else:
                                custom_fields[jira_field] = row[csv_field]
                
                # Si se mapeó description, usar el valor mapeado (evitar duplicación)
                # La descripción ya fue leída del CSV en la línea 678, solo usar mapped_description si existe
                if mapped_description:
                    # Usar la descripción mapeada (viene del field_mappings)
                    description = mapped_description.strip() if mapped_description else None
                # Si no hay mapped_description, description ya está asignada desde línea 678
                
                # Si se mapeó priority, usar el valor mapeado
                if mapped_priority:
                    priority = mapped_priority.strip() if mapped_priority else None
                
                # Aplicar valores por defecto si existen (excluyendo issuetype que ya se maneja)
                if default_values:
                    for field, value in default_values.items():
                        if field not in custom_fields and field != 'issuetype':
                            custom_fields[field] = value
                
                # ============================================================================
                # VALIDACIÓN PREVIA DE CAMPOS (Nueva funcionalidad)
                # ============================================================================
                # Obtener metadata de campos disponibles si no está en cache
                if issue_type not in available_fields_by_type:
                    logger.info(f"Fila {idx}: Obteniendo metadata de campos para tipo '{issue_type}'...")
                    available_fields_metadata = self._get_available_fields_metadata(
                        project_key, 
                        issue_type, 
                        use_cache=True
                    )
                    available_fields_by_type[issue_type] = available_fields_metadata
                else:
                    available_fields_metadata = available_fields_by_type[issue_type]
                
                # Validar y filtrar campos personalizados
                if custom_fields and available_fields_metadata:
                    valid_custom_fields, filtered_fields = self._validate_and_filter_custom_fields(
                        custom_fields,
                        available_fields_metadata,
                        idx
                    )
                    
                    # Si se filtraron campos, actualizar custom_fields
                    if filtered_fields:
                        logger.info(
                            f"Fila {idx}: Usando {len(valid_custom_fields)} campos válidos "
                            f"(filtrados {len(filtered_fields)}: {', '.join(filtered_fields)})"
                        )
                        custom_fields = valid_custom_fields
                
                # ============================================================================
                # Obtener schemas de campos para formateo (legacy, ahora incluido en metadata)
                # ============================================================================
                field_schemas = None
                cache_key = f"{project_key}:{issue_type}"
                if cache_key not in field_schemas_cache:
                    try:
                        # Obtener metadata completa de campos desde Jira API
                        url = f"{self._connection.base_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&issuetypeNames={issue_type}&expand=projects.issuetypes.fields"
                        response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
                        
                        if response.status_code == 200:
                            metadata = response.json()
                            projects = metadata.get('projects', [])
                            if projects and projects[0].get('issuetypes'):
                                for it in projects[0]['issuetypes']:
                                    if it.get('name', '').lower() == issue_type.lower():
                                        fields = it.get('fields', {})
                                        # Crear diccionario de schemas por field_id
                                        field_schemas = {}
                                        for field_id, field_info in fields.items():
                                            schema = field_info.get('schema', {})
                                            allowed_values = field_info.get('allowedValues', [])
                                            field_schemas[field_id] = {
                                                'schema': schema,
                                                'allowedValues': allowed_values
                                            }
                                        field_schemas_cache[cache_key] = field_schemas
                                        logger.debug(f"Schemas de campos obtenidos para {cache_key}: {len(field_schemas)} campos")
                                        break
                        
                        if cache_key not in field_schemas_cache:
                            field_schemas_cache[cache_key] = None
                    except Exception as e:
                        logger.warning(f"Error al obtener schemas de campos para {cache_key}: {e}")
                        field_schemas_cache[cache_key] = None
                else:
                    field_schemas = field_schemas_cache[cache_key]
                
                # Crear el issue
                issue_result = self.create_issue(
                    project_key=project_key,
                    issue_type=issue_type,
                    summary=summary,
                    description=description if description else None,
                    assignee=assignee,
                    priority=priority,
                    labels=labels,
                    custom_fields=custom_fields if custom_fields else None,
                    field_schemas=field_schemas
                )
                
                if issue_result.get('success'):
                    results['created'].append({
                        'row': idx,
                        'key': issue_result.get('key'),
                        'summary': summary,
                        'issue_type': issue_type
                    })
                    results['success_count'] += 1
                    logger.info(f"Fila {idx}: ✅ Issue creado exitosamente: {issue_result.get('key')}")
                else:
                    error_msg = issue_result.get('error', 'Error desconocido')
                    results['failed'].append({
                        'row': idx,
                        'error': error_msg,
                        'summary': summary
                    })
                    results['error_count'] += 1
                    logger.error(f"Fila {idx}: ❌ Error al crear issue: {error_msg}")
                    
                    # Invalidar cache si el error es de campo no encontrado o no disponible
                    error_lower = error_msg.lower()
                    if any(keyword in error_lower for keyword in [
                        'cannot be set',
                        'not on the appropriate screen',
                        'unknown field',
                        'field does not exist'
                    ]):
                        logger.warning(
                            f"Fila {idx}: Error de campo no disponible detectado, "
                            f"invalidando cache para '{cache_key}'"
                        )
                        self._field_metadata_cache.invalidate(cache_key)
                        # Remover también del cache local de esta ejecución
                        if issue_type in available_fields_by_type:
                            del available_fields_by_type[issue_type]
                    
            except Exception as e:
                logger.error(f"Error al procesar fila {idx}: {str(e)}")
                results['failed'].append({
                    'row': idx,
                    'error': str(e),
                    'summary': row.get('Resumen', row.get('Summary', 'N/A'))
                })
                results['error_count'] += 1
        
        # Actualizar estado de éxito general
        results['success'] = results['error_count'] == 0
        
        # Log final con estadísticas
        logger.info(
            f"Carga masiva completada: {results['success_count']}/{results['total']} exitosos, "
            f"{results['error_count']} errores"
        )
        
        return results

