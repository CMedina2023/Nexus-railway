"""
Repositorio para Features
Responsabilidad única: Acceso a datos de features (SRP)
"""
import logging
import uuid
from typing import List, Optional
from datetime import datetime

from app.models.feature import Feature
from app.database.db import get_db_connection, get_db
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)


class FeatureRepository:
    """
    Repositorio para gestionar features en la base de datos
    """
    
    def create(self, feature: Feature) -> Feature:
        """
        Crea una nueva feature en la base de datos
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if not feature.id:
                feature.id = str(uuid.uuid4())
            
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                INSERT INTO features (
                    id, project_key, epic_id, title, description, status, created_at, updated_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                feature.id,
                feature.project_key,
                feature.epic_id,
                feature.title,
                feature.description,
                feature.status,
                feature.created_at,
                feature.updated_at
            ))
            
            conn.commit()
            logger.info(f"Feature creada: ID={feature.id}, epic={feature.epic_id}")
            return feature
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear feature: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_by_id(self, feature_id: str) -> Optional[Feature]:
        """Obtiene una feature por ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, project_key, epic_id, title, description, status, created_at, updated_at
                FROM features
                WHERE id = {placeholder}
            ''', (feature_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_feature(row)
            return None
            
        finally:
            conn.close()
            
    def get_by_epic_id(self, epic_id: str) -> List[Feature]:
        """Obtiene todas las features de una épica"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, project_key, epic_id, title, description, status, created_at, updated_at
                FROM features
                WHERE epic_id = {placeholder}
                ORDER BY created_at DESC
            ''', (epic_id,))
            
            rows = cursor.fetchall()
            return [self._row_to_feature(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_all(self, project_key: Optional[str] = None) -> List[Feature]:
        """Obtiene todas las features, opcionalmente filtradas por proyecto"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            query = '''
                SELECT id, project_key, epic_id, title, description, status, created_at, updated_at
                FROM features
            '''
            params = []
            
            if project_key:
                query += f' WHERE project_key = {placeholder}'
                params.append(project_key)
                
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            return [self._row_to_feature(row) for row in rows]
            
        finally:
            conn.close()
            
    def update(self, feature: Feature) -> Feature:
        """Actualiza una feature"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            feature.updated_at = datetime.now()
            
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                UPDATE features
                SET epic_id = {placeholder}, title = {placeholder}, description = {placeholder}, 
                    status = {placeholder}, updated_at = {placeholder}
                WHERE id = {placeholder}
            ''', (
                feature.epic_id,
                feature.title,
                feature.description,
                feature.status,
                feature.updated_at,
                feature.id
            ))
            
            conn.commit()
            logger.info(f"Feature actualizada: ID={feature.id}")
            return feature
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar feature: {e}", exc_info=True)
            raise
        finally:
            conn.close()
            
    def delete(self, feature_id: str) -> bool:
        """Elimina una feature"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'DELETE FROM features WHERE id = {placeholder}', (feature_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar feature: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _row_to_feature(self, row: tuple) -> Feature:
        """Convierte fila DB a objeto Feature"""
        return Feature(
            id=row[0],
            project_key=row[1],
            epic_id=row[2],
            title=row[3],
            description=row[4],
            status=row[5],
            created_at=parse_datetime_field(row[6]),
            updated_at=parse_datetime_field(row[7])
        )
