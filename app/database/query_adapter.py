"""
Adaptador de consultas SQL para soportar múltiples bases de datos
Responsabilidad única: Convertir placeholders entre SQLite y PostgreSQL
"""
import re
from typing import Tuple, Any


def adapt_query(query: str, params: tuple, is_postgres: bool) -> Tuple[str, tuple]:
    """
    Adapta una consulta SQL y sus parámetros para el tipo de base de datos
    
    Args:
        query: Consulta SQL con placeholders ? (estilo SQLite)
        params: Tupla de parámetros
        is_postgres: True si es PostgreSQL, False si es SQLite
        
    Returns:
        Tuple[str, tuple]: Consulta adaptada y parámetros
    """
    if not is_postgres:
        # SQLite usa ? - no hay cambios
        return query, params
    
    # PostgreSQL usa %s en lugar de ?
    # Contar cuántos placeholders hay
    placeholder_count = query.count('?')
    
    if placeholder_count == 0:
        return query, params
    
    # Reemplazar ? por %s
    adapted_query = query.replace('?', '%s')
    
    return adapted_query, params


def adapt_query_dict(query: str, params: dict, is_postgres: bool) -> Tuple[str, dict]:
    """
    Adapta una consulta SQL con parámetros nombrados
    
    Args:
        query: Consulta SQL con placeholders :name (estilo nombrado)
        params: Diccionario de parámetros
        is_postgres: True si es PostgreSQL, False si es SQLite
        
    Returns:
        Tuple[str, dict]: Consulta adaptada y parámetros
    """
    if not is_postgres:
        # SQLite soporta :name - no hay cambios
        return query, params
    
    # PostgreSQL usa %(name)s en lugar de :name
    # Encontrar todos los placeholders :name
    placeholders = re.findall(r':(\w+)', query)
    
    if not placeholders:
        return query, params
    
    # Reemplazar :name por %(name)s
    adapted_query = query
    for placeholder in placeholders:
        adapted_query = adapted_query.replace(f':{placeholder}', f'%({placeholder})s')
    
    return adapted_query, params


