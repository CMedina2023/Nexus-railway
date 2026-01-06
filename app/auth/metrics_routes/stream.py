"""
Rutas de métricas en Streaming (SSE)
"""
import logging
import json
from flask import request, Response

from app.auth.decorators import login_required, get_current_user_id
from app.core.dependencies import get_user_service
from app.services.stream_generator import MetricsStreamGenerator
from . import metrics_bp

logger = logging.getLogger(__name__)

@metrics_bp.route('/<project_key>/stream', methods=['GET'])
@login_required
def generate_report_stream(project_key: str):
    """
    Genera reporte con progreso en tiempo real usando Server-Sent Events (SSE)
    
    Query params:
        - view_type: "general" | "personal"
        - filter_testcase: Filtros para casos de prueba
        - filter_bug: Filtros para bugs
        - filter: Filtros adicionales (formato antiguo)
    
    Retorna eventos SSE:
        - tipo: "inicio" - Indica inicio del proceso
        - tipo: "progreso" - Progreso de obtención de issues
        - tipo: "calculando" - Inicio de cálculo de métricas
        - tipo: "completado" - Reporte completo con métricas
        - tipo: "error" - Error en el proceso
    """
    
    # 1. Obtener usuario para el contexto de la solicitud
    try:
        user_id = get_current_user_id()
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id) if user_id else None
    except Exception as e:
        logger.error(f"Error al obtener usuario en SSE: {e}", exc_info=True)
        user = None
    
    if not user:
        error_data = {"tipo": "error", "mensaje": "Usuario no encontrado o sesión expirada"}
        return Response(f"data: {json.dumps(error_data)}\n\n", mimetype='text/event-stream')
    
    # 2. Extraer parámetros de la solicitud
    requested_view_type = request.args.get('view_type', '').lower()
    filters_testcase = request.args.getlist('filter_testcase')
    filters_bug = request.args.getlist('filter_bug')
    filters_legacy = request.args.getlist('filter')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    # 3. Preparar filtros por tipo si existen
    filters_by_type = None
    if filters_testcase or filters_bug:
        filters_by_type = {
            'testCases': filters_testcase,
            'bugs': filters_bug
        }
    
    # 4. Instanciar el orquestador de streaming
    # Se extrae toda la lógica compleja a MetricsStreamGenerator (SRP)
    stream_service = MetricsStreamGenerator(
        user=user,
        project_key=project_key,
        requested_view_type=requested_view_type,
        filters_by_type=filters_by_type,
        filters_legacy=filters_legacy,
        force_refresh=force_refresh
    )
    
    # 5. Retornar respuesta de streaming
    return Response(
        stream_service.generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream'
        }
    )
