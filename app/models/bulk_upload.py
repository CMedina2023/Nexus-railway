"""
Modelo de Carga Masiva
Responsabilidad única: Representar cargas masivas realizadas por usuarios (SRP)
"""
from datetime import datetime
from typing import Dict, Any, Optional


class BulkUpload:
    """
    Representa una carga masiva realizada por un usuario
    
    Attributes:
        id: ID único de la carga
        user_id: ID del usuario que realizó la carga
        project_key: Clave del proyecto en Jira
        upload_type: Tipo de carga ('stories', 'test_cases', 'bugs', etc.)
        total_items: Total de items en la carga
        successful_items: Items cargados exitosamente
        failed_items: Items que fallaron
        upload_details: Detalles de la carga (JSON con errores, warnings, etc.)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    def __init__(
        self,
        user_id: int,
        project_key: str,
        upload_type: str,
        total_items: int,
        successful_items: int = 0,
        failed_items: int = 0,
        upload_details: Optional[str] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.project_key = project_key
        self.upload_type = upload_type
        self.total_items = total_items
        self.successful_items = successful_items
        self.failed_items = failed_items
        self.upload_details = upload_details  # JSON string
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_key': self.project_key,
            'upload_type': self.upload_type,
            'total_items': self.total_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'upload_details': self.upload_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BulkUpload':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            user_id=data['user_id'],
            project_key=data['project_key'],
            upload_type=data['upload_type'],
            total_items=data['total_items'],
            successful_items=data.get('successful_items', 0),
            failed_items=data.get('failed_items', 0),
            upload_details=data.get('upload_details'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __repr__(self) -> str:
        return f"<BulkUpload(id={self.id}, user_id={self.user_id}, type={self.upload_type}, total={self.total_items}, success={self.successful_items})>"














