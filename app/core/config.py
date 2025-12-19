"""
Módulo de configuración centralizada para el proyecto
Lee valores de variables de entorno con valores por defecto sensibles
"""
import os
from dotenv import load_dotenv
import logging

from app.utils.exceptions import ConfigurationError

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Configuración centralizada del proyecto"""
    
    # ============================================================================
    # Google Gemini AI
    # ============================================================================
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    GEMINI_TIMEOUT_BASE = int(os.getenv('GEMINI_TIMEOUT_BASE', '180'))
    GEMINI_TIMEOUT_INCREMENT = int(os.getenv('GEMINI_TIMEOUT_INCREMENT', '60'))
    GEMINI_TIMEOUT_ANALYSIS = int(os.getenv('GEMINI_TIMEOUT_ANALYSIS', '90'))
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.2'))  # Baja temperatura para mayor consistencia
    
    # ============================================================================
    # Reintentos
    # ============================================================================
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))
    
    # ============================================================================
    # Procesamiento de Documentos
    # ============================================================================
    STORY_MAX_CHUNK_SIZE = int(os.getenv('STORY_MAX_CHUNK_SIZE', '3000'))
    MATRIX_MAX_CHUNK_SIZE = int(os.getenv('MATRIX_MAX_CHUNK_SIZE', '4000'))
    LARGE_DOCUMENT_THRESHOLD = int(os.getenv('LARGE_DOCUMENT_THRESHOLD', '5000'))
    STORY_BATCH_SIZE = int(os.getenv('STORY_BATCH_SIZE', '5'))
    MIN_DOCUMENT_LENGTH = int(os.getenv('MIN_DOCUMENT_LENGTH', '50'))
    MIN_RESPONSE_LENGTH = int(os.getenv('MIN_RESPONSE_LENGTH', '50'))
    
    # ============================================================================
    # Configuración de Jira
    # ============================================================================
    JIRA_ENV = os.getenv('JIRA_ENV', '').upper()
    
    # Lógica de switch: si JIRA_ENV está definido, usa variables con prefijo (ej: DEV_JIRA_URL)
    # De lo contrario, usa las variables estándar.
    if JIRA_ENV:
        JIRA_BASE_URL = os.getenv(f'{JIRA_ENV}_JIRA_URL', os.getenv('JIRA_BASE_URL', ''))
        JIRA_EMAIL = os.getenv(f'{JIRA_ENV}_JIRA_EMAIL', os.getenv('JIRA_EMAIL', ''))
        JIRA_API_TOKEN = os.getenv(f'{JIRA_ENV}_JIRA_TOKEN', os.getenv('JIRA_API_TOKEN', ''))
    else:
        JIRA_BASE_URL = os.getenv('JIRA_BASE_URL', '')
        JIRA_EMAIL = os.getenv('JIRA_EMAIL', '')
        JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', '')
    JIRA_TIMEOUT_SHORT = int(os.getenv('JIRA_TIMEOUT_SHORT', '10'))
    JIRA_TIMEOUT_LONG = int(os.getenv('JIRA_TIMEOUT_LONG', '15'))
    JIRA_MAX_RESULTS = int(os.getenv('JIRA_MAX_RESULTS', '100'))
    JIRA_FILTER_MAX_RESULTS = int(os.getenv('JIRA_FILTER_MAX_RESULTS', '50'))
    
    # Optimización de paginación paralela
    JIRA_PARALLEL_MAX_WORKERS = int(os.getenv('JIRA_PARALLEL_MAX_WORKERS', '3'))  # NO más de 5
    JIRA_PARALLEL_MAX_RESULTS = int(os.getenv('JIRA_PARALLEL_MAX_RESULTS', '100'))  # Límite real de Jira por página
    JIRA_PARALLEL_REQUEST_TIMEOUT = int(os.getenv('JIRA_PARALLEL_REQUEST_TIMEOUT', '30'))  # Timeout por request
    JIRA_PARALLEL_RETRY_ATTEMPTS = int(os.getenv('JIRA_PARALLEL_RETRY_ATTEMPTS', '3'))  # Reintentos por request
    JIRA_PARALLEL_RATE_LIMIT_SLEEP = float(os.getenv('JIRA_PARALLEL_RATE_LIMIT_SLEEP', '0.5'))  # Sleep entre requests
    
    # Caché de métricas
    JIRA_METRICS_CACHE_TTL_HOURS = int(os.getenv('JIRA_METRICS_CACHE_TTL_HOURS', '6'))  # TTL en horas
    
    # Caché de metadata de campos (para carga masiva)
    JIRA_FIELD_METADATA_CACHE_TTL_SECONDS = int(os.getenv('JIRA_FIELD_METADATA_CACHE_TTL_SECONDS', '300'))  # 5 minutos
    
    # Rate Limiting para creación de issues
    JIRA_CREATE_ISSUE_DELAY_SECONDS = float(os.getenv('JIRA_CREATE_ISSUE_DELAY_SECONDS', '0.5'))  # Delay entre issues
    JIRA_CREATE_ISSUE_BACKOFF_MULTIPLIER = float(os.getenv('JIRA_CREATE_ISSUE_BACKOFF_MULTIPLIER', '1.5'))  # Multiplicador de backoff
    JIRA_CREATE_ISSUE_MAX_DELAY_SECONDS = float(os.getenv('JIRA_CREATE_ISSUE_MAX_DELAY_SECONDS', '5.0'))  # Delay máximo
    
    # ============================================================================
    # Flask
    # ============================================================================
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'temp_uploads')
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '16'))
    # Railway usa PORT, Render y otros usan FLASK_PORT
    FLASK_PORT = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000')))
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    SECRET_KEY = os.getenv('SECRET_KEY', '')  # Mínimo 32 caracteres aleatorios
    
    # ============================================================================
    # Seguridad y Autenticación
    # ============================================================================
    # Base de datos
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///nexus_ai.db')
    
    # Bcrypt
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', '12'))
    
    # Sesiones
    SESSION_LIFETIME_HOURS = int(os.getenv('SESSION_LIFETIME_HOURS', '8'))
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    LOCKOUT_DURATION_SECONDS = int(os.getenv('LOCKOUT_DURATION_SECONDS', '900'))  # 15 minutos
    
    # Encriptación de tokens
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')  # Fernet key
    
    # Cookies de sesión
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @classmethod
    def validate(cls):
        """Valida que las configuraciones críticas estén presentes"""
        errors = []
        
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY no está configurada en el archivo .env")
        
        if not cls.JIRA_BASE_URL and not cls.JIRA_EMAIL:
            # Solo advertir si no hay ninguna credencial de Jira
            logger.warning("JIRA_BASE_URL y JIRA_EMAIL no están configurados (Jira opcional)")
        elif cls.JIRA_BASE_URL and not cls.JIRA_EMAIL:
            errors.append("JIRA_EMAIL no está configurada pero JIRA_BASE_URL sí")
        elif cls.JIRA_EMAIL and not cls.JIRA_BASE_URL:
            errors.append("JIRA_BASE_URL no está configurada pero JIRA_EMAIL sí")
        
        # Validar seguridad si hay autenticación habilitada
        if cls.SECRET_KEY:
            if len(cls.SECRET_KEY) < 32:
                errors.append("SECRET_KEY debe tener al menos 32 caracteres")
            if not cls.ENCRYPTION_KEY:
                logger.warning("ENCRYPTION_KEY no está configurada (necesaria para tokens)")
        
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Errores de configuración: {error_msg}")
            raise ConfigurationError(error_msg)
        
        return True
    
    @classmethod
    def get_max_content_length(cls):
        """Retorna el tamaño máximo de contenido en bytes"""
        return cls.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Validar configuración al importar el módulo (solo advertir, no fallar)
try:
    Config.validate()
except ConfigurationError as e:
    # Solo loguear el error, no detener la aplicación
    # La validación se puede hacer en tiempo de ejecución cuando sea necesario
    logger.warning(f"Advertencia de configuración: {e}")

