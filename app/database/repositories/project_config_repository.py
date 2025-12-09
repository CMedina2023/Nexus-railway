"""
Repositorio de configuración de proyectos
Responsabilidad única: Acceso a datos de configuración de proyectos (DIP)
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.db import get_db
from app.models.project_config import ProjectConfig

logger = logging.getLogger(__name__)


class ProjectConfigRepository:
    """
    Repositorio para acceso a datos de configuración de proyectos (DIP)
    Responsabilidad única: Operaciones CRUD de configuración de proyectos
    """
    
    def __init__(self):
        """Inicializa el repositorio"""
        self.db = get_db()
    
    def create(self, config: ProjectConfig) -> ProjectConfig:
        """
        Crea una nueva configuración de proyecto
        
        Args:
            config: Configuración a crear
            
        Returns:
            ProjectConfig: Configuración creada
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO project_configs (
                        id, project_key, jira_base_url, shared_email, shared_token,
                        created_by, created_at, updated_at, updated_by, active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    config.id,
                    config.project_key,
                    config.jira_base_url,
                    config.shared_email,  # Ya encriptado
                    config.shared_token,  # Ya encriptado
                    config.created_by,
                    config.created_at.isoformat(),
                    config.updated_at.isoformat(),
                    config.updated_by,
                    1 if config.active else 0
                ))
                
                logger.info(f"Configuración de proyecto creada: {config.project_key}")
                return config
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                raise ValueError(f"El proyecto {config.project_key} ya está configurado")
            logger.error(f"Error al crear configuración de proyecto: {e}")
            raise
    
    def get_by_project_key(self, project_key: str) -> Optional[ProjectConfig]:
        """
        Obtiene configuración por clave de proyecto
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            ProjectConfig: Configuración encontrada o None
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM project_configs WHERE project_key = ? AND active = 1',
                    (project_key,)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_config(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error al obtener configuración de proyecto: {e}")
            return None
    
    def get_by_id(self, config_id: str) -> Optional[ProjectConfig]:
        """
        Obtiene configuración por ID
        
        Args:
            config_id: ID de la configuración
            
        Returns:
            ProjectConfig: Configuración encontrada o None
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('SELECT * FROM project_configs WHERE id = ?', (config_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_config(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error al obtener configuración por ID: {e}")
            return None
    
    def update(self, config: ProjectConfig) -> ProjectConfig:
        """
        Actualiza una configuración de proyecto
        
        Args:
            config: Configuración a actualizar
            
        Returns:
            ProjectConfig: Configuración actualizada
        """
        try:
            config.updated_at = datetime.now()
            
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE project_configs SET
                        jira_base_url = ?,
                        shared_email = ?,
                        shared_token = ?,
                        updated_at = ?,
                        updated_by = ?,
                        active = ?
                    WHERE id = ?
                ''', (
                    config.jira_base_url,
                    config.shared_email,  # Ya encriptado
                    config.shared_token,  # Ya encriptado
                    config.updated_at.isoformat(),
                    config.updated_by,
                    1 if config.active else 0,
                    config.id
                ))
                
                logger.debug(f"Configuración de proyecto actualizada: {config.project_key}")
                return config
        except Exception as e:
            logger.error(f"Error al actualizar configuración de proyecto: {e}")
            raise
    
    def get_all(self, active_only: bool = True) -> List[ProjectConfig]:
        """
        Obtiene todas las configuraciones de proyectos
        
        Args:
            active_only: Si solo retornar configuraciones activas
            
        Returns:
            List[ProjectConfig]: Lista de configuraciones
        """
        try:
            with self.db.get_cursor() as cursor:
                if active_only:
                    cursor.execute('SELECT * FROM project_configs WHERE active = 1 ORDER BY created_at DESC')
                else:
                    cursor.execute('SELECT * FROM project_configs ORDER BY created_at DESC')
                
                rows = cursor.fetchall()
                return [self._row_to_config(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error al obtener configuraciones de proyectos: {e}")
            return []
    
    def get_base_url(self, project_key: str) -> Optional[str]:
        """
        Obtiene solo la URL base de un proyecto (método helper)
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            str: URL base o None
        """
        config = self.get_by_project_key(project_key)
        return config.jira_base_url if config else None
    
    def _row_to_config(self, row: dict) -> ProjectConfig:
        """
        Convierte una fila de la base de datos a objeto ProjectConfig
        
        Args:
            row: Diccionario con datos de la fila
            
        Returns:
            ProjectConfig: Objeto ProjectConfig
        """
        active = bool(row.get('active', 1))
        if isinstance(active, int):
            active = active == 1
        
        created_at = datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.now()
        updated_at = datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else datetime.now()
        
        return ProjectConfig(
            id=row['id'],
            project_key=row['project_key'],
            jira_base_url=row['jira_base_url'],
            shared_email=row['shared_email'],  # Encriptado
            shared_token=row['shared_token'],  # Encriptado
            created_by=row['created_by'],
            created_at=created_at,
            updated_at=updated_at,
            updated_by=row.get('updated_by'),
            active=active
        )



