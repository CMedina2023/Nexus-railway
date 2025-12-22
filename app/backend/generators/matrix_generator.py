"""
Generador de matrices de prueba
Responsabilidad única: Generar matrices de casos de prueba desde documentos
"""
import logging
from typing import Dict, Any, List

from app.backend.generators.base import Generator
from app.backend.matrix_backend import generar_matriz_test
from app.services.document_analyzer import DocumentAnalyzer

logger = logging.getLogger(__name__)


class MatrixGenerator(Generator):
    """Genera matrices de casos de prueba desde documentos"""
    
    def __init__(self):
        self.document_analyzer = DocumentAnalyzer()
    
    def generate(self, document_text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera matriz de casos de prueba desde el documento
        
        Args:
            document_text: Texto del documento
            parameters: Parámetros (context, flow, user_story, test_types, etc.)
            
        Returns:
            Dict con el resultado de la generación
        """
        try:
            context = parameters.get('context', '')
            flow = parameters.get('flow', '')
            user_story = parameters.get('user_story', '')
            test_types = parameters.get('test_types', ['funcional'])
            
            if not isinstance(test_types, list):
                test_types = [test_types] if test_types else ['funcional']
            
            skip_healing = parameters.get('skip_healing', True)  # ✅ Desactivado por defecto
            
            result = generar_matriz_test(
                context, 
                flow, 
                user_story, 
                document_text, 
                test_types,
                skip_healing=skip_healing
            )
            
            return {"tool_used": "matrix_generator", "result": result}
        except Exception as e:
            logger.error(f"Error en MatrixGenerator.generate: {e}")
            return {
                "error": str(e),
                "status": "error",
                "tool_used": "matrix_generator"
            }
    
    def can_handle(self, document_text: str, parameters: Dict[str, Any]) -> bool:
        """
        Determina si el documento puede generar matrices de prueba
        
        Args:
            document_text: Texto del documento
            parameters: Parámetros
            
        Returns:
            bool: True si puede generar matrices
        """
        analysis = self.document_analyzer.analyze_content(document_text)
        return analysis.get("can_generate_matrix", False)
    
    def get_output_format(self) -> str:
        """Retorna el formato de salida para matrices"""
        return "zip"

