"""
Paquete de rutas de métricas
Dividido por tipo de métrica / funcionalidad (Estándar vs Streaming)
"""
from flask import Blueprint

# Crear Blueprint para métricas
metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/jira/metrics')

from . import standard
from . import stream
