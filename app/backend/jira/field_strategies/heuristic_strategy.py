import logging
from typing import Any, Dict, List, Optional
from app.backend.jira.field_strategies.base_strategy import FieldStrategy
from app.backend.jira.adf_converter import AdfConverter

logger = logging.getLogger(__name__)

class HeuristicFieldStrategy(FieldStrategy):
    """
    Strategy for fields when no schema is available (heuristics based on field ID).
    """
    
    def format(self, field_id: str, field_value: str, field_schema: Dict = None, allowed_values: Optional[List] = None) -> Any:
        # Campos conocidos que requieren formato de objeto
        if field_id == 'parent' or field_id.lower() in ['parent', 'epic link', 'epiclink']:
            # Formato para parent: {"key": "NA-25"}
            return {"key": field_value}
            
        # Campo environment siempre requiere ADF
        if field_id.lower() == 'environment':
            return AdfConverter.convert(field_value)
            
        return field_value
