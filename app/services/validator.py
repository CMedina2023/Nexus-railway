"""
Servicio para validación de datos
Responsabilidad única: Validar historias de usuario y casos de prueba
"""
import logging
from typing import List, Dict, Tuple, Optional

from app.core.config import Config

logger = logging.getLogger(__name__)


class Validator:
    """Valida historias de usuario y casos de prueba"""
    
    def validate_stories(
        self, 
        stories_content: List[str]
    ) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Valida y filtra historias válidas
        
        Args:
            stories_content: Lista de historias a validar
            
        Returns:
            Tuple[Optional[List[str]], Optional[str]]: 
            - (historias_válidas, None) si hay historias válidas
            - (None, mensaje_error) si no hay historias válidas
        """
        if not stories_content or len(stories_content) == 0:
            return None, "No se generaron historias de usuario"
        
        valid_stories = [
            s for s in stories_content 
            if s and s.strip() and len(s.strip()) > Config.MIN_RESPONSE_LENGTH
        ]
        
        if not valid_stories:
            return None, "Todas las historias generadas están vacías o son inválidas"
        
        logger.info(f"Validadas {len(valid_stories)} historias de {len(stories_content)} totales")
        return valid_stories, None
    
    def validate_test_cases(
        self, 
        test_cases: List[Dict]
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Valida y filtra casos de prueba válidos
        
        Args:
            test_cases: Lista de casos de prueba a validar
            
        Returns:
            Tuple[Optional[List[Dict]], Optional[str]]: 
            - (casos_válidos, None) si hay casos válidos
            - (None, mensaje_error) si no hay casos válidos
        """
        if not test_cases or len(test_cases) == 0:
            return None, "No se generaron casos de prueba"
        
        valid_cases = []
        for case in test_cases:
            if isinstance(case, dict):
                has_title = case.get('titulo_caso_prueba', '').strip()
                has_desc = case.get('Descripcion', '').strip()
                if has_title or has_desc:
                    valid_cases.append(case)
        
        if not valid_cases:
            return None, "Todos los casos de prueba generados están vacíos"
        
        logger.info(f"Validados {len(valid_cases)} casos de {len(test_cases)} totales")
        return valid_cases, None

