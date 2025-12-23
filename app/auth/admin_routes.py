"""
Rutas de administración
Responsabilidad única: Endpoints para gestión de usuarios por administradores (SRP)
"""
import logging
from flask import Blueprint, request, jsonify, render_template, Response
from typing import Optional, List, Tuple

from app.auth.decorators import login_required, role_required, get_current_user_id
from app.auth.user_service import UserService
from app.database.repositories.user_repository import UserRepository
from app.utils.exceptions import ValidationError
from app.core.dependencies import get_user_service

logger = logging.getLogger(__name__)

# Crear Blueprint para administración
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@role_required('admin')
def admin_dashboard():
    """
    Panel de administración (solo para admins)
    
    ✅ Muestra lista de usuarios
    ✅ Estadísticas generales
    ✅ Interfaz para gestión de usuarios
    """
    logger.info("[DEBUG] admin_dashboard() - Iniciando renderizado del panel")
    try:
        current_user_id = get_current_user_id()
        logger.info(f"[DEBUG] admin_dashboard() - Usuario actual: {current_user_id}")
        return render_template('admin/dashboard.html')
    except Exception as e:
        logger.error(f"[DEBUG] admin_dashboard() - Error al renderizar: {e}", exc_info=True)
        raise


@admin_bp.route('/users', methods=['GET'])
@login_required
@role_required('admin')
def list_users() -> Tuple[Response, int]:
    """
    Lista todos los usuarios (solo admin)
    
    Query params:
        - search: Búsqueda por email (opcional)
        - active_only: Solo usuarios activos (opcional: 'true'/'false')
        - role: Filtrar por rol (opcional)
    
    Returns:
        JSON con lista de usuarios (sin información sensible)
        
    ✅ SRP: Endpoint delgado, delega filtrado al repositorio
    """
    logger.info("[DEBUG] list_users() - Iniciando listado de usuarios")
    try:
        current_user_id = get_current_user_id()
        logger.info(f"[DEBUG] list_users() - Usuario actual: {current_user_id}")
        
        user_repo = UserRepository()
        logger.info("[DEBUG] list_users() - UserRepository inicializado")
        
        # Obtener parámetros
        search = request.args.get('search', '').strip() or None
        role = request.args.get('role', '').strip() or None
        active_only_param = request.args.get('active_only', '').lower()
        active_only = None
        if active_only_param == 'true':
            active_only = True
        elif active_only_param == 'false':
            active_only = False
        
        logger.info(f"[DEBUG] list_users() - Parámetros: search={search}, role={role}, active_only={active_only}")
        
        # Obtener usuarios filtrados (lógica en repositorio - SRP)
        logger.info("[DEBUG] list_users() - Llamando a get_all_filtered()")
        users = user_repo.get_all_filtered(
            search=search,
            role=role,
            active_only=active_only
        )
        logger.info(f"[DEBUG] list_users() - Usuarios encontrados: {len(users)}")
        
        # Convertir a diccionario (sin información sensible)
        users_data = [user.to_dict(include_sensitive=False) for user in users]
        logger.info(f"[DEBUG] list_users() - Usuarios convertidos a dict: {len(users_data)}")
        
        # Calcular estadísticas
        total_users = len(users_data)
        active_users = len([u for u in users_data if u.get('active', True)])
        inactive_users = total_users - active_users
        
        role_counts = {}
        for user in users_data:
            role = user.get('role', 'usuario')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        logger.info(f"[DEBUG] list_users() - Estadísticas: total={total_users}, active={active_users}, inactive={inactive_users}, roles={role_counts}")
        
        response_data = {
            "success": True,
            "users": users_data,
            "statistics": {
                "total": total_users,
                "active": active_users,
                "inactive": inactive_users,
                "by_role": role_counts
            }
        }
        
        logger.info("[DEBUG] list_users() - Respuesta preparada exitosamente")
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"[DEBUG] list_users() - Error al listar usuarios: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Error al obtener usuarios: {str(e)}"
        }), 500


@admin_bp.route('/users/<user_id>/role', methods=['PUT'])
@login_required
@role_required('admin')
def update_user_role(user_id: str) -> Tuple[Response, int]:
    """
    Actualiza el rol de un usuario (solo admin)
    
    Body JSON:
        {
            "role": "admin" | "usuario" | "analista_qa"
        }
    
    ✅ Solo admin puede cambiar roles
    ✅ Valida que el rol sea válido
    ✅ No permite cambiar su propio rol (opcional, por seguridad)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Datos requeridos"}), 400
        
        new_role = data.get('role', '').strip()
        
        if not new_role:
            return jsonify({"error": "Rol requerido"}), 400
        
        user_service = get_user_service()
        current_user_id = get_current_user_id()
        
        # No permitir cambiar su propio rol (seguridad)
        if user_id == current_user_id:
            return jsonify({"error": "No puedes cambiar tu propio rol"}), 400
        
        # Actualizar rol
        user_service.update_user_role(user_id, new_role, updated_by=current_user_id)
        
        logger.info(f"Rol de usuario {user_id} actualizado a {new_role} por admin {current_user_id}")
        
        return jsonify({
            "success": True,
            "message": f"Rol actualizado a {new_role}",
            "user_id": user_id,
            "new_role": new_role
        }), 200
    
    except ValidationError as e:
        logger.warning(f"Error de validación al actualizar rol: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar rol: {e}", exc_info=True)
        return jsonify({"error": "Error al actualizar rol"}), 500


@admin_bp.route('/users/<user_id>/status', methods=['PUT'])
@login_required
@role_required('admin')
def update_user_status(user_id: str) -> Tuple[Response, int]:
    """
    Activa o desactiva un usuario (solo admin)
    
    Body JSON:
        {
            "active": true | false
        }
    
    ✅ Solo admin puede activar/desactivar usuarios
    ✅ No permite desactivarse a sí mismo
    ✅ SRP: Usa UserService para ambas operaciones (consistencia)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Datos requeridos"}), 400
        
        active = data.get('active')
        
        if active is None:
            return jsonify({"error": "Estado requerido (active: true/false)"}), 400
        
        user_service = get_user_service()
        current_user_id = get_current_user_id()
        
        # No permitir desactivarse a sí mismo
        if user_id == current_user_id and not active:
            return jsonify({"error": "No puedes desactivar tu propia cuenta"}), 400
        
        # Usar servicio para ambas operaciones (SRP: lógica unificada)
        if active:
            user_service.activate_user(user_id, activated_by=current_user_id)
            action = "activado"
        else:
            user_service.deactivate_user(user_id, deactivated_by=current_user_id)
            action = "desactivado"
        
        logger.info(f"Usuario {user_id} {action} por admin {current_user_id}")
        
        return jsonify({
            "success": True,
            "message": f"Usuario {action} exitosamente",
            "user_id": user_id,
            "active": active
        }), 200
    
    except ValidationError as e:
        logger.warning(f"Error de validación al actualizar estado: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar estado: {e}", exc_info=True)
        return jsonify({"error": "Error al actualizar estado"}), 500


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id: str) -> Tuple[Response, int]:
    """
    Elimina un usuario (solo admin)
    
    ✅ Solo admin puede eliminar usuarios
    ✅ No permite eliminarse a sí mismo
    ✅ Soft delete (desactivar) en lugar de eliminar físicamente (recomendado)
    """
    try:
        current_user_id = get_current_user_id()
        
        # No permitir eliminarse a sí mismo
        if user_id == current_user_id:
            return jsonify({"error": "No puedes eliminar tu propia cuenta"}), 400
        
        user_service = get_user_service()
        user_repo = UserRepository()
        
        # Verificar que el usuario existe
        user = user_repo.get_by_id(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Soft delete: desactivar en lugar de eliminar
        # (Más seguro para auditoría)
        user_service.deactivate_user(user_id)
        
        logger.warning(f"Usuario {user_id} desactivado (soft delete) por admin {current_user_id}")
        
        return jsonify({
            "success": True,
            "message": "Usuario desactivado exitosamente",
            "user_id": user_id
        }), 200
    
    except ValidationError as e:
        logger.warning(f"Error de validación al eliminar usuario: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}", exc_info=True)
        return jsonify({"error": "Error al eliminar usuario"}), 500


@admin_bp.route('/statistics', methods=['GET'])
@login_required
@role_required('admin')
def get_statistics() -> Tuple[Response, int]:
    """
    Obtiene estadísticas generales del sistema (solo admin)
    
    Returns:
        JSON con estadísticas de usuarios, logins, etc.
    """
    try:
        user_repo = UserRepository()
        users = user_repo.get_all(active_only=False)
        
        # Calcular estadísticas
        total_users = len(users)
        active_users = len([u for u in users if u.active])
        inactive_users = total_users - active_users
        
        role_counts = {}
        for user in users:
            role = user.role
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Usuarios con intentos fallidos
        users_with_failed_attempts = len([u for u in users if u.failed_login_attempts > 0])
        
        # Usuarios bloqueados
        locked_users = len([u for u in users if u.is_locked()])
        
        return jsonify({
            "success": True,
            "statistics": {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": inactive_users,
                    "by_role": role_counts,
                    "with_failed_attempts": users_with_failed_attempts,
                    "locked": locked_users
                }
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener estadísticas"}), 500

