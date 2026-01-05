import logging
from typing import Dict, List, Optional, Tuple, Any
from app.backend.jira.adf_converter import AdfConverter
from app.backend.jira.field_strategies.string_strategy import StringFieldStrategy
from app.backend.jira.field_strategies.option_strategy import OptionFieldStrategy
from app.backend.jira.field_strategies.array_strategy import ArrayFieldStrategy
from app.backend.jira.field_strategies.issue_strategy import IssueFieldStrategy
from app.backend.jira.field_strategies.heuristic_strategy import HeuristicFieldStrategy

logger = logging.getLogger(__name__)

class FieldValidator:
    """
    Clase utilitaria para validación y formateo de campos de Jira
    """

    @staticmethod
    def format_field_value_by_type(field_id: str, field_value: str, field_schema: Dict = None, allowed_values: List = None) -> Any:
        """
        Formatea un valor de campo según su tipo de schema en Jira
        
        Args:
            field_id: ID del campo en Jira
            field_value: Valor del campo (string del CSV)
            field_schema: Schema del campo obtenido de Jira (opcional)
            allowed_values: Lista de valores permitidos para campos option (opcional)
            
        Returns:
            Valor formateado según el tipo de campo
        """
        if not field_value or not field_value.strip():
            return None
        
        field_value = field_value.strip()
        
        # Si no hay schema, intentar detectar por el nombre del campo (heurística)
        if not field_schema:
            return HeuristicFieldStrategy().format(field_id, field_value, {}, allowed_values)
        
        schema_type = field_schema.get('type', 'string')
        
        # Seleccionar estrategia según el tipo
        strategy = None
        if schema_type == 'string':
            strategy = StringFieldStrategy()
        elif schema_type == 'option':
            strategy = OptionFieldStrategy()
        elif schema_type == 'array':
            strategy = ArrayFieldStrategy()
        elif schema_type in ['issue', 'issuelink']:
            strategy = IssueFieldStrategy()
            
        if strategy:
            return strategy.format(field_id, field_value, field_schema, allowed_values)
            
        return field_value

    @staticmethod
    def format_description_to_adf(description: str) -> Dict:
        """
        Convierte una descripción con formato markdown simple a formato ADF de Jira.
        Delegates to AdfConverter.
        """
        return AdfConverter.convert(description)

    @staticmethod
    def validate_and_filter_custom_fields(
        custom_fields: Dict, 
        available_fields_metadata: Dict,
        row_idx: int
    ) -> Tuple[Dict, List[str]]:
        """
        Valida campos personalizados contra metadata de Jira
        """
        if not custom_fields:
            return {}, []
        
        if not available_fields_metadata:
            logger.warning(f"Fila {row_idx}: No hay metadata disponible, no se puede validar campos. Continuando sin validación.")
            return custom_fields, []
        
        valid_fields = {}
        filtered_fields = []
        
        for field_id, field_value in custom_fields.items():
            if field_id not in available_fields_metadata:
                logger.warning(f"Fila {row_idx}: Campo '{field_id}' no está disponible en la pantalla de creación, será omitido")
                filtered_fields.append(field_id)
                continue
            
            field_info = available_fields_metadata[field_id]
            operations = field_info.get('operations', [])
            if 'set' not in operations:
                logger.warning(f"Fila {row_idx}: Campo '{field_id}' ({field_info.get('name', 'N/A')}) es read-only, será omitido")
                filtered_fields.append(field_id)
                continue
            
            valid_fields[field_id] = field_value
        
        if filtered_fields:
            logger.info(f"Fila {row_idx}: {len(filtered_fields)} campo(s) filtrado(s) (no disponibles o read-only): {filtered_fields}")
        
        return valid_fields, filtered_fields

    @staticmethod
    def normalize_issue_type(csv_type: str, available_types: List[Dict]) -> Optional[str]:
        """
        Normaliza el nombre del tipo de issue del CSV al nombre exacto que Jira espera.
        """
        if not csv_type or not available_types:
            logger.warning(f"Tipo de issue vacío o sin tipos disponibles. CSV type: '{csv_type}'")
            return None
        
        csv_type_clean = csv_type.strip()
        csv_type_lower = csv_type_clean.lower()
        
        # 1. Coincidencia exacta
        for issue_type in available_types:
            type_name = issue_type.get('name', '').strip()
            if type_name.lower() == csv_type_lower:
                return type_name
        
        # 2. Keywords
        if 'test' in csv_type_lower and 'case' in csv_type_lower:
            for issue_type in available_types:
                type_name = issue_type.get('name', '').strip()
                type_name_lower = type_name.lower()
                if 'test' in type_name_lower and 'case' in type_name_lower:
                    logger.info(f"Coincidencia por palabras clave (test+case): '{csv_type_clean}' -> '{type_name}'")
                    return type_name
        
        if 'story' in csv_type_lower or 'historia' in csv_type_lower:
            for issue_type in available_types:
                type_name = issue_type.get('name', '').strip()
                type_name_lower = type_name.lower()
                if 'story' in type_name_lower or 'historia' in type_name_lower:
                    logger.info(f"Coincidencia por palabra clave (story/historia): '{csv_type_clean}' -> '{type_name}'")
                    return type_name
        
        if 'bug' in csv_type_lower:
            for issue_type in available_types:
                type_name = issue_type.get('name', '').strip()
                type_name_lower = type_name.lower()
                if 'bug' in type_name_lower:
                    logger.info(f"Coincidencia por palabra clave (bug): '{csv_type_clean}' -> '{type_name}'")
                    return type_name
        
        logger.warning(f"No se encontró coincidencia para '{csv_type_clean}'.")
        return None
