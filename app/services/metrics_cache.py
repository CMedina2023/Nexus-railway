"""
Servicio de caché para métricas de reportes Jira
Responsabilidad única: Gestionar caché de métricas con TTL
"""
import hashlib
import json
import logging
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricsCache:
    """Servicio de caché en memoria para métricas de reportes"""
    
    def __init__(self, ttl_hours: int = 6):
        """
        Inicializa el servicio de caché
        
        Args:
            ttl_hours: Tiempo de vida del caché en horas (default: 6)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_hours * 3600
        logger.info(f"MetricsCache inicializado con TTL de {ttl_hours} horas")
    
    def _generate_cache_key(
        self,
        project_key: str,
        view_type: str,
        filters: list,
        user_id: Optional[str] = None
    ) -> str:
        """
        Genera una clave única de caché basada en proyecto, vista y filtros
        
        Args:
            project_key: Clave del proyecto
            view_type: Tipo de vista (general/personal)
            filters: Lista de filtros aplicados
            user_id: ID del usuario (solo para vistas personales)
            
        Returns:
            str: Clave de caché hash
        """
        # Ordenar filtros para consistencia
        sorted_filters = sorted(filters) if filters else []
        
        user_segment = user_id or "all"

        # Crear string para hashing
        cache_string = f"{project_key}:{view_type}:{user_segment}:{':'.join(sorted_filters)}"
        
        # Generar hash SHA256
        cache_key = hashlib.sha256(cache_string.encode('utf-8')).hexdigest()
        
        logger.debug(f"Clave de caché generada: {cache_key[:16]}... para proyecto {project_key}")
        return cache_key
    
    def get(
        self,
        project_key: str,
        view_type: str,
        filters: list,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas del caché si existen y no han expirado
        
        Args:
            project_key: Clave del proyecto
            view_type: Tipo de vista (general/personal)
            filters: Lista de filtros aplicados
            user_id: ID del usuario (solo para vistas personales)
            
        Returns:
            Dict con métricas si están en caché y válidas, None en caso contrario
        """
        cache_key = self._generate_cache_key(project_key, view_type, filters, user_id=user_id)
        
        if cache_key not in self._cache:
            logger.debug(f"Cache miss para clave: {cache_key[:16]}...")
            return None
        
        cached_data = self._cache[cache_key]
        cached_time = cached_data.get('timestamp', 0)
        age_seconds = time.time() - cached_time
        
        # Verificar si ha expirado
        if age_seconds > self._ttl_seconds:
            logger.info(f"Cache expirado para clave: {cache_key[:16]}... (edad: {age_seconds/60:.1f} min)")
            del self._cache[cache_key]
            return None
        
        logger.info(f"Cache hit para clave: {cache_key[:16]}... (edad: {age_seconds/60:.1f} min)")
        return cached_data.get('metrics')
    
    def set(
        self,
        project_key: str,
        view_type: str,
        filters: list,
        metrics: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """
        Guarda métricas en el caché
        
        Args:
            project_key: Clave del proyecto
            view_type: Tipo de vista (general/personal)
            filters: Lista de filtros aplicados
            metrics: Diccionario con las métricas calculadas
            user_id: ID del usuario (solo para vistas personales)
        """
        cache_key = self._generate_cache_key(project_key, view_type, filters, user_id=user_id)
        
        self._cache[cache_key] = {
            'metrics': metrics,
            'timestamp': time.time(),
            'project_key': project_key,
            'view_type': view_type,
            'filters': filters,
            'user_id': user_id
        }
        
        logger.info(f"Métricas guardadas en caché: {cache_key[:16]}... para proyecto {project_key}")
        
        # Limpiar entradas expiradas periódicamente (cada 100 escrituras)
        if len(self._cache) > 100 and len(self._cache) % 100 == 0:
            self._cleanup_expired()
    
    def invalidate(self, project_key: str) -> int:
        """
        Invalida todas las entradas de caché para un proyecto
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            int: Número de entradas eliminadas
        """
        keys_to_delete = [
            key for key, value in self._cache.items()
            if value.get('project_key') == project_key
        ]
        
        for key in keys_to_delete:
            del self._cache[key]
        
        logger.info(f"Caché invalidado para proyecto {project_key}: {len(keys_to_delete)} entradas eliminadas")
        return len(keys_to_delete)
    
    def _cleanup_expired(self) -> int:
        """
        Limpia todas las entradas expiradas del caché
        
        Returns:
            int: Número de entradas eliminadas
        """
        current_time = time.time()
        keys_to_delete = [
            key for key, value in self._cache.items()
            if current_time - value.get('timestamp', 0) > self._ttl_seconds
        ]
        
        for key in keys_to_delete:
            del self._cache[key]
        
        if keys_to_delete:
            logger.info(f"Limpieza de caché: {len(keys_to_delete)} entradas expiradas eliminadas")
        
        return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché
        
        Returns:
            Dict con estadísticas del caché
        """
        current_time = time.time()
        expired_count = sum(
            1 for value in self._cache.values()
            if current_time - value.get('timestamp', 0) > self._ttl_seconds
        )
        
        return {
            'total_entries': len(self._cache),
            'expired_entries': expired_count,
            'valid_entries': len(self._cache) - expired_count,
            'ttl_hours': self._ttl_seconds / 3600
        }


# Instancia global del caché (singleton)
_metrics_cache_instance: Optional[MetricsCache] = None


def get_metrics_cache(ttl_hours: int = 6) -> MetricsCache:
    """
    Obtiene la instancia global del caché de métricas (singleton)
    
    Args:
        ttl_hours: Tiempo de vida del caché en horas (solo se usa en primera inicialización)
        
    Returns:
        MetricsCache: Instancia del caché
    """
    global _metrics_cache_instance
    
    if _metrics_cache_instance is None:
        _metrics_cache_instance = MetricsCache(ttl_hours=ttl_hours)
    
    return _metrics_cache_instance





















