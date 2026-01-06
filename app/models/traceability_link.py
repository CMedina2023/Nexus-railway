"""
Modelo de Enlace de Trazabilidad
Responsabilidad única: Representar la relación entre dos artefactos del sistema (SRP)
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import uuid

class TraceabilityLinkType(Enum):
    VERIFIES = "VERIFIES"       # Test verifies Requirement
    IMPLEMENTS = "IMPLEMENTS"   # Story implements Requirement
    REFINES = "REFINES"         # Story refines Epic/Requirement
    DEPENDS_ON = "DEPENDS_ON"   # Link genérico de dependencia
    DUPLICATES = "DUPLICATES"   # Para marcar duplicados
    RELATED_TO = "RELATED_TO"   # Relación débil

class ArtifactType(Enum):
    REQUIREMENT = "REQUIREMENT"
    USER_STORY = "USER_STORY"
    TEST_CASE = "TEST_CASE"
    EPIC = "EPIC"
    FEATURE = "FEATURE"

class TraceabilityLink:
    """
    Representa un enlace direccional entre dos artefactos.
    
    Attributes:
        id: Identificador único (UUID)
        source_id: ID del artefacto origen
        source_type: Tipo del artefacto origen
        target_id: ID del artefacto destino
        target_type: Tipo del artefacto destino
        link_type: Tipo de relación
        created_at: Fecha de creación
        created_by: ID del usuario que creó el enlace (opcional)
        meta: Diccionario para metadatos adicionales
    """
    
    def __init__(
        self,
        source_id: str,
        source_type: ArtifactType,
        target_id: str,
        target_type: ArtifactType,
        link_type: TraceabilityLinkType,
        created_by: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.source_id = source_id
        self.source_type = source_type
        self.target_id = target_id
        self.target_type = target_type
        self.link_type = link_type
        self.created_by = created_by
        self.meta = meta or {}
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario serializable"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'source_type': self.source_type.value,
            'target_id': self.target_id,
            'target_type': self.target_type.value,
            'link_type': self.link_type.value,
            'created_by': self.created_by,
            'meta': self.meta,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceabilityLink':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            source_id=data['source_id'],
            source_type=ArtifactType(data['source_type']),
            target_id=data['target_id'],
            target_type=ArtifactType(data['target_type']),
            link_type=TraceabilityLinkType(data['link_type']),
            created_by=data.get('created_by'),
            meta=data.get('meta', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )

    def __repr__(self) -> str:
        return (f"<TraceabilityLink({self.source_type.value}:{self.source_id} "
                f"-> {self.link_type.value} -> "
                f"{self.target_type.value}:{self.target_id})>")
