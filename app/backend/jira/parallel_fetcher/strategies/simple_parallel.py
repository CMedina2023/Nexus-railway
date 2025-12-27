import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
from app.backend.jira.parallel_fetcher.strategies.base_strategy import PaginationStrategy
from app.utils.exceptions import JiraAPIError
from app.backend.jira.parallel_fetcher.utils.deduplication import Deduplicator

logger = logging.getLogger(__name__)

class SimpleParallelStrategy(PaginationStrategy):
    """
    Estrategia de fetching paralelo simple SIN fields.
    Obtiene issues en paralelo usando startAt.
    """
    
    def fetch_all(
        self,
        jql: str,
        total: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        fields: Optional[str] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Obtiene todas las issues SIN especificar fields (solo key e id)
        Esto permite que la paginación funcione correctamente en algunos casos.
        """
        logger.info(f"[FETCH SIN FIELDS] Obteniendo {total} issues sin fields para paginación correcta...")
        
        # Calcular número de páginas necesarias
        total_pages = (total + self.max_results_per_page - 1) // self.max_results_per_page
        
        logger.info(f"[FETCH SIN FIELDS] Calculando páginas: total={total}, max_results_per_page={self.max_results_per_page}, total_pages={total_pages}")
        
        # Crear lista de tareas (ranges de startAt)
        tasks = []
        for page in range(total_pages):
            start_at = page * self.max_results_per_page
            tasks.append(start_at)
        
        all_issues = []
        completed = 0
        errors = []
        page_ids_map = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_start_at = {
                executor.submit(self.worker.fetch_page, jql, start_at, self.max_results_per_page, None, fields=None):
                start_at
                for start_at in tasks
            }
            
            for future in as_completed(future_to_start_at):
                start_at = future_to_start_at[future]
                try:
                    result = future.result()
                    issues = result.get('issues', [])
                    
                    if issues:
                        first_ids = [str(issue.get('id', 'N/A')) for issue in issues[:5]]
                        page_ids_map[start_at] = first_ids
                        logger.info(f"[FETCH SIN FIELDS] Página startAt={start_at}: primeros 5 IDs = {first_ids}")
                        
                        # Detectar si esta página tiene los mismos IDs que la primera
                        if start_at > 0 and 0 in page_ids_map:
                            if first_ids == page_ids_map[0][:len(first_ids)]:
                                logger.error(f"[FETCH SIN FIELDS] ⚠️ CRÍTICO: Página startAt={start_at} tiene los mismos IDs que startAt=0. Jira está ignorando startAt.")
                                # Cancelar otras tareas
                                for f in future_to_start_at:
                                    f.cancel()
                                raise JiraAPIError("Jira ignoring startAt parameter - switching strategy required")

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
        
        # Eliminación de duplicados (solo id/key)
        return Deduplicator.deduplicate_issues(all_issues, log_tag="FETCH SIN FIELDS")
