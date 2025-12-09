"""
Generador de historias de usuario
Responsabilidad única: Generar historias de usuario a partir de documentos
"""
import logging
from typing import Dict, Any

from app.backend.generators.base import Generator
from app.backend.story_backend import generate_stories_with_context
from app.services.document_analyzer import DocumentAnalyzer

logger = logging.getLogger(__name__)


class StoryGenerator(Generator):
    """Genera historias de usuario desde documentos"""
    
    def __init__(self):
        self.document_analyzer = DocumentAnalyzer()
    
    def generate(self, document_text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera historias de usuario desde el documento
        
        Args:
            document_text: Texto del documento
            parameters: Parámetros (role, business_context, etc.)
            
        Returns:
            Dict con el resultado de la generación
        """
        try:
            role = parameters.get('role', 'Usuario')
            business_context = parameters.get('business_context')
            
            result = generate_stories_with_context(
                document_text, 
                role, 
                "funcionalidad", 
                business_context
            )
            
            return {"tool_used": "story_generator", "result": result}
        except Exception as e:
            logger.error(f"Error en StoryGenerator.generate: {e}")
            return {
                "error": str(e),
                "status": "error",
                "tool_used": "story_generator"
            }
    
    def can_handle(self, document_text: str, parameters: Dict[str, Any]) -> bool:
        """
        Determina si el documento puede generar historias de usuario
        
        Args:
            document_text: Texto del documento
            parameters: Parámetros
            
        Returns:
            bool: True si puede generar historias
        """
        analysis = self.document_analyzer.analyze_content(document_text)
        return analysis.get("can_generate_stories", False)
    
    def get_output_format(self) -> str:
        """Retorna el formato de salida para historias"""
        return "docx"

