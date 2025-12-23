"""
Servicio de gestión de tokens Jira
Responsabilidad única: Obtener y gestionar tokens Jira para usuarios (DIP)
"""
import logging
from typing import Optional
from dataclasses import dataclass

from app.models.user import User
from app.models.project_config import ProjectConfig
from app.models.user_jira_config import UserJiraConfig
from app.auth.encryption_service import EncryptionService
from app.database.repositories.project_config_repository import ProjectConfigRepository
from app.database.repositories.user_jira_config_repository import UserJiraConfigRepository
from app.utils.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class JiraConfig:
    """
    Configuración de Jira desencriptada para uso
    """
    base_url: str
    email: str
    token: str
    
    def to_dict(self) -> dict:
        """Convierte a diccionario (sin token por seguridad)"""
        return {
            'base_url': self.base_url,
            'email': self.email
            # No incluir token por seguridad
        }


class JiraTokenManager:
    """
    Gestión de tokens Jira (SRP + DIP)
    Responsabilidad única: Obtener y gestionar tokens para usuarios
    
    Prioridad de tokens:
    1. Token personal si existe y está activo (use_personal = true)
    2. Token compartido del proyecto (default)
    """
    
    def __init__(
        self,
        encryption_service: EncryptionService,
        project_config_repository: ProjectConfigRepository,
        user_jira_config_repository: UserJiraConfigRepository
    ):
        """
        Inicializa el gestor de tokens (DIP - inyección de dependencias)
        
        Args:
            encryption_service: Servicio de encriptación
            project_config_repository: Repositorio de configuración de proyectos
            user_jira_config_repository: Repositorio de configuración personal
        """
        self._encryption_service = encryption_service
        self._project_config_repo = project_config_repository
        self._user_jira_config_repo = user_jira_config_repository
    
    def get_token_for_user(self, user: User, project_key: str) -> JiraConfig:
        """
        Obtiene la configuración de Jira a usar para un usuario
        
        Prioridad:
        1. Token personal si existe y está activo
        2. Token compartido del proyecto
        
        ✅ Siempre desencripta tokens solo cuando se necesitan
        ✅ Nunca almacena tokens desencriptados en memoria persistente
        
        Args:
            user: Usuario actual
            project_key: Clave del proyecto
            
        Returns:
            JiraConfig: Configuración desencriptada de Jira
            
        Raises:
            ConfigurationError: Si el proyecto no está configurado
        """
        logger.info(f"[DEBUG JiraTokenManager] Obteniendo token para usuario {user.email}, proyecto {project_key}")
        
        # 1. Verificar token personal
        logger.info(f"[DEBUG JiraTokenManager] Buscando configuración personal para usuario {user.id}, proyecto {project_key}")
        personal_config = self._user_jira_config_repo.get_by_user_and_project(
            user.id, project_key
        )
        
        logger.info(f"[DEBUG JiraTokenManager] Configuración personal encontrada: {personal_config is not None}")
        if personal_config:
            logger.info(f"[DEBUG JiraTokenManager] use_personal: {personal_config.use_personal}")
        
        if personal_config and personal_config.use_personal:
            # Desencriptar solo cuando se necesita
            try:
                decrypted_token = self._encryption_service.decrypt(personal_config.personal_token)
                decrypted_email = self._encryption_service.decrypt(personal_config.personal_email)
                
                # Obtener URL base del proyecto
                shared_config = self._project_config_repo.get_by_project_key(project_key)
                if not shared_config:
                    # Fallback a variables de entorno
                    from app.core.config import Config
                    if Config.JIRA_BASE_URL:
                        logger.info(f"[DEBUG JiraTokenManager] Usando base_url desde variables de entorno para token personal")
                        return JiraConfig(
                            base_url=Config.JIRA_BASE_URL,
                            email=decrypted_email,
                            token=decrypted_token
                        )
                    raise ConfigurationError(f"Proyecto {project_key} no configurado")
                
                logger.debug(f"Usando token personal para usuario {user.email} en proyecto {project_key}")
                return JiraConfig(
                    base_url=shared_config.jira_base_url,
                    email=decrypted_email,
                    token=decrypted_token
                )
            except Exception as e:
                logger.warning(f"Error al usar token personal, usando compartido: {e}")
                # Fallback a token compartido si hay error con el personal
        
        # 2. Usar token compartido (default)
        logger.info(f"[DEBUG JiraTokenManager] Buscando configuración compartida para proyecto {project_key}")
        shared_config = self._project_config_repo.get_by_project_key(project_key)
        
        if not shared_config:
            # Fallback: usar configuración desde variables de entorno (compatibilidad hacia atrás)
            logger.info(f"[DEBUG JiraTokenManager] Proyecto {project_key} no encontrado en BD, intentando variables de entorno")
            from app.core.config import Config
            
            if Config.JIRA_BASE_URL and Config.JIRA_EMAIL and Config.JIRA_API_TOKEN:
                logger.info(f"[DEBUG JiraTokenManager] Usando configuración desde variables de entorno")
                return JiraConfig(
                    base_url=Config.JIRA_BASE_URL,
                    email=Config.JIRA_EMAIL,
                    token=Config.JIRA_API_TOKEN
                )
            
            logger.error(f"[DEBUG JiraTokenManager] Proyecto {project_key} NO está configurado en la base de datos ni en variables de entorno")
            raise ConfigurationError(
                f"Proyecto {project_key} no está configurado. "
                "Un administrador debe configurar el proyecto primero o configurar las variables de entorno JIRA_BASE_URL, JIRA_EMAIL y JIRA_API_TOKEN."
            )
        
        logger.info(f"[DEBUG JiraTokenManager] Configuración compartida encontrada: base_url={shared_config.jira_base_url}")
        
        try:
            logger.info(f"[DEBUG JiraTokenManager] Desencriptando token compartido...")
            decrypted_token = self._encryption_service.decrypt(shared_config.shared_token)
            decrypted_email = self._encryption_service.decrypt(shared_config.shared_email)
            
            logger.info(f"[DEBUG JiraTokenManager] Token desencriptado exitosamente para email: {decrypted_email}")
            logger.info(f"Usando token compartido para usuario {user.email} en proyecto {project_key}")
            return JiraConfig(
                base_url=shared_config.jira_base_url,
                email=decrypted_email,
                token=decrypted_token
            )
        except Exception as e:
            logger.error(f"[DEBUG JiraTokenManager] Error al desencriptar token compartido: {e}", exc_info=True)
            raise ConfigurationError(f"Error al acceder a la configuración de Jira: {str(e)}")
    
    def save_project_config(
        self,
        project_key: str,
        jira_base_url: str,
        email: str,
        token: str,
        created_by: str
    ) -> ProjectConfig:
        """
        Guarda configuración de proyecto (token compartido)
        
        ✅ Encripta tokens antes de guardar
        ✅ Valida que el proyecto no exista
        
        Args:
            project_key: Clave del proyecto
            jira_base_url: URL base de Jira
            email: Email de Jira
            token: Token de Jira (en texto plano)
            created_by: ID del usuario que crea la configuración
            
        Returns:
            ProjectConfig: Configuración guardada
        """
        # Verificar si ya existe
        existing = self._project_config_repo.get_by_project_key(project_key)
        if existing:
            raise ValueError(f"El proyecto {project_key} ya está configurado")
        
        # Encriptar datos sensibles
        encrypted_email = self._encryption_service.encrypt(email)
        encrypted_token = self._encryption_service.encrypt(token)
        
        # Crear configuración
        from app.models.project_config import ProjectConfig
        config = ProjectConfig(
            project_key=project_key,
            jira_base_url=jira_base_url,
            shared_email=encrypted_email,
            shared_token=encrypted_token,
            created_by=created_by
        )
        
        # Guardar
        saved_config = self._project_config_repo.create(config)
        logger.info(f"Configuración de proyecto guardada: {project_key} por {created_by}")
        
        return saved_config
    
    def update_project_config(
        self,
        project_key: str,
        jira_base_url: Optional[str] = None,
        email: Optional[str] = None,
        token: Optional[str] = None,
        updated_by: str = None
    ) -> ProjectConfig:
        """
        Actualiza configuración de proyecto
        
        ✅ Encripta tokens antes de guardar
        ✅ Solo actualiza campos proporcionados
        
        Args:
            project_key: Clave del proyecto
            jira_base_url: Nueva URL base (opcional)
            email: Nuevo email (opcional)
            token: Nuevo token (opcional)
            updated_by: ID del usuario que actualiza
            
        Returns:
            ProjectConfig: Configuración actualizada
        """
        config = self._project_config_repo.get_by_project_key(project_key)
        if not config:
            raise ValueError(f"Proyecto {project_key} no encontrado")
        
        # Actualizar solo campos proporcionados
        if jira_base_url:
            config.jira_base_url = jira_base_url
        if email:
            config.shared_email = self._encryption_service.encrypt(email)
        if token:
            config.shared_token = self._encryption_service.encrypt(token)
        
        if updated_by:
            config.updated_by = updated_by
        
        updated_config = self._project_config_repo.update(config)
        logger.info(f"Configuración de proyecto actualizada: {project_key} por {updated_by}")
        
        return updated_config
