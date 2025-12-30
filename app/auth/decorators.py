"""
Decoradores de autenticación y autorización
Responsabilidad única: Decoradores reutilizables para protección de endpoints
"""
import logging
from functools import wraps
from typing import List, Optional, Callable
from flask import session, jsonify, redirect, url_for, request, abort

from app.auth.session_service import SessionService
from app.utils.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


def login_required(f: Callable) -> Callable:
    """
    Decorador para requerir autenticación (SRP)
    
    ✅ Verifica sesión válida
    ✅ Redirige a login si no está autenticado
    ✅ Retorna JSON 401 para endpoints API
    
    Usage:
        @app.route('/api/protected')
        @login_required
        def protected_endpoint():
            return jsonify({"message": "Protected"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionService.is_authenticated():
            # Si es un endpoint API, retornar JSON
            if request.path.startswith('/api/'):
                logger.warning(f"Intento de acceso no autenticado a: {request.path}")
                return jsonify({"error": "No autenticado", "status": "unauthorized"}), 401
            # Si es una página, guardar URL original y redirigir a login
            from flask import session as flask_session
            # Guardar la URL original para redirigir después del login
            flask_session['next_url'] = request.url
            logger.debug(f"Guardando URL original para redirección: {request.url}")
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(*allowed_roles: str):
    """
    Decorador para requerir roles específicos (OCP: extensible)
    
    ✅ Verifica autenticación primero
    ✅ Verifica rol del usuario
    ✅ Retorna JSON 403 para endpoints API
    
    Args:
        *allowed_roles: Roles permitidos ('admin', 'usuario', 'analista_qa')
    
    Usage:
        @app.route('/api/admin')
        @login_required
        @role_required('admin')
        def admin_endpoint():
            return jsonify({"message": "Admin only"})
        
        @app.route('/api/admin')
        @login_required
        @role_required('admin')
        def admin_endpoint():
            return jsonify({"message": "Admin only"})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        @login_required  # Requiere autenticación primero
        def decorated_function(*args, **kwargs):
            user_role = SessionService.get_current_user_role()
            
            if not user_role or user_role not in allowed_roles:
                # Si es un endpoint API, retornar JSON
                if request.path.startswith('/api/'):
                    logger.warning(
                        f"Intento de acceso no autorizado a: {request.path} "
                        f"(usuario: {SessionService.get_current_user_email()}, "
                        f"rol: {user_role}, requerido: {allowed_roles})"
                    )
                    return jsonify({
                        "error": "No autorizado",
                        "status": "forbidden",
                        "required_roles": list(allowed_roles)
                    }), 403
                # Si es una página, retornar 403
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def get_current_user_id() -> Optional[str]:
    """
    Helper para obtener ID del usuario actual
    
    Returns:
        str: ID del usuario actual o None
    """
    return SessionService.get_current_user_id()


def get_current_user_role() -> Optional[str]:
    """
    Helper para obtener rol del usuario actual
    
    Returns:
        str: Rol del usuario actual o None
    """
    return SessionService.get_current_user_role()


def filter_by_role(f: Callable) -> Callable:
    """
    Decorador que inyecta el objeto usuario actual tras validar login (SRP)
    
    ✅ Valida login
    ✅ Obtiene el objeto usuario completo
    ✅ Inyecta el usuario como primer argumento
    
    Returns:
        Callable: Función decorada que recibe el objeto user
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        from app.core.dependencies import get_user_service
        
        user_id = SessionService.get_current_user_id()
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        return f(user, *args, **kwargs)
        
    return decorated_function



