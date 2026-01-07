"""
Repositorio para Epics
Responsabilidad única: Acceso a datos de épicas (SRP)
"""
import logging
import uuid
from typing import List, Optional
from datetime import datetime

from app.models.epic import Epic
from app.database.db import get_db_connection, get_db
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)


class EpicRepository:
    """
    Repositorio para gestionar épicas en la base de datos
    """
    
    def create(self, epic: Epic) -> Epic:
        """
        Crea una nueva épica en la base de datos
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if not epic.id:
                epic.id = str(uuid.uuid4())
            
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                INSERT INTO epics (
                    id, project_key, title, description, status, created_at, updated_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                epic.id,
                epic.project_key,
                epic.title,
                epic.description,
                epic.status,
                epic.created_at,
                epic.updated_at
            ))
            
            conn.commit()
            logger.info(f"Épica creada: ID={epic.id}, project={epic.project_key}")
            return epic
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear épica: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_by_id(self, epic_id: str) -> Optional[Epic]:
        """Obtiene una épica por ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, project_key, title, description, status, created_at, updated_at
                FROM epics
                WHERE id = {placeholder}
            ''', (epic_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_epic(row)
            return None
            
        finally:
            conn.close()
    
    def get_all(self, project_key: Optional[str] = None) -> List[Epic]:
        """Obtiene todas las épicas, opcionalmente filtradas por proyecto"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            query = '''
                SELECT id, project_key, title, description, status, created_at, updated_at
                FROM epics
            '''
            params = []
            
            if project_key:
                query += f' WHERE project_key = {placeholder}'
                params.append(project_key)
                
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            return [self._row_to_epic(row) for row in rows]
            
        finally:
            conn.close()
            
    def update(self, epic: Epic) -> Epic:
        """Actualiza una épica"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            epic.updated_at = datetime.now()
            
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                UPDATE epics
                SET title = {placeholder}, description = {placeholder}, status = {placeholder},
                    updated_at = {placeholder}
                WHERE id = {placeholder}
            ''', (
                epic.title,
                epic.description,
                epic.status,
                epic.updated_at,
                epic.id
            ))
            
            conn.commit()
            logger.info(f"Épica actualizada: ID={epic.id}")
            return epic
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar épica: {e}", exc_info=True)
            raise
        finally:
            conn.close()
            
    def delete(self, epic_id: str) -> bool:
        """Elimina una épica"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'DELETE FROM epics WHERE id = {placeholder}', (epic_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar épica: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _row_to_epic(self, row: tuple) -> Epic:
        """Convierte fila DB a objeto Epic"""
        return Epic(
            id=row[0],
            project_key=row[1],
            title=row[2],
            description=row[3],
            status=row[4],
            created_at=parse_datetime_field(row[5]),
            updated_at=parse_datetime_field(row[6])
        )
