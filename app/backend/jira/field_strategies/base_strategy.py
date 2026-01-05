from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class FieldStrategy(ABC):
    """
    Abstract base strategy for field formatting.
    """
    
    @abstractmethod
    def format(self, field_id: str, field_value: str, field_schema: Dict, allowed_values: Optional[List] = None) -> Any:
        """
        Formats the field value according to the strategy.
        """
        pass
