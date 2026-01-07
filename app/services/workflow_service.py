"""
Servicio de Workflow de Aprobación
Responsabilidad única: Orquestar lógica de negocio, transiciones y validaciones del workflow (SRP)
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.approval_status import ApprovalStatus
from app.models.approval_workflow import ApprovalWorkflow
from app.models.approval_history import ApprovalHistory
from app.database.repositories.workflow_repository import WorkflowRepository
from app.database.repositories.approval_repository import ApprovalRepository
from app.services.notification_service import NotificationService
from app.utils.workflow_exceptions import InvalidTransitionError, WorkflowPermissionError

logger = logging.getLogger(__name__)

class WorkflowService:
    """
    Servicio para gestionar el ciclo de vida de aprobación de artefactos
    Implements State machine logic and Access Control
    """
    
    def __init__(self, 
                 workflow_repo: Optional[WorkflowRepository] = None, 
                 approval_repo: Optional[ApprovalRepository] = None,
                 notification_service: Optional[NotificationService] = None):
        # Inyección de dependencias
        self.workflow_repo = workflow_repo or WorkflowRepository()
        self.approval_repo = approval_repo or ApprovalRepository()
        self.notification_service = notification_service or NotificationService()
        
        # Matriz de transiciones permitidas: {Estado_Origen: [Estados_Destino_Validos]}
        self.allowed_transitions = {
            ApprovalStatus.DRAFT: [ApprovalStatus.PENDING_REVIEW],
            ApprovalStatus.PENDING_REVIEW: [ApprovalStatus.APPROVED, ApprovalStatus.CHANGES_REQUESTED, ApprovalStatus.REJECTED, ApprovalStatus.DRAFT],
            ApprovalStatus.CHANGES_REQUESTED: [ApprovalStatus.PENDING_REVIEW, ApprovalStatus.DRAFT],
            ApprovalStatus.APPROVED: [ApprovalStatus.SYNCED, ApprovalStatus.DRAFT], # DRAFT if reverted
            ApprovalStatus.REJECTED: [ApprovalStatus.DRAFT], # Can be restored to draft
            ApprovalStatus.SYNCED: [ApprovalStatus.DRAFT] # New version
        }

    def get_workflow_for_artifact(self, artifact_type: str, artifact_id: int) -> Optional[ApprovalWorkflow]:
        """Obtiene el workflow activo para un artefacto"""
        return self.workflow_repo.get_by_artifact(artifact_type, artifact_id)

    def start_workflow(self, artifact_type: str, artifact_id: int, requester_id: int) -> ApprovalWorkflow:
        """
        Inicializa un workflow para un nuevo artefacto en estado DRAFT
        """
        existing = self.get_workflow_for_artifact(artifact_type, artifact_id)
        if existing:
            return existing
            
        workflow = ApprovalWorkflow(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            requester_id=requester_id,
            current_status=ApprovalStatus.DRAFT
        )
        
        logger.info(f"Iniciando workflow para {artifact_type}:{artifact_id} por Usuario {requester_id}")
        return self.workflow_repo.create(workflow)

    def transition_state(self, 
                        workflow_id: int, 
                        new_status: ApprovalStatus, 
                        actor_id: int, 
                        comments: Optional[str] = None,
                        snapshot: Optional[Dict[str, Any]] = None) -> ApprovalWorkflow:
        """
        Ejecuta una transición de estado si es válida y el usuario tiene permisos
        """
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} no encontrado")
            
        # 1. Validar Transición en Máquina de Estados
        if new_status not in self.allowed_transitions.get(workflow.current_status, []):
            raise InvalidTransitionError(
                f"No se puede pasar de {workflow.current_status} a {new_status}"
            )
            
        # 2. Validar Permisos (Lógica simplificada, ideal mejorar con RBAC real)
        self._validate_permissions(workflow, new_status, actor_id)
        
        # 3. Registrar Historial (Audit Log)
        history_entry = ApprovalHistory(
            workflow_id=workflow.id,
            previous_status=workflow.current_status,
            new_status=new_status,
            actor_id=actor_id,
            action=self._get_action_name(new_status),
            comments=comments,
            detailed_snapshot=snapshot
        )
        self.approval_repo.add_history(history_entry)
        
        # 4. Actualizar Estado
        workflow.current_status = new_status
        if new_status == ApprovalStatus.APPROVED:
            # Si se aprueba, podríamos guardar quién aprobó (reviewer_id)
            # Asumimos que el actor que aprueba se convierte en el reviewer oficial si no había uno
            workflow.reviewer_id = actor_id
            
        updated_workflow = self.workflow_repo.update(workflow)
        
        # 5. Notificaciones
        try:
            # Determinamos quién debe ser notificado
            # Si se aprueba/rechaza/pide cambios -> Notificar al Requester
            # Si se envía a revisión -> Notificar a Reviewers (simulado por ahora)
            
            recipient_id = workflow.requester_id
            
            # Si la acción la hizo el mismo requester (ej. submit), no notificarlo a él mismo
            # salvo confirmación, pero aquí notificamos cambio de estado relevante.
            
            if new_status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CHANGES_REQUESTED]:
                self.notification_service.notify_status_change(
                    recipient_id=workflow.requester_id,
                    artifact_type=workflow.artifact_type,
                    artifact_id=workflow.artifact_id,
                    new_status=new_status.value,
                    actor_id=actor_id,
                    comments=comments
                )
            elif new_status == ApprovalStatus.PENDING_REVIEW:
                # TODO: Obtener lista de usuarios con rol 'reviewer' o 'admin'
                # Por ahora simulamos enviando a un admin ID 1
                fake_reviewers = [1] 
                self.notification_service.notify_review_request(
                    potential_reviewers=fake_reviewers,
                    artifact_type=workflow.artifact_type,
                    artifact_id=workflow.artifact_id,
                    requester_id=actor_id
                )
                
        except Exception as e:
            # Fallo en notificación no debe romper la transacción del workflow
            logger.error(f"Error enviando notificación: {e}")
        
        logger.info(f"Workflow {workflow.id} transicionado a {new_status} por Usuario {actor_id}")
        return updated_workflow

    def get_history(self, workflow_id: int) -> List[ApprovalHistory]:
        """Obtiene el historial completo de un workflow"""
        return self.approval_repo.get_history_by_workflow(workflow_id)

    def _validate_permissions(self, workflow: ApprovalWorkflow, target_status: ApprovalStatus, actor_id: int):
        """
        Valida si el actor puede realizar la transición.
        NOTA: Esto asume que el que llama al servicio ya conoce el rol del usuario.
        Idealmente el servicio recibiría el objeto User completo con sus roles.
        """
        # Reglas básicas:
        # - Solicitante puede Mover a PENDING_REVIEW, Cancelar (a DRAFT)
        # - Reviewer (o Admin) puede APROBAR, RECHAZAR, PEDIR CAMBIOS
        
        # Por ahora, implementamos una validación lógica simple basada en IDs, 
        # asumiendo que el controlador de API valida roles de 'admin' o 'qa_lead'.
        
        if target_status == ApprovalStatus.PENDING_REVIEW:
            # Solo el dueño o un admin/editor debería poder enviar a revisión
            # Aquí permitimos que cualquiera con acceso (controlado por API) lo haga
            pass
            
        if target_status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CHANGES_REQUESTED]:
            if actor_id == workflow.requester_id:
                # Auto-aprobación generalmente prohibida, a menos que sea config
                # TODO: Leer config para permitir auto-approve en dev
                pass 

    def _get_action_name(self, status: ApprovalStatus) -> str:
        """Helper para nombre de acción legible en log"""
        mapping = {
            ApprovalStatus.PENDING_REVIEW: "SUBMIT_FOR_REVIEW",
            ApprovalStatus.APPROVED: "APPROVE_ARTIFACT",
            ApprovalStatus.REJECTED: "REJECT_ARTIFACT",
            ApprovalStatus.CHANGES_REQUESTED: "REQUEST_CHANGES",
            ApprovalStatus.DRAFT: "RESET_TO_DRAFT",
            ApprovalStatus.SYNCED: "SYNC_TO_JIRA"
        }
        return mapping.get(status, f"MOVE_TO_{status}")
