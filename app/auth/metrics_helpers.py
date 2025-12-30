"""
Funciones helper para generar métricas de Jira.
Actúa como fachada para los nuevos módulos especializados.
"""
import logging
from queue import Queue
from typing import Dict, List, Optional, Callable, Tuple

from app.backend.jira.connection import JiraConnection
from app.auth.jql.jql_builder import JQLBuilder
from app.auth.fetchers.parallel_issue_fetcher import MetricsIssueFetcher
from app.auth.calculators.metrics_calculator_helper import MetricsCalculatorHelper

logger = logging.getLogger(__name__)

def filter_issues_by_type(issues: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Filtra issues por tipo (Test Cases y Bugs)."""
    return MetricsCalculatorHelper().filter_issues_by_type(issues)

def build_jql_from_filters(project_key: str, view_type: str, filters: List[str], assignee_email: Optional[str] = None) -> str:
    """Construye un JQL query desde los filtros proporcionados."""
    return JQLBuilder.build_jql_from_filters(project_key, view_type, filters, assignee_email)

def calculate_metrics_from_issues(issues: List[Dict]) -> Dict:
    """Calcula métricas desde una lista de issues."""
    return MetricsCalculatorHelper().calculate_metrics_from_issues(issues)

def build_separate_jql_queries(project_key: str, view_type: str, filters: List[str], assignee_email: Optional[str] = None) -> Tuple[str, str]:
    """Construye dos JQL queries separados para Test Cases y Bugs."""
    return JQLBuilder.build_separate_jql_queries(project_key, view_type, filters, assignee_email)

def fetch_issues_with_separate_filters(
    connection: JiraConnection,
    project_key: str,
    view_type: str,
    filters_testcase: List[str],
    filters_bug: List[str],
    assignee_email: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict]:
    """Obtiene issues usando filtros separados para Test Cases y Bugs."""
    fetcher = MetricsIssueFetcher(connection)
    return fetcher.fetch_issues_with_separate_filters(
        project_key, view_type, filters_testcase, filters_bug, assignee_email, progress_callback
    )

def fetch_issues_with_parallel(
    connection: JiraConnection,
    jql: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict]:
    """Obtiene issues usando paginación paralela optimizada."""
    fetcher = MetricsIssueFetcher(connection)
    return fetcher.fetch_issues_parallel(jql, progress_callback)

def fetch_issues_with_progress_queue(
    connection: JiraConnection,
    jql: str,
    progress_queue: Queue
) -> List[Dict]:
    """Obtiene issues y reporta progreso mediante una cola."""
    fetcher = MetricsIssueFetcher(connection)
    return fetcher.fetch_with_progress_queue(jql, progress_queue)
