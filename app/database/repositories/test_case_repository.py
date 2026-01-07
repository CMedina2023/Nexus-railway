"""
Repositorio para Casos de Prueba
Responsabilidad única: Acceso a datos de casos de prueba generados (SRP)
"""
import logging
import json
from typing import List, Optional
from datetime import datetime

from app.models.test_case import TestCase
from app.database.db import get_db_connection, get_db
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)


class TestCaseRepository:
    """
    Repositorio para gestionar casos de prueba en la base de datos
    
    Métodos:
        - create: Crea un nuevo caso de prueba
        - get_by_id: Obtiene un caso por ID
        - get_by_user_id: Obtiene todos los casos de un usuario
        - get_all: Obtiene todos los casos
        - count_by_user: Cuenta casos de un usuario
        - count_all: Cuenta todos los casos
        - update: Actualiza un caso
        - delete: Elimina un caso
    """
    
    def create(self, test_case: TestCase) -> TestCase:
        """
        Crea un nuevo caso de prueba en la base de datos
        
        Args:
            test_case: Caso de prueba a crear
            
        Returns:
            Caso creado con ID asignado
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                INSERT INTO test_cases (
                    user_id, project_key, area, test_case_title, test_case_content,
                    jira_issue_key, requirement_id, requirement_version, coverage_status,
                    approval_status, approved_by, approved_at, created_at, updated_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                test_case.user_id,
                test_case.project_key,
                test_case.area,
                test_case.test_case_title,
                test_case.test_case_content,
                test_case.jira_issue_key,
                test_case.requirement_id,
                test_case.requirement_version,
                test_case.coverage_status,
                test_case.approval_status,
                test_case.approved_by,
                test_case.approved_at,
                test_case.created_at,
                test_case.updated_at
            ))
            
            test_case.id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Caso de prueba creado: ID={test_case.id}, user_id={test_case.user_id}, project={test_case.project_key}")
            return test_case
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear caso de prueba: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_by_id(self, test_case_id: int) -> Optional[TestCase]:
        """Obtiene un caso de prueba por ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, user_id, project_key, area, test_case_title, test_case_content,
                       jira_issue_key, requirement_id, requirement_version, coverage_status,
                       approval_status, approved_by, approved_at, created_at, updated_at
                FROM test_cases
                WHERE id = {placeholder}
            ''', (test_case_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_test_case(row)
            return None
            
        finally:
            conn.close()
    
    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[TestCase]:
        """
        Obtiene todos los casos de prueba de un usuario
        
        Args:
            user_id: ID del usuario
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de casos del usuario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            query = f'''
                SELECT id, user_id, project_key, area, test_case_title, test_case_content,
                       jira_issue_key, requirement_id, requirement_version, coverage_status,
                       approval_status, approved_by, approved_at, created_at, updated_at
                FROM test_cases
                WHERE user_id = {placeholder}
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            return [self._row_to_test_case(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_all(self, limit: Optional[int] = None) -> List[TestCase]:
        """
        Obtiene todos los casos de prueba
        
        Args:
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de todos los casos
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, user_id, project_key, area, test_case_title, test_case_content,
                       jira_issue_key, requirement_id, requirement_version, coverage_status,
                       approval_status, approved_by, approved_at, created_at, updated_at
                FROM test_cases
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [self._row_to_test_case(row) for row in rows]
            
        finally:
            conn.close()
    
    def count_by_user(self, user_id: int) -> int:
        """Cuenta los casos de prueba de un usuario (conteo real del JSON)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'SELECT test_case_content FROM test_cases WHERE user_id = {placeholder}', (user_id,))
            rows = cursor.fetchall()
            
            total_count = 0
            for row in rows:
                try:
                    test_cases = json.loads(row[0])
                    if isinstance(test_cases, list):
                        total_count += len(test_cases)
                    else:
                        total_count += 1
                except:
                    total_count += 1
            
            return total_count
        finally:
            conn.close()
    
    def count_all(self) -> int:
        """Cuenta todos los casos de prueba (conteo real del JSON)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT test_case_content FROM test_cases')
            rows = cursor.fetchall()
            
            total_count = 0
            for row in rows:
                try:
                    test_cases = json.loads(row[0])
                    if isinstance(test_cases, list):
                        total_count += len(test_cases)
                    else:
                        total_count += 1
                except:
                    total_count += 1
            
            return total_count
        finally:
            conn.close()
    
    def update(self, test_case: TestCase) -> TestCase:
        """Actualiza un caso de prueba"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            test_case.updated_at = datetime.now()
            
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                UPDATE test_cases
                SET test_case_title = {placeholder}, test_case_content = {placeholder}, jira_issue_key = {placeholder},
                    requirement_id = {placeholder}, requirement_version = {placeholder}, coverage_status = {placeholder},
                    approval_status = {placeholder}, approved_by = {placeholder}, approved_at = {placeholder},
                    updated_at = {placeholder}
                WHERE id = {placeholder}
            ''', (
                test_case.test_case_title,
                test_case.test_case_content,
                test_case.jira_issue_key,
                test_case.requirement_id,
                test_case.requirement_version,
                test_case.coverage_status,
                test_case.approval_status,
                test_case.approved_by,
                test_case.approved_at,
                test_case.updated_at,
                test_case.id
            ))
            
            conn.commit()
            logger.info(f"Caso de prueba actualizado: ID={test_case.id}")
            return test_case
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar caso de prueba: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete(self, test_case_id: int) -> bool:
        """Elimina un caso de prueba"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'DELETE FROM test_cases WHERE id = {placeholder}', (test_case_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Caso de prueba eliminado: ID={test_case_id}")
            return deleted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar caso de prueba: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete_all(self) -> int:
        """
        Elimina todos los casos de prueba de la base de datos
        
        Returns:
            Número de casos de prueba eliminados
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM test_cases')
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Se eliminaron {deleted_count} casos de prueba")
            return deleted_count
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar todos los casos de prueba: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _row_to_test_case(self, row: tuple) -> TestCase:
        """Convierte una fila de BD a objeto TestCase"""
        return TestCase(
            id=row[0],
            user_id=row[1],
            project_key=row[2],
            area=row[3],
            test_case_title=row[4],
            test_case_content=row[5],
            jira_issue_key=row[6],
            requirement_id=row[7],
            requirement_version=row[8],
            coverage_status=row[9],
            approval_status=row[10],
            approved_by=row[11],
            approved_at=parse_datetime_field(row[12]),
            created_at=parse_datetime_field(row[13]),
            updated_at=parse_datetime_field(row[14])
        )



