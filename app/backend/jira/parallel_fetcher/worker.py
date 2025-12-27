import logging
import time
import requests
from typing import Dict, Any, Optional, Callable
from app.utils.exceptions import JiraAPIError
from app.backend.jira.connection import JiraConnection
from app.backend.jira.parallel_fetcher.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class Worker:
    """Worker para realizar peticiones individuales a Jira"""
    
    def __init__(
        self,
        connection: JiraConnection,
        rate_limiter: RateLimiter,
        request_timeout: int,
        retry_attempts: int
    ):
        self._connection = connection
        self._rate_limiter = rate_limiter
        self._request_timeout = request_timeout
        self._retry_attempts = retry_attempts
        
    def fetch_page(
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
        """
        # Usar siempre GET con /rest/api/3/search/jql
        url = f"{self._connection.base_url}/rest/api/3/search/jql"
        
        last_exception = None
        
        for attempt in range(self._retry_attempts):
            try:
                # Esperar para rate limiting
                self._rate_limiter.wait()
                
                params = {
                    'jql': jql,
                    'maxResults': max_results
                }
                
                # Si hay nextPageToken, usarlo en lugar de startAt
                if next_page_token:
                    params['nextPageToken'] = next_page_token
                else:
                    params['startAt'] = start_at
                
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
                next_page_token_resp = data.get('nextPageToken', None)
                
                if progress_callback:
                    progress_callback(len(issues), total)
                
                return {
                    'issues': issues,
                    'total': total,
                    'isLast': is_last,
                    'nextPageToken': next_page_token_resp
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
        
        raise JiraAPIError(
            f"Error al obtener página después de {self._retry_attempts} intentos",
            status_code=None,
            response=str(last_exception) if last_exception else "Error desconocido"
        )

    def fetch_issue_details(self, issue_identifier: str, fields: str) -> Optional[Dict]:
        """
        Obtiene los detalles completos de una issue individual
        """
        url = f"{self._connection.base_url}/rest/api/3/issue/{issue_identifier}"
        
        params = {
            'fields': fields
        }
        
        try:
            self._rate_limiter.wait()
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
