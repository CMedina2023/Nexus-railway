"""
Modelo de Contexto del Proyecto
Responsabilidad única: Representar el entendimiento global que la IA tiene sobre un proyecto.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any
import uuid

@dataclass
class ProjectContext:
    """
    Representa el contexto unificado y procesado de un proyecto.
    Este contexto es generado por la IA a partir de múltiples documentos.

    Attributes:
        id: UUID único del contexto
        project_key: Clave del proyecto asociado
        summary: Resumen ejecutivo global del proyecto
        glossary: Diccionario de términos y definiciones
        business_rules: Lista de reglas de negocio identificadas
        tech_constraints: Lista de restricciones técnicas
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        version: Versión del contexto (para trazabilidad de cambios)
    """
    project_key: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    summary: str = ""
    glossary: Dict[str, str] = field(default_factory=dict)
    business_rules: List[str] = field(default_factory=list)
    tech_constraints: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'project_key': self.project_key,
            'summary': self.summary,
            'glossary': self.glossary,
            'business_rules': self.business_rules,
            'tech_constraints': self.tech_constraints,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        """Crea una instancia desde un diccionario"""
        created_at = datetime.fromisoformat(data['created_at']) if isinstance(data.get('created_at'), str) else data.get('created_at', datetime.now())
        updated_at = datetime.fromisoformat(data['updated_at']) if isinstance(data.get('updated_at'), str) else data.get('updated_at', datetime.now())
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            project_key=data.get('project_key', ''),
            summary=data.get('summary', ''),
            glossary=data.get('glossary', {}),
            business_rules=data.get('business_rules', []),
            tech_constraints=data.get('tech_constraints', []),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get('version', 1)
        )
