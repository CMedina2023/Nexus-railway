"""
Servicio para generar eventos SSE (Server-Sent Events) para el reporte de métricas.
"""
import json
import logging
import time
from typing import Dict, List, Optional, Any

from app.core.config import Config
from app.core.dependencies import get_jira_token_manager
from app.utils.exceptions import ConfigurationError
from app.backend.jira.connection import JiraConnection
from app.auth.jql.jql_builder import JQLBuilder
from app.auth.fetchers.parallel_issue_fetcher import MetricsIssueFetcher
from app.auth.calculators.metrics_calculator_helper import MetricsCalculatorHelper
from app.services.metrics_cache import get_metrics_cache
from app.services.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)

class MetricsStreamGenerator:
    """
    Orquesta la generación de métricas y emite eventos SSE para informar
    el progreso al cliente.
    """

    def __init__(
        self,
        user: Any,
        project_key: str,
        requested_view_type: str,
        filters_by_type: Optional[Dict[str, List[str]]] = None,
        filters_legacy: Optional[List[str]] = None,
        force_refresh: bool = False
    ):
        self.user = user
        self.project_key = project_key
        self.requested_view_type = requested_view_type.lower()
        self.filters_by_type = filters_by_type
        self.filters_legacy = filters_legacy or []
        self.force_refresh = force_refresh
        
        # Determinar view_type y filtros para caché
        if self.user.role == 'admin':
            self.view_type = self.requested_view_type if self.requested_view_type in ['general', 'personal'] else 'general'
        else:
            self.view_type = 'personal'
            
        self.cache_user_id = self.user.id if self.view_type == 'personal' else None
        
        if self.filters_by_type:
            self.filters_for_cache = self.filters_by_type.get('testCases', []) + self.filters_by_type.get('bugs', [])
        else:
            self.filters_for_cache = self.filters_legacy

    def generate(self):
        """
        Generador principal que emite eventos SSE.
        """
        try:
            # 1. Verificar permisos
            if self.view_type == 'general' and self.user.role != 'admin':
                yield self._format_sse('error', {'mensaje': 'No autorizado'})
                return

            # 2. Obtener configuración de Jira
            token_manager = get_jira_token_manager()
            try:
                jira_config = token_manager.get_token_for_user(self.user, self.project_key)
            except ConfigurationError as e:
                yield self._format_sse('error', {'mensaje': str(e)})
                return

            # 3. Crear conexión
            connection = JiraConnection(
                base_url=jira_config.base_url,
                email=jira_config.email,
                api_token=jira_config.token
            )

            # 4. Verificar caché
            metrics_cache = get_metrics_cache(Config.JIRA_METRICS_CACHE_TTL_HOURS)
            
            if not self.force_refresh:
                cached_metrics = metrics_cache.get(
                    self.project_key,
                    self.view_type,
                    self.filters_for_cache,
                    user_id=self.cache_user_id
                )

                if cached_metrics:
                    yield self._format_sse('inicio', {'total': cached_metrics.get('total_issues', 0), 'desde_cache': True})
                    yield self._format_sse('completado', {'reporte': cached_metrics, 'desde_cache': True})
                    return
            else:
                 logger.info(f"[SSE] Forzando refresco para {self.project_key}")

            # 5. Obtener Issues y Generar Reporte
            if self.filters_by_type:
                yield from self._handle_separate_filters(connection, jira_config)
            else:
                yield from self._handle_legacy_jql(connection, jira_config)

        except Exception as e:
            logger.error(f"Error crítico en SSE Stream Generator: {e}", exc_info=True)
            yield self._format_sse('error', {'mensaje': f'Error crítico: {str(e)}'})

    def _handle_separate_filters(self, connection, jira_config):
        """Maneja la obtención con los nuevos filtros separados."""
        fetcher = MetricsIssueFetcher(connection)
        all_issues = fetcher.fetch_issues_with_separate_filters(
            project_key=self.project_key,
            view_type=self.view_type,
            filters_testcase=self.filters_by_type.get('testCases', []),
            filters_bug=self.filters_by_type.get('bugs', []),
            assignee_email=jira_config.email if self.view_type == 'personal' else None
        )
        
        total = len(all_issues)
        yield self._format_sse('inicio', {'total': total})
        
        if total == 0:
            yield self._format_sse('completado', {'reporte': self._empty_report()})
            return
            
        yield self._format_sse('calculando', {})
        yield from self._calculate_and_send_metrics(all_issues)

    def _handle_legacy_jql(self, connection, jira_config):
        """Maneja la obtención con el formato de JQL antiguo."""
        # Construir JQL
        if self.filters_legacy:
            jql = JQLBuilder.build_jql_from_filters(
                project_key=self.project_key,
                view_type=self.view_type,
                filters=self.filters_legacy,
                assignee_email=jira_config.email if self.view_type == 'personal' else None
            )
        else:
            if self.view_type == 'personal':
                jql = f'project = {self.project_key} AND assignee = "{jira_config.email}"'
            else:
                jql = f'project = {self.project_key}'

        # FIX: Usar MetricsIssueFetcher directamente para asegurar consistencia con el generador principal.
        # Esto soluciona problemas donde 'project = KEY' devuelve 0 resultados en API v3.
        fetcher = MetricsIssueFetcher(connection)
        
        # Notificar inicio de búsqueda
        yield self._format_sse('inicio', {'total': 0, 'mensaje': 'Buscando issues...'})
        
        # Usar la estrategia paralela robusta (divide en Test Cases y Bugs)
        all_issues = fetcher.fetch_issues_parallel(jql)

        if not all_issues:
            logger.warning(f"[StreamGenerator] No se encontraron issues para {self.project_key}")
            yield self._format_sse('completado', {'reporte': self._empty_report()})
            return

        # Sincronizar progreso visual
        yield self._format_sse('progreso', {
            'actual': len(all_issues), 
            'total': len(all_issues), 
            'porcentaje': 100
        })

        yield self._format_sse('calculando', {'total_issues': len(all_issues)})
        yield from self._calculate_and_send_metrics(all_issues)

    def _stream_progress(self, tracker: ProgressTracker):
        """Consume el progreso del tracker y lo emite como SSE."""
        for progress in tracker.get_events():
            yield self._format_sse('progreso', {
                'actual': progress.get('actual', 0),
                'total': progress.get('total', 0),
                'porcentaje': progress.get('porcentaje', 0)
            })

    def _calculate_and_send_metrics(self, all_issues: List[Dict]):
        """Calcula métricas, guarda en caché y envía evento completado."""
        calculator = MetricsCalculatorHelper()
        metrics_result = calculator.calculate_metrics_from_issues(all_issues)
        
        response_data = {
            "project_key": self.project_key,
            "view_type": self.view_type,
            "test_cases": metrics_result['test_cases'],
            "bugs": metrics_result['bugs'],
            "general_report": metrics_result['general_report'],
            "total_issues": metrics_result['total_issues'],
            "from_cache": False
        }
        
        # Guardar en caché
        metrics_cache = get_metrics_cache(Config.JIRA_METRICS_CACHE_TTL_HOURS)
        metrics_cache.set(
            self.project_key,
            self.view_type,
            self.filters_for_cache,
            response_data,
            user_id=self.cache_user_id
        )
        
        yield self._format_sse('completado', {'reporte': response_data})

    def _get_total_count(self, connection: JiraConnection, jql: str) -> int:
        """Obtiene el número total de issues para un JQL."""
        try:
            # CORRECCIÓN PARA API JIRA V3: Usar GET /rest/api/3/search/jql con params
            # Esto coincide con la implementación exitosa en worker.py
            url = f"{connection.base_url}/rest/api/3/search/jql"
            params = {
                'jql': jql,
                'maxResults': 1,
                'validation': 'strict'
            }
            # Usar GET con params (no json body)
            response = connection.session.get(url, params=params, timeout=Config.JIRA_PARALLEL_REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                total = response.json().get('total', 0)
                logger.info(f"[SSE DEBUG] JQL: {jql} | Total encontrados: {total}")
                return total
            else:
                logger.error(f"[SSE ERROR] API Jira falló: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error al obtener total: {e}")
        return 0

    def _empty_report(self) -> Dict[str, Any]:
        """Retorna la estructura de un reporte vacío."""
        return {
            "project_key": self.project_key,
            "view_type": self.view_type,
            "test_cases": {'total': 0, 'by_status': {}, 'by_priority': {}, 'resolved': 0, 'unresolved': 0, 'percentage_resolved': 0},
            "bugs": {'total': 0, 'by_status': {}, 'by_priority': {}, 'resolved': 0, 'unresolved': 0, 'percentage_resolved': 0},
            "general_report": {'total_test_cases': 0, 'total_defects': 0},
            "total_issues": 0,
            "from_cache": False
        }

    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """Formatea un mensaje para Server-Sent Events."""
        payload = {'tipo': event_type}
        payload.update(data)
        return f"data: {json.dumps(payload)}\n\n"
