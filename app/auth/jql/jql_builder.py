"""
Módulo para la construcción de consultas JQL para métricas.
Responsabilidad: Transformar filtros y parámetros en queries JQL válidas.
"""
import logging
from typing import List, Optional, Tuple
from app.backend.jira.issue_service import TEST_CASE_VARIATIONS, BUG_VARIATIONS, build_issuetype_jql

logger = logging.getLogger(__name__)

class JQLBuilder:
    """Clase especializada en construir consultas JQL para Jira."""

    @staticmethod
    def build_jql_from_filters(project_key: str, view_type: str, filters: List[str], assignee_email: Optional[str] = None) -> str:
        """
        Construye un JQL query desde los filtros proporcionados.
        
        Args:
            project_key: Clave del proyecto.
            view_type: Tipo de vista (general/personal).
            filters: Lista de filtros en formato "field:value".
            assignee_email: Email del asignado (para vista personal).
            
        Returns:
            str: JQL query construido.
        """
        base_jql = f'project = {project_key}'
        
        if view_type == 'personal' and assignee_email:
            base_jql += f' AND assignee = "{assignee_email}"'
        
        jql_parts = [base_jql]
        
        # Filtro de issue types (siempre) - SOLO Test Cases y Bugs
        test_case_conditions = ' OR '.join([f'issuetype = "{var}"' for var in TEST_CASE_VARIATIONS])
        bug_conditions = ' OR '.join([f'issuetype = "{var}"' for var in BUG_VARIATIONS])
        issuetype_filter = f'({test_case_conditions} OR {bug_conditions})'
        jql_parts.append(issuetype_filter)
        
        # Procesar filtros adicionales
        additional_parts = JQLBuilder._process_filter_params(filters, project_key)
        jql_parts.extend(additional_parts)
        
        final_jql = ' AND '.join(jql_parts)
        logger.info(f"[JQLBuilder] JQL construido: {final_jql}")
        return final_jql

    @staticmethod
    def build_separate_jql_queries(project_key: str, view_type: str, filters: List[str], assignee_email: Optional[str] = None) -> Tuple[str, str]:
        """
        Construye dos JQL queries separados: uno para Test Cases y otro para Bugs.
        
        Args:
            project_key: Clave del proyecto.
            view_type: Tipo de vista (general/personal).
            filters: Lista de filtros en formato "field:value".
            assignee_email: Email del asignado (para vista personal).
            
        Returns:
            Tuple[str, str]: (jql_test_cases, jql_bugs)
        """
        base_jql = f'project = {project_key}'
        
        if view_type == 'personal' and assignee_email:
            base_jql += f' AND assignee = "{assignee_email}"'
        
        # Construir filtros adicionales
        additional_filters = JQLBuilder._process_filter_params(filters, project_key)
        
        # Construir JQL para Test Cases
        test_case_conditions = ' OR '.join([f'issuetype = "{var}"' for var in TEST_CASE_VARIATIONS])
        jql_test_cases_parts = [base_jql, f'({test_case_conditions})']
        jql_test_cases_parts.extend(additional_filters)
        jql_test_cases = ' AND '.join(jql_test_cases_parts)
        
        # Construir JQL para Bugs
        bug_conditions = ' OR '.join([f'issuetype = "{var}"' for var in BUG_VARIATIONS])
        jql_bugs_parts = [base_jql, f'({bug_conditions})']
        jql_bugs_parts.extend(additional_filters)
        jql_bugs = ' AND '.join(jql_bugs_parts)
        
        return jql_test_cases, jql_bugs

    @staticmethod
    def _process_filter_params(filters: List[str], project_key: str) -> List[str]:
        """Procesa los parámetros de filtro y los convierte en fragmentos JQL."""
        jql_parts = []
        for filter_param in filters:
            field, value = JQLBuilder._split_filter(filter_param)
            if not field:
                continue
            
            condition = JQLBuilder._build_field_condition(field, value, project_key)
            if condition:
                jql_parts.append(condition)
        return jql_parts

    @staticmethod
    def _split_filter(filter_param: str) -> Tuple[Optional[str], Optional[str]]:
        """Divide un parámetro de filtro en campo y valor."""
        if ':' in filter_param:
            parts = filter_param.split(':', 1)
        elif '=' in filter_param:
            parts = filter_param.split('=', 1)
        else:
            logger.warning(f"Formato de filtro inválido: {filter_param}")
            return None, None
        
        return parts[0].strip(), parts[1].strip()

    @staticmethod
    def _build_field_condition(field: str, value: str, project_key: str) -> Optional[str]:
        """Construye una condición JQL para un campo específico."""
        field_lower = field.lower()
        
        if field_lower in ['status', 'estado']:
            return f'status = "{value}"'
        if field_lower in ['priority', 'prioridad']:
            return f'priority = "{value}"'
        if field_lower in ['assignee', 'asignado']:
            return f'assignee = "{value}"'
        if field_lower in ['issuetype', 'tipo']:
            issuetype_jql = build_issuetype_jql(value, project_key)
            if ' AND (' in issuetype_jql:
                issuetype_condition = issuetype_jql.split(' AND (', 1)[1].rstrip(')')
                return f'({issuetype_condition})'
            return f'issuetype = "{value}"'
        if field_lower in ['label', 'labels', 'etiqueta', 'etiquetas']:
            return f'labels = "{value}"'
        if field_lower in ['affectedversion', 'affectsversions', 'affects version']:
            return f'affectedVersion = "{value}"'
        if field_lower in ['fixversions', 'version de correccion', 'version', 'versión']:
            return f'fixVersions = "{value}"'
        
        # Campos personalizados o estándar por nombre
        if field.startswith('customfield_'):
            return f'{field} = "{value}"'
        
        return f'"{field}" = "{value}"'
