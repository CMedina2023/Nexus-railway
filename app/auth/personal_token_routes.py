"""
Rutas de tokens personales de Jira
Responsabilidad única: Endpoints para gestión de tokens personales (SRP)
"""
import logging
import re
from flask import Blueprint, request, jsonify

from app.auth.decorators import login_required, get_current_user_id
from app.services.jira_token_manager import JiraTokenManager
from app.backend.jira.connection import JiraConnection
from app.auth.encryption_service import EncryptionService
from app.database.repositories.user_jira_config_repository import UserJiraConfigRepository
from app.database.repositories.project_config_repository import ProjectConfigRepository
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Crear Blueprint para tokens personales
personal_token_bp = Blueprint('personal_token', __name__, url_prefix='/api/jira/personal-token')


@personal_token_bp.route('/<project_key>', methods=['POST', 'PUT'])
@login_required
def save_personal_token(project_key: str):
    """
    Guarda o actualiza token personal de Jira para un usuario
    
    ✅ Todos los usuarios pueden configurar su token personal
    ✅ Valida token antes de guardar
    ✅ Encripta token antes de almacenar
    
    Body JSON:
        {
            "email": "user@company.com",
            "token": "token-en-texto-plano",
            "use_personal": true
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Datos requeridos"}), 400
        
        email = data.get('email', '').strip()
        token = data.get('token', '').strip()
        use_personal = data.get('use_personal', False)
        
        # Validación básica
        if not email or not token:
            return jsonify({"error": "Email y token son requeridos"}), 400
        
        # Validar formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"error": "Email inválido"}), 400
        
        # Obtener usuario actual
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Usuario no autenticado"}), 401
        
        # Obtener URL base del proyecto
        project_repo = ProjectConfigRepository()
        project_config = project_repo.get_by_project_key(project_key)
        
        if not project_config:
            return jsonify({
                "error": f"Proyecto {project_key} no está configurado. "
                         "Un administrador debe configurar el proyecto primero."
            }), 404
        
        # Validar token probando conexión con Jira
        try:
            test_connection = JiraConnection(
                base_url=project_config.jira_base_url,
                email=email,
                api_token=token
            )
            connection_test = test_connection.test_connection()
            
            if not connection_test.get('success'):
                return jsonify({
                    "error": "Token inválido o no se pudo conectar con Jira",
                    "details": connection_test.get('error', 'Error desconocido')
                }), 400
        except Exception as e:
            logger.error(f"Error al validar token personal: {e}")
            return jsonify({
                "error": "Error al validar token con Jira",
                "details": str(e)
            }), 400
        
        # Encriptar token
        encryption_service = EncryptionService()
        encrypted_email = encryption_service.encrypt(email)
        encrypted_token = encryption_service.encrypt(token)
        
        # Verificar si ya existe configuración
        user_jira_repo = UserJiraConfigRepository()
        existing_config = user_jira_repo.get_by_user_and_project(user_id, project_key)
        
        from app.models.user_jira_config import UserJiraConfig
        from datetime import datetime
        
        if existing_config:
            # Actualizar
            existing_config.personal_email = encrypted_email
            existing_config.personal_token = encrypted_token
            existing_config.use_personal = use_personal
            existing_config.updated_at = datetime.now()
            
            updated_config = user_jira_repo.update(existing_config)
            logger.info(f"Token personal actualizado para usuario {user_id} en proyecto {project_key}")
            
            return jsonify({
                "message": "Token personal actualizado exitosamente",
                "project_key": updated_config.project_key,
                "use_personal": updated_config.use_personal
            }), 200
        else:
            # Crear nuevo
            new_config = UserJiraConfig(
                user_id=user_id,
                project_key=project_key,
                personal_email=encrypted_email,
                personal_token=encrypted_token,
                use_personal=use_personal
            )
            
            saved_config = user_jira_repo.create(new_config)
            logger.info(f"Token personal creado para usuario {user_id} en proyecto {project_key}")
            
            return jsonify({
                "message": "Token personal guardado exitosamente",
                "project_key": saved_config.project_key,
                "use_personal": saved_config.use_personal
            }), 201
    
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al guardar token personal: {e}", exc_info=True)
        return jsonify({"error": "Error al guardar token personal"}), 500


@personal_token_bp.route('/<project_key>', methods=['GET'])
@login_required
def get_personal_token(project_key: str):
    """
    Obtiene configuración personal de token (sin datos sensibles)
    
    ✅ Solo el usuario puede ver su propia configuración
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Usuario no autenticado"}), 401
        
        user_jira_repo = UserJiraConfigRepository()
        config = user_jira_repo.get_by_user_and_project(user_id, project_key)
        
        if not config:
            return jsonify({
                "exists": False,
                "message": "No hay configuración personal para este proyecto"
            }), 200
        
        return jsonify({
            "exists": True,
            "project_key": config.project_key,
            "use_personal": config.use_personal,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
            # No retornar tokens o emails encriptados
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener token personal: {e}")
        return jsonify({"error": "Error al obtener configuración personal"}), 500


@personal_token_bp.route('/<project_key>/toggle', methods=['POST'])
@login_required
def toggle_personal_token(project_key: str):
    """
    Activa/desactiva uso de token personal
    
    ✅ Permite cambiar entre token personal y compartido
    """
    try:
        data = request.get_json()
        use_personal = data.get('use_personal', False) if data else False
        
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Usuario no autenticado"}), 401
        
        user_jira_repo = UserJiraConfigRepository()
        config = user_jira_repo.get_by_user_and_project(user_id, project_key)
        
        if not config:
            return jsonify({
                "error": "No hay configuración personal para este proyecto. "
                         "Primero debes configurar un token personal."
            }), 404
        
        config.use_personal = use_personal
        from datetime import datetime
        config.updated_at = datetime.now()
        
        updated_config = user_jira_repo.update(config)
        logger.info(
            f"Toggle de token personal para usuario {user_id} en proyecto {project_key}: "
            f"use_personal={use_personal}"
        )
        
        return jsonify({
            "message": f"Token personal {'activado' if use_personal else 'desactivado'} exitosamente",
            "project_key": updated_config.project_key,
            "use_personal": updated_config.use_personal
        }), 200
    
    except Exception as e:
        logger.error(f"Error al toggle token personal: {e}")
        return jsonify({"error": "Error al cambiar configuración de token"}), 500


@personal_token_bp.route('/<project_key>', methods=['DELETE'])
@login_required
def delete_personal_token(project_key: str):
    """
    Elimina configuración personal de token
    
    ✅ Solo el usuario puede eliminar su propia configuración
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Usuario no autenticado"}), 401
        
        user_jira_repo = UserJiraConfigRepository()
        config = user_jira_repo.get_by_user_and_project(user_id, project_key)
        
        if not config:
            return jsonify({"error": "Configuración no encontrada"}), 404
        
        user_jira_repo.delete(config.id)
        logger.info(f"Token personal eliminado para usuario {user_id} en proyecto {project_key}")
        
        return jsonify({
            "message": "Configuración personal eliminada exitosamente"
        }), 200
    
    except Exception as e:
        logger.error(f"Error al eliminar token personal: {e}")
        return jsonify({"error": "Error al eliminar configuración personal"}), 500

