"""
Rutas de API para Versionado
Responsabilidad: Exponer endpoints REST para gestionar versiones (SRP)
"""
from flask import Blueprint, request, jsonify, g
from typing import Dict, Any

from app.services.version_service import VersionService
from app.utils.logging_config import get_logger

# Configuración de logger y blueprint
logger = get_logger(__name__)
version_bp = Blueprint('version_api', __name__, url_prefix='/api/versions')
version_service = VersionService()

def _get_user_id() -> str:
    """Helper para obtener ID de usuario (simulado si no hay auth real implementada aún)"""
    # TODO: Integrar con sistema real de auth cuando esté disponible
    return str(g.user.id) if hasattr(g, 'user') else 'SYSTEM'

@version_bp.route('/<string:artifact_type>/<int:artifact_id>/history', methods=['GET'])
def get_history(artifact_type: str, artifact_id: int):
    """
    Obtiene el historial completo de versiones de un artefacto.
    GET /api/versions/{artifact_type}/{id}/history
    """
    try:
        # Validar tipo de artefacto
        artifact_type = artifact_type.upper()
        if artifact_type not in ['TEST_CASE', 'USER_STORY']:
            return jsonify({'error': 'Invalid artifact type'}), 400

        history = version_service.get_history(artifact_type, artifact_id)
        
        return jsonify({
            'artifact_type': artifact_type,
            'artifact_id': artifact_id,
            'count': len(history),
            'versions': history
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@version_bp.route('/<string:artifact_type>/<int:artifact_id>/<string:version_number>', methods=['GET'])
def get_version(artifact_type: str, artifact_id: int, version_number: str):
    """
    Obtiene los detalles de una versión específica.
    GET /api/versions/{artifact_type}/{id}/1.0
    """
    try:
        artifact_type = artifact_type.upper()
        version = version_service.repository.get_version_by_number(
            artifact_type, artifact_id, version_number
        )
        
        if not version:
            return jsonify({'error': f'Version {version_number} not found'}), 404
            
        return jsonify(version.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error fetching version: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@version_bp.route('/<string:artifact_type>/<int:artifact_id>/rollback', methods=['POST'])
def rollback_version(artifact_type: str, artifact_id: int):
    """
    Realiza un rollback a una versión anterior.
    POST /api/versions/{artifact_type}/{id}/rollback
    Body: { "target_version": "1.0" }
    """
    try:
        data = request.get_json()
        if not data or 'target_version' not in data:
            return jsonify({'error': 'Missing target_version'}), 400
            
        target_version = data['target_version']
        artifact_type = artifact_type.upper()
        user_id = _get_user_id()
        
        new_version = version_service.rollback_to_version(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            target_version_number=target_version,
            user_id=user_id
        )
        
        return jsonify({
            'message': f'Successfully rolled back to content of v{target_version}',
            'new_current_version': new_version.version_number,
            'version_details': new_version.to_dict()
        }), 201
        
    except ValueError as val_err:
        return jsonify({'error': str(val_err)}), 400
    except Exception as e:
        logger.error(f"Error executing rollback: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@version_bp.route('/<string:artifact_type>/<int:artifact_id>/diff', methods=['GET'])
def compare_versions(artifact_type: str, artifact_id: int):
    """
    Compara dos versiones y retorna las diferencias.
    GET /api/versions/{artifact_type}/{id}/diff?v1=1.0&v2=2.0
    """
    try:
        v1 = request.args.get('v1')
        v2 = request.args.get('v2')
        
        if not v1 or not v2:
            return jsonify({'error': 'Missing v1 or v2 parameters'}), 400
            
        artifact_type = artifact_type.upper()
        
        diff = version_service.get_version_diff(
            artifact_type, artifact_id, v1, v2
        )
        
        return jsonify({
            'artifact_type': artifact_type,
            'v1': v1,
            'v2': v2,
            'diff': diff
        }), 200
        
    except ValueError as val_err:
        return jsonify({'error': str(val_err)}), 404
    except Exception as e:
        logger.error(f"Error calculating diff: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
