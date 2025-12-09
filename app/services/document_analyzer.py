"""
Servicio para análisis de contenido de documentos
Responsabilidad única: Analizar documentos para determinar qué se puede generar
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """Analiza el contenido de documentos para determinar capacidades de generación"""
    
    # Palabras clave para historias de usuario
    STORY_KEYWORDS = [
        'como', 'quiero', 'para', 'usuario', 'historia', 'requerimiento',
        'funcionalidad', 'feature', 'user story', 'criterio de aceptación'
    ]
    
    # Palabras clave para matriz de pruebas
    MATRIX_KEYWORDS = [
        'prueba', 'test', 'caso', 'escenario', 'validación', 'verificación',
        'matriz', 'matrix', 'test case', 'condición', 'resultado esperado'
    ]
    
    # Umbral mínimo de caracteres para considerar un documento válido
    MIN_DOCUMENT_LENGTH = 100
    
    # Umbral mínimo de palabras clave encontradas
    MIN_KEYWORD_COUNT = 2
    
    def analyze_content(self, document_text: str) -> Dict:
        """
        Analiza el contenido del documento para determinar qué se puede generar
        
        Args:
            document_text: Texto del documento a analizar
            
        Returns:
            Dict con información sobre qué se puede generar:
            - can_generate_stories: bool
            - can_generate_matrix: bool
            - story_keywords_found: int
            - matrix_keywords_found: int
            - document_length: int
        """
        text_lower = document_text.lower()
        
        # Contar palabras clave encontradas
        story_score = sum(1 for keyword in self.STORY_KEYWORDS if keyword in text_lower)
        matrix_score = sum(1 for keyword in self.MATRIX_KEYWORDS if keyword in text_lower)
        
        # Determinar qué se puede generar
        can_generate_stories = (
            story_score >= self.MIN_KEYWORD_COUNT or 
            len(document_text) > self.MIN_DOCUMENT_LENGTH
        )
        
        can_generate_matrix = (
            matrix_score >= self.MIN_KEYWORD_COUNT or 
            len(document_text) > self.MIN_DOCUMENT_LENGTH
        )
        
        result = {
            "can_generate_stories": can_generate_stories,
            "can_generate_matrix": can_generate_matrix,
            "story_keywords_found": story_score,
            "matrix_keywords_found": matrix_score,
            "document_length": len(document_text)
        }
        
        logger.debug(f"Análisis de documento: {result}")
        
        return result

