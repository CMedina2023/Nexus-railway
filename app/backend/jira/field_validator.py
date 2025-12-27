import logging
import json
from typing import Dict, List, Optional, Tuple, Any

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
        
        # Si no hay schema, intentar detectar por el nombre del campo
        if not field_schema:
            # Campos conocidos que requieren formato de objeto
            if field_id == 'parent' or field_id.lower() in ['parent', 'epic link', 'epiclink']:
                # Formato para parent: {"key": "NA-25"}
                return {"key": field_value}
            # Campo environment siempre requiere ADF
            if field_id.lower() == 'environment':
                return FieldValidator.format_description_to_adf(field_value)
            return field_value
        
        schema_type = field_schema.get('type', 'string')
        schema_items = field_schema.get('items', {})
        schema_custom = field_schema.get('custom', '')
        
        # Campo de tipo "string" con schema custom que requiere ADF
        if schema_type == 'string' and schema_custom:
            if len(field_value) > 50 or '\n' in field_value or '\t' in field_value:
                has_newlines = '\n' in field_value
                logger.debug(f"Campo '{field_id}' detectado como requeridor de ADF (longitud: {len(field_value)}, tiene saltos de línea: {has_newlines})")
                return FieldValidator.format_description_to_adf(field_value)
        
        # Campo de tipo "option" (select/dropdown)
        if schema_type == 'option':
            default_values_map = {
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
            
            if allowed_values:
                # Primero intentar con el valor original
                for av in allowed_values:
                    if isinstance(av, dict):
                        av_name = av.get('value', av.get('name', ''))
                        av_id = av.get('id')
                        if av_name and av_name.lower() == field_value.lower():
                            if av_id:
                                return {"id": str(av_id)}
                            return {"name": av_name}
                    elif isinstance(av, str):
                        if av.lower() == field_value.lower():
                            return {"name": av}
                
                # Intentar con valores por defecto
                field_id_lower = field_id.lower()
                default_value = None
                for key, default in default_values_map.items():
                    if key in field_id_lower:
                        default_value = default
                        break
                
                if default_value:
                    logger.info(f"Valor '{field_value}' no encontrado para campo '{field_id}', intentando con valor por defecto '{default_value}'")
                    for av in allowed_values:
                        if isinstance(av, dict):
                            av_name = av.get('value', av.get('name', ''))
                            av_id = av.get('id')
                            if av_name and av_name.lower() == default_value.lower():
                                if av_id:
                                    return {"id": str(av_id)}
                                return {"name": av_name}
                        elif isinstance(av, str):
                            if av.lower() == default_value.lower():
                                return {"name": av}
                
                logger.warning(f"Valor '{field_value}' y valor por defecto '{default_value}' no encontrados en allowedValues para campo '{field_id}'.")
                return None
            
            return {"name": field_value}
        
        # Array de options
        if schema_type == 'array' and schema_items.get('type') == 'option':
            if ',' in field_value:
                values = [v.strip() for v in field_value.split(',')]
                formatted_values = []
                for val in values:
                    if val:
                        found = False
                        if allowed_values:
                            for av in allowed_values:
                                if isinstance(av, dict):
                                    av_name = av.get('value', av.get('name', ''))
                                    av_id = av.get('id')
                                    if av_name and av_name.lower() == val.lower():
                                        if av_id:
                                            formatted_values.append({"id": str(av_id)})
                                        else:
                                            formatted_values.append({"name": av_name})
                                        found = True
                                        break
                                elif isinstance(av, str):
                                    if av.lower() == val.lower():
                                        formatted_values.append({"name": av})
                                        found = True
                                        break
                        if not found:
                            formatted_values.append({"name": val})
                return formatted_values
            else:
                if allowed_values:
                    for av in allowed_values:
                        if isinstance(av, dict):
                            av_name = av.get('value', av.get('name', ''))
                            av_id = av.get('id')
                            if av_name and av_name.lower() == field_value.lower():
                                if av_id:
                                    return [{"id": str(av_id)}]
                                return [{"name": av_name}]
                        elif isinstance(av, str):
                            if av.lower() == field_value.lower():
                                return [{"name": av}]
                return [{"name": field_value}]
        
        # Campo de tipo "issue"
        if schema_type == 'issue':
            return {"key": field_value}
        
        # Campo de tipo "issuelink"
        if schema_type == 'issuelink':
            return {"key": field_value}
        
        # Array de issues
        if schema_type == 'array' and schema_items.get('type') == 'issue':
            if ',' in field_value:
                keys = [k.strip() for k in field_value.split(',')]
                return [{"key": key} for key in keys if key]
            else:
                return [{"key": field_value}]
        
        # Array de issuelinks
        if schema_type == 'array' and schema_items.get('type') == 'issuelink':
            if ',' in field_value:
                keys = [k.strip() for k in field_value.split(',')]
                return [{"key": key} for key in keys if key]
            else:
                return [{"key": field_value}]
        
        return field_value

    @staticmethod
    def format_description_to_adf(description: str) -> Dict:
        """
        Convierte una descripción con formato markdown simple a formato ADF de Jira.
        """
        if not description:
            return {
                "type": "doc",
                "version": 1,
                "content": []
            }
        
        lines = description.split('\n')
        adf_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                adf_content.append({
                    "type": "paragraph",
                    "content": []
                })
                continue
            
            if line.startswith('* '):
                text = line[2:].strip()
                if ':' in text:
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        label = parts[0].strip()
                        value = parts[1].strip()
                        adf_content.append({
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "* ", "marks": []},
                                {"type": "text", "text": f"{label}:", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f" {value}", "marks": []}
                            ]
                        })
                    else:
                        adf_content.append({
                            "type": "paragraph",
                            "content": [{"type": "text", "text": f"* {text}", "marks": []}]
                        })
                else:
                    adf_content.append({
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"* {text}", "marks": []}]
                    })
            elif line.startswith('  • ') or line.startswith('• '):
                text = line.replace('•', '').strip()
                adf_content.append({
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "  • ", "marks": []},
                        {"type": "text", "text": text, "marks": []}
                    ]
                })
            else:
                adf_content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": line, "marks": []}]
                })
        
        return {
            "type": "doc",
            "version": 1,
            "content": adf_content
        }

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
