import logging
from typing import Any, Dict, List, Optional
from app.backend.jira.field_strategies.base_strategy import FieldStrategy
from app.backend.jira.adf_converter import AdfConverter

logger = logging.getLogger(__name__)

class StringFieldStrategy(FieldStrategy):
    """
    Strategy for formatting string fields.
    """
    
    def format(self, field_id: str, field_value: str, field_schema: Dict, allowed_values: Optional[List] = None) -> Any:
        schema_custom = field_schema.get('custom', '')
        
        # Check if it requires ADF conversion
        if schema_custom and (len(field_value) > 50 or '\n' in field_value or '\t' in field_value):
            has_newlines = '\n' in field_value
            logger.debug(f"Campo '{field_id}' detectado como requeridor de ADF (longitud: {len(field_value)}, tiene saltos de línea: {has_newlines})")
            return AdfConverter.convert(field_value)
            
        return field_value
