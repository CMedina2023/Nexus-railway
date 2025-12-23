"""
Rutas de métricas de Jira
Responsabilidad única: Endpoints para métricas generales y personales (SRP)
"""
import logging
import time
import json
from queue import Queue
from threading import Thread
from flask import Blueprint, request, jsonify, Response
from typing import Optional

from app.auth.decorators import login_required, role_required, get_current_user_id
from app.auth.session_service import SessionService
from app.services.jira_token_manager import JiraTokenManager
from app.services.metrics_cache import get_metrics_cache
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_service import IssueService
from app.auth.metrics_helpers import build_jql_from_filters, calculate_metrics_from_issues
from app.models.user import User
from app.auth.user_service import UserService
from app.core.dependencies import get_user_service, get_jira_token_manager
from app.utils.exceptions import ConfigurationError
from app.core.config import Config
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.models.jira_report import JiraReport

logger = logging.getLogger(__name__)

# Crear Blueprint para métricas
metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/jira/metrics')


@metrics_bp.route('/<project_key>', methods=['GET'])
@login_required
def get_project_metrics(project_key: str):
    """
    Obtiene métricas del proyecto (generales o personales según parámetro)
    
    Query params:
        - view_type: "general" | "personal" (default: "personal")
    
    ✅ General: Solo Admin
    ✅ Personal: Todos los usuarios autenticados
    ✅ Filtra por assignee cuando es personal
    """
    try:
        logger.info(f"[DEBUG] Iniciando get_project_metrics para proyecto: {project_key}")
        
        # Obtener usuario y su rol
        user_id = get_current_user_id()
        logger.info(f"[DEBUG] User ID obtenido: {user_id}")
        
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id) if user_id else None
        
        if not user:
            logger.error(f"[DEBUG] Usuario no encontrado con ID: {user_id}")
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        logger.info(f"[DEBUG] Usuario encontrado: {user.email}, rol: {user.role}")
        
        user_role = user.role
        
        # Determinar tipo de vista según rol
        # Admin: puede ver general o personal (default: general)
        # Usuario: SOLO puede ver personal (forzado)
        requested_view_type = request.args.get('view_type', '').lower()
        logger.info(f"[DEBUG] view_type solicitado: {requested_view_type}, rol usuario: {user_role}")
        
        if user_role == 'admin':
            view_type = requested_view_type if requested_view_type in ['general', 'personal'] else 'general'
        else:
            # Usuarios no admin SOLO pueden ver métricas personales (analista_qa y usuario)
            view_type = 'personal'
            logger.info(f"[DEBUG] Usuario {user.email} (rol: {user_role}) - forzando vista personal")
        
        logger.info(f"[DEBUG] view_type final: {view_type}")
        cache_user_id = user.id if view_type == 'personal' else None
        
        # Verificar permisos para vista general
        if view_type == 'general' and user_role != 'admin':
            logger.warning(f"[DEBUG] Intento no autorizado de {user.email} (rol: {user_role}) a ver métricas generales")
            return jsonify({
                "error": "No autorizado. Solo Admin puede ver métricas generales"
            }), 403
        
        
        # Obtener configuración de Jira para el usuario
        logger.info(f"[DEBUG] Obteniendo configuración de Jira para usuario {user.email}, proyecto {project_key}")
        token_manager = get_jira_token_manager()
        
        try:
            jira_config = token_manager.get_token_for_user(user, project_key)
            logger.info(f"[DEBUG] Configuración de Jira obtenida: base_url={jira_config.base_url}, email={jira_config.email}")
        except ConfigurationError as e:
            logger.error(f"[DEBUG] Error de configuración: {str(e)}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"[DEBUG] Error inesperado al obtener configuración: {e}", exc_info=True)
            return jsonify({"error": f"Error al obtener configuración: {str(e)}"}), 400
        
        # Crear conexión y servicios
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        project_service = ProjectService(connection)
        issue_service = IssueService(connection, project_service)
        
        # Obtener filtros de query params (formato nuevo: separados por tipo)
        filters_testcase = request.args.getlist('filter_testcase')
        filters_bug = request.args.getlist('filter_bug')
        filters_legacy = request.args.getlist('filter')  # Formato antiguo para compatibilidad
        
        # Determinar si usar formato nuevo o antiguo
        if filters_testcase or filters_bug:
            # Formato nuevo: filtros separados por tipo
            filters_by_type = {
                'testCases': filters_testcase,
                'bugs': filters_bug
            }
            logger.info(f"[DEBUG] Filtros recibidos (separados): Test Cases: {len(filters_testcase)}, Bugs: {len(filters_bug)}")
            # Para caché, usar una clave combinada
            filters_for_cache = filters_testcase + filters_bug
        else:
            # Formato antiguo: filtros combinados
            filters_by_type = None
            filters_for_cache = filters_legacy
            logger.info(f"[DEBUG] Filtros recibidos (legacy): {filters_legacy}")
        
        # Verificar caché antes de obtener issues
        start_time = time.time()
        metrics_cache = get_metrics_cache(Config.JIRA_METRICS_CACHE_TTL_HOURS)
        cached_metrics = metrics_cache.get(
            project_key,
            view_type,
            filters_for_cache,
            user_id=cache_user_id
        )
        
        if cached_metrics:
            cache_time = time.time() - start_time
            logger.info(f"[PERFORMANCE] Métricas obtenidas desde caché en {cache_time*1000:.2f}ms para proyecto {project_key}, view_type: {view_type}")
            response_data = cached_metrics.copy()
            response_data['project_key'] = project_key
            response_data['view_type'] = view_type
            response_data['from_cache'] = True
            return jsonify(response_data), 200
        
        # Construir JQL usando helper
        fetch_start = time.time()
        fetch_time = 0.0
        
        if filters_by_type and (filters_by_type.get('testCases') or filters_by_type.get('bugs')):
            # Formato nuevo: filtros separados por tipo
            logger.info(f"[DEBUG] Usando filtros separados por tipo")
            try:
                from app.auth.metrics_helpers import fetch_issues_with_separate_filters
                all_issues = fetch_issues_with_separate_filters(
                    connection=connection,
                    project_key=project_key,
                    view_type=view_type,
                    filters_testcase=filters_by_type.get('testCases', []),
                    filters_bug=filters_by_type.get('bugs', []),
                    assignee_email=jira_config.email if view_type == 'personal' else None
                )
                fetch_time = time.time() - fetch_start
                issues_per_sec = len(all_issues) / fetch_time if fetch_time > 0 else 0
                logger.info(f"[PERFORMANCE] Issues obtenidas en {fetch_time:.2f}s ({len(all_issues)} issues, {issues_per_sec:.1f} issues/segundo)")
            except Exception as e:
                logger.error(f"[DEBUG] Error al obtener issues con filtros separados: {str(e)}", exc_info=True)
                # Fallback: obtener sin filtros
                fetch_start_fallback = time.time()
                if view_type == 'personal':
                    all_issues = issue_service.get_issues_by_assignee(
                        project_key=project_key,
                        assignee_email=jira_config.email,
                        max_results=1000
                    )
                else:
                    all_issues = issue_service.get_all_issues(
                        project_key=project_key,
                        max_results=1000
                    )
                fetch_time = time.time() - fetch_start_fallback
                logger.info(f"[PERFORMANCE] Issues obtenidas con fallback en {fetch_time:.2f}s ({len(all_issues)} issues)")
        elif filters_legacy and len(filters_legacy) > 0:
            # Formato antiguo: filtros combinados
            final_jql = build_jql_from_filters(
                project_key=project_key,
                view_type=view_type,
                filters=filters_legacy,
                assignee_email=jira_config.email if view_type == 'personal' else None
            )
            logger.info(f"[DEBUG] JQL final con filtros (legacy): {final_jql}")
            
            # Obtener issues con filtros aplicados usando paginación paralela optimizada
            logger.info(f"[OPTIMIZADO] Obteniendo issues con JQL personalizado usando paginación paralela")
            try:
                from app.auth.metrics_helpers import fetch_issues_with_parallel
                all_issues = fetch_issues_with_parallel(connection, final_jql)
                fetch_time = time.time() - fetch_start
                issues_per_sec = len(all_issues) / fetch_time if fetch_time > 0 else 0
                logger.info(f"[PERFORMANCE] Issues obtenidas en {fetch_time:.2f}s ({len(all_issues)} issues, {issues_per_sec:.1f} issues/segundo)")
            except Exception as e:
                logger.error(f"[DEBUG] Error al obtener issues con paginación paralela: {str(e)}", exc_info=True)
                # Fallback: obtener sin filtros (usar max_results=1000 explícitamente)
                fetch_start_fallback = time.time()
                if view_type == 'personal':
                    all_issues = issue_service.get_issues_by_assignee(
                        project_key=project_key,
                        assignee_email=jira_config.email,
                        max_results=1000
                    )
                else:
                    all_issues = issue_service.get_all_issues(
                        project_key=project_key,
                        max_results=1000
                    )
                fetch_time = time.time() - fetch_start_fallback
                logger.info(f"[PERFORMANCE] Issues obtenidas con fallback en {fetch_time:.2f}s ({len(all_issues)} issues)")
        else:
            # Sin filtros, construir JQL simple y usar paginación paralela
            logger.info(f"[OPTIMIZADO] Obteniendo issues - view_type: {view_type}, project_key: {project_key}")
            if view_type == 'personal':
                # JQL para vista personal
                jql = f'project = {project_key} AND assignee = "{jira_config.email}"'
                logger.info(f"[DEBUG] Filtrando por assignee: {jira_config.email}")
            else:
                # JQL para vista general
                jql = f'project = {project_key}'
                logger.info(f"[DEBUG] Obteniendo todas las issues del proyecto {project_key}")
            
            # Usar paginación paralela optimizada
            try:
                from app.auth.metrics_helpers import fetch_issues_with_parallel
                all_issues = fetch_issues_with_parallel(connection, jql)
                fetch_time = time.time() - fetch_start
                issues_per_sec = len(all_issues) / fetch_time if fetch_time > 0 else 0
                logger.info(f"[PERFORMANCE] Issues obtenidas en {fetch_time:.2f}s ({len(all_issues)} issues, {issues_per_sec:.1f} issues/segundo)")
            except Exception as e:
                logger.error(f"[DEBUG] Error con paginación paralela, usando fallback: {str(e)}")
                fetch_start_fallback = time.time()
                # Fallback: usar métodos normales (usar max_results=1000 explícitamente)
                if view_type == 'personal':
                    all_issues = issue_service.get_issues_by_assignee(
                        project_key=project_key,
                        assignee_email=jira_config.email,
                        max_results=1000
                    )
                else:
                    all_issues = issue_service.get_all_issues(
                        project_key=project_key,
                        max_results=1000
                    )
                fetch_time = time.time() - fetch_start_fallback
                logger.info(f"[PERFORMANCE] Issues obtenidas con fallback en {fetch_time:.2f}s ({len(all_issues)} issues)")
        
        # Log de tipos de issues encontrados para debug
        issue_types_found = {}
        for issue in all_issues:
            issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', 'Unknown')
            issue_types_found[issue_type] = issue_types_found.get(issue_type, 0) + 1
        logger.info(f"[DEBUG] Tipos de issues encontrados: {issue_types_found}")
        
        # Calcular métricas usando helper
        calc_start = time.time()
        metrics_result = calculate_metrics_from_issues(all_issues)
        calc_time = time.time() - calc_start
        
        logger.info(f"[PERFORMANCE] Métricas calculadas en {calc_time*1000:.2f}ms - test_cases: {metrics_result['test_case_count']}, bugs: {metrics_result['bug_count']}")
        
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
        
        # Guardar reporte en base de datos local para métricas por usuario
        try:
            report_repo = JiraReportRepository()
            jira_report = JiraReport(
                user_id=user.id,
                project_key=project_key,
                report_type='metrics',
                report_title=f'Reporte de Métricas - {project_key} ({view_type})',
                report_content=json.dumps(response_data, ensure_ascii=False),
                jira_issue_key='N/A'  # Reportes de métricas son locales, no se suben a Jira
            )
            report_repo.create(jira_report)
            logger.info(f"Reporte de métricas guardado en BD local para user_id={user.id}, proyecto={project_key}")
        except Exception as e:
            logger.error(f"Error al guardar reporte en BD local: {e}", exc_info=True)
            # No fallar la operación si falla el guardado en BD local
        
        total_time = time.time() - start_time
        logger.info(f"[PERFORMANCE] Reporte completo generado en {total_time:.2f}s (fetch: {fetch_time:.2f}s, calc: {calc_time*1000:.2f}ms) para proyecto {project_key}, {len(all_issues)} issues")
        logger.info(f"[CACHE] Métricas guardadas en caché para proyecto {project_key}, view_type: {view_type}")
        
        logger.info(f"[DEBUG] Retornando respuesta exitosa para proyecto {project_key}, view_type: {view_type}")
        return jsonify(response_data), 200
    
    except ConfigurationError as e:
        logger.error(f"[DEBUG] ConfigurationError: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"[DEBUG] Error al obtener métricas: {e}", exc_info=True)
        return jsonify({"error": f"Error al obtener métricas del proyecto: {str(e)}"}), 500


@metrics_bp.route('/<project_key>/general', methods=['GET'])
@login_required
@role_required('admin')
def get_general_metrics(project_key: str):
    """
    Obtiene métricas generales del proyecto
    
    ✅ Solo Admin
    ✅ Muestra TODAS las issues del proyecto
    """
    return get_project_metrics(project_key)


@metrics_bp.route('/<project_key>/personal', methods=['GET'])
@login_required
def get_personal_metrics(project_key: str):
    """
    Obtiene métricas personales del proyecto
    
    ✅ Todos los usuarios autenticados
    ✅ Filtra por assignee del usuario
    """
    # Forzar vista personal
    view_type = request.args.get('view_type', 'personal')
    request.args = request.args.copy()
    request.args['view_type'] = 'personal'
    
    return get_project_metrics(project_key)


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
    import json
    from flask import has_request_context
    
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
                from app.backend.jira.parallel_issue_fetcher import ParallelIssueFetcher
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



