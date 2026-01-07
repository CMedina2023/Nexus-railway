"""
Repositorio para Workflows de Aprobación
Responsabilidad única: Gestión de persistencia de estados de aprobación (SRP)
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.models.approval_workflow import ApprovalWorkflow
from app.models.approval_status import ApprovalStatus
from app.database.db import get_db_connection, get_db
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)

class WorkflowRepository:
    """
    Repositorio para gestionar workflows de aprobación en la base de datos
    """
    
    def create(self, workflow: ApprovalWorkflow) -> ApprovalWorkflow:
        """
        Crea un nuevo workflow de aprobación
        
        Args:
            workflow: Objeto ApprovalWorkflow a persistir
            
        Returns:
            ApprovalWorkflow con ID generado
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            # Convert status to string value for storage
            status_val = workflow.current_status.value if isinstance(workflow.current_status, ApprovalStatus) else workflow.current_status
            
            cursor.execute(f'''
                INSERT INTO approval_workflows (
                    artifact_type, artifact_id, current_status, requester_id,
                    reviewer_id, created_at, updated_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                workflow.artifact_type,
                workflow.artifact_id,
                status_val,
                workflow.requester_id,
                workflow.reviewer_id,
                workflow.created_at,
                workflow.updated_at
            ))
            
            workflow.id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Workflow creado: ID={workflow.id} para {workflow.artifact_type}:{workflow.artifact_id}")
            return workflow
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear workflow: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def get_by_id(self, workflow_id: int) -> Optional[ApprovalWorkflow]:
        """Obtiene un workflow por su ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, artifact_type, artifact_id, current_status, requester_id,
                       reviewer_id, created_at, updated_at
                FROM approval_workflows
                WHERE id = {placeholder}
            ''', (workflow_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_workflow(row)
            return None
        finally:
            conn.close()

    def get_by_artifact(self, artifact_type: str, artifact_id: int) -> Optional[ApprovalWorkflow]:
        """Obtiene el workflow activo para un artefacto específico"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, artifact_type, artifact_id, current_status, requester_id,
                       reviewer_id, created_at, updated_at
                FROM approval_workflows
                WHERE artifact_type = {placeholder} AND artifact_id = {placeholder}
            ''', (artifact_type, artifact_id))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_workflow(row)
            return None
        finally:
            conn.close()
            
    def update(self, workflow: ApprovalWorkflow) -> ApprovalWorkflow:
        """Actualiza el estado y campos de un workflow"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            workflow.updated_at = datetime.now()
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            status_val = workflow.current_status.value if isinstance(workflow.current_status, ApprovalStatus) else workflow.current_status
            
            cursor.execute(f'''
                UPDATE approval_workflows
                SET current_status = {placeholder}, reviewer_id = {placeholder}, updated_at = {placeholder}
                WHERE id = {placeholder}
            ''', (
                status_val,
                workflow.reviewer_id,
                workflow.updated_at,
                workflow.id
            ))
            
            conn.commit()
            logger.info(f"Workflow actualizado: ID={workflow.id}, Estado={status_val}")
            return workflow
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar workflow: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def delete(self, workflow_id: int) -> bool:
        """Elimina un workflow por ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'DELETE FROM approval_workflows WHERE id = {placeholder}', (workflow_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar workflow: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def _row_to_workflow(self, row: tuple) -> ApprovalWorkflow:
        """Helper para convertir fila DB a objeto"""
        return ApprovalWorkflow(
            id=row[0],
            artifact_type=row[1],
            artifact_id=row[2],
            current_status=ApprovalStatus(row[3]),
            requester_id=row[4],
            reviewer_id=row[5],
            created_at=parse_datetime_field(row[6]),
            updated_at=parse_datetime_field(row[7])
        )
