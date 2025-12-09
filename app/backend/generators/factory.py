"""
Factory para crear generadores
Responsabilidad única: Crear y gestionar instancias de generadores
"""
import logging
from typing import Optional, Dict, Any

from app.backend.generators.base import Generator
from app.backend.generators.story_generator import StoryGenerator
from app.backend.generators.matrix_generator import MatrixGenerator

logger = logging.getLogger(__name__)


class GeneratorFactory:
    """Factory para crear y gestionar generadores de contenido"""
    
    def __init__(self):
        """Inicializa el factory con generadores por defecto"""
        self._generators: Dict[str, Generator] = {
            'story': StoryGenerator(),
            'matrix': MatrixGenerator(),
        }
    
    def get_generator(self, task_type: str) -> Optional[Generator]:
        """
        Obtiene un generador por tipo de tarea
        
        Args:
            task_type: Tipo de tarea ('story', 'matrix', etc.)
            
        Returns:
            Generator o None si no existe
        """
        return self._generators.get(task_type)
    
    def auto_detect_generator(
        self, 
        document_text: str, 
        parameters: Dict[str, Any]
    ) -> Generator:
        """
        Detecta automáticamente el generador apropiado basándose en el contenido
        
        Args:
            document_text: Texto del documento
            parameters: Parámetros de generación
            
        Returns:
            Generator: El generador más apropiado (default: StoryGenerator)
        """
        best_generator = None
        best_score = 0
        
        for generator in self._generators.values():
            if generator.can_handle(document_text, parameters):
                # Calcular score (simple: preferir el primero que pueda manejar)
                score = 1
                if best_score < score:
                    best_score = score
                    best_generator = generator
                    break  # Usar el primero que pueda manejar
        
        # Si no se encontró ninguno, usar StoryGenerator por defecto
        return best_generator or self._generators.get('story')
    
    def register_generator(self, task_type: str, generator: Generator):
        """
        Registra un nuevo generador (extensión sin modificar código existente)
        
        Args:
            task_type: Tipo de tarea para el nuevo generador
            generator: Instancia del generador
            
        Ejemplo:
            factory = GeneratorFactory()
            factory.register_generator('custom', CustomGenerator())
        """
        if not isinstance(generator, Generator):
            raise ValueError(f"El generador debe implementar la interfaz Generator")
        
        self._generators[task_type] = generator
        logger.info(f"Generador '{task_type}' registrado exitosamente")
    
    def list_available_generators(self) -> list:
        """
        Lista todos los generadores disponibles
        
        Returns:
            List[str]: Lista de tipos de generadores disponibles
        """
        return list(self._generators.keys())

