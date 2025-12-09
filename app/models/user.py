"""
Modelo de Usuario
Responsabilidad única: Representar un usuario del sistema
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class User:
    """
    Modelo de usuario con seguridad integrada
    
    Atributos:
        id: UUID único del usuario
        email: Email único del usuario (validado)
        password_hash: Hash bcrypt de la contraseña
        role: Rol del usuario ('admin', 'usuario', 'analista_qa')
        active: Si el usuario está activo
        failed_login_attempts: Intentos de login fallidos
        locked_until: Fecha hasta cuando está bloqueado
        last_login: Última vez que inició sesión
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        created_by: ID del usuario que lo creó (auditoría)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    password_hash: str = ""
    role: str = "usuario"  # 'admin', 'usuario', 'analista_qa'
    active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    def is_locked(self) -> bool:
        """
        Verifica si la cuenta está bloqueada
        
        Returns:
            bool: True si la cuenta está bloqueada
        """
        if not self.locked_until:
            return False
        return datetime.now() < self.locked_until
    
    def increment_failed_attempts(self):
        """Incrementa los intentos de login fallidos"""
        from app.core.config import Config
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= Config.MAX_LOGIN_ATTEMPTS:
            from datetime import timedelta
            self.locked_until = datetime.now() + timedelta(seconds=Config.LOCKOUT_DURATION_SECONDS)
    
    def reset_failed_attempts(self):
        """Resetea los intentos de login fallidos"""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def update_last_login(self):
        """Actualiza la fecha de último login"""
        self.last_login = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convierte el usuario a diccionario
        
        Args:
            include_sensitive: Si incluir datos sensibles (password_hash)
            
        Returns:
            dict: Representación del usuario
        """
        data = {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            data['failed_login_attempts'] = self.failed_login_attempts
            data['locked_until'] = self.locked_until.isoformat() if self.locked_until else None
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Crea un usuario desde un diccionario
        
        Args:
            data: Diccionario con datos del usuario
            
        Returns:
            User: Instancia de usuario
        """
        # Convertir strings de datetime a datetime objects
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        locked_until = datetime.fromisoformat(data['locked_until']) if data.get('locked_until') else None
        last_login = datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            role=data.get('role', 'usuario'),
            active=bool(data.get('active', True)),
            failed_login_attempts=int(data.get('failed_login_attempts', 0)),
            locked_until=locked_until,
            last_login=last_login,
            created_at=created_at,
            updated_at=updated_at,
            created_by=data.get('created_by')
        )



