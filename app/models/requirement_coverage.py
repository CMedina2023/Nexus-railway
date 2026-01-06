"""
Modelo de Cobertura de Requerimientos
Responsabilidad única: Representar el estado de cobertura de un requerimiento (SRP)
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import uuid

class CoverageStatus(Enum):
    UNCOVERED = "UNCOVERED"         # Sin historias ni tests
    PARTIAL_STORY = "PARTIAL_STORY" # Tiene historias pero no tests
    PARTIAL_TEST = "PARTIAL_TEST"   # Tiene tests pero faltan historias (raro pero posible)
    FULL_COVERAGE = "FULL_COVERAGE" # Tiene historias implementadas y tests pasando

class RequirementCoverage:
    """
    Resumen de cobertura de un requerimiento.
    Se actualiza asíncronamente cuando cambian los enlaces de trazabilidad.
    
    Attributes:
        id: Identificador único (UUID)
        requirement_id: ID del requerimiento asociado
        test_count: Cantidad de casos de prueba asociados
        story_count: Cantidad de historias de usuario asociadas
        coverage_score: Puntaje calculado de cobertura (0.0 - 1.0)
        status: Estado general de la cobertura
        last_updated: Fecha de última actualización/cálculo
    """
    
    def __init__(
        self,
        requirement_id: str,
        test_count: int = 0,
        story_count: int = 0,
        coverage_score: float = 0.0,
        status: CoverageStatus = CoverageStatus.UNCOVERED,
        id: Optional[str] = None,
        last_updated: Optional[datetime] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.requirement_id = requirement_id
        self.test_count = test_count
        self.story_count = story_count
        self.coverage_score = coverage_score
        self.status = status
        self.last_updated = last_updated or datetime.now()

    def update_stats(self, test_count: int, story_count: int) -> None:
        """Recalcula el estado basado en nuevos conteos"""
        self.test_count = test_count
        self.story_count = story_count
        self.last_updated = datetime.now()
        self._calculate_status()

    def _calculate_status(self) -> None:
        """Lógica interna para determinar el estado y score"""
        # Lógica simplificada inicial
        has_tests = self.test_count > 0
        has_stories = self.story_count > 0
        
        if has_tests and has_stories:
            self.status = CoverageStatus.FULL_COVERAGE
            self.coverage_score = 1.0
        elif has_stories:
            self.status = CoverageStatus.PARTIAL_STORY
            self.coverage_score = 0.5
        elif has_tests:
            self.status = CoverageStatus.PARTIAL_TEST
            self.coverage_score = 0.5
        else:
            self.status = CoverageStatus.UNCOVERED
            self.coverage_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario serializable"""
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'test_count': self.test_count,
            'story_count': self.story_count,
            'coverage_score': self.coverage_score,
            'status': self.status.value,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequirementCoverage':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get('id'),
            requirement_id=data['requirement_id'],
            test_count=data.get('test_count', 0),
            story_count=data.get('story_count', 0),
            coverage_score=data.get('coverage_score', 0.0),
            status=CoverageStatus(data.get('status', 'UNCOVERED')),
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None
        )

    def __repr__(self) -> str:
        return f"<RequirementCoverage(req={self.requirement_id}, status={self.status.value}, score={self.coverage_score})>"
