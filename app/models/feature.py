"""
Modelo de Feature (Funcionalidad)
Responsabilidad única: Representar una funcionalidad mayor que agrupa historias, perteneciente a una épica (SRP)
"""
from datetime import datetime
from typing import Dict, Any, Optional

class Feature:
    """
    Representa una Feature en el sistema.
    
    Attributes:
        id: ID único de la feature (UUID)
        project_key: Clave del proyecto al que pertenece
        epic_id: ID de la épica a la que pertenece (opcional, aunque recomendado)
        title: Título de la feature
        description: Descripción detallada
        status: Estado actual (DRAFT, ACTIVE, COMPLETED, ARCHIVED)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    def __init__(
        self,
        project_key: str,
        title: str,
        description: str,
        epic_id: Optional[str] = None,
        status: str = 'DRAFT',
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.project_key = project_key
        self.epic_id = epic_id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'project_key': self.project_key,
            'epic_id': self.epic_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feature':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            project_key=data['project_key'],
            epic_id=data.get('epic_id'),
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'DRAFT'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __repr__(self) -> str:
        return f"<Feature(id={self.id}, project={self.project_key}, epic={self.epic_id}, title='{self.title}')>"
