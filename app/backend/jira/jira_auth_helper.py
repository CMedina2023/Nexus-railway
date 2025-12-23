"""
Helper para obtener conexión Jira basada en usuario autenticado
Responsabilidad única: Obtener conexión Jira con tokens del usuario actual
"""
import logging
from typing import Optional

from app.backend.jira.connection import JiraConnection
from app.services.jira_token_manager import JiraTokenManager
from app.auth.session_service import SessionService
from app.auth.user_service import UserService
from app.core.dependencies import get_user_service, get_jira_token_manager
from app.utils.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def get_jira_connection_for_user(project_key: str) -> JiraConnection:
    """
    Obtiene una conexión Jira para el usuario actual
    
    ✅ Usa JiraTokenManager para obtener tokens
    ✅ Prioriza token personal si está activo
    ✅ Usa token compartido del proyecto si no hay personal
    
    Args:
        project_key: Clave del proyecto
        
    Returns:
        JiraConnection: Conexión configurada con tokens del usuario
        
    Raises:
        ConfigurationError: Si el usuario no está autenticado o el proyecto no está configurado
    """
    # Verificar que el usuario esté autenticado
    if not SessionService.is_authenticated():
        raise ConfigurationError("Usuario no autenticado")
    
    user_id = SessionService.get_current_user_id()
    if not user_id:
        raise ConfigurationError("Usuario no autenticado")
    
    # Obtener usuario actual
    user_service = get_user_service()
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise ConfigurationError("Usuario no encontrado")
    
    # Obtener configuración de Jira usando JiraTokenManager
    token_manager = get_jira_token_manager()
    jira_config = token_manager.get_token_for_user(user, project_key)
    
    # Crear conexión con los tokens obtenidos
    connection = JiraConnection(
        base_url=jira_config.base_url,
        email=jira_config.email,
        api_token=jira_config.token
    )
    
    return connection


def get_jira_connection_shared(project_key: str) -> Optional[JiraConnection]:
    """
    Obtiene una conexión Jira usando token compartido (para admins)
    
    Args:
        project_key: Clave del proyecto
        
    Returns:
        JiraConnection: Conexión con token compartido o None
    """
    try:
        from app.services.jira_token_manager import JiraTokenManager
        from app.database.repositories.project_config_repository import ProjectConfigRepository
        from app.auth.encryption_service import EncryptionService
        
        # Obtener configuración compartida directamente
        project_repo = ProjectConfigRepository()
        project_config = project_repo.get_by_project_key(project_key)
        
        if not project_config:
            return None
        
        # Desencriptar tokens
        from app.core.dependencies import get_encryption_service
        encryption_service = get_encryption_service()
        decrypted_email = encryption_service.decrypt(project_config.shared_email)
        decrypted_token = encryption_service.decrypt(project_config.shared_token)
        
        # Crear conexión
        connection = JiraConnection(
            base_url=project_config.jira_base_url,
            email=decrypted_email,
            api_token=decrypted_token
        )
        
        return connection
    
    except Exception as e:
        logger.error(f"Error al obtener conexión compartida: {e}")
        return None

