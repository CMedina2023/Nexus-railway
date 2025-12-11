"""
Repositorio de usuarios
Responsabilidad única: Acceso a datos de usuarios (DIP)
Implementa DIP: Abstrae acceso a base de datos
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.db import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Repositorio para acceso a datos de usuarios (DIP)
    Responsabilidad única: Operaciones CRUD de usuarios en base de datos
    """
    
    def __init__(self):
        """Inicializa el repositorio"""
        self.db = get_db()
    
    def create(self, user: User) -> User:
        """
        Crea un nuevo usuario en la base de datos
        
        Args:
            user: Usuario a crear
            
        Returns:
            User: Usuario creado con ID
        
        Raises:
            ValueError: Si el email ya existe
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO users (
                        id, email, password_hash, role, active,
                        failed_login_attempts, locked_until, last_login,
                        created_at, updated_at, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.id,
                    user.email,
                    user.password_hash,
                    user.role,
                    1 if user.active else 0,
                    user.failed_login_attempts,
                    user.locked_until.isoformat() if user.locked_until else None,
                    user.last_login.isoformat() if user.last_login else None,
                    user.created_at.isoformat(),
                    user.updated_at.isoformat(),
                    user.created_by
                ))
                
                logger.info(f"Usuario creado: {user.email}")
                return user
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                raise ValueError(f"El email {user.email} ya está registrado")
            logger.error(f"Error al crear usuario: {e}")
            raise
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            User: Usuario encontrado o None
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_user(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error al obtener usuario por ID: {e}")
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email
        
        Args:
            email: Email del usuario
            
        Returns:
            User: Usuario encontrado o None
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_user(dict(row))
                return None
        except Exception as e:
            logger.error(f"Error al obtener usuario por email: {e}")
            return None
    
    def update(self, user: User) -> User:
        """
        Actualiza un usuario en la base de datos
        
        Args:
            user: Usuario a actualizar
            
        Returns:
            User: Usuario actualizado
        """
        try:
            user.updated_at = datetime.now()
            
            with self.db.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE users SET
                        email = ?,
                        password_hash = ?,
                        role = ?,
                        active = ?,
                        failed_login_attempts = ?,
                        locked_until = ?,
                        last_login = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (
                    user.email,
                    user.password_hash,
                    user.role,
                    1 if user.active else 0,
                    user.failed_login_attempts,
                    user.locked_until.isoformat() if user.locked_until else None,
                    user.last_login.isoformat() if user.last_login else None,
                    user.updated_at.isoformat(),
                    user.id
                ))
                
                logger.debug(f"Usuario actualizado: {user.email}")
                return user
        except Exception as e:
            logger.error(f"Error al actualizar usuario: {e}")
            raise
    
    def get_all(self, active_only: bool = False) -> List[User]:
        """
        Obtiene todos los usuarios
        
        Args:
            active_only: Si solo retornar usuarios activos
            
        Returns:
            List[User]: Lista de usuarios
        """
        try:
            with self.db.get_cursor() as cursor:
                if active_only:
                    cursor.execute('SELECT * FROM users WHERE active = 1 ORDER BY created_at DESC')
                else:
                    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
                
                rows = cursor.fetchall()
                return [self._row_to_user(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error al obtener usuarios: {e}")
            return []
    
    def get_all_filtered(
        self, 
        search: Optional[str] = None,
        role: Optional[str] = None,
        active_only: Optional[bool] = None
    ) -> List[User]:
        """
        Obtiene usuarios con filtros aplicados (SRP: lógica de filtrado en repositorio)
        
        Args:
            search: Búsqueda por email (opcional)
            role: Filtrar por rol (opcional)
            active_only: Solo usuarios activos (opcional)
            
        Returns:
            List[User]: Lista de usuarios filtrados
        """
        try:
            with self.db.get_cursor() as cursor:
                query = 'SELECT * FROM users WHERE 1=1'
                params = []
                
                if active_only is not None:
                    query += ' AND active = ?'
                    params.append(1 if active_only else 0)
                
                if role:
                    query += ' AND role = ?'
                    params.append(role)
                
                if search:
                    query += ' AND email LIKE ?'
                    params.append(f'%{search}%')
                
                query += ' ORDER BY created_at DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [self._row_to_user(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error al obtener usuarios filtrados: {e}")
            return []
    
    def delete(self, user_id: str) -> bool:
        """
        Elimina un usuario de la base de datos
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                logger.info(f"Usuario eliminado: {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error al eliminar usuario: {e}")
            return False
    
    def _row_to_user(self, row: dict) -> User:
        """
        Convierte una fila de la base de datos a objeto User
        
        Args:
            row: Diccionario con datos de la fila
            
        Returns:
            User: Objeto User
        """
        # Convertir campos booleanos
        active = bool(row.get('active', 1))
        if isinstance(active, int):
            active = active == 1
        
        # Convertir datetime strings
        created_at = datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.now()
        updated_at = datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else datetime.now()
        locked_until = datetime.fromisoformat(row['locked_until']) if row.get('locked_until') else None
        last_login = datetime.fromisoformat(row['last_login']) if row.get('last_login') else None
        
        # Log para debugging del password_hash
        password_hash = row['password_hash']
        logger.info(f"Leyendo usuario de BD - Email: {row['email']}, Hash type: {type(password_hash)}, Hash length: {len(password_hash) if password_hash else 0}, Hash starts with: {password_hash[:10] if password_hash else 'None'}")
        
        return User(
            id=row['id'],
            email=row['email'],
            password_hash=password_hash,
            role=row['role'],
            active=active,
            failed_login_attempts=int(row.get('failed_login_attempts', 0)),
            locked_until=locked_until,
            last_login=last_login,
            created_at=created_at,
            updated_at=updated_at,
            created_by=row.get('created_by')
        )



