"""
Modelo de Historial de Aprobación
Responsabilidad única: Registrar logs de auditoría de cambios de estado
"""
from datetime import datetime
from typing import Dict, Any, Optional
import json
from app.models.approval_status import ApprovalStatus

class ApprovalHistory:
    """
    Log de cambios de estado en el workflow
    
    Attributes:
        id: ID único del registro histórico
        workflow_id: ID del workflow asociado
        previous_status: Estado anterior
        new_status: Nuevo estado
        actor_id: ID del usuario que realizó la acción
        action: Acción realizada (SUBMIT, APPROVE, REJECT, etc.)
        comments: Comentarios de la revisión
        detailed_snapshot: Snapshot JSON del artefacto en ese momento (opcional)
        created_at: Fecha del evento
    """
    
    def __init__(
        self,
        workflow_id: int,
        previous_status: ApprovalStatus,
        new_status: ApprovalStatus,
        actor_id: int,
        action: str,
        comments: Optional[str] = None,
        detailed_snapshot: Optional[Dict[str, Any]] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.workflow_id = workflow_id
        self.previous_status = previous_status
        self.new_status = new_status
        self.actor_id = actor_id
        self.action = action
        self.comments = comments
        self.detailed_snapshot = detailed_snapshot
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        prev_status = self.previous_status.value if isinstance(self.previous_status, ApprovalStatus) else self.previous_status
        new_status = self.new_status.value if isinstance(self.new_status, ApprovalStatus) else self.new_status
        
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'previous_status': prev_status,
            'new_status': new_status,
            'actor_id': self.actor_id,
            'action': self.action,
            'comments': self.comments,
            'detailed_snapshot': json.dumps(self.detailed_snapshot) if self.detailed_snapshot else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalHistory':
        """Crea una instancia desde un diccionario"""
        prev_str = data.get('previous_status', 'DRAFT')
        new_str = data.get('new_status', 'DRAFT')
        
        previous_status = ApprovalStatus(prev_str) if isinstance(prev_str, str) else prev_str
        new_status = ApprovalStatus(new_str) if isinstance(new_str, str) else new_str
        
        snapshot = data.get('detailed_snapshot')
        if isinstance(snapshot, str):
            try:
                snapshot = json.loads(snapshot)
            except:
                snapshot = None
        
        return cls(
            id=data.get('id'),
            workflow_id=data['workflow_id'],
            previous_status=previous_status,
            new_status=new_status,
            actor_id=data['actor_id'],
            action=data['action'],
            comments=data.get('comments'),
            detailed_snapshot=snapshot,
            created_at=data.get('created_at')
        )
    
    def __repr__(self) -> str:
        return f"<ApprovalHistory(id={self.id}, wf={self.workflow_id}, action={self.action})>"
