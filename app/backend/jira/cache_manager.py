import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.core.config import Config

logger = logging.getLogger(__name__)

class FieldMetadataCache:
    """
    Cache con TTL (Time-To-Live) para metadata de campos de Jira
    Permite invalidación manual en caso de errores
    """
    
    def __init__(self, ttl_seconds: int = None):
        """
        Inicializa el cache con TTL
        
        Args:
            ttl_seconds: Tiempo de vida del cache en segundos (default: Config.JIRA_FIELD_METADATA_CACHE_TTL_SECONDS)
        """
        self._cache = {}  # {cache_key: {'data': ..., 'timestamp': ...}}
        self._ttl_seconds = ttl_seconds or Config.JIRA_FIELD_METADATA_CACHE_TTL_SECONDS
        logger.info(f"FieldMetadataCache inicializado con TTL de {self._ttl_seconds} segundos")
    
    def get(self, cache_key: str) -> Optional[Dict]:
        """
        Obtiene datos del cache si existen y no han expirado
        
        Args:
            cache_key: Clave del cache (ej: "RB:tests Case")
            
        Returns:
            Dict con metadata si existe y es válido, None si no existe o expiró
        """
        if cache_key not in self._cache:
            return None
        
        cached_item = self._cache[cache_key]
        timestamp = cached_item.get('timestamp')
        data = cached_item.get('data')
        
        # Verificar si el cache ha expirado
        if timestamp and datetime.now() - timestamp > timedelta(seconds=self._ttl_seconds):
            logger.debug(f"Cache expirado para '{cache_key}', eliminando...")
            del self._cache[cache_key]
            return None
        
        logger.debug(f"Cache hit para '{cache_key}'")
        return data
    
    def set(self, cache_key: str, data: Dict) -> None:
        """
        Guarda datos en el cache con timestamp actual
        
        Args:
            cache_key: Clave del cache
            data: Datos a guardar
        """
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cache actualizado para '{cache_key}'")
    
    def invalidate(self, cache_key: str) -> None:
        """
        Invalida (elimina) una entrada del cache
        
        Args:
            cache_key: Clave del cache a invalidar
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info(f"Cache invalidado para '{cache_key}'")
    
    def clear(self) -> None:
        """Limpia todo el cache"""
        self._cache.clear()
        logger.info("Cache completamente limpiado")
