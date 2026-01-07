"""
Modelo de Caso de Prueba generado
Responsabilidad única: Representar casos de prueba generados por usuarios (SRP)
"""
from datetime import datetime
from typing import Dict, Any, Optional


class TestCase:
    
    """
    Representa un caso de prueba generado por un usuario
    
    Attributes:
        id: ID único del caso de prueba
        user_id: ID del usuario que generó el caso
        project_key: Clave del proyecto en Jira
        area: Área que solicitó la generación (Finanzas, RRHH, TI, etc.)
        test_case_title: Título del caso de prueba
        test_case_content: Contenido completo del caso (JSON)
        jira_issue_key: Clave del issue en Jira (si se subió)
        requirement_id: ID del requerimiento asociado (trazabilidad)
        requirement_version: Versión del requerimiento asociado
        coverage_status: Estado de cobertura del requerimiento
        approval_status: Estado de aprobación (pending, approved, rejected)
        approved_by: ID del usuario que aprobó/rechazó
        approved_at: Fecha de aprobación/rechazo
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    def __init__(
        self,
        user_id: int,
        project_key: str,
        test_case_title: str,
        test_case_content: str,
        area: Optional[str] = None,
        jira_issue_key: Optional[str] = None,
        requirement_id: Optional[str] = None,
        requirement_version: Optional[str] = None,
        coverage_status: Optional[str] = None,
        approval_status: Optional[str] = 'pending',
        approved_by: Optional[int] = None,
        approved_at: Optional[datetime] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.project_key = project_key
        self.area = area
        self.test_case_title = test_case_title
        self.test_case_content = test_case_content  # JSON string
        self.jira_issue_key = jira_issue_key
        self.requirement_id = requirement_id
        self.requirement_version = requirement_version
        self.coverage_status = coverage_status
        self.approval_status = approval_status
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_key': self.project_key,
            'area': self.area,
            'test_case_title': self.test_case_title,
            'test_case_content': self.test_case_content,
            'jira_issue_key': self.jira_issue_key,
            'requirement_id': self.requirement_id,
            'requirement_version': self.requirement_version,
            'coverage_status': self.coverage_status,
            'approval_status': self.approval_status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            user_id=data['user_id'],
            project_key=data['project_key'],
            area=data.get('area'),
            test_case_title=data['test_case_title'],
            test_case_content=data['test_case_content'],
            jira_issue_key=data.get('jira_issue_key'),
            requirement_id=data.get('requirement_id'),
            requirement_version=data.get('requirement_version'),
            coverage_status=data.get('coverage_status'),
            approval_status=data.get('approval_status'),
            approved_by=data.get('approved_by'),
            approved_at=data.get('approved_at'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, user_id={self.user_id}, project={self.project_key}, title='{self.test_case_title[:30]}...')>"



