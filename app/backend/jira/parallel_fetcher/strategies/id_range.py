import logging
import re
from typing import List, Dict, Optional, Callable
from app.backend.jira.parallel_fetcher.strategies.base_strategy import PaginationStrategy

logger = logging.getLogger(__name__)

class IdRangePaginationStrategy(PaginationStrategy):
    """
    Estrategia basada en rangos de ID (secuencial o paralela).
    Actualmente usa lógica secuencial 'id > last_id' que es muy robusta y permite fields.
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
        Método secuencial basado en ID que puede obtener fields directamente
        """
        fields_desc = "con fields" if fields else "sin fields"
        logger.info(f"[PAGINACIÓN POR ID SECUENCIAL] Iniciando paginación secuencial basada en ID para {total} issues ({fields_desc})...")
        
        all_issues = []
        last_id = None
        page_size = self.max_results_per_page
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
                # Obtener página
                page_result = self.worker.fetch_page(
                    jql_with_id,
                    start_at=0,  # Siempre empezar desde 0 con esta estrategia
                    max_results=page_size,
                    progress_callback=None,
                    fields=fields
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
