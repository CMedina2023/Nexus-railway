"""
Rutas de API para Workflow de Aprobación
Responsabilidad única: Exponer endpoints REST para gestionar el ciclo de vida de aprobación (SRP)
"""
from flask import Blueprint, request, jsonify, g, session
from typing import Optional

from app.services.workflow_service import WorkflowService
from app.models.approval_status import ApprovalStatus
from app.utils.workflow_exceptions import WorkflowError, InvalidTransitionError, WorkflowPermissionError, ArtifactNotFoundError
from app.auth.decorators import login_required, role_required

# Blueprint definition
workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')

# Service instantiation (Singleton pattern via module scope)
workflow_service = WorkflowService()

def get_current_user_id() -> int:
    """Helper para obtener ID de usuario de la sesión"""
    # Asumiendo que g.user.id o session['user_id'] está disponible
    if hasattr(g, 'user') and g.user:
        return g.user.id
    return session.get('user_id')

@workflow_bp.route('/submit', methods=['POST'])
@login_required
def submit_for_review():
    """
    Envía un artefacto a revisión (DRAFT -> PENDING_REVIEW)
    Payload: { "artifact_type": "USER_STORY", "artifact_id": 123 }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        artifact_type = data.get('artifact_type')
        artifact_id = data.get('artifact_id')
        
        if not artifact_type or not artifact_id:
            return jsonify({'error': 'Missing artifact_type or artifact_id'}), 400
            
        user_id = get_current_user_id()
        
        # Asegurar que el workflow existe o iniciarlo
        workflow = workflow_service.start_workflow(artifact_type, int(artifact_id), user_id)
        
        # Realizar transición
        updated_workflow = workflow_service.transition_state(
            workflow_id=workflow.id,
            new_status=ApprovalStatus.PENDING_REVIEW,
            actor_id=user_id,
            comments="Submitted for review"
        )
        
        return jsonify(updated_workflow.to_dict()), 200
        
    except WorkflowError as e:
        return jsonify({'error': str(e), 'type': e.__class__.__name__}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@workflow_bp.route('/approve', methods=['POST'])
@login_required
# @role_required('admin', 'qa_lead') # TODO: Uncomment when RBAC is fully active
def approve_artifact():
    """
    Aprueba un artefacto (PENDING_REVIEW -> APPROVED)
    Payload: { "workflow_id": 1, "comments": "Looks good" }
    """
    try:
        data = request.get_json()
        workflow_id = data.get('workflow_id')
        comments = data.get('comments', 'Approved')
        
        if not workflow_id:
            return jsonify({'error': 'Missing workflow_id'}), 400
            
        user_id = get_current_user_id()
        
        updated_workflow = workflow_service.transition_state(
            workflow_id=int(workflow_id),
            new_status=ApprovalStatus.APPROVED,
            actor_id=user_id,
            comments=comments
        )
        
        return jsonify(updated_workflow.to_dict()), 200
        
    except WorkflowError as e:
        return jsonify({'error': str(e), 'type': e.__class__.__name__}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@workflow_bp.route('/reject', methods=['POST'])
@login_required
# @role_required('admin', 'qa_lead')
def reject_artifact():
    """
    Rechaza un artefacto (PENDING_REVIEW -> REJECTED)
    Payload: { "workflow_id": 1, "comments": "Invalid requirements" }
    """
    try:
        data = request.get_json()
        workflow_id = data.get('workflow_id')
        comments = data.get('comments')
        
        if not workflow_id or not comments:
            return jsonify({'error': 'Missing workflow_id or comments'}), 400
            
        user_id = get_current_user_id()
        
        updated_workflow = workflow_service.transition_state(
            workflow_id=int(workflow_id),
            new_status=ApprovalStatus.REJECTED,
            actor_id=user_id,
            comments=comments
        )
        
        return jsonify(updated_workflow.to_dict()), 200
        
    except WorkflowError as e:
        return jsonify({'error': str(e), 'type': e.__class__.__name__}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@workflow_bp.route('/request-changes', methods=['POST'])
@login_required
# @role_required('admin', 'qa_lead')
def request_changes():
    """
    Solicita cambios en un artefacto (PENDING_REVIEW -> CHANGES_REQUESTED)
    Payload: { "workflow_id": 1, "comments": "Fix typo in acceptance criteria" }
    """
    try:
        data = request.get_json()
        workflow_id = data.get('workflow_id')
        comments = data.get('comments')
        
        if not workflow_id or not comments:
            return jsonify({'error': 'Missing workflow_id or comments'}), 400
            
        user_id = get_current_user_id()
        
        updated_workflow = workflow_service.transition_state(
            workflow_id=int(workflow_id),
            new_status=ApprovalStatus.CHANGES_REQUESTED,
            actor_id=user_id,
            comments=comments
        )
        
        return jsonify(updated_workflow.to_dict()), 200
        
    except WorkflowError as e:
        return jsonify({'error': str(e), 'type': e.__class__.__name__}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@workflow_bp.route('/<int:artifact_id>/history', methods=['GET'])
@login_required
def get_workflow_history(artifact_id):
    """
    Obtiene el historial de un workflow
    Query param: artifact_type (required)
    """
    try:
        artifact_type = request.args.get('artifact_type')
        if not artifact_type:
            return jsonify({'error': 'Missing artifact_type query param'}), 400
            
        workflow = workflow_service.get_workflow_for_artifact(artifact_type, artifact_id)
        if not workflow:
            return jsonify({'error': 'Workflow not found for this artifact'}), 404
            
        history = workflow_service.get_history(workflow.id)
        
        return jsonify({
            'workflow': workflow.to_dict(),
            'history': [entry.to_dict() for entry in history]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflow_bp.route('/<int:artifact_id>/status', methods=['GET'])
@login_required
def get_workflow_status(artifact_id):
    """
    Obtiene el estado actual de un artefacto
    Query param: artifact_type (required)
    """
    try:
        artifact_type = request.args.get('artifact_type')
        if not artifact_type:
            return jsonify({'error': 'Missing artifact_type query param'}), 400
            
        workflow = workflow_service.get_workflow_for_artifact(artifact_type, artifact_id)
        if not workflow:
            # Si no existe, implícitamente es DRAFT
            return jsonify({'current_status': 'DRAFT', 'exists': False}), 200
            
        return jsonify(workflow.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
