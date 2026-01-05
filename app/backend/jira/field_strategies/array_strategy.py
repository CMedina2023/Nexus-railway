import logging
from typing import Any, Dict, List, Optional
from app.backend.jira.field_strategies.base_strategy import FieldStrategy

logger = logging.getLogger(__name__)

class ArrayFieldStrategy(FieldStrategy):
    """
    Strategy for formatting array fields.
    """
    
    def format(self, field_id: str, field_value: str, field_schema: Dict, allowed_values: Optional[List] = None) -> Any:
        schema_items = field_schema.get('items', {})
        item_type = schema_items.get('type')
        
        if item_type == 'option':
            return self._format_option_array(field_value, allowed_values)
        
        if item_type in ['issue', 'issuelink']:
            return self._format_issue_array(field_value)
            
        # Fallback for unknown item types, though unlikely to be hit based on original code
        if ',' in field_value:
             return [v.strip() for v in field_value.split(',')]
        return [field_value]

    def _format_option_array(self, field_value: str, allowed_values: Optional[List]) -> List[Dict]:
        values = [v.strip() for v in field_value.split(',')] if ',' in field_value else [field_value]
        formatted_values = []
        
        for val in values:
            if not val:
                continue
                
            found_match = None
            if allowed_values:
                found_match = self._find_option_match(val, allowed_values)
                
            if found_match:
                formatted_values.append(found_match)
            else:
                formatted_values.append({"name": val})
                
        return formatted_values

    def _format_issue_array(self, field_value: str) -> List[Dict]:
        values = [v.strip() for v in field_value.split(',')] if ',' in field_value else [field_value]
        return [{"key": val} for val in values if val]

    def _find_option_match(self, value: str, allowed_values: List) -> Optional[Dict]:
        value_lower = value.lower()
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
