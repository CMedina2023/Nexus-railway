"""
Servicio de estadísticas para administración
Responsabilidad única: Calcular estadísticas de usuarios y sistema (SRP)
"""
import logging
from typing import List, Dict, Any
from app.models.user import User

logger = logging.getLogger(__name__)

class AdminStatsService:
    """
    Servicio para centralizar la lógica de cálculo de estadísticas
    """
    
    @staticmethod
    def calculate_basic_stats(users: List[User]) -> Dict[str, Any]:
        """
        Calcula estadísticas básicas sobre una lista de usuarios
        
        Args:
            users: Lista de objetos User
            
        Returns:
            Dict con estadísticas (total, activos, inactivos, roles)
        """
        total_users = len(users)
        active_users = len([u for u in users if u.active])
        inactive_users = total_users - active_users
        
        role_counts = {}
        for user in users:
            role_val = getattr(user, 'role', 'usuario')
            role_counts[role_val] = role_counts.get(role_val, 0) + 1
            
        return {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
            "by_role": role_counts
        }

    @staticmethod
    def calculate_extended_stats(users: List[User]) -> Dict[str, Any]:
        """
        Calcula estadísticas completas incluyendo seguridad
        
        Args:
            users: Lista completa de usuarios
            
        Returns:
            Dict con estadísticas detalladas
        """
        # Reutilizar estadísticas básicas
        stats = AdminStatsService.calculate_basic_stats(users)
        
        # Agregar metricas de seguridad
        users_with_failed_attempts = len([u for u in users if getattr(u, 'failed_login_attempts', 0) > 0])
        locked_users = len([u for u in users if hasattr(u, 'is_locked') and u.is_locked()])
        
        stats["with_failed_attempts"] = users_with_failed_attempts
        stats["locked"] = locked_users
        
        return stats
