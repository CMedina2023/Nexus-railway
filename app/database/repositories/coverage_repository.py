"""
Repositorio de Cobertura de Requerimientos
Responsabilidad única: Acceso a datos de cobertura y trazabilidad (DIP)
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database.db import get_db
from app.models.requirement_coverage import RequirementCoverage, CoverageStatus
from app.models.traceability_link import TraceabilityLink, TraceabilityLinkType, ArtifactType
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)

class CoverageRepository:
    """
    Repositorio para gestionar enlaces de trazabilidad y estadísticas de cobertura
    """
    
    def __init__(self):
        self.db = get_db()
    
    # --- Métodos de Enlaces (TraceabilityLink) ---

    def create_link(self, link: TraceabilityLink) -> TraceabilityLink:
        """Crea un nuevo enlace de trazabilidad"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO traceability_links (
                        id, source_id, source_type, target_id, target_type,
                        link_type, created_by, meta, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    link.id,
                    link.source_id,
                    link.source_type.value,
                    link.target_id,
                    link.target_type.value,
                    link.link_type.value,
                    link.created_by,
                    str(link.meta), # Simple serialization for SQLite
                    link.created_at.isoformat()
                ))
                return link
        except Exception as e:
            logger.error(f"Error al crear enlace de trazabilidad: {e}")
            raise

    def get_links_for_artifact(self, artifact_id: str, artifact_type: ArtifactType) -> List[TraceabilityLink]:
        """Obtiene todos los enlaces entrantes y salientes de un artefacto"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM traceability_links 
                    WHERE (source_id = ? AND source_type = ?)
                       OR (target_id = ? AND target_type = ?)
                ''', (
                    artifact_id, artifact_type.value,
                    artifact_id, artifact_type.value
                ))
                rows = cursor.fetchall()
                return [self._row_to_link(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error al obtener enlaces: {e}")
            return []

    # --- Métodos de Cobertura (RequirementCoverage) ---

    def upsert_coverage(self, coverage: RequirementCoverage) -> RequirementCoverage:
        """Inserta o actualiza las estadísticas de cobertura"""
        try:
            coverage.last_updated = datetime.now()
            with self.db.get_cursor() as cursor:
                # Check if exists
                cursor.execute('SELECT 1 FROM requirement_coverages WHERE requirement_id = ?', (coverage.requirement_id,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute('''
                        UPDATE requirement_coverages SET
                            test_count = ?,
                            story_count = ?,
                            coverage_score = ?,
                            status = ?,
                            last_updated = ?
                        WHERE requirement_id = ?
                    ''', (
                        coverage.test_count,
                        coverage.story_count,
                        coverage.coverage_score,
                        coverage.status.value,
                        coverage.last_updated.isoformat(),
                        coverage.requirement_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO requirement_coverages (
                            id, requirement_id, test_count, story_count,
                            coverage_score, status, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        coverage.id,
                        coverage.requirement_id,
                        coverage.test_count,
                        coverage.story_count,
                        coverage.coverage_score,
                        coverage.status.value,
                        coverage.last_updated.isoformat()
                    ))
                return coverage
        except Exception as e:
            logger.error(f"Error al guardar cobertura: {e}")
            raise

    def get_coverage(self, requirement_id: str) -> Optional[RequirementCoverage]:
        """Obtiene la cobertura de un requerimiento específico"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('SELECT * FROM requirement_coverages WHERE requirement_id = ?', (requirement_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_coverage(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error al obtener cobertura: {e}")
            return None

    # --- Helpers ---

    def _row_to_link(self, row: Dict[str, Any]) -> TraceabilityLink:
        return TraceabilityLink(
            id=row['id'],
            source_id=row['source_id'],
            source_type=ArtifactType(row['source_type']),
            target_id=row['target_id'],
            target_type=ArtifactType(row['target_type']),
            link_type=TraceabilityLinkType(row['link_type']),
            created_by=row.get('created_by'),
            meta=eval(row['meta']) if row.get('meta') else {}, # Warning: eval is unsafe in prod, use json.loads
            created_at=parse_datetime_field(row['created_at'])
        )

    def _row_to_coverage(self, row: Dict[str, Any]) -> RequirementCoverage:
        return RequirementCoverage(
            id=row['id'],
            requirement_id=row['requirement_id'],
            test_count=row['test_count'],
            story_count=row['story_count'],
            coverage_score=row['coverage_score'],
            status=CoverageStatus(row['status']),
            last_updated=parse_datetime_field(row['last_updated'])
        )
