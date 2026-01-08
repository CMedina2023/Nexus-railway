"""
Modelo de Versión de Artefacto
Responsabilidad única: Representar una versión inmutable de un artefacto (TestCase, UserStory) (SRP)
"""
from datetime import datetime
from typing import Dict, Any, Optional

class ArtifactVersion:
    """
    Representa una versión histórica de un artefacto del sistema.
    Almacena una copia de seguridad (snapshot) del contenido.
    
    Attributes:
        id: ID único de la versión
        artifact_id: ID del artefacto original (TestCase.id, UserStory.id)
        artifact_type: Tipo de artefacto ('TEST_CASE', 'USER_STORY')
        version_number: Número de versión semántica (ej. "1.0", "1.1")
        change_reason: Razón del cambio o creación de esta versión
        content_snapshot: Contenido completo del artefacto en formato JSON/Texto
        created_by: Identificador del usuario o sistema que creó la versión
        created_at: Fecha de creación de la versión
        parent_version_id: ID de la versión anterior (para historial lineal)
    """

    def __init__(
        self,
        artifact_id: int,
        artifact_type: str,
        version_number: str,
        content_snapshot: str,
        change_reason: Optional[str] = None,
        created_by: Optional[str] = 'SYSTEM',
        created_at: Optional[datetime] = None,
        parent_version_id: Optional[int] = None,
        id: Optional[int] = None
    ):
        self.id = id
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.version_number = version_number
        self.content_snapshot = content_snapshot
        self.change_reason = change_reason
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
        self.parent_version_id = parent_version_id

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'artifact_id': self.artifact_id,
            'artifact_type': self.artifact_type,
            'version_number': self.version_number,
            'content_snapshot': self.content_snapshot,
            'change_reason': self.change_reason,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'parent_version_id': self.parent_version_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArtifactVersion':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            artifact_id=data['artifact_id'],
            artifact_type=data['artifact_type'],
            version_number=data['version_number'],
            content_snapshot=data['content_snapshot'],
            change_reason=data.get('change_reason'),
            created_by=data.get('created_by'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            parent_version_id=data.get('parent_version_id')
        )

    def __repr__(self) -> str:
        return f"<ArtifactVersion(v={self.version_number}, type={self.artifact_type}, art_id={self.artifact_id})>"
