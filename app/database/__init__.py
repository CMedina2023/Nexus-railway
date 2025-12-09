"""
Módulo de base de datos
Responsabilidad única: Gestión de base de datos y repositorios
"""
from app.database.db import get_db, init_db

__all__ = [
    'get_db',
    'init_db'
]



