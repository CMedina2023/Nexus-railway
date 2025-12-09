"""
Servicio de gestión de sesiones
Responsabilidad única: Gestionar sesiones de usuario de forma segura
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from flask import session as flask_session

from app.models.user import User
from app.core.config import Config

logger = logging.getLogger(__name__)


class SessionService:
    """
    Servicio de gestión de sesiones (SRP)
    Responsabilidad única: Gestión de sesiones de usuario
    """
    
    # Claves de sesión
    USER_ID_KEY = 'user_id'
    USER_EMAIL_KEY = 'user_email'
    USER_ROLE_KEY = 'user_role'
    LOGIN_TIME_KEY = 'login_time'
    
    @staticmethod
    def create_session(user: User):
        """
        Crea una sesión de usuario
        
        ✅ Almacena datos mínimos necesarios
        ✅ Marca tiempo de login
        ✅ No almacena datos sensibles (no password_hash)
        
        Args:
            user: Usuario a crear sesión
        """
        flask_session[SessionService.USER_ID_KEY] = user.id
        flask_session[SessionService.USER_EMAIL_KEY] = user.email
        flask_session[SessionService.USER_ROLE_KEY] = user.role
        flask_session[SessionService.LOGIN_TIME_KEY] = datetime.now().isoformat()
        flask_session.permanent = True  # Sesión persistente
        
        logger.info(f"Sesión creada para usuario: {user.email} (rol: {user.role})")
    
    @staticmethod
    def get_current_user_id() -> Optional[str]:
        """
        Obtiene el ID del usuario actual de la sesión
        
        Returns:
            str: ID del usuario o None
        """
        return flask_session.get(SessionService.USER_ID_KEY)
    
    @staticmethod
    def get_current_user_role() -> Optional[str]:
        """
        Obtiene el rol del usuario actual de la sesión
        
        Returns:
            str: Rol del usuario o None
        """
        return flask_session.get(SessionService.USER_ROLE_KEY)
    
    @staticmethod
    def get_current_user_email() -> Optional[str]:
        """
        Obtiene el email del usuario actual de la sesión
        
        Returns:
            str: Email del usuario o None
        """
        return flask_session.get(SessionService.USER_EMAIL_KEY)
    
    @staticmethod
    def is_authenticated() -> bool:
        """
        Verifica si el usuario está autenticado
        
        Returns:
            bool: True si el usuario está autenticado
        """
        return SessionService.USER_ID_KEY in flask_session
    
    @staticmethod
    def destroy_session():
        """
        Destruye la sesión del usuario (logout)
        
        ✅ Limpia todos los datos de sesión
        ✅ Logging de logout
        """
        user_email = flask_session.get(SessionService.USER_EMAIL_KEY, 'Unknown')
        
        flask_session.clear()
        
        logger.info(f"Sesión destruida para usuario: {user_email}")
    
    @staticmethod
    def update_session(user: User):
        """
        Actualiza los datos de la sesión
        
        Útil cuando el usuario cambia de rol o datos actualizados
        
        Args:
            user: Usuario actualizado
        """
        if SessionService.is_authenticated():
            flask_session[SessionService.USER_EMAIL_KEY] = user.email
            flask_session[SessionService.USER_ROLE_KEY] = user.role
            logger.debug(f"Sesión actualizada para usuario: {user.email}")
    
    @staticmethod
    def get_session_info() -> dict:
        """
        Obtiene información de la sesión actual (sin datos sensibles)
        
        Returns:
            dict: Información de la sesión
        """
        logger.debug("[DEBUG] get_session_info() - Iniciando")
        try:
            # Verificar que flask_session esté disponible
            from flask import has_request_context
            if not has_request_context():
                logger.warning("[DEBUG] get_session_info() - No hay contexto de request")
                return {'authenticated': False}
            
            if not SessionService.is_authenticated():
                logger.debug("[DEBUG] get_session_info() - No autenticado, retornando {}")
                return {'authenticated': False}
            
            logger.debug("[DEBUG] get_session_info() - Usuario autenticado, obteniendo datos")
            user_id = flask_session.get(SessionService.USER_ID_KEY)
            email = flask_session.get(SessionService.USER_EMAIL_KEY)
            role = flask_session.get(SessionService.USER_ROLE_KEY)
            login_time_str = flask_session.get(SessionService.LOGIN_TIME_KEY)
            
            logger.debug(f"[DEBUG] get_session_info() - Datos de sesión: user_id={user_id}, email={email}, role={role}")
            
            login_time_iso = None
            if login_time_str:
                try:
                    login_time = datetime.fromisoformat(login_time_str)
                    logger.debug(f"[DEBUG] get_session_info() - login_time parseado: {login_time}")
                    login_time_iso = login_time.isoformat()
                except (ValueError, TypeError) as e:
                    logger.warning(f"[DEBUG] get_session_info() - Error al parsear login_time '{login_time_str}': {e}")
                    # Intentar parsear con formato alternativo si es necesario
                    try:
                        if isinstance(login_time_str, str):
                            login_time = datetime.fromisoformat(login_time_str.replace('Z', '+00:00'))
                            login_time_iso = login_time.isoformat()
                    except Exception:
                        pass
            
            result = {
                'user_id': user_id,
                'email': email,
                'role': role,
                'login_time': login_time_iso,
                'authenticated': True
            }
            
            logger.debug(f"[DEBUG] get_session_info() - Resultado: {result}")
            return result
        
        except Exception as e:
            logger.error(f"[DEBUG] get_session_info() - Error: {e}", exc_info=True)
            # Retornar dict vacío en lugar de lanzar excepción
            return {'authenticated': False, 'error': str(e)}


