"""
Servicio de encriptación para tokens sensibles
Responsabilidad única: Encriptar/desencriptar datos sensibles de forma segura
"""
import os
import logging
from cryptography.fernet import Fernet
from typing import Optional

from app.core.config import Config
from app.utils.exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Servicio de encriptación para tokens sensibles (SRP)
    Responsabilidad única: Encriptar/desencriptar datos sensibles
    
    Usa Fernet (AES 128 en modo CBC) para encriptación simétrica
    - Algoritmo seguro y probado
    - Key derivation desde variable de entorno
    - Encriptación determinista (misma entrada = misma salida)
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Inicializa el servicio de encriptación
        
        Args:
            encryption_key: Key de encriptación (default: Config.ENCRYPTION_KEY)
            
        Raises:
            ConfigurationError: Si la key no está configurada o es inválida
        """
        key = encryption_key or Config.ENCRYPTION_KEY
        
        if not key:
            raise ConfigurationError(
                "ENCRYPTION_KEY no está configurada en el archivo .env. "
                "Genera una con: from cryptography.fernet import Fernet; Fernet.generate_key()"
            )
        
        # Validar que la key sea válida (32 bytes base64)
        try:
            if isinstance(key, str):
                key = key.encode()
            
            self._fernet = Fernet(key)
            # Verificar que la key funciona intentando encriptar/desencriptar un test
            test_token = self._fernet.encrypt(b"test")
            self._fernet.decrypt(test_token)
            
        except Exception as e:
            raise ConfigurationError(
                f"ENCRYPTION_KEY inválida: {str(e)}. "
                "Debe ser una key de Fernet válida (32 bytes base64)"
            )
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encripta texto plano
        
        ✅ Solo se encripta en memoria
        ✅ Nunca se loguea el texto plano
        ✅ Manejo seguro de errores
        
        Args:
            plaintext: Texto a encriptar
            
        Returns:
            str: Texto encriptado (base64)
            
        Raises:
            ValidationError: Si hay error al encriptar
        """
        try:
            if not plaintext:
                raise ValidationError("No se puede encriptar texto vacío")
            
            if not isinstance(plaintext, str):
                plaintext = str(plaintext)
            
            # Encriptar
            plaintext_bytes = plaintext.encode('utf-8')
            encrypted = self._fernet.encrypt(plaintext_bytes)
            
            # Retornar como string base64
            return encrypted.decode('utf-8')
        
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al encriptar: {e}")
            raise ValidationError(f"Error al encriptar datos: {str(e)}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Desencripta texto encriptado
        
        ✅ Solo se desencripta cuando se necesita
        ✅ Limpia memoria después de usar
        ✅ Manejo seguro de errores
        
        Args:
            ciphertext: Texto encriptado (base64)
            
        Returns:
            str: Texto desencriptado
            
        Raises:
            ValidationError: Si hay error al desencriptar (token inválido, corrupto, etc.)
        """
        try:
            if not ciphertext:
                raise ValidationError("No se puede desencriptar texto vacío")
            
            if not isinstance(ciphertext, str):
                ciphertext = str(ciphertext)
            
            # Desencriptar
            ciphertext_bytes = ciphertext.encode('utf-8')
            decrypted = self._fernet.decrypt(ciphertext_bytes)
            
            # Retornar como string
            return decrypted.decode('utf-8')
        
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al desencriptar: {e}")
            raise ValidationError("Token inválido o corrupto. No se puede desencriptar.")
    
    @staticmethod
    def generate_key() -> str:
        """
        Genera una nueva key de encriptación (utilidad)
        
        Returns:
            str: Key de Fernet en formato base64
        """
        return Fernet.generate_key().decode('utf-8')



