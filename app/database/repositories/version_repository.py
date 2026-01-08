"""
Repositorio para Versionado de Artefactos
Responsabilidad única: Acceso a datos de versiones históricas y logs de cambios (SRP)
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.artifact_version import ArtifactVersion
from app.models.change_log import ChangeLog
from app.database.db import get_db_connection, get_db
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)


class VersionRepository:
    """
    Repositorio para gestionar versiones de artefactos y logs de cambios en la base de datos.
    
    Métodos:
        - create_version: Crea un nuevo snapshot de versión
        - get_version_by_id: Obtiene una versión por su ID único
        - get_version_by_number: Obtiene una versión específica de un artefacto (ej. "1.0")
        - get_artifact_history: Obtiene todas las versiones de un artefacto
        - get_latest_version: Obtiene la última versión guardada de un artefacto
        - log_change: Registra un cambio granular en el change_log
        - get_change_logs: Obtiene el historial de cambios de un artefacto
    """

    # --- Gestión de Versiones (ArtifactVersion) ---

    def create_version(self, version: ArtifactVersion) -> ArtifactVersion:
        """
        Guarda una nueva versión de un artefacto.
        
        Args:
            version: Instancia de ArtifactVersion a guardar.
            
        Returns:
            La misma instancia con el ID asignado.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                INSERT INTO artifact_versions (
                    artifact_type, artifact_id, version_number, content_snapshot,
                    change_reason, created_by, created_at, parent_version_id
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                version.artifact_type,
                version.artifact_id,
                version.version_number,
                version.content_snapshot,
                version.change_reason,
                version.created_by,
                version.created_at,
                version.parent_version_id
            ))
            
            version.id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Versión creada: {version.artifact_type} #{version.artifact_id} v{version.version_number} (ID={version.id})")
            return version
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear versión de artefacto: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def get_version_by_id(self, version_id: int) -> Optional[ArtifactVersion]:
        """Obtiene una versión por su ID de base de datos."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, artifact_type, artifact_id, version_number, content_snapshot,
                       change_reason, created_by, created_at, parent_version_id
                FROM artifact_versions
                WHERE id = {placeholder}
            ''', (version_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_artifact_version(row)
            return None
            
        finally:
            conn.close()

    def get_version_by_number(self, artifact_type: str, artifact_id: int, version_number: str) -> Optional[ArtifactVersion]:
        """Obtiene una versión específica buscando por número (ej. '1.0')."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, artifact_type, artifact_id, version_number, content_snapshot,
                       change_reason, created_by, created_at, parent_version_id
                FROM artifact_versions
                WHERE artifact_type = {placeholder} 
                  AND artifact_id = {placeholder}
                  AND version_number = {placeholder}
            ''', (artifact_type, artifact_id, version_number))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_artifact_version(row)
            return None
            
        finally:
            conn.close()

    def get_artifact_history(self, artifact_type: str, artifact_id: int) -> List[ArtifactVersion]:
        """Obtiene el historial completo de versiones de un artefacto, ordenado del más reciente al más antiguo."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, artifact_type, artifact_id, version_number, content_snapshot,
                       change_reason, created_by, created_at, parent_version_id
                FROM artifact_versions
                WHERE artifact_type = {placeholder} AND artifact_id = {placeholder}
                ORDER BY created_at DESC
            ''', (artifact_type, artifact_id))
            
            rows = cursor.fetchall()
            return [self._row_to_artifact_version(row) for row in rows]
            
        finally:
            conn.close()

    def get_latest_version(self, artifact_type: str, artifact_id: int) -> Optional[ArtifactVersion]:
        """Obtiene la última versión registrada de un artefacto."""
        # Reutilizamos get_artifact_history para obtener el primero, 
        # aunque podría ser más eficiente con LIMIT 1
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, artifact_type, artifact_id, version_number, content_snapshot,
                       change_reason, created_by, created_at, parent_version_id
                FROM artifact_versions
                WHERE artifact_type = {placeholder} AND artifact_id = {placeholder}
                ORDER BY created_at DESC
                LIMIT 1
            ''', (artifact_type, artifact_id))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_artifact_version(row)
            return None
            
        finally:
            conn.close()

    def count_versions(self, artifact_type: str, artifact_id: int) -> int:
        """Cuenta cuántas versiones tiene un artefacto."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT COUNT(*) FROM artifact_versions
                WHERE artifact_type = {placeholder} AND artifact_id = {placeholder}
            ''', (artifact_type, artifact_id))
            
            return cursor.fetchone()[0]
        finally:
            conn.close()

    # --- Gestión de Change Logs (ChangeLog) ---

    def log_change(self, change_log: ChangeLog) -> ChangeLog:
        """
        Registra un cambio puntual en el historial.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                INSERT INTO change_logs (
                    artifact_type, artifact_id, version_id,
                    changed_field, old_value, new_value,
                    changed_by, changed_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                change_log.artifact_type,
                change_log.artifact_id,
                change_log.version_id,
                change_log.changed_field,
                change_log.old_value,
                change_log.new_value,
                change_log.changed_by,
                change_log.changed_at
            ))
            
            change_log.id = cursor.lastrowid
            conn.commit()
            return change_log
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al registrar change_log: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def get_change_logs(self, artifact_type: str, artifact_id: int, limit: int = 100) -> List[ChangeLog]:
        """Obtiene los logs de cambios de un artefacto."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, artifact_type, artifact_id, version_id,
                       changed_field, old_value, new_value, changed_by, changed_at
                FROM change_logs
                WHERE artifact_type = {placeholder} AND artifact_id = {placeholder}
                ORDER BY changed_at DESC
                LIMIT {limit}
            ''', (artifact_type, artifact_id))
            
            rows = cursor.fetchall()
            return [self._row_to_change_log(row) for row in rows]
            
        finally:
            conn.close()

    # --- Métodos Auxiliares ---

    def _row_to_artifact_version(self, row: tuple) -> ArtifactVersion:
        """Mapper de fila a objeto ArtifactVersion"""
        return ArtifactVersion(
            id=row[0],
            artifact_type=row[1],
            artifact_id=row[2],
            version_number=row[3],
            content_snapshot=row[4],
            change_reason=row[5],
            created_by=row[6],
            created_at=parse_datetime_field(row[7]),
            parent_version_id=row[8]
        )

    def _row_to_change_log(self, row: tuple) -> ChangeLog:
        """Mapper de fila a objeto ChangeLog"""
        return ChangeLog(
            id=row[0],
            artifact_type=row[1],
            artifact_id=row[2],
            version_id=row[3],
            changed_field=row[4],
            old_value=row[5],
            new_value=row[6],
            changed_by=row[7],
            changed_at=parse_datetime_field(row[8])
        )
