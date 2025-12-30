"""
Servicio para la obtención y cálculo de métricas de Jira.
"""
import logging
import time
import json
from typing import Optional, Dict, Any, List

from app.services.metrics_cache import get_metrics_cache
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_service import IssueService
from app.auth.jql.jql_builder import JQLBuilder
from app.auth.calculators.metrics_calculator_helper import MetricsCalculatorHelper
from app.auth.fetchers.parallel_issue_fetcher import MetricsIssueFetcher
from app.core.dependencies import get_jira_token_manager
from app.utils.exceptions import ConfigurationError
from app.core.config import Config
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.models.jira_report import JiraReport
from app.services.metrics_formatter import MetricsFormatter
from app.utils.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class MetricsService:
    """
    Servicio encargado de la lógica de negocio para métricas.
    """

    def __init__(self):
        self.token_manager = get_jira_token_manager()
        self.calculator = MetricsCalculatorHelper()
        self.cache = get_metrics_cache(Config.JIRA_METRICS_CACHE_TTL_HOURS)
        self.report_repo = JiraReportRepository()
        self.formatter = MetricsFormatter()

    def get_project_metrics(
        self,
        user: Any,
        project_key: str,
        requested_view_type: str,
        filters_testcase: List[str] = None,
        filters_bug: List[str] = None,
        filters_legacy: List[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene y calcula las métricas para un proyecto y usuario específicos.

        Args:
            user: Usuario que solicita las métricas.
            project_key: Clave del proyecto en Jira.
            requested_view_type: Tipo de vista solicitada ('general' o 'personal').
            filters_testcase: Lista de filtros para casos de prueba.
            filters_bug: Lista de filtros para fallos.
            filters_legacy: Lista de filtros en formato antiguo.

        Returns:
            Dict[str, Any]: Diccionario con los datos de las métricas.
        """
        start_time_total = time.time()
        view_type = self._determine_view_type(user, requested_view_type)
        cache_user_id = user.id if view_type == 'personal' else None
        
        # Procesar filtros
        filters_by_type, filters_for_cache = self._process_filters(
            filters_testcase, filters_bug, filters_legacy
        )

        # Verificar caché
        cached_data = self.cache.get(
            project_key,
            view_type,
            filters_for_cache,
            user_id=cache_user_id
        )
        if cached_data:
            logger.info(f"[CACHE] Métricas obtenidas desde caché para {project_key} ({view_type})")
            cached_data["from_cache"] = True
            cached_data["view_type"] = view_type
            return cached_data

        # Obtener configuración de Jira
        jira_config = self.token_manager.get_token_for_user(user, project_key)
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )

        # Obtener issues
        all_issues, fetch_time = self._fetch_issues(
            connection, project_key, view_type, jira_config.email, 
            filters_by_type, filters_legacy
        )

        # Calcular métricas
        calc_start = time.time()
        metrics_result = self.calculator.calculate_metrics_from_issues(all_issues)
        calc_time = time.time() - calc_start

        # Preparar resultado usando el formateador
        result = self.formatter.format_project_metrics(
            project_key=project_key,
            view_type=view_type,
            metrics_result=metrics_result,
            from_cache=False
        )

        # Guardar en caché
        self.cache.set(
            project_key,
            view_type,
            filters_for_cache,
            result,
            user_id=cache_user_id
        )

        # Guardar en BD local
        self._save_report_to_db(user.id, project_key, view_type, result)

        logger.info(
            f"[PERFORMANCE] Reporte completo generado en {time.time() - start_time_total:.2f}s "
            f"(fetch: {fetch_time:.2f}s, calc: {calc_time*1000:.2f}ms) "
            f"para proyecto {project_key}, {len(all_issues)} issues"
        )
        return result

    def _determine_view_type(self, user: Any, requested_view_type: str) -> str:
        """Determina el tipo de vista permitido según el rol del usuario."""
        if user.role == 'admin':
            return requested_view_type if requested_view_type in ['general', 'personal'] else 'general'
        return 'personal'

    def _process_filters(
        self, 
        tc_filters: List[str], 
        bug_filters: List[str], 
        legacy_filters: List[str]
    ) -> tuple:
        """Procesa y normaliza los filtros recibidos."""
        if tc_filters or bug_filters:
            filters_by_type = {
                'testCases': tc_filters or [],
                'bugs': bug_filters or []
            }
            filters_for_cache = (tc_filters or []) + (bug_filters or [])
            return filters_by_type, filters_for_cache
        
        return None, legacy_filters or []

    def _fetch_issues(
        self,
        connection: JiraConnection,
        project_key: str,
        view_type: str,
        email: str,
        filters_by_type: Optional[Dict],
        filters_legacy: Optional[List[str]]
    ) -> tuple:
        """Obtiene las issues de Jira con manejo de fallbacks."""
        fetch_start = time.time()
        fetcher = MetricsIssueFetcher(connection)
        issue_service = IssueService(connection, ProjectService(connection))

        try:
            if filters_by_type:
                all_issues = fetcher.fetch_issues_with_separate_filters(
                    project_key=project_key,
                    view_type=view_type,
                    filters_testcase=filters_by_type.get('testCases', []),
                    filters_bug=filters_by_type.get('bugs', []),
                    assignee_email=email if view_type == 'personal' else None
                )
            elif filters_legacy:
                final_jql = JQLBuilder.build_jql_from_filters(
                    project_key=project_key,
                    view_type=view_type,
                    filters=filters_legacy,
                    assignee_email=email if view_type == 'personal' else None
                )
                all_issues = fetcher.fetch_issues_parallel(final_jql)
            else:
                jql = f'project = {project_key}'
                if view_type == 'personal':
                    jql += f' AND assignee = "{email}"'
                all_issues = fetcher.fetch_issues_parallel(jql)
        except Exception as e:
            logger.error(f"Error en fetch optimizado, usando fallback: {e}")
            if view_type == 'personal':
                all_issues = issue_service.get_issues_by_assignee(project_key, email, max_results=1000)
            else:
                all_issues = issue_service.get_all_issues(project_key, max_results=1000)
        
        return all_issues, time.time() - fetch_start

    def _save_report_to_db(self, user_id: int, project_key: str, view_type: str, data: Dict):
        """Guarda el reporte en la base de datos local."""
        try:
            jira_report = JiraReport(
                user_id=user_id,
                project_key=project_key,
                report_type='metrics',
                report_title=f'Reporte de Métricas - {project_key} ({view_type})',
                report_content=json.dumps(data, ensure_ascii=False),
                jira_issue_key='N/A'
            )
            self.report_repo.create(jira_report)
        except Exception as e:
            logger.error(f"Error al guardar reporte en BD local: {e}")
