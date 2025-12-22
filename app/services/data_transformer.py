"""
Servicio para transformación y normalización de datos
Responsabilidad única: Transformación de datos entre formatos
"""
import json
import logging
from typing import Any, List, Dict, Optional

logger = logging.getLogger(__name__)

from app.services.text_processor import TextProcessor


class DataTransformer:
    """Transforma y normaliza datos de diferentes formatos"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def clean_matrix_data(self, matrix_data: Any) -> List[Dict]:
        """
        Limpia y normaliza los datos de la matriz de pruebas
        
        Args:
            matrix_data: Datos de matriz en cualquier formato (dict, list, string)
            
        Returns:
            List[Dict]: Lista de casos de prueba normalizados
        """
        cleaned_data = []
        
        if not matrix_data:
            return cleaned_data
        
        # Si es un string, intentar parsearlo como JSON
        if isinstance(matrix_data, str):
            try:
                matrix_data = json.loads(matrix_data)
            except json.JSONDecodeError:
                logger.error("Los datos de matriz son un string pero no es JSON válido")
                return cleaned_data
        
        # Si es un diccionario, buscar la lista de casos de prueba
        if isinstance(matrix_data, dict):
            matrix_data = self._extract_list_from_dict(matrix_data)
            if not matrix_data:
                return cleaned_data
        
        # Asegurarse de que es una lista
        if not isinstance(matrix_data, list):
            matrix_data = [matrix_data]
        
        # Limpiar y normalizar cada item
        for item in matrix_data:
            if isinstance(item, dict):
                cleaned_item = self._normalize_test_case(item, len(cleaned_data))
                cleaned_data.append(cleaned_item)
            else:
                logger.warning(f"Elemento ignorado en clean_matrix_data: {type(item)} - {str(item)[:100]}")
        
        return cleaned_data
    
    def _extract_list_from_dict(self, data: Dict) -> Optional[List]:
        """Extrae la lista de casos de prueba de un diccionario"""
        # Buscar claves que contengan la lista de casos
        matrix_keys = ['matrix', 'test_cases', 'cases', 'test_cases_list', 'data']
        for key in matrix_keys:
            if key in data and isinstance(data[key], list):
                logger.info(f"Encontrados datos en clave: {key}")
                return data[key]
        
        # Si es un diccionario de caso individual, convertirlo a lista
        if any(k in data for k in ['id_caso_prueba', 'titulo_caso_prueba', 'Descripcion', 'id', 'title']):
            logger.info("Convertido diccionario de caso individual a lista")
            return [data]
        
        # Buscar recursivamente en valores del diccionario
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                logger.info(f"Encontrados datos en clave recursiva: {key}")
                return value
        
        logger.warning("No se pudo encontrar lista de casos en el diccionario")
        return None
    
    def _normalize_test_case(self, item: Dict, index: int) -> Dict:
        """
        Normaliza un caso de prueba individual.
        Mapea variaciones de llaves a la nomenclatura estándar del sistema
        y preserva la estructura de los datos para su validación posterior.
        """
        # Mapeo de variaciones de llaves a estándar (utilizado por el validador y exportador)
        standard_map = {
            'id_caso_prueba': 'id_caso_prueba',
            'id': 'id_caso_prueba',
            'titulo_caso_prueba': 'titulo_caso_prueba',
            'titulo': 'titulo_caso_prueba',
            'summary': 'titulo_caso_prueba',
            'descripcion': 'Descripcion',
            'description': 'Descripcion',
            'precondiciones': 'Precondiciones',
            'preconditions': 'Precondiciones',
            'tipo_de_prueba': 'Tipo_de_prueba',
            'tipo_prueba': 'Tipo_de_prueba',
            'test_type': 'Tipo_de_prueba',
            'nivel_de_prueba': 'Nivel_de_prueba',
            'test_level': 'Nivel_de_prueba',
            'tipo_de_ejecucion': 'Tipo_de_ejecucion',
            'execution_type': 'Tipo_de_ejecucion',
            'pasos': 'Pasos',
            'steps': 'Pasos',
            'resultado_esperado': 'Resultado_esperado',
            'expected_result': 'Resultado_esperado',
            'resultado': 'Resultado_esperado',
            'categoria': 'Categoria',
            'category': 'Categoria',
            'ambiente': 'Ambiente',
            'environment': 'Ambiente',
            'ciclo': 'Ciclo',
            'cycle': 'Ciclo',
            'issuetype': 'issuetype',
            'prioridad': 'Prioridad',
            'priority': 'Prioridad',
            'historia_de_usuario': 'historia_de_usuario',
            'user_story': 'historia_de_usuario'
        }
        
        cleaned_item = {}
        processed_keys = set()
        
        # 1. Aplicar mapeo estándar
        for key, value in item.items():
            key_lower = key.lower().replace(' ', '_').replace('-', '_')
            target_key = standard_map.get(key_lower)
            
            if target_key:
                # Si ya procesamos esta llave (ej: vino 'steps' y 'pasos'), priorizar la última
                cleaned_item[target_key] = value
                processed_keys.add(target_key)
            else:
                # Mantener llaves no reconocidas pero normalizadas
                cleaned_item[key_lower] = value
        
        # 2. Asegurar campos mínimos y tipos correctos (sin colapsar listas aún)
        if 'id_caso_prueba' not in cleaned_item:
            cleaned_item['id_caso_prueba'] = f"TC{index + 1:03d}"
            
        # El validador espera que Pasos y Resultado_esperado sean listas para validación semántica
        for field in ['Pasos', 'Resultado_esperado']:
            if field in cleaned_item and isinstance(cleaned_item[field], str):
                val_str = cleaned_item[field]
                # Intentar separar si viene como string con saltos de línea, números o viñetas
                items = [s.strip() for s in re.split(r'\d+\.|\n-|\n•|\r\n-|\r\n•', val_str) if s.strip()]
                if not items:
                    items = [s.strip() for s in val_str.split('\n') if s.strip()]
                cleaned_item[field] = items if items else [val_str]
            elif field not in cleaned_item:
                cleaned_item[field] = []
            
        return cleaned_item
    
    def extract_stories_from_result(self, result: Any) -> List[str]:
        """
        Extrae las historias de usuario del resultado del agente
        
        Args:
            result: Resultado del agente en cualquier formato
            
        Returns:
            List[str]: Lista de historias extraídas
        """
        if isinstance(result, dict):
            return self._extract_stories_from_dict(result)
        elif isinstance(result, list):
            return result  # Ya es una lista de historias
        elif isinstance(result, str):
            return self.text_processor.split_story_text_into_individual_stories(result)
        else:
            logger.warning(f"Tipo de resultado no soportado: {type(result)}")
            return []
    
    def _extract_stories_from_dict(self, result_dict: Dict) -> List[str]:
        """Extrae historias de un diccionario"""
        # Buscar en result.stories
        nested_stories = self._get_nested_value(result_dict, ['result', 'stories'])
        if nested_stories:
            return self._process_story_list(nested_stories)
        
        # Buscar en result.story (singular)
        nested_story = self._get_nested_value(result_dict, ['result', 'story'])
        if nested_story:
            return self.text_processor.split_story_text_into_individual_stories(nested_story)
        
        # Buscar directamente en stories
        if 'stories' in result_dict:
            return self._process_story_list(result_dict['stories'])
        
        # Buscar en result.story si está en el resultado directamente
        if 'story' in result_dict:
            story = result_dict['story']
            if isinstance(story, str):
                return self.text_processor.split_story_text_into_individual_stories(story)
        
        # Buscar en cualquier clave que contenga 'story'
        for key, value in result_dict.items():
            if isinstance(value, list) and value:
                first_item = value[0]
                if isinstance(first_item, str) and any(
                    marker in first_item.lower() 
                    for marker in ['como', 'quiero', 'para', 'historia']
                ):
                    return self._process_story_list(value)
            elif isinstance(value, str) and any(
                marker in value.lower() 
                for marker in ['historia #', 'historia#', 'como', 'quiero', 'para']
            ):
                stories = self.text_processor.split_story_text_into_individual_stories(value)
                if stories:
                    return stories
        
        return []
    
    def _get_nested_value(self, data: Dict, path: List[str]) -> Any:
        """Obtiene un valor de una ruta anidada"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _process_story_list(self, stories: List) -> List[str]:
        """Procesa una lista de historias"""
        if len(stories) == 1 and isinstance(stories[0], str) and len(stories[0]) > 500:
            # String largo que puede contener múltiples historias
            return self.text_processor.split_story_text_into_individual_stories(stories[0])
        return [self.text_processor.clean_story_text(s) if isinstance(s, str) else str(s) 
                for s in stories if s]

