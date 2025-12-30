"""
Paquete de rutas de métricas
Dividido por tipo de métrica / funcionalidad (Estándar vs Streaming)
"""
from flask import Blueprint, jsonify
import logging
from app.utils.exceptions import ConfigurationError

# Crear Blueprint para métricas
metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/jira/metrics')

logger = logging.getLogger(__name__)

@metrics_bp.errorhandler(ConfigurationError)
def handle_configuration_error(e):
    """Manejador para errores de configuración"""
    logger.error(f"Error de configuración en métricas: {str(e)}")
    return jsonify({"error": str(e)}), 400

@metrics_bp.errorhandler(Exception)
def handle_unexpected_error(e):
    """Manejador para errores inesperados"""
    logger.error(f"Error inesperado en métricas: {str(e)}", exc_info=True)
    return jsonify({"error": f"Error interno en métricas: {str(e)}"}), 500

from . import standard
from . import stream
