"""
Servicio para procesamiento y limpieza de texto
Responsabilidad única: Limpieza y transformación de texto
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


class TextProcessor:
    """Procesa y limpia texto de historias de usuario"""
    
    MIN_STORY_LENGTH = 50
    
    def clean_story_text(self, story_text: str) -> str:
        """
        Limpia el texto de la historia removiendo formato excesivo
        
        Args:
            story_text: Texto de la historia a limpiar
            
        Returns:
            str: Texto limpio
        """
        # Remover bloques de código ```
        story_text = story_text.replace('```json', '').replace('```', '')
        
        # Remover caracteres de escape excesivos
        story_text = story_text.replace('\\n', '\n').replace('\\"', '"')
        
        # Remover líneas de separación excesivas
        story_text = story_text.replace(
            '╔════════════════════════════════════════════════════════════════════════════════',
            ''
        )
        story_text = story_text.replace(
            '════════════════════════════════════════════════════════════════════════════════',
            ''
        )
        
        # Remover JSON escapes
        story_text = story_text.replace('\"', '"')
        
        # Limpiar espacios y saltos de línea múltiples
        story_text = story_text.strip()
        while '\n\n\n' in story_text:
            story_text = story_text.replace('\n\n\n', '\n\n')
        
        return story_text
    
    def split_story_text_into_individual_stories(self, story_text: str) -> List[str]:
        """
        Divide un texto que contiene múltiples historias en historias individuales
        
        Args:
            story_text: Texto que puede contener múltiples historias
            
        Returns:
            List[str]: Lista de historias individuales
        """
        if not story_text or not isinstance(story_text, str):
            return []
        
        stories = []
        
        # Buscar todas las ocurrencias de "HISTORIA #" (con diferentes variaciones)
        pattern = r'HISTORIA\s*#\s*\d+|HISTORIA\s+NO\s+FUNCIONAL\s*#\s*\d+|HISTORIA\s+#\s*\d+'
        matches = list(re.finditer(pattern, story_text, re.IGNORECASE | re.MULTILINE))
        
        if len(matches) > 1:
            # Hay múltiples historias, dividir el texto
            for i, match in enumerate(matches):
                start_pos = match.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(story_text)
                story = story_text[start_pos:end_pos].strip()
                if story and len(story) > self.MIN_STORY_LENGTH:
                    stories.append(story)
            logger.info(f"Divididas {len(stories)} historias individuales usando patrón 'HISTORIA #'")
        
        elif len(matches) == 1:
            # Solo una coincidencia, intentar buscar por separadores
            stories = self._try_split_by_separators(story_text)
            if not stories:
                stories = [story_text.strip()]
                logger.info("Una historia encontrada en el texto")
        
        else:
            # No se encontró el patrón "HISTORIA #", intentar otros métodos
            stories = self._try_split_by_separators(story_text)
            if not stories:
                stories = self._try_split_by_como_pattern(story_text)
                if not stories:
                    stories = [story_text.strip()] if story_text.strip() else []
                    logger.info("Texto tratado como una sola historia (sin separadores detectados)")
        
        return stories
    
    def _try_split_by_separators(self, text: str) -> List[str]:
        """Intenta dividir por separadores de líneas '═'"""
        parts = re.split(r'\n\s*═{20,}\s*\n', text)
        if len(parts) > 1:
            stories = [p.strip() for p in parts if p.strip() and len(p.strip()) > self.MIN_STORY_LENGTH]
            if stories:
                logger.info(f"Divididas {len(stories)} historias por separadores de líneas '═'")
            return stories
        return []
    
    def _try_split_by_como_pattern(self, text: str) -> List[str]:
        """Intenta dividir por patrones 'COMO:'"""
        como_matches = list(re.finditer(r'^\s*COMO\s*:', text, re.IGNORECASE | re.MULTILINE))
        if len(como_matches) > 1:
            stories = []
            for i, match in enumerate(como_matches):
                start_pos = match.start()
                end_pos = como_matches[i + 1].start() if i + 1 < len(como_matches) else len(text)
                story = text[start_pos:end_pos].strip()
                if story and len(story) > self.MIN_STORY_LENGTH:
                    stories.append(story)
            if stories:
                logger.info(f"Divididas {len(stories)} historias usando patrón 'COMO:'")
            return stories
        return []

