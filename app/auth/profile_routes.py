"""
Rutas de perfil de usuario
Responsabilidad única: Endpoints para gestión de perfil personal (SRP)
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from typing import Optional

from app.auth.decorators import login_required, get_current_user_id
from app.auth.user_service import UserService
from app.auth.password_service import PasswordService
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.user_jira_config_repository import UserJiraConfigRepository
from app.database.repositories.user_jira_config_repository import UserJiraConfigRepository
from app.utils.exceptions import ValidationError
from app.core.dependencies import get_user_service

logger = logging.getLogger(__name__)

# Crear Blueprint para perfil
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def profile_dashboard():
    """
    Página de perfil del usuario (requiere autenticación)
    
    ✅ Muestra información del usuario
    ✅ Permite cambiar contraseña
    ✅ Muestra tokens personales de Jira configurados
    """
    from app.auth.session_service import SessionService
    
    user_id = SessionService.get_current_user_id()
    user_service = get_user_service()
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return render_template('auth/login.html', error="Usuario no encontrado"), 404
    
    # Obtener configuraciones personales de Jira
    jira_config_repo = UserJiraConfigRepository()
    jira_configs = jira_config_repo.get_by_user_id(user_id)
    
    return render_template('profile/dashboard.html', 
                         user=user.to_dict(include_sensitive=False),
                         jira_configs=[config.to_dict() for config in jira_configs] if jira_configs else [])


@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Cambia la contraseña del usuario actual (requiere autenticación)
    
    Body JSON o Form:
        {
            "current_password": "contraseña actual",
            "new_password": "nueva contraseña",
            "confirm_password": "confirmar nueva contraseña"
        }
    
    ✅ Valida contraseña actual
    ✅ Valida fortaleza de nueva contraseña
    ✅ Verifica que las contraseñas coincidan
    ✅ Actualiza hash de contraseña
    """
    try:
        from app.auth.session_service import SessionService
        
        data = request.get_json() if request.is_json else request.form
        user_id = SessionService.get_current_user_id()
        
        if not user_id:
            return jsonify({"error": "No autenticado"}), 401
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validación básica
        if not current_password or not new_password or not confirm_password:
            error_msg = "Todos los campos son requeridos"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('profile/dashboard.html', error=error_msg), 400
        
        # Verificar que las contraseñas nuevas coincidan
        if new_password != confirm_password:
            error_msg = "Las contraseñas nuevas no coinciden"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('profile/dashboard.html', error=error_msg), 400
        
        # Obtener usuario
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            error_msg = "Usuario no encontrado"
            if request.is_json:
                return jsonify({"error": error_msg}), 404
            return render_template('profile/dashboard.html', error=error_msg), 404
        
        # Verificar contraseña actual
        password_service = PasswordService()
        if not password_service.verify_password(current_password, user.password_hash):
            logger.warning(f"Intento de cambio de contraseña con contraseña actual incorrecta: {user.email}")
            error_msg = "Contraseña actual incorrecta"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('profile/dashboard.html', error=error_msg), 400
        
        # Validar fortaleza de nueva contraseña
        is_valid, errors = password_service.validate_password_strength(new_password)
        if not is_valid:
            error_msg = f"Contraseña inválida: {'; '.join(errors)}"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('profile/dashboard.html', error=error_msg), 400
        
        # Verificar que la nueva contraseña sea diferente
        if password_service.verify_password(new_password, user.password_hash):
            error_msg = "La nueva contraseña debe ser diferente a la actual"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('profile/dashboard.html', error=error_msg), 400
        
        # Actualizar contraseña
        user_repo = UserRepository()
        user.password_hash = password_service.hash_password(new_password)
        user.updated_at = datetime.now()
        user_repo.update(user)
        
        logger.info(f"Contraseña actualizada para usuario: {user.email}")
        
        success_msg = "Contraseña actualizada exitosamente"
        if request.is_json:
            return jsonify({"success": True, "message": success_msg}), 200
        
        return render_template('profile/dashboard.html', success=success_msg)
    
    except ValidationError as e:
        logger.warning(f"Error de validación al cambiar contraseña: {e}")
        error_msg = str(e)
        if request.is_json:
            return jsonify({"error": error_msg}), 400
        return render_template('profile/dashboard.html', error=error_msg), 400
    except Exception as e:
        logger.error(f"Error al cambiar contraseña: {e}", exc_info=True)
        error_msg = "Error al cambiar contraseña. Intenta nuevamente."
        if request.is_json:
            return jsonify({"error": error_msg}), 500
        return render_template('profile/dashboard.html', error=error_msg), 500


@profile_bp.route('/info', methods=['GET'])
@login_required
def get_profile_info():
    """
    Obtiene información del perfil del usuario actual (requiere autenticación)
    
    Returns:
        JSON con información del perfil (sin datos sensibles)
    """
    try:
        from app.auth.session_service import SessionService
        
        user_id = SessionService.get_current_user_id()
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Obtener configuraciones personales de Jira
        jira_config_repo = UserJiraConfigRepository()
        jira_configs = jira_config_repo.get_by_user_id(user_id)
        
        return jsonify({
            "success": True,
            "user": user.to_dict(include_sensitive=False),
            "jira_configs": [config.to_dict() for config in jira_configs] if jira_configs else []
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener información del perfil: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener información del perfil"}), 500

