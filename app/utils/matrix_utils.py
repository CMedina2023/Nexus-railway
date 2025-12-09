"""
Utilidades comunes para procesamiento de datos de matriz de pruebas
"""
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_matrix_data(result: Any) -> Optional[List[Dict]]:
    """
    Extrae los datos de la matriz de pruebas de diferentes estructuras de respuesta.
    
    Esta función centraliza la lógica de extracción que estaba duplicada en App.py.
    Busca los datos en múltiples ubicaciones posibles dentro de la estructura de respuesta.
    
    Args:
        result: Resultado del procesamiento que puede tener múltiples formatos
        
    Returns:
        List[Dict] con los casos de prueba, o None si no se encontraron datos
    """
    matrix_data = None
    
    if not result:
        return None
    
    # Si es una lista directamente, usarla
    if isinstance(result, list):
        if result and isinstance(result[0], dict):
            logger.info(f"Datos de matriz encontrados como lista directa: {len(result)} elementos")
            return result
    
    # Si es un diccionario, buscar en diferentes ubicaciones
    if isinstance(result, dict):
        # PRIMERO: Buscar en 'result' si existe (estructura de agent_manager)
        if 'result' in result and isinstance(result['result'], dict):
            result_data = result['result']
            matrix_data = _search_in_dict(result_data, 'result')
            if matrix_data:
                logger.info(f"Datos de matriz encontrados en 'result': {len(matrix_data)} elementos")
                return matrix_data
        
        # SEGUNDO: Buscar directamente en el diccionario
        matrix_data = _search_in_dict(result, 'root')
        if matrix_data:
            logger.info(f"Datos de matriz encontrados en raíz: {len(matrix_data)} elementos")
            return matrix_data
        
        # TERCERO: Si el diccionario tiene estructura de caso de prueba, usarlo como único caso
        if any(key in result for key in ['id_caso_prueba', 'titulo_caso_prueba', 'Descripcion', 'id', 'title']):
            logger.info("Diccionario tiene estructura de caso de prueba, usando como caso único")
            return [result]
    
    # Si no se encontró nada
    logger.warning("No se pudo encontrar datos de matriz en la estructura de respuesta")
    return None


def _search_in_dict(data: Dict, context: str) -> Optional[List[Dict]]:
    """
    Busca datos de matriz dentro de un diccionario.
    
    Args:
        data: Diccionario donde buscar
        context: Contexto para logging (ej: 'result', 'root')
        
    Returns:
        Lista de casos de prueba o None
    """
    # Claves comunes donde pueden estar los datos
    common_keys = ['matrix', 'test_cases', 'cases', 'test_cases_list', 'data']
    
    # Buscar en claves comunes
    for key in common_keys:
        if key in data and isinstance(data[key], list):
            if data[key] and isinstance(data[key][0], dict):
                return data[key]
    
    # Buscar recursivamente en valores del diccionario
    for key, value in data.items():
        if isinstance(value, list) and value:
            if isinstance(value[0], dict):
                # Verificar si parece ser una lista de casos de prueba
                first_item = value[0]
                if any(k in first_item for k in ['id_caso_prueba', 'titulo_caso_prueba', 'Descripcion', 'id', 'title']):
                    logger.info(f"Datos encontrados en clave recursiva '{context}.{key}': {len(value)} elementos")
                    return value
        elif isinstance(value, dict):
            # Buscar dentro de diccionarios anidados
            nested_result = _search_in_dict(value, f"{context}.{key}")
            if nested_result:
                return nested_result
    
    return None

