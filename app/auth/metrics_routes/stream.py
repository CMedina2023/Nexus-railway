"""
Rutas de métricas en Streaming (SSE)
"""
import logging
import time
import json
from queue import Queue
from threading import Thread
from flask import request, Response, has_request_context

from app.auth.decorators import login_required, get_current_user_id
from app.services.jira_token_manager import JiraTokenManager
from app.services.metrics_cache import get_metrics_cache
from app.backend.jira.connection import JiraConnection
from app.auth.metrics_helpers import build_jql_from_filters, calculate_metrics_from_issues
from app.core.dependencies import get_user_service, get_jira_token_manager
from app.utils.exceptions import ConfigurationError
from app.core.config import Config
from app.backend.jira.parallel_fetcher import ParallelIssueFetcher

from . import metrics_bp

logger = logging.getLogger(__name__)

@metrics_bp.route('/<project_key>/stream', methods=['GET'])
@login_required
def generate_report_stream(project_key: str):
    """
    Genera reporte con progreso en tiempo real usando Server-Sent Events (SSE)
    
    Query params:
        - view_type: "general" | "personal"
        - filter: Lista de filtros (puede repetirse)
    
    Retorna eventos SSE:
        - tipo: "inicio" - Indica inicio del proceso
        - tipo: "progreso" - Progreso de obtención de issues
        - tipo: "calculando" - Inicio de cálculo de métricas
        - tipo: "completado" - Reporte completo con métricas
        - tipo: "error" - Error en el proceso
    """
    
    # Obtener usuario ANTES del generador para evitar problemas de contexto
    try:
        user_id = get_current_user_id()
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id) if user_id else None
    except Exception as e:
        logger.error(f"Error al obtener usuario en SSE: {e}", exc_info=True)
        user = None
    
    if not user:
        def generate():
            yield f"data: {json.dumps({'tipo': 'error', 'mensaje': 'Usuario no encontrado'})}\n\n"
        return Response(generate(), mimetype='text/event-stream')
    
    user_role = user.role
    requested_view_type = request.args.get('view_type', '').lower()
    
    # Obtener filtros ANTES del generador para evitar problemas de contexto
    filters_testcase = request.args.getlist('filter_testcase')
    filters_bug = request.args.getlist('filter_bug')
    filters_legacy = request.args.getlist('filter')  # Formato antiguo
    
    # Determinar si usar formato nuevo o antiguo
    if filters_testcase or filters_bug:
        filters_by_type = {
            'testCases': filters_testcase,
            'bugs': filters_bug
        }
        filters_for_cache = filters_testcase + filters_bug
    else:
        filters_by_type = None
        filters_for_cache = filters_legacy
    
    def generate():
        """Generador para eventos SSE"""
        try:
            
            if user_role == 'admin':
                view_type = requested_view_type if requested_view_type in ['general', 'personal'] else 'general'
            else:
                view_type = 'personal'
            cache_user_id = user.id if view_type == 'personal' else None
            
            # Verificar permisos
            if view_type == 'general' and user_role != 'admin':
                yield f"data: {json.dumps({'tipo': 'error', 'mensaje': 'No autorizado'})}\n\n"
                return
            
            # Obtener configuración de Jira
            token_manager = get_jira_token_manager()
            try:
                jira_config = token_manager.get_token_for_user(user, project_key)
            except ConfigurationError as e:
                yield f"data: {json.dumps({'tipo': 'error', 'mensaje': str(e)})}\n\n"
                return
            
            # Crear conexión
            connection = JiraConnection(
                base_url=jira_config.base_url,
                email=jira_config.email,
                api_token=jira_config.token
            )
            
            # Usar las variables de filtros obtenidas antes del generador
            # (filters_by_type y filters_for_cache ya están definidas fuera)
            
            # Verificar caché
            metrics_cache = get_metrics_cache(Config.JIRA_METRICS_CACHE_TTL_HOURS)
            cached_metrics = metrics_cache.get(
                project_key,
                view_type,
                filters_for_cache,
                user_id=cache_user_id
            )
            
            if cached_metrics:
                # Enviar desde caché (instantáneo)
                yield f"data: {json.dumps({'tipo': 'inicio', 'total': cached_metrics.get('total_issues', 0), 'desde_cache': True})}\n\n"
                yield f"data: {json.dumps({'tipo': 'completado', 'reporte': cached_metrics, 'desde_cache': True})}\n\n"
                return
            
            # Construir JQL o usar filtros separados
            all_issues = []
            use_separate_filters = filters_by_type and (filters_by_type.get('testCases') or filters_by_type.get('bugs'))
            
            if use_separate_filters:
                # Formato nuevo: filtros separados por tipo
                from app.auth.metrics_helpers import fetch_issues_with_separate_filters
                
                # Obtener issues directamente con filtros separados
                all_issues = fetch_issues_with_separate_filters(
                    connection=connection,
                    project_key=project_key,
                    view_type=view_type,
                    filters_testcase=filters_by_type.get('testCases', []),
                    filters_bug=filters_by_type.get('bugs', []),
                    assignee_email=jira_config.email if view_type == 'personal' else None
                )
                
                total = len(all_issues)
                yield f"data: {json.dumps({'tipo': 'inicio', 'total': total})}\n\n"
                
                if total == 0:
                    response_data = {
                        "project_key": project_key,
                        "view_type": view_type,
                        "test_cases": {'total': 0, 'by_status': {}, 'by_priority': {}, 'resolved': 0, 'unresolved': 0, 'percentage_resolved': 0},
                        "bugs": {'total': 0, 'by_status': {}, 'by_priority': {}, 'resolved': 0, 'unresolved': 0, 'percentage_resolved': 0},
                        "general_report": {'total_test_cases': 0, 'total_defects': 0},
                        "total_issues": 0,
                        "from_cache": False
                    }
                    yield f"data: {json.dumps({'tipo': 'completado', 'reporte': response_data})}\n\n"
                    return
                
                # Ya tenemos los issues, saltar al cálculo de métricas
                yield f"data: {json.dumps({'tipo': 'calculando'})}\n\n"
                
                # Calcular métricas
                from app.auth.metrics_helpers import calculate_metrics_from_issues
                response_data = calculate_metrics_from_issues(all_issues)
                response_data['project_key'] = project_key
                response_data['view_type'] = view_type
                response_data['from_cache'] = False
                
                # Guardar en caché
                metrics_cache.set(
                    project_key,
                    view_type,
                    filters_for_cache,
                    response_data,
                    user_id=cache_user_id
                )
                
                yield f"data: {json.dumps({'tipo': 'completado', 'reporte': response_data})}\n\n"
                return
            else:
                # Formato antiguo: JQL único
                if filters_legacy and len(filters_legacy) > 0:
                    jql = build_jql_from_filters(
                        project_key=project_key,
                        view_type=view_type,
                        filters=filters_legacy,
                        assignee_email=jira_config.email if view_type == 'personal' else None
                    )
                else:
                    if view_type == 'personal':
                        jql = f'project = {project_key} AND assignee = "{jira_config.email}"'
                    else:
                        jql = f'project = {project_key}'
                
                # Obtener total primero
                parallel_fetcher = ParallelIssueFetcher(connection)
                
                # Obtener total con maxResults=1 (Jira no permite 0, requiere entre 1 y 5,000)
                try:
                    url = f"{connection.base_url}/rest/api/3/search/jql"
                    params = {
                        'jql': jql,
                        'startAt': 0,
                        'maxResults': 1,
                        'fields': 'key'
                    }
                    response = connection.session.get(url, params=params, timeout=Config.JIRA_PARALLEL_REQUEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        data = response.json()
                        total = data.get('total', 0)
                    else:
                        total = 0
                except Exception as e:
                    logger.error(f"Error al obtener total: {e}")
                    total = 0
                
                # Enviar evento de inicio
                yield f"data: {json.dumps({'tipo': 'inicio', 'total': total})}\n\n"
                
                if total == 0:
                    # No hay issues, retornar reporte vacío
                    response_data = {
                        "project_key": project_key,
                        "view_type": view_type,
                        "test_cases": {'total': 0, 'by_status': {}, 'by_priority': {}, 'resolved': 0, 'unresolved': 0, 'percentage_resolved': 0},
                        "bugs": {'total': 0, 'by_status': {}, 'by_priority': {}, 'resolved': 0, 'unresolved': 0, 'percentage_resolved': 0},
                        "general_report": {'total_test_cases': 0, 'total_defects': 0},
                        "total_issues": 0,
                        "from_cache": False
                    }
                    yield f"data: {json.dumps({'tipo': 'completado', 'reporte': response_data})}\n\n"
                    return
                
                # Cola para reportar progreso desde threads
                progress_queue = Queue()
                fetch_error = None
                
                # Función para obtener issues en thread separado
                def fetch_issues_thread():
                    nonlocal all_issues, fetch_error
                    try:
                        from app.auth.metrics_helpers import fetch_issues_with_progress_queue
                        all_issues = fetch_issues_with_progress_queue(connection, jql, progress_queue)
                        progress_queue.put({'done': True})  # Señal de finalización
                    except Exception as e:
                        fetch_error = e
                        progress_queue.put({'error': str(e)})
                
                # Iniciar thread para obtener issues
                fetch_thread = Thread(target=fetch_issues_thread, daemon=True)
                fetch_thread.start()
            
            # Leer progreso de la cola y enviar eventos SSE
            fetch_complete = False
            while not fetch_complete:
                try:
                    # Obtener progreso con timeout
                    try:
                        progress_data = progress_queue.get(timeout=1.0)
                    except:
                        # Timeout, verificar si el thread terminó
                        if not fetch_thread.is_alive():
                            fetch_complete = True
                        continue
                    
                    if 'error' in progress_data:
                        fetch_error = Exception(progress_data['error'])
                        fetch_complete = True
                        break
                    
                    if progress_data.get('done'):
                        fetch_complete = True
                        break
                    
                    # Enviar evento de progreso
                    yield f"data: {json.dumps({'tipo': 'progreso', 'actual': progress_data.get('actual', 0), 'total': progress_data.get('total', 0), 'porcentaje': progress_data.get('porcentaje', 0)})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error al leer progreso: {e}")
            
            # Esperar a que termine el thread
            fetch_thread.join(timeout=10)
            
            if fetch_error:
                raise fetch_error
            
            # Obtener issues con paginación paralela (fallback si hubo error con cola)
            if not all_issues:
                try:
                    from app.auth.metrics_helpers import fetch_issues_with_parallel
                    all_issues = fetch_issues_with_parallel(connection, jql)
                except Exception as e:
                    logger.error(f"Error en fallback de obtención de issues: {e}", exc_info=True)
                    yield f"data: {json.dumps({'tipo': 'error', 'mensaje': f'Error al obtener issues: {str(e)}'})}\n\n"
                    return
            
            # Enviar evento de cálculo
            yield f"data: {json.dumps({'tipo': 'calculando', 'total_issues': len(all_issues)})}\n\n"
            
            # Calcular métricas
            try:
                metrics_result = calculate_metrics_from_issues(all_issues)
                
                response_data = {
                    "project_key": project_key,
                    "view_type": view_type,
                    "test_cases": metrics_result['test_cases'],
                    "bugs": metrics_result['bugs'],
                    "general_report": metrics_result['general_report'],
                    "total_issues": metrics_result['total_issues'],
                    "from_cache": False
                }
                
                # Guardar en caché
                metrics_cache.set(
                    project_key,
                    view_type,
                    filters_for_cache,
                    response_data,
                    user_id=cache_user_id
                )
                
                # Enviar evento de completado
                yield f"data: {json.dumps({'tipo': 'completado', 'reporte': response_data})}\n\n"
                
            except Exception as e:
                logger.error(f"Error al generar reporte: {e}", exc_info=True)
                yield f"data: {json.dumps({'tipo': 'error', 'mensaje': str(e)})}\n\n"
        
        except Exception as e:
            logger.error(f"Error crítico en SSE: {e}", exc_info=True)
            yield f"data: {json.dumps({'tipo': 'error', 'mensaje': f'Error crítico: {str(e)}'})}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
