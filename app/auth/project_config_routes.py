"""
Rutas de configuración de proyectos
Responsabilidad única: Endpoints para gestión de configuración de proyectos (SRP)
"""
import logging
from flask import Blueprint, request, jsonify
from typing import Optional

from app.auth.decorators import login_required, role_required, get_current_user_id
from app.services.jira_token_manager import JiraTokenManager
from app.backend.jira.connection import JiraConnection
from app.utils.exceptions import ValidationError, ConfigurationError

logger = logging.getLogger(__name__)

# Crear Blueprint para configuración de proyectos
project_config_bp = Blueprint('project_config', __name__, url_prefix='/api/projects')


@project_config_bp.route('/config', methods=['POST'])
@login_required
@role_required('admin')
def create_project_config():
    """
    Crea configuración de proyecto (token compartido)
    
    ✅ Solo Admin puede crear configuraciones
    ✅ Valida token antes de guardar
    ✅ Encripta tokens antes de almacenar
    
    Body JSON:
        {
            "project_key": "PROJ",
            "jira_base_url": "https://company.atlassian.net",
            "email": "jira@company.com",
            "token": "token-en-texto-plano"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Datos requeridos"}), 400
        
        project_key = data.get('project_key', '').strip()
        jira_base_url = data.get('jira_base_url', '').strip()
        email = data.get('email', '').strip()
        token = data.get('token', '').strip()
        
        # Validación básica
        if not all([project_key, jira_base_url, email, token]):
            return jsonify({"error": "Todos los campos son requeridos"}), 400
        
        # Validar formato de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"error": "Email inválido"}), 400
        
        # Validar URL
        if not jira_base_url.startswith('http://') and not jira_base_url.startswith('https://'):
            return jsonify({"error": "URL inválida. Debe comenzar con http:// o https://"}), 400
        
        # Validar token probando conexión con Jira
        try:
            test_connection = JiraConnection(
                base_url=jira_base_url,
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
            logger.error(f"Error al validar token: {e}")
            return jsonify({
                "error": "Error al validar token con Jira",
                "details": str(e)
            }), 400
        
        # Guardar configuración (encriptada)
        user_id = get_current_user_id()
        token_manager = JiraTokenManager()
        
        config = token_manager.save_project_config(
            project_key=project_key,
            jira_base_url=jira_base_url,
            email=email,
            token=token,
            created_by=user_id or 'system'
        )
        
        logger.info(f"Configuración de proyecto creada: {project_key} por {user_id}")
        
        return jsonify({
            "message": "Configuración de proyecto creada exitosamente",
            "project_key": config.project_key,
            "jira_base_url": config.jira_base_url,
            "validated": True
        }), 201
    
    except ValueError as e:
        logger.warning(f"Error de validación al crear configuración: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error inesperado al crear configuración: {e}", exc_info=True)
        return jsonify({"error": "Error al crear configuración de proyecto"}), 500


@project_config_bp.route('/config/<project_key>', methods=['GET'])
@login_required
@role_required('admin')
def get_project_config(project_key: str):
    """
    Obtiene configuración de proyecto (sin datos sensibles)
    
    ✅ Admin y Manager pueden ver configuración
    ✅ No retorna tokens encriptados
    """
    try:
        from app.database.repositories.project_config_repository import ProjectConfigRepository
        
        repo = ProjectConfigRepository()
        config = repo.get_by_project_key(project_key)
        
        if not config:
            return jsonify({"error": f"Proyecto {project_key} no encontrado"}), 404
        
        return jsonify({
            "project_key": config.project_key,
            "jira_base_url": config.jira_base_url,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "active": config.active
            # No retornar tokens o emails encriptados
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener configuración: {e}")
        return jsonify({"error": "Error al obtener configuración"}), 500


@project_config_bp.route('/config/<project_key>', methods=['PUT'])
@login_required
@role_required('admin')
def update_project_config(project_key: str):
    """
    Actualiza configuración de proyecto
    
    ✅ Solo Admin puede actualizar
    ✅ Valida token si se actualiza
    ✅ Encripta tokens antes de guardar
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos requeridos"}), 400
        
        user_id = get_current_user_id()
        token_manager = JiraTokenManager()
        
        # Obtener configuración actual
        from app.database.repositories.project_config_repository import ProjectConfigRepository
        repo = ProjectConfigRepository()
        current_config = repo.get_by_project_key(project_key)
        
        if not current_config:
            return jsonify({"error": f"Proyecto {project_key} no encontrado"}), 404
        
        # Valores a actualizar
        jira_base_url = data.get('jira_base_url', '').strip() or None
        email = data.get('email', '').strip() or None
        token = data.get('token', '').strip() or None
        
        # Validar token si se actualiza
        if token:
            test_url = jira_base_url or current_config.jira_base_url
            test_email = email or current_config.shared_email
            
            # Necesitamos desencriptar email actual si no se actualiza
            if not email:
                encryption_service = JiraTokenManager()._encryption_service
                test_email = encryption_service.decrypt(current_config.shared_email)
            
            try:
                test_connection = JiraConnection(
                    base_url=test_url,
                    email=test_email,
                    api_token=token
                )
                connection_test = test_connection.test_connection()
                
                if not connection_test.get('success'):
                    return jsonify({
                        "error": "Token inválido o no se pudo conectar con Jira",
                        "details": connection_test.get('error', 'Error desconocido')
                    }), 400
            except Exception as e:
                logger.error(f"Error al validar token: {e}")
                return jsonify({
                    "error": "Error al validar token con Jira",
                    "details": str(e)
                }), 400
        
        # Actualizar
        updated_config = token_manager.update_project_config(
            project_key=project_key,
            jira_base_url=jira_base_url,
            email=email,
            token=token,
            updated_by=user_id or 'system'
        )
        
        logger.info(f"Configuración de proyecto actualizada: {project_key} por {user_id}")
        
        return jsonify({
            "message": "Configuración actualizada exitosamente",
            "project_key": updated_config.project_key,
            "jira_base_url": updated_config.jira_base_url
        }), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar configuración: {e}", exc_info=True)
        return jsonify({"error": "Error al actualizar configuración"}), 500


@project_config_bp.route('/list', methods=['GET'])
@login_required
def list_projects():
    """
    Lista todos los proyectos configurados
    
    ✅ Todos los usuarios autenticados pueden ver la lista
    ✅ No retorna datos sensibles
    """
    try:
        from app.database.repositories.project_config_repository import ProjectConfigRepository
        
        repo = ProjectConfigRepository()
        configs = repo.get_all(active_only=True)
        
        projects = [{
            "project_key": config.project_key,
            "jira_base_url": config.jira_base_url,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        } for config in configs]
        
        return jsonify({
            "projects": projects,
            "count": len(projects)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al listar proyectos: {e}")
        return jsonify({"error": "Error al listar proyectos"}), 500



