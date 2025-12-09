"""
Módulo para interactuar con la API de Jira
NOTA: Este módulo mantiene compatibilidad hacia atrás.
Para nuevo código, usar app.backend.jira.jira_client_wrapper.JiraClient
"""
# Importar el nuevo JiraClient que usa servicios especializados
from app.backend.jira.jira_client_wrapper import JiraClient

# Re-exportar para compatibilidad hacia atrás
__all__ = ['JiraClient']

# Configuración de Jira desde config centralizado (para compatibilidad)
from app.core.config import Config
JIRA_BASE_URL = Config.JIRA_BASE_URL
JIRA_EMAIL = Config.JIRA_EMAIL
JIRA_API_TOKEN = Config.JIRA_API_TOKEN

# Estados que representan finalización real (para compatibilidad)
FINAL_STATUSES = {
    'done',
    'closed',
    'resolved',
    'finalizado',
    'completado',
    'terminado',
    'liberado',
    'Exitoso',
    'listo para produccion',
    'listo para producción'
}

# Mantener la clase antigua como alias para compatibilidad
# La nueva implementación está en jira_client_wrapper.py
