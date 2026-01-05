import logging
from typing import Any, Dict, List, Optional
from app.backend.jira.field_strategies.base_strategy import FieldStrategy

logger = logging.getLogger(__name__)

class OptionFieldStrategy(FieldStrategy):
    """
    Strategy for formatting option fields (select/dropdown).
    """
    
    DEFAULT_VALUES_MAP = {
        'tipo de prueba': 'Funcional',
        'tipo_prueba': 'Funcional',
        'test type': 'Funcional',
        'nivel de prueba': 'UAT',
        'nivel_prueba': 'UAT',
        'test level': 'UAT',
        'environment': 'QA',
        'ambiente': 'QA',
        'entorno': 'QA'
    }

    def format(self, field_id: str, field_value: str, field_schema: Dict, allowed_values: Optional[List] = None) -> Any:
        if not allowed_values:
            return {"name": field_value}

        # 1. Try with original value
        result = self._find_value_in_allowed(field_value, allowed_values)
        if result:
            return result

        # 2. Try with default values
        default_value = self._get_default_value(field_id)
        if default_value:
            logger.info(f"Valor '{field_value}' no encontrado para campo '{field_id}', intentando con valor por defecto '{default_value}'")
            result = self._find_value_in_allowed(default_value, allowed_values)
            if result:
                return result

        logger.warning(f"Valor '{field_value}' y valor por defecto '{default_value}' no encontrados en allowedValues para campo '{field_id}'.")
        return None

    def _get_default_value(self, field_id: str) -> Optional[str]:
        field_id_lower = field_id.lower()
        for key, default in self.DEFAULT_VALUES_MAP.items():
            if key in field_id_lower:
                return default
        return None

    def _find_value_in_allowed(self, value_to_find: str, allowed_values: List) -> Optional[Dict[str, str]]:
        if not value_to_find:
            return None
            
        value_lower = value_to_find.lower()
        
        for av in allowed_values:
            if isinstance(av, dict):
                av_name = av.get('value', av.get('name', ''))
                av_id = av.get('id')
                if av_name and av_name.lower() == value_lower:
                    if av_id:
                        return {"id": str(av_id)}
                    return {"name": av_name}
            elif isinstance(av, str):
                if av.lower() == value_lower:
                    return {"name": av}
        return None
