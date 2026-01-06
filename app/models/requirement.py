"""
Modelo de Requerimiento para Trazabilidad
Responsabilidad única: Representar un requerimiento de negocio o técnico (SRP)
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import uuid

class RequirementType(Enum):
    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    BUSINESS_RULE = "BUSINESS_RULE"
    TECHNICAL_CONSTRAINT = "TECHNICAL_CONSTRAINT"

class RequirementPriority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RequirementStatus(Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"

class Requirement:
    """
    Representa un requerimiento único en el sistema.
    
    Attributes:
        id: Identificador único (UUID)
        project_id: ID del proyecto al que pertenece
        code: Código legible (ej. REQ-AUTH-001)
        title: Título corto del requerimiento
        description: Descripción detallada (soporta Markdown)
        type: Tipo de requerimiento
        priority: Prioridad del requerimiento
        status: Estado actual
        source_document_id: ID del documento origen (si existe)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    def __init__(
        self,
        project_id: str,
        code: str,
        title: str,
        description: str,
        type: RequirementType,
        priority: RequirementPriority,
        status: RequirementStatus = RequirementStatus.DRAFT,
        source_document_id: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.project_id = project_id
        self.code = code
        self.title = title
        self.description = description
        self.type = type
        self.priority = priority
        self.status = status
        self.source_document_id = source_document_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario serializable"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'type': self.type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'source_document_id': self.source_document_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Requirement':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            project_id=data['project_id'],
            code=data['code'],
            title=data['title'],
            description=data['description'],
            type=RequirementType(data['type']),
            priority=RequirementPriority(data['priority']),
            status=RequirementStatus(data.get('status', 'DRAFT')),
            source_document_id=data.get('source_document_id'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )

    def __repr__(self) -> str:
        return f"<Requirement(code={self.code}, title='{self.title[:30]}...', status={self.status.value})>"
