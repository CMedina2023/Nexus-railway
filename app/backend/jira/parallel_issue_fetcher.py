"""
Servicio para obtención paralela de issues de Jira
Responsabilidad única: Gestionar paginación paralela con rate limiting
"""
import logging
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any
from threading import Lock

from app.backend.jira.connection import JiraConnection
from app.core.config import Config
from app.utils.exceptions import JiraAPIError

logger = logging.getLogger(__name__)


class ParallelIssueFetcher:
    """Servicio para obtener issues en paralelo con manejo de rate limiting"""
    
    def __init__(
        self,
        connection: JiraConnection,
        max_workers: int = None,
        max_results_per_page: int = None,
        request_timeout: int = None,
        retry_attempts: int = None,
        rate_limit_sleep: float = None
    ):
        """
        Inicializa el fetcher paralelo
        
        Args:
            connection: Conexión con Jira
            max_workers: Número máximo de workers paralelos (default: Config.JIRA_PARALLEL_MAX_WORKERS)
            max_results_per_page: Máximo de resultados por página (default: Config.JIRA_PARALLEL_MAX_RESULTS)
            request_timeout: Timeout por request en segundos (default: Config.JIRA_PARALLEL_REQUEST_TIMEOUT)
            retry_attempts: Número de reintentos por request (default: Config.JIRA_PARALLEL_RETRY_ATTEMPTS)
            rate_limit_sleep: Tiempo de espera entre requests para evitar rate limiting (default: Config.JIRA_PARALLEL_RATE_LIMIT_SLEEP)
        """
        self._connection = connection
        self._max_workers = max_workers or Config.JIRA_PARALLEL_MAX_WORKERS
        self._max_results_per_page = max_results_per_page or Config.JIRA_PARALLEL_MAX_RESULTS
        self._request_timeout = request_timeout or Config.JIRA_PARALLEL_REQUEST_TIMEOUT
        self._retry_attempts = retry_attempts or Config.JIRA_PARALLEL_RETRY_ATTEMPTS
        self._rate_limit_sleep = rate_limit_sleep or Config.JIRA_PARALLEL_RATE_LIMIT_SLEEP
        
        # Lock para sincronización de rate limiting
        self._rate_limit_lock = Lock()
        self._last_request_time = 0.0
        
        # Campos mínimos necesarios para métricas
        self._required_fields = 'key,summary,status,issuetype,priority,assignee,created,updated,resolution,labels,fixVersions,affectsVersions'
        
        logger.info(f"ParallelIssueFetcher inicializado: max_workers={self._max_workers}, "
                   f"max_results={self._max_results_per_page}, timeout={self._request_timeout}s")
    
    def _wait_for_rate_limit(self) -> None:
        """
        Espera el tiempo necesario para respetar el rate limiting
        """
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last_request = current_time - self._last_request_time
            
            if time_since_last_request < self._rate_limit_sleep:
                sleep_time = self._rate_limit_sleep - time_since_last_request
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    def _fetch_page(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        fields: Optional[str] = None,
        next_page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene una página de issues
        
        Args:
            jql: Query JQL
            start_at: Índice de inicio
            max_results: Máximo de resultados
            progress_callback: Callback opcional para reportar progreso (actual, total)
            fields: Campos a obtener (None = sin campos, solo key e id)
            next_page_token: Token de siguiente página (si está disponible, se usa en lugar de startAt)
            
        Returns:
            Dict con 'issues' (lista) y 'total' (int)
            
        Raises:
            JiraAPIError: Si hay error en la API
        """
        # Usar siempre GET con /rest/api/3/search/jql (el endpoint POST /rest/api/3/search fue removido)
        url = f"{self._connection.base_url}/rest/api/3/search/jql"
        
        # Reintentos con exponential backoff
        last_exception = None
        
        for attempt in range(self._retry_attempts):
            try:
                # Esperar para rate limiting
                self._wait_for_rate_limit()
                
                params = {
                    'jql': jql,
                    'maxResults': max_results
                }
                
                # Si hay nextPageToken, usarlo en lugar de startAt (más confiable)
                if next_page_token:
                    params['nextPageToken'] = next_page_token
                else:
                    params['startAt'] = start_at
                
                # Solo agregar fields si se especifica (None = sin fields para que la paginación funcione)
                if fields:
                    params['fields'] = fields
                
                logger.debug(f"Obteniendo página: startAt={start_at}, maxResults={max_results}, fields={'sí' if fields else 'no'} (intento {attempt + 1}/{self._retry_attempts})")
                
                response = self._connection.session.get(
                    url,
                    params=params,
                    timeout=self._request_timeout
                )
                
                # Manejar rate limiting (HTTP 429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', '60'))
                    logger.warning(f"Rate limit alcanzado (429). Esperando {retry_after} segundos...")
                    
                    if attempt < self._retry_attempts - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        raise JiraAPIError(
                            f"Rate limit después de {self._retry_attempts} intentos",
                            status_code=429,
                            response=response.text
                        )
                
                # Manejar otros errores HTTP
                if response.status_code != 200:
                    error_msg = f"Error HTTP {response.status_code}: {response.text}"
                    logger.error(f"Error al obtener página {start_at}: {error_msg}")
                    
                    if attempt < self._retry_attempts - 1:
                        # Exponential backoff
                        sleep_time = 2 ** attempt
                        logger.info(f"Reintentando en {sleep_time} segundos...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        raise JiraAPIError(
                            error_msg,
                            status_code=response.status_code,
                            response=response.text
                        )
                
                # Parsear respuesta
                data = response.json()
                issues = data.get('issues', [])
                total = data.get('total', 0)
                is_last = data.get('isLast', False)
                next_page_token = data.get('nextPageToken', None)
                
                # Reportar progreso si hay callback
                if progress_callback:
                    progress_callback(len(issues), total)
                
                return {
                    'issues': issues,
                    'total': total,
                    'isLast': is_last,
                    'nextPageToken': next_page_token
                }
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self._retry_attempts - 1:
                    sleep_time = 2 ** attempt
                    logger.warning(f"Error de conexión (intento {attempt + 1}/{self._retry_attempts}): {e}. Reintentando en {sleep_time} segundos...")
                    time.sleep(sleep_time)
                    continue
                else:
                    raise JiraAPIError(
                        f"Error de conexión después de {self._retry_attempts} intentos: {e}",
                        status_code=None,
                        response=str(e)
                    )
        
        # Si llegamos aquí, todos los intentos fallaron
        raise JiraAPIError(
            f"Error al obtener página después de {self._retry_attempts} intentos",
            status_code=None,
            response=str(last_exception) if last_exception else "Error desconocido"
        )
    
    def _get_approximate_count(self, jql: str) -> int:
        """
        Obtiene un conteo aproximado de issues usando el endpoint approximate-count
        Esto ayuda a evitar el bug donde total=0 pero hay issues
        
        Args:
            jql: Query JQL
            
        Returns:
            int: Conteo aproximado de issues
        """
        try:
            url = f"{self._connection.base_url}/rest/api/3/search/approximate-count"
            
            # Simplificar JQL para approximate-count (puede tener problemas con JQLs muy complejos)
            simplified_jql = self._simplify_jql_for_count(jql)
            
            logger.info(f"[APPROXIMATE-COUNT] JQL original: {jql[:200]}...")
            logger.info(f"[APPROXIMATE-COUNT] JQL simplificado: {simplified_jql[:200]}...")
            
            payload = {"jql": simplified_jql}
            
            self._wait_for_rate_limit()
            response = self._connection.session.post(
                url,
                json=payload,
                timeout=self._request_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                logger.info(f"[APPROXIMATE-COUNT] Conteo aproximado obtenido: {count}")
                return count
            else:
                logger.warning(f"[APPROXIMATE-COUNT] Error al obtener conteo: HTTP {response.status_code}: {response.text}")
                # Si falla con JQL simplificado, intentar con JQL original
                if simplified_jql != jql:
                    logger.info(f"[APPROXIMATE-COUNT] Intentando con JQL original...")
                    payload_original = {"jql": jql}
                    response_original = self._connection.session.post(
                        url,
                        json=payload_original,
                        timeout=self._request_timeout
                    )
                    if response_original.status_code == 200:
                        data_original = response_original.json()
                        count_original = data_original.get('count', 0)
                        logger.info(f"[APPROXIMATE-COUNT] Conteo con JQL original: {count_original}")
                        return count_original
                return 0
                
        except Exception as e:
            logger.error(f"[APPROXIMATE-COUNT] Error al obtener conteo aproximado: {e}", exc_info=True)
            return 0
    
    def _simplify_jql_for_count(self, jql: str) -> str:
        """
        Simplifica el JQL para approximate-count usando solo variaciones comunes de issuetype
        Esto ayuda cuando el endpoint tiene problemas con JQLs muy complejos
        
        Args:
            jql: Query JQL original
            
        Returns:
            str: JQL simplificado
        """
        # Extraer proyecto
        project_match = re.search(r'project\s*=\s*(\w+)', jql)
        if not project_match:
            return jql  # No se puede simplificar sin proyecto
        
        project_key = project_match.group(1)
        
        # Extraer filtros adicionales (después del bloque de issuetypes)
        # Buscar el patrón: ) AND filtros
        filters_match = re.search(r'\)\s*AND\s*(.+)', jql)
        additional_filters = filters_match.group(1) if filters_match else ''
        
        # Determinar si el JQL es para Test Cases, Bugs, o ambos
        has_test_case = any(v in jql for v in ['Test Case', 'test case', 'TestCase', 'Caso de Prueba'])
        has_bug = any(v in jql for v in ['Bug', 'bug', 'BUG', 'Error', 'error', 'Defect', 'defect'])
        
        # Construir JQL simplificado
        issuetype_parts = []
        if has_test_case:
            issuetype_parts.append('issuetype = "Test Case"')
        if has_bug:
            issuetype_parts.append('issuetype = "Bug"')
        
        if not issuetype_parts:
            return jql  # No hay issuetypes conocidos, retornar original
        
        simplified = f'project = {project_key} AND ({' OR '.join(issuetype_parts)})'
        if additional_filters:
            simplified += f' AND {additional_filters}'
        
        return simplified
    
    def _fetch_all_issues_without_fields(
        self,
        jql: str,
        total: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Obtiene todas las issues SIN especificar fields (solo key e id)
        Esto permite que la paginación funcione correctamente
        
        Args:
            jql: Query JQL
            total: Total aproximado de issues
            progress_callback: Callback opcional para reportar progreso
            
        Returns:
            List[Dict]: Lista de issues (solo con key e id)
        """
        logger.info(f"[FETCH SIN FIELDS] Obteniendo {total} issues sin fields para paginación correcta...")
        
        # Calcular número de páginas necesarias
        total_pages = (total + self._max_results_per_page - 1) // self._max_results_per_page
        
        logger.info(f"[FETCH SIN FIELDS] Calculando páginas: total={total}, max_results_per_page={self._max_results_per_page}, total_pages={total_pages}")
        
        # Crear lista de tareas (ranges de startAt)
        tasks = []
        for page in range(total_pages):
            start_at = page * self._max_results_per_page
            tasks.append(start_at)
        
        # Obtener issues en paralelo (sin fields)
        # IMPORTANTE: Si Jira ignora startAt, todas las páginas retornarán las mismas issues
        # Necesitamos detectar esto temprano y usar paginación secuencial
        all_issues = []
        completed = 0
        errors = []
        page_ids_map = {}  # Mapa de startAt -> primeros IDs para detectar duplicados
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Enviar todas las tareas
            future_to_start_at = {
                executor.submit(self._fetch_page, jql, start_at, self._max_results_per_page, None, fields=None):
                start_at
                for start_at in tasks
            }
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_start_at):
                start_at = future_to_start_at[future]
                try:
                    result = future.result()
                    issues = result.get('issues', [])
                    
                    # Verificar IDs de las primeras issues de cada página
                    if issues:
                        first_ids = [str(issue.get('id', 'N/A')) for issue in issues[:5]]  # Primeros 5 para mejor detección
                        page_ids_map[start_at] = first_ids
                        logger.info(f"[FETCH SIN FIELDS] Página startAt={start_at}: primeros 5 IDs = {first_ids}")
                        
                        # Detectar si esta página tiene los mismos IDs que la primera (startAt=0)
                        if start_at > 0 and 0 in page_ids_map:
                            if first_ids == page_ids_map[0][:len(first_ids)]:
                                logger.error(f"[FETCH SIN FIELDS] ⚠️ CRÍTICO: Página startAt={start_at} tiene los mismos IDs que startAt=0. Jira está ignorando startAt.")
                                logger.error(f"[FETCH SIN FIELDS] ⚠️ Esto significa que Jira retorna siempre las primeras 100 issues sin importar startAt.")
                                logger.error(f"[FETCH SIN FIELDS] ⚠️ Cambiando a paginación SECUENCIAL usando nextPageToken si está disponible.")
                                # Cancelar otras tareas pendientes
                                for f in future_to_start_at:
                                    if f != future:
                                        f.cancel()
                                # Obtener la primera página completa
                                first_page_result = None
                                for f, sa in future_to_start_at.items():
                                    if sa == 0:
                                        try:
                                            first_page_result = f.result()
                                        except:
                                            pass
                                        break
                                
                                if first_page_result:
                                    # Usar paginación secuencial normal (ya maneja nextPageToken)
                                    initial_issues = first_page_result.get('issues', [])
                                    return self._fetch_all_issues_sequential(
                                        jql,
                                        initial_issues,
                                        first_page_result.get('isLast', False),
                                        first_page_result.get('nextPageToken'),
                                        total,
                                        progress_callback
                                    )
                                break
                    
                    all_issues.extend(issues)
                    completed += 1
                    
                    logger.info(f"[FETCH SIN FIELDS] Página completada: startAt={start_at}, issues={len(issues)}, "
                              f"total acumulado={len(all_issues)}, completadas={completed}/{total_pages}")
                    
                    if progress_callback:
                        progress_callback(len(all_issues), total)
                    
                except Exception as e:
                    error_msg = f"Error al obtener página startAt={start_at}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors.append({
                        'start_at': start_at,
                        'error': str(e)
                    })
        
        # Si detectamos el bug, usar solo la primera página
        if len(all_issues) > 0 and len(page_ids_map) > 1:
            first_page_ids = page_ids_map.get(0, [])
            all_same = all(
                page_ids_map.get(start_at, [])[:len(first_page_ids)] == first_page_ids[:len(page_ids_map.get(start_at, []))]
                for start_at in page_ids_map
                if start_at > 0
            )
            if all_same:
                logger.error(f"[FETCH SIN FIELDS] ⚠️ CONFIRMADO: Todas las páginas tienen los mismos IDs. Bug de Jira detectado.")
                logger.warning(f"[FETCH SIN FIELDS] Usando solo las primeras 100 issues debido a limitación de Jira.")
                # Mantener solo las primeras 100 issues
                all_issues = all_issues[:100]
        
        # Verificar si hubo errores críticos
        if errors and len(errors) >= total_pages / 2:
            error_summary = f"{len(errors)} de {total_pages} páginas fallaron"
            logger.error(f"Muchos errores en obtención sin fields: {error_summary}")
            raise JiraAPIError(
                f"Error crítico en obtención sin fields: {error_summary}",
                status_code=None,
                response=str(errors)
            )
        
        # Eliminar duplicados por key
        # Cuando no hay fields, Jira siempre retorna 'key' en el nivel superior
        seen_keys = set()
        unique_issues = []
        issues_without_key = []
        
        # Debug: ver estructura de las primeras issues
        if all_issues:
            sample_issues = all_issues[:3]  # Primeras 3 issues
            for idx, issue in enumerate(sample_issues):
                if isinstance(issue, dict):
                    logger.info(f"[FETCH SIN FIELDS] Issue {idx} - keys disponibles: {list(issue.keys())}")
                    logger.info(f"[FETCH SIN FIELDS] Issue {idx} - key: {issue.get('key')}, id: {issue.get('id')}")
        
        for issue in all_issues:
            # Cuando no hay fields, Jira solo retorna 'id', NO 'key'
            # Usar 'id' para identificar issues únicas
            issue_id = None
            issue_key = None
            if isinstance(issue, dict):
                issue_id = issue.get('id')
                issue_key = issue.get('key')  # Puede no estar presente
            
            # Usar id como identificador principal (siempre está presente)
            if issue_id:
                # Convertir id a string para comparación consistente
                issue_id_str = str(issue_id)
                if issue_id_str not in seen_keys:
                    seen_keys.add(issue_id_str)
                    unique_issues.append(issue)
                else:
                    # Duplicado real - loguear para debug
                    logger.debug(f"[FETCH SIN FIELDS] Duplicado detectado por id: {issue_id_str}")
            else:
                # Issues sin id - no debería pasar, pero las agregamos
                issues_without_key.append(issue)
                unique_issues.append(issue)  # Incluir para no perder datos
        
        if issues_without_key:
            logger.warning(f"[FETCH SIN FIELDS] ⚠️ {len(issues_without_key)} issues sin key detectadas. Muestra: {str(issues_without_key[0])[:300] if issues_without_key else 'N/A'}")
        
        if len(unique_issues) != len(all_issues):
            logger.warning(f"[FETCH SIN FIELDS] Se encontraron {len(all_issues) - len(unique_issues)} issues duplicadas (total: {len(all_issues)}, únicas: {len(unique_issues)})")
            logger.info(f"[FETCH SIN FIELDS] Muestra de keys únicas: {list(seen_keys)[:10] if seen_keys else 'ninguna'}")
        
        logger.info(f"[FETCH SIN FIELDS] ✓ Obtenidas {len(unique_issues)} issues únicas sin fields (con key: {len(seen_keys)}, sin key: {len(issues_without_key)})")
        return unique_issues
    
    def _get_id_range(self, jql: str) -> Optional[tuple[int, int]]:
        """
        Obtiene el rango de IDs (mínimo y máximo) para las issues que coinciden con el JQL
        
        Args:
            jql: Query JQL
            
        Returns:
            tuple(min_id, max_id) o None si no se puede obtener
        """
        try:
            # Obtener primera issue para obtener min_id
            first_page = self._fetch_page(
                f"{jql} ORDER BY id ASC",
                start_at=0,
                max_results=1,
                fields=None
            )
            first_issues = first_page.get('issues', [])
            if not first_issues:
                return None
            
            min_id = None
            for issue in first_issues:
                issue_id = issue.get('id')
                if issue_id:
                    try:
                        min_id = int(issue_id)
                        break
                    except (ValueError, TypeError):
                        continue
            
            if min_id is None:
                return None
            
            # Obtener última issue para obtener max_id
            last_page = self._fetch_page(
                f"{jql} ORDER BY id DESC",
                start_at=0,
                max_results=1,
                fields=None
            )
            last_issues = last_page.get('issues', [])
            if not last_issues:
                return None
            
            max_id = None
            for issue in last_issues:
                issue_id = issue.get('id')
                if issue_id:
                    try:
                        max_id = int(issue_id)
                        break
                    except (ValueError, TypeError):
                        continue
            
            if max_id is None:
                return None
            
            return (min_id, max_id)
            
        except Exception as e:
            logger.error(f"[PAGINACIÓN POR ID] Error al obtener rango de IDs: {e}", exc_info=True)
            return None
    
    def _fetch_range_parallel(self, jql_base: str, min_id: int, max_id: int) -> List[Dict]:
        """
        Obtiene issues en un rango específico de IDs
        
        Args:
            jql_base: JQL base sin filtros de ID
            min_id: ID mínimo (inclusive)
            max_id: ID máximo (inclusive)
            
        Returns:
            List[Dict]: Lista de issues en el rango
        """
        # Construir JQL con rango de IDs
        jql_with_range = f"{jql_base} AND id >= {min_id} AND id <= {max_id} ORDER BY id ASC"
        
        all_issues = []
        last_id = min_id - 1  # Empezar desde min_id - 1 para incluir min_id
        page_size = self._max_results_per_page
        max_pages = 50  # Límite de seguridad por rango
        
        pages_fetched = 0
        while pages_fetched < max_pages:
            # Construir JQL con filtro de ID
            if last_id >= min_id:
                jql_with_id = jql_base.replace('ORDER BY', f'AND id > {last_id} AND id <= {max_id} ORDER BY')
            else:
                jql_with_id = jql_with_range
            
            try:
                page_result = self._fetch_page(
                    jql_with_id,
                    start_at=0,
                    max_results=page_size,
                    fields=None
                )
                
                page_issues = page_result.get('issues', [])
                
                if not page_issues:
                    break
                
                # Obtener el ID de la última issue de esta página
                last_issue_id = None
                for issue in page_issues:
                    issue_id = issue.get('id')
                    if issue_id:
                        try:
                            issue_id_int = int(issue_id)
                            if issue_id_int > max_id:
                                # Si el ID excede el rango, parar
                                break
                            if last_issue_id is None or issue_id_int > last_issue_id:
                                last_issue_id = issue_id_int
                        except (ValueError, TypeError):
                            continue
                
                if last_issue_id is None or last_issue_id > max_id:
                    # Agregar las issues válidas antes de parar
                    valid_issues = [issue for issue in page_issues 
                                   if issue.get('id') and int(issue.get('id', 0)) <= max_id]
                    all_issues.extend(valid_issues)
                    break
                
                all_issues.extend(page_issues)
                pages_fetched += 1
                
                # Si obtuvimos menos issues que el tamaño de página, probablemente es la última página
                if len(page_issues) < page_size:
                    break
                
                last_id = last_issue_id
                
            except Exception as e:
                logger.error(f"[PAGINACIÓN POR ID] Error en rango {min_id}-{max_id}, página {pages_fetched + 1}: {e}")
                break
        
        return all_issues
    
    def _fetch_all_issues_by_id_range(
        self,
        jql: str,
        total: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        fields: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene todas las issues usando paginación basada en rangos de ID
        Esta estrategia evita los bugs de startAt y nextPageToken
        Como usamos id > last_id, podemos obtener fields directamente
        
        Args:
            jql: Query JQL (se agregará ORDER BY id ASC si no está presente)
            total: Total aproximado de issues
            progress_callback: Callback opcional para reportar progreso
            fields: Campos a obtener (None = sin campos, solo key e id)
            
        Returns:
            List[Dict]: Lista completa de issues únicas
        """
        # Usar el método secuencial que funciona correctamente
        return self._fetch_all_issues_by_id_range_sequential(jql, total, progress_callback, fields)
    
    def _fetch_all_issues_by_id_range_sequential(
        self,
        jql: str,
        total: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        fields: Optional[str] = None
    ) -> List[Dict]:
        """
        Método secuencial basado en ID que puede obtener fields directamente
        Como usamos id > last_id en lugar de startAt, debería funcionar incluso con fields
        
        Args:
            jql: Query JQL
            total: Total aproximado de issues
            progress_callback: Callback opcional para reportar progreso
            fields: Campos a obtener (None = sin campos, solo key e id)
        """
        fields_desc = "con fields" if fields else "sin fields"
        logger.info(f"[PAGINACIÓN POR ID SECUENCIAL] Iniciando paginación secuencial basada en ID para {total} issues ({fields_desc})...")
        
        all_issues = []
        last_id = None
        page_size = self._max_results_per_page
        max_pages = (total // page_size) + 10  # Límite de seguridad
        pages_fetched = 0
        
        # Asegurar que el JQL tiene ORDER BY id ASC
        jql_base = jql.strip()
        if 'ORDER BY' not in jql_base.upper():
            jql_base = f"{jql_base} ORDER BY id ASC"
        elif 'ORDER BY id ASC' not in jql_base.upper():
            # Reemplazar cualquier ORDER BY existente
            jql_base = re.sub(r'\s+ORDER BY\s+[^$]+', '', jql_base, flags=re.IGNORECASE)
            jql_base = f"{jql_base} ORDER BY id ASC"
        
        while pages_fetched < max_pages:
            # Construir JQL con filtro de ID
            if last_id is not None:
                # Agregar condición id > last_id
                if 'ORDER BY' in jql_base:
                    # Insertar antes de ORDER BY
                    jql_with_id = jql_base.replace('ORDER BY', f'AND id > {last_id} ORDER BY')
                else:
                    jql_with_id = f"{jql_base} AND id > {last_id}"
            else:
                jql_with_id = jql_base
            
            logger.info(f"[PAGINACIÓN POR ID SECUENCIAL] Página {pages_fetched + 1}: obteniendo issues con id > {last_id if last_id else 'inicial'} ({fields_desc})...")
            
            try:
                # Obtener página - ahora podemos usar fields porque usamos id > last_id, no startAt
                page_result = self._fetch_page(
                    jql_with_id,
                    start_at=0,  # Siempre empezar desde 0 con esta estrategia
                    max_results=page_size,
                    progress_callback=None,
                    fields=fields  # Ahora podemos usar fields directamente
                )
                
                page_issues = page_result.get('issues', [])
                
                if not page_issues:
                    logger.info(f"[PAGINACIÓN POR ID SECUENCIAL] No hay más issues. Total obtenidas: {len(all_issues)}")
                    break
                
                # Obtener el ID de la última issue de esta página
                last_issue_id = None
                for issue in page_issues:
                    issue_id = issue.get('id')
                    if issue_id:
                        try:
                            issue_id_int = int(issue_id)
                            if last_issue_id is None or issue_id_int > last_issue_id:
                                last_issue_id = issue_id_int
                        except (ValueError, TypeError):
                            continue
                
                if last_issue_id is None:
                    logger.warning(f"[PAGINACIÓN POR ID SECUENCIAL] No se pudo obtener ID de issues. Deteniendo.")
                    break
                
                # Agregar issues (verificar duplicados por ID)
                seen_ids = {str(issue.get('id')) for issue in all_issues if issue.get('id')}
                new_issues = []
                for issue in page_issues:
                    issue_id_str = str(issue.get('id', ''))
                    if issue_id_str and issue_id_str not in seen_ids:
                        seen_ids.add(issue_id_str)
                        new_issues.append(issue)
                
                all_issues.extend(new_issues)
                pages_fetched += 1
                
                logger.info(f"[PAGINACIÓN POR ID SECUENCIAL] Página {pages_fetched}: {len(new_issues)} issues nuevas "
                           f"(total acumulado: {len(all_issues)}, último ID: {last_issue_id})")
                
                if progress_callback:
                    progress_callback(len(all_issues), total)
                
                # Si obtuvimos menos issues que el tamaño de página, probablemente es la última página
                if len(page_issues) < page_size:
                    logger.info(f"[PAGINACIÓN POR ID SECUENCIAL] Página incompleta ({len(page_issues)} < {page_size}). Finalizando.")
                    break
                
                # Actualizar last_id para la siguiente iteración
                last_id = last_issue_id
                
            except Exception as e:
                logger.error(f"[PAGINACIÓN POR ID SECUENCIAL] Error en página {pages_fetched + 1}: {e}", exc_info=True)
                # Si hay error, intentar continuar con el siguiente ID
                if last_id is not None:
                    last_id += 1  # Incrementar en 1 para evitar bucle infinito
                else:
                    break
        
        logger.info(f"[PAGINACIÓN POR ID SECUENCIAL] ✓ Completada: {len(all_issues)} issues únicas obtenidas en {pages_fetched} páginas")
        return all_issues
    
    def _fetch_issue_details(self, issue_identifier: str) -> Optional[Dict]:
        """
        Obtiene los detalles completos de una issue individual
        
        Args:
            issue_identifier: Key o ID de la issue (ej: PDCN-123 o 123456)
            
        Returns:
            Dict con los detalles de la issue o None si hay error
        """
        url = f"{self._connection.base_url}/rest/api/3/issue/{issue_identifier}"
        
        params = {
            'fields': self._required_fields
        }
        
        try:
            self._wait_for_rate_limit()
            response = self._connection.session.get(
                url,
                params=params,
                timeout=self._request_timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"[FETCH DETAILS] Issue {issue_identifier} no encontrada (404)")
                return None
            else:
                logger.error(f"[FETCH DETAILS] Error al obtener issue {issue_identifier}: HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"[FETCH DETAILS] Error al obtener issue {issue_identifier}: {e}", exc_info=True)
            return None
    
    def _fetch_issues_details_parallel(
        self,
        issue_keys: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Obtiene los detalles completos de múltiples issues en paralelo
        
        Args:
            issue_keys: Lista de keys de issues
            progress_callback: Callback opcional para reportar progreso
            
        Returns:
            List[Dict]: Lista de issues con campos completos
        """
        if not issue_keys:
            return []
        
        logger.info(f"[FETCH DETAILS PARALLEL] Obteniendo detalles de {len(issue_keys)} issues en paralelo...")
        
        all_issues = []
        completed = 0
        errors = []
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Enviar todas las tareas
            future_to_key = {
                executor.submit(self._fetch_issue_details, key): key
                for key in issue_keys
            }
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    issue = future.result()
                    if issue:
                        all_issues.append(issue)
                    completed += 1
                    
                    if completed % 50 == 0 or completed == len(issue_keys):
                        logger.info(f"[FETCH DETAILS PARALLEL] Progreso: {completed}/{len(issue_keys)} issues obtenidas")
                    
                    if progress_callback:
                        progress_callback(completed, len(issue_keys))
                    
                except Exception as e:
                    error_msg = f"Error al obtener issue {key}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors.append({
                        'key': key,
                        'error': str(e)
                    })
        
        if errors:
            logger.warning(f"[FETCH DETAILS PARALLEL] Se encontraron {len(errors)} errores al obtener detalles")
        
        logger.info(f"[FETCH DETAILS PARALLEL] ✓ Obtenidas {len(all_issues)} issues con campos completos de {len(issue_keys)} solicitadas")
        return all_issues
    
    def fetch_all_issues_parallel(
        self,
        jql: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Obtiene todas las issues usando paginación paralela
        
        Args:
            jql: Query JQL
            progress_callback: Callback opcional para reportar progreso (actual, total)
            
        Returns:
            List[Dict]: Lista completa de issues
        """
        logger.info(f"Iniciando obtención paralela de issues con JQL: {jql[:100]}...")
        
        # Obtener total usando approximate-count (evita bug de total=0)
        total = self._get_approximate_count(jql)
        
        # Obtener primera página para tener las issues iniciales
        try:
            logger.info(f"[DEBUG JQL] Obteniendo primera página de issues con JQL: {jql}")
            # Obtener primera página sin fields para verificar que hay issues
            initial_page = self._fetch_page(jql, start_at=0, max_results=1, progress_callback=None, fields=None)
            initial_issues = initial_page.get('issues', [])
            
            logger.info(f"[DEBUG JQL] Total aproximado obtenido: {total}")
            logger.info(f"[DEBUG JQL] Issues en petición inicial: {len(initial_issues)}")
            
            # Función helper para detectar si el total es sospechoso (puede ser un límite artificial)
            def is_suspicious_total(t: int) -> bool:
                """Detecta si el total puede ser un límite artificial de Jira"""
                if t == 0:
                    return False
                # IMPORTANTE: Cuando se especifican 'fields' en la query, Jira SIEMPRE limita a 100 issues por página
                # Por lo tanto, cualquier total que sea múltiplo de 100 puede ser sospechoso
                # Si es exactamente 100, 1000, 5000 (límites comunes de Jira)
                if t in [100, 1000, 5000]:
                    return True
                # Si es un múltiplo exacto de 100, puede ser sospechoso (especialmente cuando hay fields)
                if t % 100 == 0:
                    return True
                return False
            
            # Si total es 0 y no hay issues, no hay resultados
            if total == 0 and len(initial_issues) == 0:
                logger.warning(f"[DEBUG JQL] No hay issues que coincidan con el JQL: {jql[:100]}...")
                return []
            
            # Si total es 0 pero hay issues, usar paginación por ID (más confiable que secuencial)
            if total == 0 and len(initial_issues) > 0:
                logger.warning(f"[DEBUG JQL] ⚠️ Total aproximado=0 pero hay {len(initial_issues)} issue(s). Usando paginación por ID.")
                # Estimar un total razonable para la paginación por ID
                estimated_total = 1000  # Estimación conservadora
                # Obtener fields directamente si están requeridos
                return self._fetch_all_issues_by_id_range(
                    jql, 
                    estimated_total, 
                    progress_callback,
                    fields=self._required_fields if self._required_fields else None
                )
            
            # Si total es sospechoso (múltiplo de 100), usar paginación por ID para estar seguros
            if is_suspicious_total(total):
                logger.warning(f"[DEBUG JQL] ⚠️ Total sospechoso: {total}. Usando paginación por ID.")
                # Obtener fields directamente si están requeridos
                return self._fetch_all_issues_by_id_range(
                    jql, 
                    total, 
                    progress_callback,
                    fields=self._required_fields if self._required_fields else None
                )
            
            logger.info(f"Total de issues a obtener: {total}")
            
            # ESTRATEGIA: Usar paginación basada en ID para evitar bugs de startAt/nextPageToken
            # Como usamos id > last_id en lugar de startAt, podemos obtener fields directamente
            if self._required_fields:
                logger.info(f"[DEBUG PAGINACIÓN] ⚠️ Fields especificados detectados. Usando paginación por ID con fields directamente:")
                logger.info(f"[DEBUG PAGINACIÓN] Como usamos 'id > last_id' en lugar de 'startAt', podemos obtener fields directamente")
                logger.info(f"[DEBUG PAGINACIÓN] Esto evita las {total} requests individuales y es mucho más rápido")
                
                # Obtener todas las issues CON fields directamente usando paginación por ID
                all_issues = self._fetch_all_issues_by_id_range(
                    jql,
                    total,
                    progress_callback,
                    fields=self._required_fields  # Obtener fields directamente
                )
                
                logger.info(f"[DEBUG PAGINACIÓN] ✓ Obtenidas {len(all_issues)} issues con campos completos directamente")
                return all_issues
            else:
                # Si no hay fields requeridos, usar paginación por ID también
                logger.info(f"[DEBUG PAGINACIÓN] Usando paginación basada en ID (sin fields requeridos)")
                return self._fetch_all_issues_by_id_range(jql, total, progress_callback)
            
        except Exception as e:
            logger.error(f"Error al obtener total de issues: {e}")
            raise
        
        # Calcular número de páginas necesarias
        total_pages = (total + self._max_results_per_page - 1) // self._max_results_per_page
        
        logger.info(f"[DEBUG PAGINACIÓN] Calculando páginas: total={total}, max_results_per_page={self._max_results_per_page}, total_pages={total_pages}")
        logger.info(f"Obteniendo {total} issues en {total_pages} páginas con {self._max_workers} workers")
        
        # Crear lista de tareas (ranges de startAt)
        tasks = []
        for page in range(total_pages):
            start_at = page * self._max_results_per_page
            tasks.append(start_at)
        
        # Obtener issues en paralelo
        all_issues = []
        completed = 0
        errors = []
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Enviar todas las tareas (sin fields para que la paginación funcione)
            future_to_start_at = {
                executor.submit(self._fetch_page, jql, start_at, self._max_results_per_page, progress_callback, fields=None):
                start_at
                for start_at in tasks
            }
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_start_at):
                start_at = future_to_start_at[future]
                try:
                    result = future.result()
                    issues = result.get('issues', [])
                    all_issues.extend(issues)
                    completed += 1
                    
                    logger.info(f"Página completada: startAt={start_at}, issues={len(issues)}, "
                              f"total acumulado={len(all_issues)}, completadas={completed}/{total_pages}")
                    
                except Exception as e:
                    error_msg = f"Error al obtener página startAt={start_at}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors.append({
                        'start_at': start_at,
                        'error': str(e)
                    })
        
        # Verificar si hubo errores críticos
        if errors and len(errors) >= total_pages / 2:
            error_summary = f"{len(errors)} de {total_pages} páginas fallaron"
            logger.error(f"Muchos errores en obtención paralela: {error_summary}")
            raise JiraAPIError(
                f"Error crítico en obtención paralela: {error_summary}",
                status_code=None,
                response=str(errors)
            )
        
        # Ordenar issues por start_at para mantener orden consistente
        # Como ya vienen ordenadas, solo necesitamos verificar que no haya duplicados
        seen_keys = set()
        unique_issues = []
        for issue in all_issues:
            issue_key = issue.get('key')
            if issue_key and issue_key not in seen_keys:
                seen_keys.add(issue_key)
                unique_issues.append(issue)
            elif not issue_key:
                # Issues sin key son inválidas pero las incluimos para no perder datos
                unique_issues.append(issue)
        
        # Si hay diferencias, loguear
        if len(unique_issues) != len(all_issues):
            logger.warning(f"Se encontraron {len(all_issues) - len(unique_issues)} issues duplicadas")
        
        logger.info(f"[DEBUG PAGINACIÓN] Obtención paralela completada: {len(unique_issues)} issues únicas de {len(all_issues)} obtenidas (total esperado: {total})")
        
        # Verificar si obtuvimos todas las issues esperadas
        if len(unique_issues) < total:
            logger.warning(f"[DEBUG PAGINACIÓN] ⚠️ ADVERTENCIA: Se obtuvieron {len(unique_issues)} issues pero se esperaban {total}. Puede haber un problema con la paginación.")
        elif len(unique_issues) > total:
            logger.warning(f"[DEBUG PAGINACIÓN] ⚠️ ADVERTENCIA: Se obtuvieron {len(unique_issues)} issues pero se esperaban {total}. Puede haber duplicados o el total era incorrecto.")
        else:
            logger.info(f"[DEBUG PAGINACIÓN] ✓ Todas las issues obtenidas correctamente: {len(unique_issues)} == {total}")
        
        return unique_issues

    def _fetch_all_issues_sequential(
        self,
        jql: str,
        initial_issues: List[Dict],
        initial_is_last: bool,
        initial_next_token: Optional[str],
        total: int = 0,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Obtiene todas las issues usando paginación secuencial basada en "página incompleta".
        Esta estrategia ignora el campo 'total' y se detiene cuando una página retorna
        menos issues que maxResults (página incompleta = última página).
        
        Args:
            jql: Query JQL
            initial_issues: Issues de la primera página
            initial_is_last: Si la primera página es la última
            initial_next_token: Token de siguiente página de la primera respuesta
            progress_callback: Callback opcional para reportar progreso
            
        Returns:
            List[Dict]: Lista completa de issues
        """
        logger.info(f"[PAGINACIÓN SECUENCIAL] Iniciando paginación secuencial basada en página incompleta")
        
        all_issues = list(initial_issues)
        start_at = len(initial_issues)
        page_size = self._max_results_per_page
        
        # Límites de seguridad estrictos
        # Si total=0, usar límite más alto porque necesitamos obtener todas las issues aunque Jira tenga el bug
        max_issues_limit = 10000
        max_pages_limit = 50 if total == 0 else 100  # Límite más alto cuando total=0 (50 páginas = 5000 issues máximo)
        
        if total == 0:
            logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Total=0: usando límite de {max_pages_limit} páginas para obtener todas las issues")
        
        pages_fetched = 0
        is_last = initial_is_last
        next_token = initial_next_token
        consecutive_duplicate_pages = 0  # Contador de páginas duplicadas consecutivas
        
        # Si la primera página ya es la última, retornar
        if is_last or not next_token:
            logger.info(f"[PAGINACIÓN SECUENCIAL] Primera página es la última. Retornando {len(all_issues)} issues.")
            if progress_callback:
                progress_callback(len(all_issues), len(all_issues))
            return all_issues
        
        # Reportar progreso inicial
        if progress_callback:
            progress_callback(len(all_issues), len(all_issues) + page_size)  # Estimación conservadora
        
        logger.info(f"[PAGINACIÓN SECUENCIAL] Obteniendo páginas adicionales (startAt={start_at}, page_size={page_size})")
        
        while True:
            # Verificar límites de seguridad
            if len(all_issues) >= max_issues_limit:
                logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Límite de seguridad alcanzado: {len(all_issues)} issues. Deteniendo.")
                break
            
            if pages_fetched >= max_pages_limit:
                logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Límite de páginas alcanzado: {pages_fetched} páginas. Deteniendo.")
                break
            
            try:
                logger.info(f"[PAGINACIÓN SECUENCIAL] Obteniendo página {pages_fetched + 1}/{max_pages_limit}: startAt={start_at}, maxResults={page_size}")
                
                page_result = self._fetch_page(
                    jql, 
                    start_at=start_at, 
                    max_results=page_size, 
                    progress_callback=None,
                    fields=None,  # Sin fields para que la paginación funcione
                    next_page_token=next_token  # Usar nextPageToken si está disponible
                )
                
                page_issues = page_result.get('issues', [])
                is_last = page_result.get('isLast', False)
                next_token = page_result.get('nextPageToken', None)
                
                logger.info(f"[PAGINACIÓN SECUENCIAL] Página obtenida: {len(page_issues)} issues (page_size={page_size})")
                
                # Si no hay issues, parar (página vacía = última página)
                if not page_issues:
                    logger.info(f"[PAGINACIÓN SECUENCIAL] Página vacía - finalizando")
                    break
                
                # Detectar duplicados ANTES de agregar
                # Cuando no hay fields, las issues solo tienen 'id', no 'key'
                is_duplicate_page = False
                # Siempre detectar duplicados cuando no hay fields (fields=None significa sin fields)
                if total == 0 or self._required_fields:
                    # Obtener IDs de las issues de esta página (cuando no hay fields, solo tienen id)
                    page_ids = {str(issue.get('id', '')) for issue in page_issues if issue.get('id')}
                    # Si no hay IDs, intentar con keys
                    if not page_ids:
                        page_ids = {issue.get('key', '') for issue in page_issues if issue.get('key')}
                    
                    # Obtener IDs de las issues ya agregadas
                    existing_ids = {str(issue.get('id', '')) for issue in all_issues if issue.get('id')}
                    # Si no hay IDs, intentar con keys
                    if not existing_ids:
                        existing_ids = {issue.get('key', '') for issue in all_issues if issue.get('key')}
                    
                    # Si todas las issues de esta página ya están en las anteriores, es un duplicado (bug de Jira)
                    if page_ids and page_ids.issubset(existing_ids):
                        is_duplicate_page = True
                        consecutive_duplicate_pages += 1
                        logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Página {pages_fetched + 1} completa de duplicados detectada ({consecutive_duplicate_pages} consecutivas). Todas las {len(page_issues)} issues ya existen.")
                        
                        # CRÍTICO: Cuando hay fields, Jira ignora completamente startAt y siempre retorna
                        # las primeras 100 issues. No hay forma de obtener más issues únicas.
                        # Detener inmediatamente después de la primera página duplicada.
                        if self._required_fields:
                            logger.error(
                                f"[PAGINACIÓN SECUENCIAL] ⚠️ LIMITACIÓN DE JIRA: Cuando se especifican 'fields', "
                                f"Jira ignora el parámetro 'startAt' y siempre retorna las primeras 100 issues. "
                                f"Se obtuvieron {len(all_issues)} issues únicas de {total} esperadas. "
                                f"Esta es una limitación conocida de la API de Jira cuando se usan campos específicos."
                            )
                            break
                        
                        # Para total=0 (sin fields), intentar una vez más antes de detener
                        if consecutive_duplicate_pages >= 2:
                            logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ {consecutive_duplicate_pages} páginas consecutivas de duplicados. Deteniendo por bug de Jira.")
                            break
                        else:
                            # Saltar esta página duplicada pero continuar (solo para total=0)
                            logger.info(f"[PAGINACIÓN SECUENCIAL] Saltando página duplicada pero continuando...")
                            start_at += len(page_issues)
                            pages_fetched += 1
                            continue
                    else:
                        # Resetear contador si esta página no es duplicada
                        consecutive_duplicate_pages = 0
                
                # Agregar issues
                all_issues.extend(page_issues)
                
                # Si tenemos un total confiable y ya lo alcanzamos, parar
                if total > 0 and len(all_issues) >= total:
                    logger.info(f"[PAGINACIÓN SECUENCIAL] Total alcanzado: {len(all_issues)} >= {total}")
                    break
                
                # CRITERIO SIMPLE: Si la página está incompleta (< page_size), es la última página
                # EXCEPCIÓN: Si total es confiable y aún no lo alcanzamos, continuar
                if len(page_issues) < page_size:
                    # Si tenemos un total confiable y aún no lo alcanzamos, puede haber más páginas
                    if total > 0 and len(all_issues) < total:
                        logger.info(f"[PAGINACIÓN SECUENCIAL] Página incompleta ({len(page_issues)} < {page_size}) pero aún faltan issues ({len(all_issues)} < {total}). Continuando...")
                        # Continuar una página más
                        start_at += len(page_issues)
                        pages_fetched += 1
                        continue
                    else:
                        logger.info(f"[PAGINACIÓN SECUENCIAL] Página incompleta ({len(page_issues)} < {page_size}) - ÚLTIMA PÁGINA detectada")
                        break
                
                # Si la página está llena (== page_size), continuar iterando (hay más páginas)
                logger.debug(f"[PAGINACIÓN SECUENCIAL] Página llena ({len(page_issues)} == {page_size}) - continuando a siguiente página")
                start_at += len(page_issues)
                pages_fetched += 1
                
                # Reportar progreso
                if progress_callback:
                    progress_callback(len(all_issues), total if total > 0 else len(all_issues) + page_size)
                
            except Exception as e:
                logger.error(f"[PAGINACIÓN SECUENCIAL] Error al obtener página {pages_fetched + 1}: {e}", exc_info=True)
                break
        
        # Eliminar duplicados por id (cuando no hay fields, solo tienen id, no key)
        seen_ids = set()
        unique_issues = []
        for issue in all_issues:
            # Preferir id (siempre está presente cuando no hay fields)
            issue_id = issue.get('id')
            issue_key = issue.get('key')
            
            # Usar id como identificador principal
            if issue_id:
                issue_id_str = str(issue_id)
                if issue_id_str not in seen_ids:
                    seen_ids.add(issue_id_str)
                    unique_issues.append(issue)
            elif issue_key:
                # Fallback a key si no hay id
                if issue_key not in seen_ids:
                    seen_ids.add(issue_key)
                    unique_issues.append(issue)
            else:
                # Issues sin id ni key - incluirlas para no perder datos
                unique_issues.append(issue)
        
        if len(unique_issues) != len(all_issues):
            logger.warning(f"[PAGINACIÓN SECUENCIAL] Se encontraron {len(all_issues) - len(unique_issues)} issues duplicadas")
        
        logger.info(f"[PAGINACIÓN SECUENCIAL] Completada: {len(unique_issues)} issues únicas de {len(all_issues)} total")
        
        if progress_callback:
            progress_callback(len(unique_issues), len(unique_issues))
        
        return unique_issues
