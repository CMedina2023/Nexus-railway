"""
Repositorio para Cargas Masivas
Responsabilidad única: Acceso a datos de cargas masivas (SRP)
"""
import logging
from typing import List, Optional
from datetime import datetime

from app.models.bulk_upload import BulkUpload
from app.database.db import get_db_connection, get_db

logger = logging.getLogger(__name__)


class BulkUploadRepository:
    """
    Repositorio para gestionar cargas masivas en la base de datos
    
    Métodos:
        - create: Crea una nueva carga
        - get_by_id: Obtiene una carga por ID
        - get_by_user_id: Obtiene todas las cargas de un usuario
        - get_all: Obtiene todas las cargas
        - count_by_user: Cuenta cargas de un usuario
        - count_all: Cuenta todas las cargas
        - update: Actualiza una carga
        - delete: Elimina una carga
    """
    
    def create(self, upload: BulkUpload) -> BulkUpload:
        """
        Crea una nueva carga masiva en la base de datos
        
        Args:
            upload: Carga a crear
            
        Returns:
            Carga creada con ID asignado
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                INSERT INTO bulk_uploads (
                    user_id, project_key, upload_type, total_items,
                    successful_items, failed_items, upload_details,
                    created_at, updated_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                upload.user_id,
                upload.project_key,
                upload.upload_type,
                upload.total_items,
                upload.successful_items,
                upload.failed_items,
                upload.upload_details,
                upload.created_at,
                upload.updated_at
            ))
            
            upload.id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Carga masiva creada: ID={upload.id}, user_id={upload.user_id}, type={upload.upload_type}, total={upload.total_items}")
            return upload
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear carga masiva: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_by_id(self, upload_id: int) -> Optional[BulkUpload]:
        """Obtiene una carga masiva por ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, user_id, project_key, upload_type, total_items,
                       successful_items, failed_items, upload_details,
                       created_at, updated_at
                FROM bulk_uploads
                WHERE id = {placeholder}
            ''', (upload_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_upload(row)
            return None
            
        finally:
            conn.close()
    
    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[BulkUpload]:
        """
        Obtiene todas las cargas masivas de un usuario
        
        Args:
            user_id: ID del usuario
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de cargas del usuario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            query = f'''
                SELECT id, user_id, project_key, upload_type, total_items,
                       successful_items, failed_items, upload_details,
                       created_at, updated_at
                FROM bulk_uploads
                WHERE user_id = {placeholder}
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            return [self._row_to_upload(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_all(self, limit: Optional[int] = None) -> List[BulkUpload]:
        """
        Obtiene todas las cargas masivas
        
        Args:
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de todas las cargas
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, user_id, project_key, upload_type, total_items,
                       successful_items, failed_items, upload_details,
                       created_at, updated_at
                FROM bulk_uploads
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [self._row_to_upload(row) for row in rows]
            
        finally:
            conn.close()
    
    def count_by_user(self, user_id: int, upload_type: Optional[str] = None) -> int:
        """
        Cuenta las cargas masivas de un usuario
        
        Args:
            user_id: ID del usuario
            upload_type: Tipo de carga (opcional, para filtrar)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            if upload_type:
                cursor.execute(f'SELECT COUNT(*) FROM bulk_uploads WHERE user_id = {placeholder} AND upload_type = {placeholder}', 
                             (user_id, upload_type))
            else:
                cursor.execute(f'SELECT COUNT(*) FROM bulk_uploads WHERE user_id = {placeholder}', (user_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def count_all(self, upload_type: Optional[str] = None) -> int:
        """
        Cuenta todas las cargas masivas
        
        Args:
            upload_type: Tipo de carga (opcional, para filtrar)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            if upload_type:
                cursor.execute(f'SELECT COUNT(*) FROM bulk_uploads WHERE upload_type = {placeholder}', (upload_type,))
            else:
                cursor.execute('SELECT COUNT(*) FROM bulk_uploads')
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def update(self, upload: BulkUpload) -> BulkUpload:
        """Actualiza una carga masiva"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            upload.updated_at = datetime.now()
            
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                UPDATE bulk_uploads
                SET successful_items = {placeholder}, failed_items = {placeholder}, upload_details = {placeholder},
                    updated_at = {placeholder}
                WHERE id = {placeholder}
            ''', (
                upload.successful_items,
                upload.failed_items,
                upload.upload_details,
                upload.updated_at,
                upload.id
            ))
            
            conn.commit()
            logger.info(f"Carga masiva actualizada: ID={upload.id}")
            return upload
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar carga masiva: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete(self, upload_id: int) -> bool:
        """Elimina una carga masiva"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'DELETE FROM bulk_uploads WHERE id = {placeholder}', (upload_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Carga masiva eliminada: ID={upload_id}")
            return deleted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar carga masiva: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete_all(self) -> int:
        """
        Elimina todas las cargas masivas de la base de datos
        
        Returns:
            Número de cargas masivas eliminadas
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM bulk_uploads')
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Se eliminaron {deleted_count} cargas masivas")
            return deleted_count
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar todas las cargas masivas: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _row_to_upload(self, row: tuple) -> BulkUpload:
        """Convierte una fila de BD a objeto BulkUpload"""
        return BulkUpload(
            id=row[0],
            user_id=row[1],
            project_key=row[2],
            upload_type=row[3],
            total_items=row[4],
            successful_items=row[5],
            failed_items=row[6],
            upload_details=row[7],
            created_at=datetime.fromisoformat(row[8]) if row[8] else None,
            updated_at=datetime.fromisoformat(row[9]) if row[9] else None
        )



