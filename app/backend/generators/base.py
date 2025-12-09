"""
Interfaz base para todos los generadores
Responsabilidad única: Definir el contrato para generadores
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class Generator(ABC):
    """Interfaz base para todos los generadores de contenido"""
    
    @abstractmethod
    def generate(self, document_text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera contenido basado en el documento y parámetros
        
        Args:
            document_text: Texto del documento a procesar
            parameters: Diccionario con parámetros de generación
            
        Returns:
            Dict con el resultado de la generación
        """
        pass
    
    @abstractmethod
    def can_handle(self, document_text: str, parameters: Dict[str, Any]) -> bool:
        """
        Determina si este generador puede manejar el documento dado
        
        Args:
            document_text: Texto del documento
            parameters: Parámetros de generación
            
        Returns:
            bool: True si puede manejar, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_output_format(self) -> str:
        """
        Retorna el formato de archivo de salida
        
        Returns:
            str: Formato de salida (ej: 'docx', 'zip', 'json')
        """
        pass

