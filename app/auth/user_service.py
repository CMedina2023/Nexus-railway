"""
Servicio de gestión de usuarios
Responsabilidad única: Lógica de negocio para gestión de usuarios
"""
import re
import logging
from typing import Optional, List, Tuple
from datetime import datetime

from app.models.user import User
from app.auth.password_service import PasswordService
from app.database.repositories.user_repository import UserRepository
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class UserService:
    """
    Servicio de gestión de usuarios (SRP)
    Responsabilidad única: Lógica de negocio para usuarios (crear, validar, autenticar)
    """
    # Roles soportados en el sistema
    VALID_ROLES = ['admin', 'usuario', 'analista_qa']
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService
    ):
        """
        Inicializa el servicio de usuarios
        
        Args:
            user_repository: Repositorio de usuarios (DIP - inyección de dependencias)
            password_service: Servicio de contraseñas (DIP - inyección de dependencias)
        """
        self._user_repository = user_repository
        self._password_service = password_service
    
    def validate_email(self, email: str) -> bool:
        """
        Valida formato de email de forma segura
        
        ✅ Valida formato con regex
        ✅ Previene inyecciones
        
        Args:
            email: Email a validar
            
        Returns:
            bool: True si el email es válido
        """
        if not email or not isinstance(email, str):
            return False
        
        # Validar formato de email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def create_user(
        self,
        email: str,
        password: str,
        role: str = 'usuario',
        created_by: Optional[str] = None
    ) -> User:
        """
        Crea un nuevo usuario con validaciones
        
        ✅ Valida email
        ✅ Valida fortaleza de contraseña
        ✅ Hash seguro de contraseña
        ✅ Validación de rol
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            role: Rol del usuario ('admin', 'usuario', 'analista_qa')
            created_by: ID del usuario que lo crea (para auditoría)
            
        Returns:
            User: Usuario creado
            
        Raises:
            ValidationError: Si hay errores de validación
        """
        # Validar email
        if not self.validate_email(email):
            raise ValidationError("Email inválido")
        
        # Validar fortaleza de contraseña
        is_valid, errors = self._password_service.validate_password_strength(password)
        if not is_valid:
            raise ValidationError(f"Contraseña inválida: {'; '.join(errors)}")
        
        # Validar rol
        if role not in self.VALID_ROLES:
            raise ValidationError(f"Rol inválido. Roles válidos: {', '.join(self.VALID_ROLES)}")
        
        # Verificar que el email no exista
        existing_user = self._user_repository.get_by_email(email)
        if existing_user:
            # No revelar si el usuario existe (seguridad)
            raise ValidationError("No se puede crear el usuario")
        
        # Crear hash de contraseña
        password_hash = self._password_service.hash_password(password)
        
        # Crear usuario
        user = User(
            email=email.lower().strip(),  # Normalizar email
            password_hash=password_hash,
            role=role,
            created_by=created_by
        )
        
        # Guardar en base de datos
        try:
            created_user = self._user_repository.create(user)
            logger.info(f"Usuario creado: {created_user.email} (rol: {role})")
            return created_user
        except ValueError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error al crear usuario: {e}")
            raise ValidationError("Error al crear usuario")
    
    def authenticate_user(self, email: str, password: str) -> Tuple[Optional[User], str]:
        """
        Autentica un usuario
        
        ✅ Validación de email
        ✅ Verificación de contraseña
        ✅ Manejo de bloqueo de cuenta
        ✅ Reset de intentos fallidos si login exitoso
        ✅ Mensajes genéricos (no revelar si usuario existe)
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Tuple[Optional[User], str]: (Usuario si autenticado, mensaje)
        """
        # Validar email
        if not self.validate_email(email):
            return None, "Credenciales inválidas"  # Mensaje genérico
        
        # Normalizar email
        email = email.lower().strip()
        
        # Obtener usuario
        user = self._user_repository.get_by_email(email)
        
        # Mensaje genérico si no existe (no revelar si el usuario existe)
        if not user:
            logger.warning(f"Intento de login con email no existente: {email}")
            return None, "Credenciales inválidas"
        
        # Verificar si la cuenta está activa
        if not user.active:
            logger.warning(f"Intento de login con cuenta inactiva: {email}")
            return None, "Cuenta desactivada"
        
        # Verificar si la cuenta está bloqueada
        if user.is_locked():
            logger.warning(f"Intento de login con cuenta bloqueada: {email}")
            return None, f"Cuenta bloqueada. Intenta nuevamente más tarde."
        
        # Verificar contraseña
        if not self._password_service.verify_password(password, user.password_hash):
            # Incrementar intentos fallidos
            user.increment_failed_attempts()
            self._user_repository.update(user)
            
            logger.warning(
                f"Login fallido para {email}. "
                f"Intentos fallidos: {user.failed_login_attempts}"
            )
            
            if user.is_locked():
                return None, "Cuenta bloqueada debido a múltiples intentos fallidos"
            
            return None, "Credenciales inválidas"
        
        # Login exitoso: resetear intentos fallidos
        user.reset_failed_attempts()
        user.update_last_login()
        self._user_repository.update(user)
        
        logger.info(f"Login exitoso: {email}")
        return user, "Login exitoso"
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            User: Usuario encontrado o None
        """
        return self._user_repository.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email
        
        Args:
            email: Email del usuario
            
        Returns:
            User: Usuario encontrado o None
        """
        if not self.validate_email(email):
            return None
        
        return self._user_repository.get_by_email(email.lower().strip())
    
    def update_user_role(self, user_id: str, new_role: str, updated_by: str) -> User:
        """
        Actualiza el rol de un usuario
        
        ✅ Validación de rol
        ✅ Auditoría (updated_by)
        
        Args:
            user_id: ID del usuario
            new_role: Nuevo rol
            updated_by: ID del usuario que realiza la actualización
            
        Returns:
            User: Usuario actualizado
            
        Raises:
            ValidationError: Si hay errores de validación
        """
        if new_role not in self.VALID_ROLES:
            raise ValidationError(f"Rol inválido. Roles válidos: {', '.join(self.VALID_ROLES)}")
        
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise ValidationError("Usuario no encontrado")
        
        user.role = new_role
        user.updated_at = datetime.now()
        
        updated_user = self._user_repository.update(user)
        logger.info(f"Rol de usuario actualizado: {updated_user.email} -> {new_role} (por {updated_by})")
        return updated_user
    
    def activate_user(self, user_id: str, activated_by: Optional[str] = None) -> User:
        """
        Activa un usuario
        
        ✅ Validación de existencia
        ✅ Auditoría
        
        Args:
            user_id: ID del usuario
            activated_by: ID del usuario que activa (opcional)
            
        Returns:
            User: Usuario activado
            
        Raises:
            ValidationError: Si el usuario no existe
        """
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise ValidationError("Usuario no encontrado")
        
        user.active = True
        user.updated_at = datetime.now()
        
        updated_user = self._user_repository.update(user)
        logger.info(f"Usuario activado: {updated_user.email} (por {activated_by})")
        return updated_user
    
    def deactivate_user(self, user_id: str, deactivated_by: Optional[str] = None) -> User:
        """
        Desactiva un usuario (soft delete)
        
        ✅ No elimina físicamente
        ✅ Auditoría
        
        Args:
            user_id: ID del usuario
            deactivated_by: ID del usuario que desactiva (opcional)
            
        Returns:
            User: Usuario desactivado
            
        Raises:
            ValidationError: Si el usuario no existe
        """
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise ValidationError("Usuario no encontrado")
        
        user.active = False
        user.updated_at = datetime.now()
        
        updated_user = self._user_repository.update(user)
        logger.info(f"Usuario desactivado: {updated_user.email} (por {deactivated_by})")
        return updated_user
    
    def get_all_users(self, active_only: bool = True) -> List[User]:
        """
        Obtiene todos los usuarios
        
        Args:
            active_only: Si solo retornar usuarios activos
            
        Returns:
            List[User]: Lista de usuarios
        """
        return self._user_repository.get_all(active_only=active_only)

