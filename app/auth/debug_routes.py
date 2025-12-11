"""
Rutas de debug temporales para diagnóstico de usuarios
⚠️ SOLO PARA DEBUG - ELIMINAR EN PRODUCCIÓN
Responsabilidad única: Endpoints de diagnóstico temporal
"""
import logging
from flask import Blueprint, jsonify

from app.auth.user_service import UserService
from app.auth.password_service import PasswordService
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')


@debug_bp.route('/check_user/<email>', methods=['GET'])
def check_user(email):
    """
    Verifica si un usuario existe y su estado
    
    ⚠️ SOLO PARA DEBUG - ELIMINAR EN PRODUCCIÓN
    
    Args:
        email: Email del usuario a verificar
        
    Returns:
        JSON con información del usuario o error 404
    """
    try:
        user_service = UserService()
        user = user_service.get_user_by_email(email)
        
        if user:
            return jsonify({
                "found": True,
                "email": user.email,
                "active": user.active,
                "is_locked": user.is_locked(),
                "failed_attempts": user.failed_login_attempts,
                "role": user.role,
                "hash_preview": user.password_hash[:30] + "...",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }), 200
        else:
            return jsonify({
                "found": False,
                "message": "Usuario no encontrado en la base de datos"
            }), 404
    
    except Exception as e:
        logger.error(f"Error en check_user: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@debug_bp.route('/test_password/<email>/<password>', methods=['GET'])
def test_password(email, password):
    """
    Prueba si una contraseña es correcta para un usuario
    
    ⚠️ SOLO PARA DEBUG - ELIMINAR EN PRODUCCIÓN
    
    Args:
        email: Email del usuario
        password: Contraseña a probar
        
    Returns:
        JSON indicando si la contraseña es válida
    """
    try:
        repo = UserRepository()
        user = repo.get_by_email(email.lower().strip())
        
        if not user:
            return jsonify({
                "error": "Usuario no encontrado",
                "email_searched": email.lower().strip()
            }), 404
        
        password_service = PasswordService()
        is_valid = password_service.verify_password(password, user.password_hash)
        
        return jsonify({
            "email": user.email,
            "password_tested": password,
            "password_length": len(password),
            "is_valid": is_valid,
            "message": "✅ Contraseña correcta" if is_valid else "❌ Contraseña incorrecta"
        }), 200
    
    except Exception as e:
        logger.error(f"Error en test_password: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@debug_bp.route('/recreate_user/<email>/<password>', methods=['POST'])
def recreate_user(email, password):
    """
    Elimina y recrea un usuario con nueva contraseña
    
    ⚠️ SOLO PARA DEBUG - ELIMINAR EN PRODUCCIÓN
    
    Args:
        email: Email del usuario
        password: Nueva contraseña
        
    Returns:
        JSON con información del usuario recreado
    """
    try:
        repo = UserRepository()
        
        # Eliminar usuario existente si existe
        user = repo.get_by_email(email.lower().strip())
        if user:
            repo.delete(user.id)
            logger.info(f"Usuario {email} eliminado para recreación")
        
        # Crear usuario nuevo
        user_service = UserService()
        new_user = user_service.create_user(
            email=email,
            password=password,
            role='usuario'
        )
        
        return jsonify({
            "message": "Usuario recreado exitosamente",
            "email": new_user.email,
            "role": new_user.role,
            "active": new_user.active,
            "created_at": new_user.created_at.isoformat()
        }), 201
    
    except Exception as e:
        logger.error(f"Error en recreate_user: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@debug_bp.route('/unlock_user/<email>', methods=['POST'])
def unlock_user(email):
    """
    Desbloquea un usuario y resetea intentos fallidos
    
    ⚠️ SOLO PARA DEBUG - ELIMINAR EN PRODUCCIÓN
    
    Args:
        email: Email del usuario
        
    Returns:
        JSON con información del usuario desbloqueado
    """
    try:
        repo = UserRepository()
        user = repo.get_by_email(email.lower().strip())
        
        if not user:
            return jsonify({
                "error": "Usuario no encontrado",
                "email_searched": email.lower().strip()
            }), 404
        
        user.reset_failed_attempts()
        user.active = True
        repo.update(user)
        
        logger.info(f"Usuario {email} desbloqueado")
        
        return jsonify({
            "message": "Usuario desbloqueado exitosamente",
            "email": user.email,
            "active": user.active,
            "failed_attempts": user.failed_login_attempts,
            "is_locked": user.is_locked()
        }), 200
    
    except Exception as e:
        logger.error(f"Error en unlock_user: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@debug_bp.route('/list_users', methods=['GET'])
def list_users():
    """
    Lista todos los usuarios en la base de datos
    
    ⚠️ SOLO PARA DEBUG - ELIMINAR EN PRODUCCIÓN
    
    Returns:
        JSON con lista de usuarios (sin hashes de contraseñas)
    """
    try:
        user_service = UserService()
        users = user_service.get_all_users(active_only=False)
        
        users_data = []
        for user in users:
            users_data.append({
                "email": user.email,
                "role": user.role,
                "active": user.active,
                "is_locked": user.is_locked(),
                "failed_attempts": user.failed_login_attempts,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        
        return jsonify({
            "total_users": len(users_data),
            "users": users_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error en list_users: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

