"""
Servicio de normalización de historias de usuario
Responsabilidad única: Normalizar y validar estructura de historias generadas (SRP)
"""
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class StoryNormalizer:
    """
    Normaliza y valida historias de usuario generadas.
    
    Responsabilidades:
    - Normalizar formato de historias
    - Validar estructura completa de historias
    - Detectar y corregir inconsistencias de formato
    """
    
    # Componentes requeridos en una historia completa
    REQUIRED_COMPONENTS = {
        'como': r'COMO\s*:',
        'quiero': r'QUIERO\s*:',
        'para': r'PARA\s*:',
        'criterios': r'CRITERIOS\s+DE\s+ACEPTACI[ÓO]N',
    }
    
    def __init__(self):
        """Inicializa el normalizador de historias"""
        pass
    
    def normalize_story_text(self, story_text: str) -> str:
        """
        Normaliza el formato de una historia de usuario.
        
        Args:
            story_text: Texto de la historia a normalizar
            
        Returns:
            Texto normalizado
        """
        if not story_text or not isinstance(story_text, str):
            return ""
        
        # Normalizar espacios en blanco múltiples
        normalized = re.sub(r'\s+', ' ', story_text)
        
        # Normalizar saltos de línea múltiples
        normalized = re.sub(r'\n{3,}', '\n\n', normalized)
        
        # Normalizar formato de "HISTORIA #"
        normalized = re.sub(
            r'HISTORIA\s*#\s*(\d+)',
            r'HISTORIA #\1',
            normalized,
            flags=re.IGNORECASE
        )
        
        # Normalizar separadores de líneas
        normalized = re.sub(r'═{10,}', '═' * 70, normalized)
        
        # Asegurar que los componentes clave estén en mayúsculas
        for component, pattern in self.REQUIRED_COMPONENTS.items():
            normalized = re.sub(
                pattern,
                lambda m: m.group(0).upper(),
                normalized,
                flags=re.IGNORECASE
            )
        
        return normalized.strip()
    
    def validate_story_structure(self, story_text: str) -> Dict[str, bool]:
        """
        Valida que una historia tenga todos los componentes requeridos.
        
        Args:
            story_text: Texto de la historia a validar
            
        Returns:
            Dict con estado de cada componente requerido
        """
        if not story_text:
            return {component: False for component in self.REQUIRED_COMPONENTS.keys()}
        
        validation = {}
        story_lower = story_text.lower()
        
        for component, pattern in self.REQUIRED_COMPONENTS.items():
            # Buscar el componente en el texto
            match = re.search(pattern, story_text, re.IGNORECASE)
            if match:
                # Verificar que hay contenido después del componente
                start_pos = match.end()
                content_after = story_text[start_pos:start_pos + 200].strip()
                validation[component] = len(content_after) > 10
            else:
                validation[component] = False
        
        return validation
    
    def is_story_complete(self, story_text: str) -> bool:
        """
        Verifica si una historia tiene todos los componentes requeridos.
        
        Args:
            story_text: Texto de la historia a verificar
            
        Returns:
            True si la historia está completa, False en caso contrario
        """
        validation = self.validate_story_structure(story_text)
        return all(validation.values())
    
    def normalize_stories(self, stories: List[str]) -> List[str]:
        """
        Normaliza una lista de historias.
        
        Args:
            stories: Lista de historias a normalizar
            
        Returns:
            Lista de historias normalizadas
        """
        normalized = []
        for story in stories:
            if story and isinstance(story, str):
                normalized_story = self.normalize_story_text(story)
                if normalized_story:
                    normalized.append(normalized_story)
        
        logger.info(f"Normalizadas {len(normalized)} de {len(stories)} historias")
        return normalized
    
    def filter_complete_stories(self, stories: List[str]) -> List[str]:
        """
        Filtra solo las historias que tienen estructura completa.
        
        Args:
            stories: Lista de historias a filtrar
            
        Returns:
            Lista de historias completas
        """
        complete_stories = []
        incomplete_count = 0
        
        for story in stories:
            if story and isinstance(story, str):
                if self.is_story_complete(story):
                    complete_stories.append(story)
                else:
                    incomplete_count += 1
                    validation = self.validate_story_structure(story)
                    missing = [comp for comp, present in validation.items() if not present]
                    logger.warning(
                        f"Historia incompleta detectada. Componentes faltantes: {', '.join(missing)}"
                    )
        
        if incomplete_count > 0:
            logger.info(
                f"Filtradas {incomplete_count} historias incompletas. "
                f"Quedan {len(complete_stories)} historias completas"
            )
        
        return complete_stories
    
    def normalize_and_validate(self, stories: List[str]) -> List[str]:
        """
        Normaliza y valida una lista de historias, retornando solo las completas.
        
        Args:
            stories: Lista de historias a procesar
            
        Returns:
            Lista de historias normalizadas y completas
        """
        # Primero normalizar
        normalized = self.normalize_stories(stories)
        
        # Luego filtrar solo las completas
        complete = self.filter_complete_stories(normalized)
        
        return complete




