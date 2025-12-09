"""
Módulo para gestión de agente y selección de herramientas
Responsabilidad única: Orquestar la selección y uso de generadores
"""
from typing import Optional, Dict, Any
import logging

from app.backend.generators.factory import GeneratorFactory

logger = logging.getLogger(__name__)


def simple_agent_processing(task_type: str, document_text: str, parameters: dict) -> Dict[str, Any]:
    """
    Función simplificada que decide qué herramienta usar usando Factory Pattern
    
    Implementa OCP (Open/Closed Principle): 
    - Abierto para extensión (registrar nuevos generadores)
    - Cerrado para modificación (no modifica código existente al agregar nuevos)
    
    Args:
        task_type: Tipo de tarea ('story', 'matrix', 'auto')
        document_text: Texto del documento
        parameters: Parámetros de generación
        
    Returns:
        Dict con el resultado de la generación:
        - {"tool_used": "...", "result": ...} si es exitoso
        - {"error": "...", "status": "error"} si hay error
    """
    try:
        factory = GeneratorFactory()
        
        # Obtener el generador apropiado
        if task_type == 'auto':
            generator = factory.auto_detect_generator(document_text, parameters)
            logger.info(f"Generador auto-detectado: {type(generator).__name__}")
        else:
            generator = factory.get_generator(task_type)
        
        if not generator:
            error_msg = (
                f"Tipo de tarea desconocido: {task_type}. "
                f"Tipos disponibles: {factory.list_available_generators()}"
            )
            logger.error(error_msg)
            return {"error": error_msg, "status": "error"}
        
        # Generar usando el generador apropiado
        result = generator.generate(document_text, parameters)
        logger.info(f"Generación completada con {generator.get_output_format()} como formato de salida")
        
        return result

    except Exception as e:
        logger.error(f"Error en simple_agent_processing: {e}", exc_info=True)
        return {"error": str(e), "status": "error"}


def get_download_type(tool_used: str) -> str:
    """
    Determina el tipo de archivo basado en la herramienta usada
    
    Args:
        tool_used: Nombre de la herramienta usada
        
    Returns:
        str: Tipo de archivo ('zip', 'docx', 'txt')
    """
    if 'matrix' in tool_used:
        return 'zip'
    elif 'story' in tool_used:
        return 'docx'
    return 'txt'
