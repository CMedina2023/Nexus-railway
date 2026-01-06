"""
Repositorio de Requerimientos
Responsabilidad única: Acceso a datos de requerimientos (DIP)
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database.db import get_db
from app.models.requirement import Requirement, RequirementType, RequirementPriority, RequirementStatus
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)

class RequirementRepository:
    """
    Repositorio para acceso a datos de requerimientos (DIP)
    """
    
    def __init__(self):
        self.db = get_db()
    
    def create(self, requirement: Requirement) -> Requirement:
        """Crea un nuevo requerimiento"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO requirements (
                        id, project_id, code, title, description,
                        type, priority, status, source_document_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    requirement.id,
                    requirement.project_id,
                    requirement.code,
                    requirement.title,
                    requirement.description,
                    requirement.type.value,
                    requirement.priority.value,
                    requirement.status.value,
                    requirement.source_document_id,
                    requirement.created_at.isoformat(),
                    requirement.updated_at.isoformat()
                ))
                logger.info(f"Requerimiento creado: {requirement.code}")
                return requirement
        except Exception as e:
            logger.error(f"Error al crear requerimiento: {e}")
            raise
    
    def get_by_id(self, req_id: str) -> Optional[Requirement]:
        """Obtiene un requerimiento por ID"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('SELECT * FROM requirements WHERE id = ?', (req_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_requirement(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error al obtener requerimiento: {e}")
            return None

    def get_by_project(self, project_id: str) -> List[Requirement]:
        """Obtiene todos los requerimientos de un proyecto"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM requirements 
                    WHERE project_id = ? 
                    ORDER BY code ASC
                ''', (project_id,))
                rows = cursor.fetchall()
                return [self._row_to_requirement(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error al obtener requerimientos del proyecto: {e}")
            return []

    def update(self, requirement: Requirement) -> Requirement:
        """Actualiza un requerimiento existente"""
        try:
            requirement.updated_at = datetime.now()
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE requirements SET
                        code = ?,
                        title = ?,
                        description = ?,
                        type = ?,
                        priority = ?,
                        status = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (
                    requirement.code,
                    requirement.title,
                    requirement.description,
                    requirement.type.value,
                    requirement.priority.value,
                    requirement.status.value,
                    requirement.updated_at.isoformat(),
                    requirement.id
                ))
                return requirement
        except Exception as e:
            logger.error(f"Error al actualizar requerimiento: {e}")
            raise

    def delete(self, req_id: str) -> bool:
        """Elimina un requerimiento"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('DELETE FROM requirements WHERE id = ?', (req_id,))
                return True
        except Exception as e:
            logger.error(f"Error al eliminar requerimiento: {e}")
            return False

    def _row_to_requirement(self, row: Dict[str, Any]) -> Requirement:
        """Convierte fila de BD a objeto Requirement"""
        return Requirement(
            id=row['id'],
            project_id=row['project_id'],
            code=row['code'],
            title=row['title'],
            description=row['description'],
            type=RequirementType(row['type']),
            priority=RequirementPriority(row['priority']),
            status=RequirementStatus(row.get('status', 'DRAFT')),
            source_document_id=row.get('source_document_id'),
            created_at=parse_datetime_field(row['created_at']),
            updated_at=parse_datetime_field(row['updated_at'])
        )
