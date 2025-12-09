"""
Excepciones personalizadas para el proyecto
"""
from typing import Optional


class NexusAIException(Exception):
    """Excepción base para todas las excepciones del proyecto"""
    pass


class ConfigurationError(NexusAIException):
    """Error de configuración (variables de entorno faltantes, etc.)"""
    pass


class FileProcessingError(NexusAIException):
    """Error al procesar archivos (lectura, escritura, formato no soportado)"""
    pass


class AIGenerationError(NexusAIException):
    """Error en la generación de contenido con IA (timeout, API error, etc.)"""
    pass


class ValidationError(NexusAIException):
    """Error de validación (contenido vacío, formato inválido, etc.)"""
    pass


class AuthenticationError(NexusAIException):
    """Error de autenticación (usuario no autenticado)"""
    pass


class AuthorizationError(NexusAIException):
    """Error de autorización (usuario sin permisos)"""
    pass


class JiraConnectionError(NexusAIException):
    """Error de conexión con Jira"""
    pass


class JiraAPIError(NexusAIException):
    """Error en la API de Jira"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class DocumentTooLargeError(NexusAIException):
    """Error cuando el documento es demasiado grande"""
    def __init__(self, message: str, size_mb: Optional[float] = None):
        super().__init__(message)
        self.size_mb = size_mb


class EmptyContentError(ValidationError):
    """Error cuando el contenido está vacío"""
    pass

