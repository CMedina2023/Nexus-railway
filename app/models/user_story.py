"""
Modelo de Historia de Usuario generada
Responsabilidad única: Representar historias generadas por usuarios (SRP)
"""
from datetime import datetime
from typing import Dict, Any, Optional


class UserStory:
    """
    Representa una historia de usuario generada por un usuario
    
    Attributes:
        id: ID único de la historia
        user_id: ID del usuario que generó la historia
        project_key: Clave del proyecto en Jira
        area: Área que solicitó la generación (Finanzas, RRHH, TI, etc.)
        story_title: Título de la historia
        story_content: Contenido completo de la historia (JSON)
        jira_issue_key: Clave del issue en Jira (si se subió)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    def __init__(
        self,
        user_id: int,
        project_key: str,
        story_title: str,
        story_content: str,
        area: Optional[str] = None,
        jira_issue_key: Optional[str] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        requirement_id: Optional[str] = None,
        epic_id: Optional[str] = None,
        feature_id: Optional[str] = None,
        parent_story_id: Optional[int] = None,
        dependencies: Optional[str] = None
    ):
        self.id = id
        self.user_id = user_id
        self.project_key = project_key
        self.area = area
        self.story_title = story_title
        self.story_content = story_content  # JSON string
        self.jira_issue_key = jira_issue_key
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # Nuevos campos de jerarquía
        self.requirement_id = requirement_id
        self.epic_id = epic_id
        self.feature_id = feature_id
        self.parent_story_id = parent_story_id
        self.dependencies = dependencies  # JSON string list of IDs

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_key': self.project_key,
            'area': self.area,
            'story_title': self.story_title,
            'story_content': self.story_content,
            'jira_issue_key': self.jira_issue_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'requirement_id': self.requirement_id,
            'epic_id': self.epic_id,
            'feature_id': self.feature_id,
            'parent_story_id': self.parent_story_id,
            'dependencies': self.dependencies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserStory':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            user_id=data['user_id'],
            project_key=data['project_key'],
            area=data.get('area'),
            story_title=data['story_title'],
            story_content=data['story_content'],
            jira_issue_key=data.get('jira_issue_key'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            requirement_id=data.get('requirement_id'),
            epic_id=data.get('epic_id'),
            feature_id=data.get('feature_id'),
            parent_story_id=data.get('parent_story_id'),
            dependencies=data.get('dependencies')
        )
    
    def __repr__(self) -> str:
        return f"<UserStory(id={self.id}, user_id={self.user_id}, project={self.project_key}, title='{self.story_title[:30]}...')>"



