"""
Repositorio para Reportes de Jira
Responsabilidad única: Acceso a datos de reportes creados en Jira (SRP)
"""
import logging
import sqlite3
from typing import List, Optional
from datetime import datetime

from app.models.jira_report import JiraReport
from app.database.db import get_db_connection

logger = logging.getLogger(__name__)


class JiraReportRepository:
    """
    Repositorio para gestionar reportes de Jira en la base de datos
    
    Métodos:
        - create: Crea un nuevo reporte
        - get_by_id: Obtiene un reporte por ID
        - get_by_user_id: Obtiene todos los reportes de un usuario
        - get_all: Obtiene todos los reportes
        - count_by_user: Cuenta reportes de un usuario
        - count_all: Cuenta todos los reportes
        - update: Actualiza un reporte
        - delete: Elimina un reporte
    """
    
    def create(self, report: JiraReport) -> JiraReport:
        """
        Crea un nuevo reporte en la base de datos
        
        Args:
            report: Reporte a crear
            
        Returns:
            Reporte creado con ID asignado
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO jira_reports (
                    user_id, project_key, report_type, report_title, report_content,
                    jira_issue_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.user_id,
                report.project_key,
                report.report_type,
                report.report_title,
                report.report_content,
                report.jira_issue_key,
                report.created_at,
                report.updated_at
            ))
            
            report.id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Reporte creado: ID={report.id}, user_id={report.user_id}, type={report.report_type}, jira_key={report.jira_issue_key}")
            return report
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error al crear reporte: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_by_id(self, report_id: int) -> Optional[JiraReport]:
        """Obtiene un reporte por ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, user_id, project_key, report_type, report_title, report_content,
                       jira_issue_key, created_at, updated_at
                FROM jira_reports
                WHERE id = ?
            ''', (report_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_report(row)
            return None
            
        finally:
            conn.close()
    
    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[JiraReport]:
        """
        Obtiene todos los reportes de un usuario
        
        Args:
            user_id: ID del usuario
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de reportes del usuario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, user_id, project_key, report_type, report_title, report_content,
                       jira_issue_key, created_at, updated_at
                FROM jira_reports
                WHERE user_id = ?
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            return [self._row_to_report(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_all(self, limit: Optional[int] = None) -> List[JiraReport]:
        """
        Obtiene todos los reportes
        
        Args:
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de todos los reportes
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, user_id, project_key, report_type, report_title, report_content,
                       jira_issue_key, created_at, updated_at
                FROM jira_reports
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [self._row_to_report(row) for row in rows]
            
        finally:
            conn.close()
    
    def count_by_user(self, user_id: int, report_type: Optional[str] = None) -> int:
        """
        Cuenta los reportes de un usuario
        
        Args:
            user_id: ID del usuario
            report_type: Tipo de reporte (opcional, para filtrar)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if report_type:
                cursor.execute('SELECT COUNT(*) FROM jira_reports WHERE user_id = ? AND report_type = ?', 
                             (user_id, report_type))
            else:
                cursor.execute('SELECT COUNT(*) FROM jira_reports WHERE user_id = ?', (user_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def count_all(self, report_type: Optional[str] = None) -> int:
        """
        Cuenta todos los reportes
        
        Args:
            report_type: Tipo de reporte (opcional, para filtrar)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if report_type:
                cursor.execute('SELECT COUNT(*) FROM jira_reports WHERE report_type = ?', (report_type,))
            else:
                cursor.execute('SELECT COUNT(*) FROM jira_reports')
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def update(self, report: JiraReport) -> JiraReport:
        """Actualiza un reporte"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            report.updated_at = datetime.now()
            
            cursor.execute('''
                UPDATE jira_reports
                SET report_title = ?, report_content = ?, updated_at = ?
                WHERE id = ?
            ''', (
                report.report_title,
                report.report_content,
                report.updated_at,
                report.id
            ))
            
            conn.commit()
            logger.info(f"Reporte actualizado: ID={report.id}")
            return report
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error al actualizar reporte: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete(self, report_id: int) -> bool:
        """Elimina un reporte"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM jira_reports WHERE id = ?', (report_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Reporte eliminado: ID={report_id}")
            return deleted
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error al eliminar reporte: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete_all(self) -> int:
        """
        Elimina todos los reportes de Jira de la base de datos
        
        Returns:
            Número de reportes eliminados
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM jira_reports')
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Se eliminaron {deleted_count} reportes de Jira")
            return deleted_count
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error al eliminar todos los reportes: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _row_to_report(self, row: tuple) -> JiraReport:
        """Convierte una fila de BD a objeto JiraReport"""
        return JiraReport(
            id=row[0],
            user_id=row[1],
            project_key=row[2],
            report_type=row[3],
            report_title=row[4],
            report_content=row[5],
            jira_issue_key=row[6],
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None
        )



