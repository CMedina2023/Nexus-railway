"""
Modelo de Workflow de Aprobación
Responsabilidad única: Representar el estado actual del workflow de un artefacto
"""
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.approval_status import ApprovalStatus

class ApprovalWorkflow:
    """
    Representa el estado de aprobación de un artefacto
    
    Attributes:
        id: ID único del registro de workflow
        artifact_type: Tipo de artefacto ('USER_STORY', 'TEST_CASE')
        artifact_id: ID del artefacto asociado
        current_status: Estado actual (ApprovalStatus)
        requester_id: ID del usuario que solicita revisión
        reviewer_id: ID del usuario asignado para revisar (opcional)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    def __init__(
        self,
        artifact_type: str,
        artifact_id: int,
        requester_id: int,
        current_status: ApprovalStatus = ApprovalStatus.DRAFT,
        reviewer_id: Optional[int] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.artifact_type = artifact_type
        self.artifact_id = artifact_id
        self.requester_id = requester_id
        self.current_status = current_status
        self.reviewer_id = reviewer_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'artifact_type': self.artifact_type,
            'artifact_id': self.artifact_id,
            'requester_id': self.requester_id,
            'current_status': self.current_status.value if isinstance(self.current_status, ApprovalStatus) else self.current_status,
            'reviewer_id': self.reviewer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalWorkflow':
        """Crea una instancia desde un diccionario"""
        status_str = data.get('current_status', 'DRAFT')
        # Manejar caso donde status viene como string o ya como Enum
        status = ApprovalStatus(status_str) if isinstance(status_str, str) else status_str
        
        return cls(
            id=data.get('id'),
            artifact_type=data['artifact_type'],
            artifact_id=data['artifact_id'],
            requester_id=data['requester_id'],
            current_status=status,
            reviewer_id=data.get('reviewer_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __repr__(self) -> str:
        return f"<ApprovalWorkflow(id={self.id}, artifact={self.artifact_type}:{self.artifact_id}, status={self.current_status})>"
