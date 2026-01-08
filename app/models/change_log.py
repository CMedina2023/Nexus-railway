"""
Modelo de Registro de Cambios (ChangeLog)
Responsabilidad única: Rastrear cambios granulares en los artefactos para auditoría (SRP)
"""
from datetime import datetime
from typing import Dict, Any, Optional

class ChangeLog:
    """
    Representa un registro de auditoría de un cambio específico en un campo.
    Útil para mostrar 'qué cambió' sin cargar todo el snapshot.
    
    Attributes:
        id: ID único del log
        artifact_id: ID del artefacto modificado
        artifact_type: Tipo de artefacto ('TEST_CASE', 'USER_STORY')
        version_id: ID de la versión asociada a este cambio
        changed_field: Nombre del campo que cambió (ej. 'priority', 'status')
        old_value: Valor anterior del campo
        new_value: Valor nuevo del campo
        changed_by: Usuario que realizó el cambio
        changed_at: Fecha del cambio
    """

    def __init__(
        self,
        artifact_id: int,
        artifact_type: str,
        changed_field: str,
        old_value: str,
        new_value: str,
        version_id: Optional[int] = None,
        changed_by: Optional[str] = 'SYSTEM',
        changed_at: Optional[datetime] = None,
        id: Optional[int] = None
    ):
        self.id = id
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.version_id = version_id
        self.changed_field = changed_field
        self.old_value = old_value
        self.new_value = new_value
        self.changed_by = changed_by
        self.changed_at = changed_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'artifact_id': self.artifact_id,
            'artifact_type': self.artifact_type,
            'version_id': self.version_id,
            'changed_field': self.changed_field,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeLog':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            artifact_id=data['artifact_id'],
            artifact_type=data['artifact_type'],
            version_id=data.get('version_id'),
            changed_field=data['changed_field'],
            old_value=data.get('old_value', ''),
            new_value=data.get('new_value', ''),
            changed_by=data.get('changed_by'),
            changed_at=datetime.fromisoformat(data['changed_at']) if data.get('changed_at') else None
        )

    def __repr__(self) -> str:
        return f"<ChangeLog(field={self.changed_field}, art_id={self.artifact_id})>"
