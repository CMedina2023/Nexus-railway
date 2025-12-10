"""
Modelo de Reporte en Jira
Responsabilidad única: Representar reportes creados por usuarios en Jira (SRP)
"""
from datetime import datetime
from typing import Dict, Any, Optional


class JiraReport:
    """
    Representa un reporte creado por un usuario en Jira
    
    Attributes:
        id: ID único del reporte
        user_id: ID del usuario que creó el reporte
        project_key: Clave del proyecto en Jira
        report_type: Tipo de reporte ('bug', 'test_case', 'story', etc.)
        report_title: Título del reporte
        report_content: Contenido completo del reporte (JSON)
        jira_issue_key: Clave del issue en Jira
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    def __init__(
        self,
        user_id: int,
        project_key: str,
        report_type: str,
        report_title: str,
        report_content: str,
        jira_issue_key: str,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.project_key = project_key
        self.report_type = report_type
        self.report_title = report_title
        self.report_content = report_content  # JSON string
        self.jira_issue_key = jira_issue_key
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_key': self.project_key,
            'report_type': self.report_type,
            'report_title': self.report_title,
            'report_content': self.report_content,
            'jira_issue_key': self.jira_issue_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JiraReport':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            user_id=data['user_id'],
            project_key=data['project_key'],
            report_type=data['report_type'],
            report_title=data['report_title'],
            report_content=data['report_content'],
            jira_issue_key=data['jira_issue_key'],
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __repr__(self) -> str:
        return f"<JiraReport(id={self.id}, user_id={self.user_id}, type={self.report_type}, jira_key={self.jira_issue_key})>"









