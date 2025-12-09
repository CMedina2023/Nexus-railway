"""
Modelo de Configuración Personal de Jira por Usuario
Responsabilidad única: Representar configuración personal de Jira de un usuario
"""
from datetime import datetime
from dataclasses import dataclass, field
import uuid


@dataclass
class UserJiraConfig:
    """
    Configuración personal de Jira por usuario
    
    Atributos:
        id: UUID único de la configuración
        user_id: ID del usuario (FK)
        project_key: Clave del proyecto (FK)
        personal_email: Email personal (encriptado)
        personal_token: Token personal (encriptado)
        use_personal: Si usar token personal o compartido
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    project_key: str = ""
    personal_email: str = ""  # Encriptado en DB
    personal_token: str = ""  # Encriptado en DB
    use_personal: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
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
            'user_id': self.user_id,
            'project_key': self.project_key,
            'use_personal': self.use_personal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data['personal_email'] = self.personal_email
            data['personal_token'] = self.personal_token
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserJiraConfig':
        """
        Crea una configuración desde un diccionario
        
        Args:
            data: Diccionario con datos de la configuración
            
        Returns:
            UserJiraConfig: Instancia de configuración
        """
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            project_key=data.get('project_key', ''),
            personal_email=data.get('personal_email', ''),
            personal_token=data.get('personal_token', ''),
            use_personal=bool(data.get('use_personal', False)),
            created_at=created_at,
            updated_at=updated_at
        )



