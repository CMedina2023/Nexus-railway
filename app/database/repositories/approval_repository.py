"""
Repositorio para Historial de Aprobación
Responsabilidad única: Gestión de logs de auditoría de workflows (SRP)
"""
import logging
import json
from typing import List, Optional
from datetime import datetime

from app.models.approval_history import ApprovalHistory
from app.models.approval_status import ApprovalStatus
from app.database.db import get_db_connection, get_db
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)

class ApprovalRepository:
    """
    Repositorio para gestionar el historial de aprobaciones
    """
    
    def add_history(self, entry: ApprovalHistory) -> ApprovalHistory:
        """
        Agrega una entrada al historial
        
        Args:
            entry: Objeto ApprovalHistory a persistir
            
        Returns:
            ApprovalHistory con ID generado
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            prev_status = entry.previous_status.value if isinstance(entry.previous_status, ApprovalStatus) else entry.previous_status
            new_status = entry.new_status.value if isinstance(entry.new_status, ApprovalStatus) else entry.new_status
            
            # Serializar snapshot si existe
            snapshot_json = None
            if entry.detailed_snapshot:
                snapshot_json = json.dumps(entry.detailed_snapshot)
            
            cursor.execute(f'''
                INSERT INTO approval_history (
                    workflow_id, previous_status, new_status, actor_id,
                    action, comments, detailed_snapshot, created_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                entry.workflow_id,
                prev_status,
                new_status,
                entry.actor_id,
                entry.action,
                entry.comments,
                snapshot_json,
                entry.created_at
            ))
            
            entry.id = cursor.lastrowid
            conn.commit()
            
            logger.debug(f"Historial agregado: ID={entry.id} para Workflow={entry.workflow_id}")
            return entry
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al agregar historial: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def get_history_by_workflow(self, workflow_id: int) -> List[ApprovalHistory]:
        """Obtiene todo el historial de un workflow específico"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, workflow_id, previous_status, new_status, actor_id,
                       action, comments, detailed_snapshot, created_at
                FROM approval_history
                WHERE workflow_id = {placeholder}
                ORDER BY created_at DESC
            ''', (workflow_id,))
            
            rows = cursor.fetchall()
            return [self._row_to_history(row) for row in rows]
        finally:
            conn.close()

    def _row_to_history(self, row: tuple) -> ApprovalHistory:
        """Helper para convertir fila DB a objeto"""
        snapshot = None
        if row[7]:
            try:
                snapshot = json.loads(row[7])
            except:
                snapshot = None
                
        return ApprovalHistory(
            id=row[0],
            workflow_id=row[1],
            previous_status=ApprovalStatus(row[2]),
            new_status=ApprovalStatus(row[3]),
            actor_id=row[4],
            action=row[5],
            comments=row[6],
            detailed_snapshot=snapshot,
            created_at=parse_datetime_field(row[8])
        )
