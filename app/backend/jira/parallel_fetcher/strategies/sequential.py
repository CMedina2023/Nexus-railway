import logging
from typing import List, Dict, Optional, Callable
from app.backend.jira.parallel_fetcher.strategies.base_strategy import PaginationStrategy

logger = logging.getLogger(__name__)

class SequentialPaginationStrategy(PaginationStrategy):
    """
    Obtiene issues secuencialmente. 
    Ideal para cuando approximate-count no funciona o para máxima seguridad de datos.
    """
    
    def fetch_all(
        self,
        jql: str,
        total: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        fields: Optional[str] = None,
        initial_issues: List[Dict] = None,
        initial_is_last: bool = False,
        initial_next_token: Optional[str] = None,
        required_fields: bool = False, # Pass if fields are actually required/present
        **kwargs
    ) -> List[Dict]:
        """
        Obtiene todas las issues usando paginación secuencial basada en "página incompleta".
        """
        logger.info(f"[PAGINACIÓN SECUENCIAL] Iniciando paginación secuencial basada en página incompleta")
        
        all_issues = list(initial_issues) if initial_issues else []
        start_at = len(all_issues)
        page_size = self.max_results_per_page
        
        # Límites de seguridad estrictos
        max_issues_limit = 10000
        max_pages_limit = 50 if total == 0 else 100
        
        if total == 0:
            logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Total=0: usando límite de {max_pages_limit} páginas para obtener todas las issues")
        
        pages_fetched = 0
        is_last = initial_is_last
        next_token = initial_next_token
        consecutive_duplicate_pages = 0
        
        # Si la primera página ya es la última
        if is_last or (not next_token and not is_last and len(all_issues) > 0 and len(all_issues) < page_size):
            # Nota: a veces is_last es false pero no hay next_token.
             # Si no hay initial issues, asumimos que debemos buscar.
             # Pero si nos pasaron initial_issues y next_token es None, asumimos fin.
             if initial_issues is not None:
                logger.info(f"[PAGINACIÓN SECUENCIAL] Primera página es la última. Retornando {len(all_issues)} issues.")
                if progress_callback:
                    progress_callback(len(all_issues), len(all_issues))
                return all_issues
        
        if progress_callback:
            progress_callback(len(all_issues), len(all_issues) + page_size)
        
        logger.info(f"[PAGINACIÓN SECUENCIAL] Obteniendo páginas adicionales (startAt={start_at}, page_size={page_size})")
        
        while True:
            if len(all_issues) >= max_issues_limit:
                logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Límite de seguridad alcanzado: {len(all_issues)} issues. Deteniendo.")
                break
            
            if pages_fetched >= max_pages_limit:
                logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Límite de páginas alcanzado: {pages_fetched} páginas. Deteniendo.")
                break
            
            try:
                logger.info(f"[PAGINACIÓN SECUENCIAL] Obteniendo página {pages_fetched + 1}/{max_pages_limit}: startAt={start_at}, maxResults={page_size}")
                
                # Fetch page using worker
                page_result = self.worker.fetch_page(
                    jql, 
                    start_at=start_at, 
                    max_results=page_size, 
                    progress_callback=None,
                    fields=fields, 
                    next_page_token=next_token 
                )
                
                page_issues = page_result.get('issues', [])
                is_last = page_result.get('isLast', False)
                next_token = page_result.get('nextPageToken', None)
                
                logger.info(f"[PAGINACIÓN SECUENCIAL] Página obtenida: {len(page_issues)} issues (page_size={page_size})")
                
                if not page_issues:
                    logger.info(f"[PAGINACIÓN SECUENCIAL] Página vacía - finalizando")
                    break
                
                # Detectar duplicados
                is_duplicate_page = False
                if total == 0 or required_fields:
                     # Obtener IDs de las issues de esta página
                    page_ids = {str(issue.get('id', '')) for issue in page_issues if issue.get('id')}
                    if not page_ids:
                        page_ids = {issue.get('key', '') for issue in page_issues if issue.get('key')}
                    
                    existing_ids = {str(issue.get('id', '')) for issue in all_issues if issue.get('id')}
                    if not existing_ids:
                        existing_ids = {issue.get('key', '') for issue in all_issues if issue.get('key')}
                    
                    if page_ids and page_ids.issubset(existing_ids):
                        is_duplicate_page = True
                        consecutive_duplicate_pages += 1
                        logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ Página {pages_fetched + 1} completa de duplicados detectada ({consecutive_duplicate_pages} consecutivas).")
                        
                        if required_fields:
                            logger.error(
                                f"[PAGINACIÓN SECUENCIAL] ⚠️ LIMITACIÓN DE JIRA: Cuando se especifican 'fields', "
                                f"Jira ignora el parámetro 'startAt' y siempre retorna las primeras issues. "
                                f"Se obtuvieron {len(all_issues)} issues únicas."
                            )
                            break
                        
                        if consecutive_duplicate_pages >= 2:
                            logger.warning(f"[PAGINACIÓN SECUENCIAL] ⚠️ {consecutive_duplicate_pages} páginas consecutivas de duplicados. Deteniendo.")
                            break
                        else:
                            logger.info(f"[PAGINACIÓN SECUENCIAL] Saltando página duplicada pero continuando...")
                            start_at += len(page_issues)
                            pages_fetched += 1
                            continue
                    else:
                        consecutive_duplicate_pages = 0
                
                all_issues.extend(page_issues)
                
                if total > 0 and len(all_issues) >= total:
                    logger.info(f"[PAGINACIÓN SECUENCIAL] Total alcanzado: {len(all_issues)} >= {total}")
                    break
                
                # Check for completion
                if len(page_issues) < page_size:
                    if total > 0 and len(all_issues) < total:
                        logger.info(f"[PAGINACIÓN SECUENCIAL] Página incompleta  pero aún faltan issues. Continuando...")
                        start_at += len(page_issues)
                        pages_fetched += 1
                        continue
                    else:
                        logger.info(f"[PAGINACIÓN SECUENCIAL] Página incompleta - ÚLTIMA PÁGINA detectada")
                        break
                
                start_at += len(page_issues)
                pages_fetched += 1
                
                if progress_callback:
                    progress_callback(len(all_issues), total if total > 0 else len(all_issues) + page_size)
                
            except Exception as e:
                logger.error(f"[PAGINACIÓN SECUENCIAL] Error al obtener página {pages_fetched + 1}: {e}", exc_info=True)
                break
        
        return all_issues
