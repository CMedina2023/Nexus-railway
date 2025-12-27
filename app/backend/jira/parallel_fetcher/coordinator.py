import logging
import time
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.backend.jira.connection import JiraConnection
from app.core.config import Config
from app.utils.exceptions import JiraAPIError
from app.backend.jira.parallel_fetcher.rate_limiter import RateLimiter
from app.backend.jira.parallel_fetcher.worker import Worker
from app.backend.jira.parallel_fetcher.utils.jql_helper import JQLHelper
from app.backend.jira.parallel_fetcher.strategies.sequential import SequentialPaginationStrategy
from app.backend.jira.parallel_fetcher.strategies.id_range import IdRangePaginationStrategy
from app.backend.jira.parallel_fetcher.strategies.simple_parallel import SimpleParallelStrategy

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
        """
        self._connection = connection
        self._max_workers = max_workers or Config.JIRA_PARALLEL_MAX_WORKERS
        self._max_results_per_page = max_results_per_page or Config.JIRA_PARALLEL_MAX_RESULTS
        self._request_timeout = request_timeout or Config.JIRA_PARALLEL_REQUEST_TIMEOUT
        self._retry_attempts = retry_attempts or Config.JIRA_PARALLEL_RETRY_ATTEMPTS
        self._rate_limit_sleep = rate_limit_sleep or Config.JIRA_PARALLEL_RATE_LIMIT_SLEEP
        
        self.rate_limiter = RateLimiter(self._rate_limit_sleep)
        self.worker = Worker(
            connection=self._connection,
            rate_limiter=self.rate_limiter,
            request_timeout=self._request_timeout,
            retry_attempts=self._retry_attempts
        )
        
        # Strategies
        self.strategies = {
            'sequential': SequentialPaginationStrategy(self.worker, self._max_workers, self._max_results_per_page),
            'id_range': IdRangePaginationStrategy(self.worker, self._max_workers, self._max_results_per_page),
            'simple_parallel': SimpleParallelStrategy(self.worker, self._max_workers, self._max_results_per_page)
        }
        
        # Campos mínimos necesarios para métricas
        self._required_fields = 'key,summary,status,issuetype,priority,assignee,created,updated,resolution,labels,fixVersions,affectsVersions'
        
        logger.info(f"ParallelIssueFetcher inicializado: max_workers={self._max_workers}, "
                   f"max_results={self._max_results_per_page}, timeout={self._request_timeout}s")

    def fetch_all_issues_parallel(
        self,
        jql: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Obtiene todas las issues usando paginación paralela (delegando a estrategias)
        """
        logger.info(f"Iniciando obtención paralela de issues con JQL: {jql[:100]}...")
        
        try:
            logger.info(f"[DEBUG JQL] Obteniendo primera página de issues con JQL: {jql}")
            # Obtener primera página para verificar
            initial_page = self.worker.fetch_page(jql, start_at=0, max_results=1, progress_callback=None, fields=None)
            initial_issues = initial_page.get('issues', [])
            total_from_response = initial_page.get('total', 0)
            
            logger.info(f"[DEBUG JQL] Total de la respuesta: {total_from_response}")
            logger.info(f"[DEBUG JQL] Issues en petición inicial: {len(initial_issues)}")
            
            if len(initial_issues) == 0:
                logger.warning(f"[DEBUG JQL] No hay issues que coincidan con el JQL: {jql[:100]}...")
                return []
            
            logger.info(f"[DEBUG JQL] ⚠️ Hay {len(initial_issues)} issue(s). Usando paginación por ID (más confiable).")
            
            estimated_total = total_from_response if total_from_response > 0 else 1000
            
            # Usar estrategia de ID Range
            strategy = self.strategies['id_range']
            return strategy.fetch_all(
                jql=jql,
                total=estimated_total,
                progress_callback=progress_callback,
                fields=self._required_fields if self._required_fields else None
            )
            
        except Exception as e:
            logger.error(f"Error al obtener issues: {e}", exc_info=True)
            raise

    def fetch_issues_details_parallel(
        self,
        issue_keys: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Obtiene los detalles completos de múltiples issues en paralelo
        """
        if not issue_keys:
            return []
        
        logger.info(f"[FETCH DETAILS PARALLEL] Obteniendo detalles de {len(issue_keys)} issues en paralelo...")
        
        all_issues = []
        completed = 0
        errors = []
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_key = {
                executor.submit(self.worker.fetch_issue_details, key, self._required_fields): key
                for key in issue_keys
            }
            
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

    def get_approximate_count(self, jql: str) -> int:
        """
        Obtiene un conteo aproximado de issues usando el endpoint approximate-count
        """
        try:
            url = f"{self._connection.base_url}/rest/api/3/search/approximate-count"
            
            # Simplificar JQL
            simplified_jql = JQLHelper.simplify_jql_for_count(jql)
            
            logger.info(f"[APPROXIMATE-COUNT] JQL original: {jql[:200]}...")
            logger.info(f"[APPROXIMATE-COUNT] JQL simplificado: {simplified_jql[:200]}...")
            
            payload = {"jql": simplified_jql}
            
            self.rate_limiter.wait()
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
