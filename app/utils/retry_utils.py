"""
Módulo de utilidades para manejo de reintentos con backoff exponencial
"""
import time
import logging
import inspect
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    retry_delay: int = 2,
    timeout_base: int = 180,
    timeout_increment: int = 60,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorador para reintentos con backoff exponencial.
    
    Args:
        max_retries (int): Número máximo de reintentos
        retry_delay (int): Delay inicial en segundos para backoff
        timeout_base (int): Timeout base en segundos
        timeout_increment (int): Incremento de timeout por intento
        exceptions (tuple): Tupla de excepciones que deben activar reintento
        on_retry (callable): Función opcional a llamar antes de cada reintento
        
    Returns:
        callable: Función decorada
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for retry in range(max_retries):
                try:
                    # Calcular timeout progresivo
                    timeout_seconds = timeout_base + (retry * timeout_increment)
                    
                    # Verificar si la función acepta timeout como parámetro
                    if 'timeout' not in kwargs and 'timeout_seconds' not in kwargs:
                        try:
                            sig = inspect.signature(func)
                            params = sig.parameters
                            # Solo pasar timeout si la función realmente lo acepta
                            if 'timeout' in params or 'timeout_seconds' in params:
                                param_name = 'timeout' if 'timeout' in params else 'timeout_seconds'
                                kwargs[param_name] = timeout_seconds
                        except (ValueError, TypeError):
                            # Si no se puede inspeccionar la firma, no pasar timeout
                            pass
                    else:
                        # Si ya está en kwargs, actualizar el valor
                        if 'timeout' in kwargs:
                            kwargs['timeout'] = timeout_seconds
                        elif 'timeout_seconds' in kwargs:
                            kwargs['timeout_seconds'] = timeout_seconds
                    
                    # Ejecutar función
                    result = func(*args, **kwargs)
                    
                    # Si hay resultado válido, retornarlo
                    if result is not None:
                        return result
                        
                    # Si llegamos aquí y no es el último intento, reintentar
                    if retry < max_retries - 1:
                        delay = retry_delay * (2 ** retry)
                        logger.warning(
                            f"{func.__name__}: Resultado vacío, reintentando en {delay}s "
                            f"(intento {retry + 1}/{max_retries})"
                        )
                        if on_retry:
                            on_retry(retry + 1, max_retries)
                        time.sleep(delay)
                    
                except exceptions as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Si es el último intento, lanzar la excepción
                    if retry == max_retries - 1:
                        logger.error(
                            f"{func.__name__}: Falló después de {max_retries} intentos: {e}"
                        )
                        raise
                    
                    # Calcular delay para backoff exponencial
                    delay = retry_delay * (2 ** retry)
                    
                    # Mensaje especial para timeouts
                    if "timeout" in error_msg or "timed out" in error_msg:
                        logger.warning(
                            f"{func.__name__}: Timeout detectado, reintentando en {delay}s "
                            f"(intento {retry + 1}/{max_retries})"
                        )
                    else:
                        logger.warning(
                            f"{func.__name__}: Error detectado, reintentando en {delay}s "
                            f"(intento {retry + 1}/{max_retries}): {e}"
                        )
                    
                    if on_retry:
                        on_retry(retry + 1, max_retries, e)
                    
                    time.sleep(delay)
            
            # Si llegamos aquí sin éxito, lanzar última excepción o error genérico
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__}: Falló después de {max_retries} intentos sin excepción")
        
        return wrapper
    return decorator


def call_with_retry(
    func: Callable,
    *args,
    max_retries: int = 3,
    retry_delay: int = 2,
    timeout_base: int = 180,
    timeout_increment: int = 60,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Ejecuta una función con reintentos y backoff exponencial.
    
    Esta función es útil cuando no puedes usar el decorador.
    
    Args:
        func (callable): Función a ejecutar
        *args: Argumentos posicionales para la función
        max_retries (int): Número máximo de reintentos
        retry_delay (int): Delay inicial en segundos
        timeout_base (int): Timeout base en segundos
        timeout_increment (int): Incremento de timeout por intento
        exceptions (tuple): Excepciones que activan reintento
        **kwargs: Argumentos con nombre para la función
        
    Returns:
        Any: Resultado de la función
    """
    last_exception = None
    
    for retry in range(max_retries):
        try:
            # Calcular timeout progresivo
            timeout_seconds = timeout_base + (retry * timeout_increment)
            
            # Verificar si la función acepta timeout como parámetro
            if 'timeout' not in kwargs and 'timeout_seconds' not in kwargs:
                try:
                    sig = inspect.signature(func)
                    params = sig.parameters
                    # Solo pasar timeout si la función realmente lo acepta
                    if 'timeout' in params or 'timeout_seconds' in params:
                        param_name = 'timeout' if 'timeout' in params else 'timeout_seconds'
                        kwargs[param_name] = timeout_seconds
                except (ValueError, TypeError):
                    # Si no se puede inspeccionar la firma, no pasar timeout
                    pass
            
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Si hay resultado válido, retornarlo
            if result is not None:
                return result
                
            # Si llegamos aquí y no es el último intento, reintentar
            if retry < max_retries - 1:
                delay = retry_delay * (2 ** retry)
                logger.warning(
                    f"{func.__name__ if hasattr(func, '__name__') else 'function'}: "
                    f"Resultado vacío, reintentando en {delay}s (intento {retry + 1}/{max_retries})"
                )
                time.sleep(delay)
                
        except exceptions as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Si es el último intento, lanzar la excepción
            if retry == max_retries - 1:
                logger.error(
                    f"{func.__name__ if hasattr(func, '__name__') else 'function'}: "
                    f"Falló después de {max_retries} intentos: {e}"
                )
                raise
            
            # Calcular delay para backoff exponencial
            delay = retry_delay * (2 ** retry)
            
            # Mensaje especial para timeouts
            if "timeout" in error_msg or "timed out" in error_msg:
                logger.warning(
                    f"{func.__name__ if hasattr(func, '__name__') else 'function'}: "
                    f"Timeout detectado, reintentando en {delay}s (intento {retry + 1}/{max_retries})"
                )
            else:
                logger.warning(
                    f"{func.__name__ if hasattr(func, '__name__') else 'function'}: "
                    f"Error detectado, reintentando en {delay}s (intento {retry + 1}/{max_retries}): {e}"
                )
            
            time.sleep(delay)
    
    # Si llegamos aquí sin éxito, lanzar última excepción o error genérico
    if last_exception:
        raise last_exception
    raise RuntimeError(
        f"{func.__name__ if hasattr(func, '__name__') else 'function'}: "
        f"Falló después de {max_retries} intentos sin excepción"
    )

