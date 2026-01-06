"""
Rutas de métricas estándar (JSON)
"""
import logging
from flask import request, jsonify

from app.auth.decorators import login_required, role_required, get_current_user_id
from app.services.metrics_service import MetricsService
from app.core.dependencies import get_user_service
from app.utils.exceptions import ConfigurationError

from . import metrics_bp

logger = logging.getLogger(__name__)

# Instancia global del servicio para evitar recreación
metrics_service = MetricsService()

@metrics_bp.route('/<project_key>', methods=['GET'])
@login_required
def get_project_metrics(project_key: str):
    """
    Obtiene métricas del proyecto (generales o personales según parámetro)
    
    Query params:
        - view_type: "general" | "personal" (default: "personal")
    """
    user_id = get_current_user_id()
    user_service = get_user_service()
    user = user_service.get_user_by_id(user_id) if user_id else None
    
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Extraer parámetros de la request
    requested_view_type = request.args.get('view_type', '').lower()
    filters_testcase = request.args.getlist('filter_testcase')
    filters_bug = request.args.getlist('filter_bug')
    filters_legacy = request.args.getlist('filter')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    # Orquestar llamada al servicio
    result = metrics_service.get_project_metrics(
        user=user,
        project_key=project_key,
        requested_view_type=requested_view_type,
        filters_testcase=filters_testcase,
        filters_bug=filters_bug,
        filters_legacy=filters_legacy,
        force_refresh=force_refresh
    )
    
    return jsonify(result), 200

@metrics_bp.route('/<project_key>/general', methods=['GET'])
@login_required
@role_required('admin')
def get_general_metrics(project_key: str):
    """
    Obtiene métricas generales del proyecto (Solo Admin)
    """
    # Forzar vista general
    request.args = request.args.copy()
    request.args['view_type'] = 'general'
    return get_project_metrics(project_key)

@metrics_bp.route('/<project_key>/personal', methods=['GET'])
@login_required
def get_personal_metrics(project_key: str):
    """
    Obtiene métricas personales del proyecto
    """
    # Forzar vista personal
    request.args = request.args.copy()
    request.args['view_type'] = 'personal'
    return get_project_metrics(project_key)
