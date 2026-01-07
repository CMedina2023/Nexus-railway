"""
Repositorio para Historias de Usuario
Responsabilidad única: Acceso a datos de historias generadas (SRP)
"""
import logging
import json
from typing import List, Optional
from datetime import datetime

from app.models.user_story import UserStory
from app.database.db import get_db_connection, get_db
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)


class UserStoryRepository:
    """
    Repositorio para gestionar historias de usuario en la base de datos
    
    Métodos:
        - create: Crea una nueva historia
        - get_by_id: Obtiene una historia por ID
        - get_by_user_id: Obtiene todas las historias de un usuario
        - get_all: Obtiene todas las historias
        - count_by_user: Cuenta historias de un usuario
        - count_all: Cuenta todas las historias
        - update: Actualiza una historia
        - delete: Elimina una historia
    """
    
    def create(self, story: UserStory) -> UserStory:
        """
        Crea una nueva historia en la base de datos
        
        Args:
            story: Historia a crear
            
        Returns:
            Historia creada con ID asignado
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Detectar tipo de base de datos
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                INSERT INTO user_stories (
                    user_id, project_key, area, story_title, story_content,
                    jira_issue_key, created_at, updated_at,
                    requirement_id, epic_id, feature_id, parent_story_id, dependencies
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                story.user_id,
                story.project_key,
                story.area,
                story.story_title,
                story.story_content,
                story.jira_issue_key,
                story.created_at,
                story.updated_at,
                story.requirement_id,
                story.epic_id,
                story.feature_id,
                story.parent_story_id,
                story.dependencies
            ))
            
            story.id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Historia creada: ID={story.id}, user_id={story.user_id}, project={story.project_key}")
            return story
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear historia: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_by_id(self, story_id: int) -> Optional[UserStory]:
        """Obtiene una historia por ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                SELECT id, user_id, project_key, area, story_title, story_content,
                       jira_issue_key, created_at, updated_at,
                       requirement_id, epic_id, feature_id, parent_story_id, dependencies
                FROM user_stories
                WHERE id = {placeholder}
            ''', (story_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_story(row)
            return None
            
        finally:
            conn.close()
    
    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[UserStory]:
        """
        Obtiene todas las historias de un usuario
        
        Args:
            user_id: ID del usuario
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de historias del usuario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            query = f'''
                SELECT id, user_id, project_key, area, story_title, story_content,
                       jira_issue_key, created_at, updated_at,
                       requirement_id, epic_id, feature_id, parent_story_id, dependencies
                FROM user_stories
                WHERE user_id = {placeholder}
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            return [self._row_to_story(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_all(self, limit: Optional[int] = None) -> List[UserStory]:
        """
        Obtiene todas las historias
        
        Args:
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de todas las historias
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, user_id, project_key, area, story_title, story_content,
                       jira_issue_key, created_at, updated_at,
                       requirement_id, epic_id, feature_id, parent_story_id, dependencies
                FROM user_stories
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [self._row_to_story(row) for row in rows]
            
        finally:
            conn.close()
    
    def count_by_user(self, user_id: int) -> int:
        """Cuenta las historias de un usuario (conteo real del JSON)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'SELECT story_content FROM user_stories WHERE user_id = {placeholder}', (user_id,))
            rows = cursor.fetchall()
            
            total_count = 0
            for row in rows:
                try:
                    stories = json.loads(row[0])
                    if isinstance(stories, list):
                        total_count += len(stories)
                    else:
                        total_count += 1
                except:
                    total_count += 1
            
            return total_count
        finally:
            conn.close()
    
    def count_all(self) -> int:
        """Cuenta todas las historias (conteo real del JSON)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT story_content FROM user_stories')
            rows = cursor.fetchall()
            
            total_count = 0
            for row in rows:
                try:
                    stories = json.loads(row[0])
                    if isinstance(stories, list):
                        total_count += len(stories)
                    else:
                        total_count += 1
                except:
                    total_count += 1
            
            return total_count
        finally:
            conn.close()
    
    def update(self, story: UserStory) -> UserStory:
        """Actualiza una historia"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            story.updated_at = datetime.now()
            
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            
            cursor.execute(f'''
                UPDATE user_stories
                SET story_title = {placeholder}, story_content = {placeholder}, jira_issue_key = {placeholder},
                    updated_at = {placeholder},
                    requirement_id = {placeholder}, epic_id = {placeholder}, feature_id = {placeholder},
                    parent_story_id = {placeholder}, dependencies = {placeholder}
                WHERE id = {placeholder}
            ''', (
                story.story_title,
                story.story_content,
                story.jira_issue_key,
                story.updated_at,
                story.requirement_id,
                story.epic_id,
                story.feature_id,
                story.parent_story_id,
                story.dependencies,
                story.id
            ))
            
            conn.commit()
            logger.info(f"Historia actualizada: ID={story.id}")
            return story
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar historia: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete(self, story_id: int) -> bool:
        """Elimina una historia"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            db = get_db()
            placeholder = '%s' if db.is_postgres else '?'
            cursor.execute(f'DELETE FROM user_stories WHERE id = {placeholder}', (story_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Historia eliminada: ID={story_id}")
            return deleted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar historia: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete_all(self) -> int:
        """
        Elimina todas las historias de usuario de la base de datos
        
        Returns:
            Número de historias eliminadas
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM user_stories')
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Se eliminaron {deleted_count} historias de usuario")
            return deleted_count
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar todas las historias: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _row_to_story(self, row: tuple) -> UserStory:
        """Convierte una fila de BD a objeto UserStory"""
        # Manejo de compatibilidad hacia atrás si faltan columnas en el resultado
        try:
            requirement_id = row[9] if len(row) > 9 else None
            epic_id = row[10] if len(row) > 10 else None
            feature_id = row[11] if len(row) > 11 else None
            parent_story_id = row[12] if len(row) > 12 else None
            dependencies = row[13] if len(row) > 13 else None
        except (IndexError, KeyError):
            # Si row no soporta índice numérico o está fuera de rango
            requirement_id = None
            epic_id = None
            feature_id = None
            parent_story_id = None
            dependencies = None

        return UserStory(
            id=row[0],
            user_id=row[1],
            project_key=row[2],
            area=row[3],
            story_title=row[4],
            story_content=row[5],
            jira_issue_key=row[6],
            created_at=parse_datetime_field(row[7]),
            updated_at=parse_datetime_field(row[8]),
            requirement_id=requirement_id,
            epic_id=epic_id,
            feature_id=feature_id,
            parent_story_id=parent_story_id,
            dependencies=dependencies
        )



