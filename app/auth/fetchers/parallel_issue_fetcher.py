"""
Módulo para la obtención paralela de issues de Jira.
Responsabilidad: Orquestar la recuperación eficiente de datos desde Jira API.
"""
import logging
import re
from queue import Queue
from typing import Dict, List, Optional, Callable
from app.backend.jira.connection import JiraConnection
from app.backend.jira.parallel_fetcher import ParallelIssueFetcher as CoreParallelFetcher
from app.backend.jira.issue_service import TEST_CASE_VARIATIONS, BUG_VARIATIONS
from app.auth.jql.jql_builder import JQLBuilder

logger = logging.getLogger(__name__)

class MetricsIssueFetcher:
    """Clase para gestionar la obtención de issues para reportes de métricas."""

    def __init__(self, connection: JiraConnection):
        self.connection = connection
        self.core_fetcher = CoreParallelFetcher(connection)

    def fetch_issues_with_separate_filters(
        self,
        project_key: str,
        view_type: str,
        filters_testcase: List[str],
        filters_bug: List[str],
        assignee_email: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """Obtiene issues usando filtros separados para Test Cases y Bugs."""
        jql_builder = JQLBuilder()
        
        # Construir JQLs específicos
        jql_test_cases = self._build_filtered_jql(project_key, view_type, filters_testcase, TEST_CASE_VARIATIONS, assignee_email)
        jql_bugs = self._build_filtered_jql(project_key, view_type, filters_bug, BUG_VARIATIONS, assignee_email)
        
        logger.info(f"[Fetcher] JQL Test Cases: {jql_test_cases[:100]}...")
        logger.info(f"[Fetcher] JQL Bugs: {jql_bugs[:100]}...")
        
        all_issues = []
        
        # Obtener Test Cases
        try:
            test_cases = self.core_fetcher.fetch_all_issues_parallel(jql_test_cases)
            all_issues.extend(test_cases)
        except Exception as e:
            logger.error(f"Error al obtener Test Cases: {e}")
            
        # Obtener Bugs
        try:
            bugs = self.core_fetcher.fetch_all_issues_parallel(jql_bugs)
            all_issues.extend(bugs)
        except Exception as e:
            logger.error(f"Error al obtener Bugs: {e}")
            
        unique_issues = self._remove_duplicates(all_issues)
        
        if progress_callback:
            progress_callback(len(unique_issues), len(unique_issues))
            
        return unique_issues

    def fetch_issues_parallel(
        self,
        jql: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """Obtiene issues usando consultas separadas para evitar bugs de Jira total=0."""
        project_key = self._extract_project_key(jql)
        if not project_key:
            return self.core_fetcher.fetch_all_issues_parallel(jql, progress_callback=progress_callback)
            
        additional_filters = self._extract_additional_filters(jql)
        
        # Construir JQLs separados
        test_case_conditions = ' OR '.join([f'issuetype = "{var}"' for var in TEST_CASE_VARIATIONS])
        bug_conditions = ' OR '.join([f'issuetype = "{var}"' for var in BUG_VARIATIONS])
        
        jql_test_cases = f'project = {project_key} AND ({test_case_conditions})'
        jql_bugs = f'project = {project_key} AND ({bug_conditions})'
        
        if additional_filters:
            jql_test_cases += f' AND {additional_filters}'
            jql_bugs += f' AND {additional_filters}'
            
        all_issues = []
        try:
            all_issues.extend(self.core_fetcher.fetch_all_issues_parallel(jql_test_cases))
            all_issues.extend(self.core_fetcher.fetch_all_issues_parallel(jql_bugs))
        except Exception as e:
            logger.error(f"Error en fetch_issues_parallel: {e}")
            
        unique_issues = self._remove_duplicates(all_issues)
        
        if progress_callback:
            progress_callback(len(unique_issues), len(unique_issues))
            
        return unique_issues

    def fetch_with_progress_queue(self, jql: str, progress_queue: Queue) -> List[Dict]:
        """Obtiene issues y reporta progreso mediante una cola SSE."""
        def internal_callback(actual: int, total: int):
            porcentaje = int((actual / total * 100)) if total > 0 else 0
            progress_queue.put({'actual': actual, 'total': total, 'porcentaje': porcentaje})
            
        return self.core_fetcher.fetch_all_issues_parallel(jql, progress_callback=internal_callback)

    def _build_filtered_jql(self, project_key: str, view_type: str, filters: List[str], variations: List[str], email: Optional[str]) -> str:
        base = f'project = {project_key}'
        if view_type == 'personal' and email:
            base += f' AND assignee = "{email}"'
            
        type_cond = ' OR '.join([f'issuetype = "{v}"' for v in variations])
        parts = [base, f'({type_cond})']
        
        # Usar JQLBuilder para procesar filtros
        from app.auth.jql.jql_builder import JQLBuilder
        parts.extend(JQLBuilder._process_filter_params(filters, project_key))
        
        return ' AND '.join(parts)

    def _remove_duplicates(self, issues: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for issue in issues:
            key = issue.get('key')
            if key not in seen:
                seen.add(key)
                unique.append(issue)
        return unique

    def _extract_project_key(self, jql: str) -> Optional[str]:
        if 'project = ' in jql:
            start = jql.find('project = ') + len('project = ')
            end = jql.find(' AND', start)
            if end == -1: end = len(jql)
            return jql[start:end].strip()
        return None

    def _extract_additional_filters(self, jql: str) -> str:
        # Busca el final del bloque de issuetypes
        match = re.search(r'\)\s*AND\s*(.*)$', jql, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""
