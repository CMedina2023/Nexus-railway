"""
Servicio de gestión de contraseñas
Responsabilidad única: Hashing y validación de contraseñas de forma segura
"""
import re
import logging
import bcrypt
from typing import Tuple, List

from app.core.config import Config

logger = logging.getLogger(__name__)


class PasswordService:
    """
    Servicio dedicado a gestión de contraseñas (SRP)
    Responsabilidad única: Hashing y validación de contraseñas
    """
    
    # Configuración desde Config (no hardcodeado)
    BCRYPT_ROUNDS = Config.BCRYPT_ROUNDS
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash seguro de contraseña usando bcrypt con salt automático
        
        ✅ Usa bcrypt (resistente a rainbow tables)
        ✅ Salt automático por cada hash (generado por bcrypt)
        ✅ Número de rondas configurable (mínimo 12)
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña (incluye salt)
            
        Raises:
            ValueError: Si la contraseña está vacía
        """
        if not password:
            raise ValueError("La contraseña no puede estar vacía")
        
        if not isinstance(password, str):
            password = str(password)
        
        # Generar hash con salt automático
        # bcrypt.gensalt() genera un salt aleatorio y lo incluye en el hash
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=PasswordService.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Retornar como string para almacenar en DB
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verifica contraseña de forma segura (timing-safe)
        
        ✅ Timing-safe comparison (previene timing attacks)
        ✅ Nunca expone información sobre la contraseña
        ✅ Maneja errores de forma segura
        
        Args:
            password: Contraseña en texto plano a verificar
            password_hash: Hash almacenado de la contraseña
            
        Returns:
            bool: True si la contraseña es correcta, False en caso contrario
        """
        try:
            if not password or not password_hash:
                return False
            
            if not isinstance(password, str):
                password = str(password)
            if not isinstance(password_hash, str):
                password_hash = str(password_hash)
            
            # Verificar contraseña (timing-safe)
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            
            # bcrypt.checkpw es timing-safe (siempre tarda lo mismo)
            return bcrypt.checkpw(password_bytes, hash_bytes)
        
        except Exception as e:
            # Siempre retornar False en caso de error (security by default)
            logger.warning(f"Error al verificar contraseña: {e}")
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """
        Valida fortaleza de contraseña
        
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        
        Args:
            password: Contraseña a validar
            
        Returns:
            Tuple[bool, List[str]]: (es_válida, lista_de_errores)
        """
        errors = []
        
        if not password:
            errors.append("La contraseña no puede estar vacía")
            return False, errors
        
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        if not re.search(r'[A-Z]', password):
            errors.append("La contraseña debe contener al menos una mayúscula")
        
        if not re.search(r'[a-z]', password):
            errors.append("La contraseña debe contener al menos una minúscula")
        
        if not re.search(r'\d', password):
            errors.append("La contraseña debe contener al menos un número")
        
        # Opcional: caracteres especiales (no obligatorio por seguridad)
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        #     errors.append("La contraseña debe contener al menos un carácter especial")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def needs_rehash(password_hash: str) -> bool:
        """
        Verifica si un hash necesita ser regenerado (rondas cambiadas)
        
        Args:
            password_hash: Hash actual de la contraseña
            
        Returns:
            bool: True si necesita rehash
        """
        try:
            # Extraer el número de rondas del hash actual
            # El formato de bcrypt es: $2b$rounds$salt+hash
            parts = password_hash.split('$')
            if len(parts) < 3:
                return True
            
            rounds = int(parts[2])
            return rounds < PasswordService.BCRYPT_ROUNDS
        
        except Exception:
            return True



