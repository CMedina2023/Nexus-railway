"""
Modelo de Configuración de Proyecto Jira
Responsabilidad única: Representar configuración de un proyecto Jira
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class ProjectConfig:
    """
    Configuración de proyecto Jira con encriptación
    
    Atributos:
        id: UUID único de la configuración
        project_key: Clave del proyecto (único)
        jira_base_url: URL base de Jira
        shared_email: Email compartido (encriptado)
        shared_token: Token compartido (encriptado)
        created_by: ID del usuario que lo creó
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        updated_by: ID del usuario que lo actualizó
        active: Si la configuración está activa
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_key: str = ""
    jira_base_url: str = ""
    shared_email: str = ""  # Encriptado en DB
    shared_token: str = ""  # Encriptado en DB
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[str] = None
    active: bool = True
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convierte la configuración a diccionario
        
        Args:
            include_sensitive: Si incluir datos sensibles (tokens)
            
        Returns:
            dict: Representación de la configuración
        """
        data = {
            'id': self.id,
            'project_key': self.project_key,
            'jira_base_url': self.jira_base_url,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by,
            'active': self.active
        }
        
        if include_sensitive:
            data['shared_email'] = self.shared_email
            data['shared_token'] = self.shared_token
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectConfig':
        """
        Crea una configuración desde un diccionario
        
        Args:
            data: Diccionario con datos de la configuración
            
        Returns:
            ProjectConfig: Instancia de configuración
        """
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            project_key=data.get('project_key', ''),
            jira_base_url=data.get('jira_base_url', ''),
            shared_email=data.get('shared_email', ''),
            shared_token=data.get('shared_token', ''),
            created_by=data.get('created_by', ''),
            created_at=created_at,
            updated_at=updated_at,
            updated_by=data.get('updated_by'),
            active=bool(data.get('active', True))
        )



