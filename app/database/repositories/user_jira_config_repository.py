"""
Repositorio de configuración personal de Jira por usuario
Responsabilidad única: Acceso a datos de configuración personal de Jira (DIP)
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.db import get_db
from app.models.user_jira_config import UserJiraConfig
from app.database.query_adapter import parse_datetime_field

logger = logging.getLogger(__name__)


class UserJiraConfigRepository:
    """
    Repositorio para acceso a datos de configuración personal de Jira (DIP)
    Responsabilidad única: Operaciones CRUD de configuración personal de Jira
    """
    
    def __init__(self):
        """Inicializa el repositorio"""
        self.db = get_db()
    
    def create(self, config: UserJiraConfig) -> UserJiraConfig:
        """
        Crea una nueva configuración personal de Jira
        
        Args:
            config: Configuración a crear
            
        Returns:
            UserJiraConfig: Configuración creada
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_jira_configs (
                        id, user_id, project_key, personal_email, personal_token,
                        use_personal, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    config.id,
                    config.user_id,
                    config.project_key,
                    config.personal_email,  # Ya encriptado
                    config.personal_token,  # Ya encriptado
                    1 if config.use_personal else 0,
                    config.created_at.isoformat(),
                    config.updated_at.isoformat()
                ))
                
                logger.info(f"Configuración personal de Jira creada para usuario {config.user_id}")
                return config
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                raise ValueError(f"El usuario ya tiene configuración para el proyecto {config.project_key}")
            logger.error(f"Error al crear configuración personal de Jira: {e}")
            raise
    
    def get_by_user_and_project(self, user_id: str, project_key: str) -> Optional[UserJiraConfig]:
        """
        Obtiene configuración personal por usuario y proyecto
        
        Args:
            user_id: ID del usuario
            project_key: Clave del proyecto
            
        Returns:
            UserJiraConfig: Configuración encontrada o None
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM user_jira_configs WHERE user_id = ? AND project_key = ?',
                    (user_id, project_key)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_config(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error al obtener configuración personal de Jira: {e}")
            return None
    
    def get_by_user_id(self, user_id: str) -> List[UserJiraConfig]:
        """
        Obtiene todas las configuraciones personales de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            List[UserJiraConfig]: Lista de configuraciones
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM user_jira_configs WHERE user_id = ? ORDER BY created_at DESC',
                    (user_id,)
                )
                rows = cursor.fetchall()
                return [self._row_to_config(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error al obtener configuraciones personales de usuario: {e}")
            return []
    
    def update(self, config: UserJiraConfig) -> UserJiraConfig:
        """
        Actualiza una configuración personal de Jira
        
        Args:
            config: Configuración a actualizar
            
        Returns:
            UserJiraConfig: Configuración actualizada
        """
        try:
            config.updated_at = datetime.now()
            
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE user_jira_configs SET
                        personal_email = ?,
                        personal_token = ?,
                        use_personal = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (
                    config.personal_email,  # Ya encriptado
                    config.personal_token,  # Ya encriptado
                    1 if config.use_personal else 0,
                    config.updated_at.isoformat(),
                    config.id
                ))
                
                logger.debug(f"Configuración personal de Jira actualizada: {config.id}")
                return config
        except Exception as e:
            logger.error(f"Error al actualizar configuración personal de Jira: {e}")
            raise
    
    def delete(self, config_id: str) -> bool:
        """
        Elimina una configuración personal de Jira
        
        Args:
            config_id: ID de la configuración
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('DELETE FROM user_jira_configs WHERE id = ?', (config_id,))
                logger.info(f"Configuración personal de Jira eliminada: {config_id}")
                return True
        except Exception as e:
            logger.error(f"Error al eliminar configuración personal de Jira: {e}")
            return False
    
    def _row_to_config(self, row: dict) -> UserJiraConfig:
        """
        Convierte una fila de la base de datos a objeto UserJiraConfig
        
        Args:
            row: Diccionario con datos de la fila
            
        Returns:
            UserJiraConfig: Objeto UserJiraConfig
        """
        use_personal = bool(row.get('use_personal', 0))
        if isinstance(use_personal, int):
            use_personal = use_personal == 1
        
        created_at = parse_datetime_field(row.get('created_at')) or datetime.now()
        updated_at = parse_datetime_field(row.get('updated_at')) or datetime.now()
        
        return UserJiraConfig(
            id=row['id'],
            user_id=row['user_id'],
            project_key=row['project_key'],
            personal_email=row['personal_email'],  # Encriptado
            personal_token=row['personal_token'],  # Encriptado
            use_personal=use_personal,
            created_at=created_at,
            updated_at=updated_at
        )



