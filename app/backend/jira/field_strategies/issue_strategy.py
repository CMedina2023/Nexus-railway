from typing import Any, Dict, List, Optional
from app.backend.jira.field_strategies.base_strategy import FieldStrategy

class IssueFieldStrategy(FieldStrategy):
    """
    Strategy for formatting issue and issuelink fields.
    """
    
    def format(self, field_id: str, field_value: str, field_schema: Dict, allowed_values: Optional[List] = None) -> Any:
        # Both issue and issuelink use {"key": value} format
        return {"key": field_value}
