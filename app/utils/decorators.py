"""
Decoradores comunes para validación y manejo de errores
Responsabilidad única: Decoradores reutilizables para validación y manejo de errores
"""
import logging
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


def validate_file_upload(func: Callable) -> Callable:
    """
    Decorador para validar archivos subidos en endpoints Flask
    
    Args:
        func: Función del endpoint a decorar
        
    Returns:
        Función decorada con validación de archivo
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request, jsonify
        
        # Verificar que hay archivo
        if 'file' not in request.files:
            return jsonify({"error": "No se subió ningún archivo"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó un archivo"}), 400
        
        # Verificar formato
        from app.utils.file_utils import is_valid_file_format
        if not is_valid_file_format(file.filename):
            return jsonify({"error": "Formato de archivo no válido. Use .pdf, .docx o .doc"}), 400
        
        return func(*args, **kwargs)
    
    return wrapper


def handle_errors(default_message: str = "Error interno del servidor", status_code: int = 500):
    """
    Decorador para manejar errores de forma consistente
    
    Args:
        default_message: Mensaje de error por defecto
        status_code: Código de estado HTTP por defecto
        
    Returns:
        Decorador que maneja errores
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                logger.warning(f"Error de validación en {func.__name__}: {e}")
                from flask import jsonify
                return jsonify({"error": str(e)}), 400
            except FileNotFoundError as e:
                logger.error(f"Archivo no encontrado en {func.__name__}: {e}")
                from flask import jsonify
                return jsonify({"error": f"Archivo no encontrado: {str(e)}"}), 404
            except PermissionError as e:
                logger.error(f"Error de permisos en {func.__name__}: {e}")
                from flask import jsonify
                return jsonify({"error": f"Error de permisos: {str(e)}"}), 403
            except Exception as e:
                logger.error(f"Error no manejado en {func.__name__}: {e}", exc_info=True)
                from flask import jsonify
                return jsonify({"error": default_message if not str(e) else str(e)}), status_code
        
        return wrapper
    
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    Decorador para registrar ejecución de funciones
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada con logging
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Ejecutando {func.__name__} con args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} ejecutada exitosamente")
            return result
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
            raise
    
    return wrapper


def validate_required_params(*param_names: str):
    """
    Decorador para validar parámetros requeridos en request
    
    Args:
        *param_names: Nombres de parámetros requeridos
        
    Returns:
        Decorador que valida parámetros
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            missing = []
            for param in param_names:
                if param not in request.form and param not in request.json:
                    missing.append(param)
            
            if missing:
                return jsonify({
                    "error": f"Parámetros faltantes: {', '.join(missing)}"
                }), 400
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorador para reintentar una función en caso de fallo
    
    Args:
        max_retries: Número máximo de reintentos
        delay: Tiempo de espera entre reintentos en segundos
        
    Returns:
        Decorador que reintenta la función
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Intento {attempt + 1} fallido en {func.__name__}: {e}. "
                            f"Reintentando en {delay} segundos..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Todos los intentos fallaron en {func.__name__}: {e}")
            
            # Si llegamos aquí, todos los intentos fallaron
            raise last_exception
        
        return wrapper
    
    return decorator

