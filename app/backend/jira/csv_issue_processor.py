import logging
from typing import Dict, List, Optional
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_fetcher import IssueFetcher
from app.backend.jira.field_validator import FieldValidator
from app.backend.jira.issue_creator import IssueCreator
from app.core.config import Config

logger = logging.getLogger(__name__)

class CSVIssueProcessor:
    """Servicio encargado de procesar y crear issues en Jira a partir de archivos CSV"""
    
    def __init__(self, connection: JiraConnection, project_service: ProjectService, fetcher: IssueFetcher, creator: IssueCreator):
        """
        Inicializa el procesador de CSV.
        
        Args:
            connection: Conexión con Jira.
            project_service: Servicio de proyectos.
            fetcher: Buscador de issues y metadata.
            creator: Creador de issues individuales.
        """
        self._connection = connection
        self._project_service = project_service
        self._fetcher = fetcher
        self._creator = creator

    def create_issues_from_csv(self, csv_data: List[Dict], project_key: str, 
                               field_mappings: Dict = None, default_values: Dict = None,
                               filter_issue_types: bool = True) -> Dict:
        """
        Crea múltiples issues en Jira desde datos CSV.
        
        Args:
            csv_data: Lista de diccionarios con datos de las filas del CSV.
            project_key: Clave del proyecto en Jira.
            field_mappings: Mapeo de columnas CSV a campos Jira.
            default_values: Valores por defecto para campos.
            filter_issue_types: Si se deben filtrar los tipos de issue.
            
        Returns:
            Dict con resultados de la operación (creados, fallidos, conteos).
        """
        results = {
            'success': True, 'created': [], 'failed': [],
            'total': len(csv_data), 'success_count': 0, 'error_count': 0
        }
        
        available_types = self._project_service.get_issue_types(project_key, filter_types=filter_issue_types)
        if not available_types:
            return {
                'success': False, 'error': 'No se pudieron obtener los tipos de issue del proyecto',
                'created': [], 'failed': [], 'total': len(csv_data),
                'success_count': 0, 'error_count': len(csv_data)
            }
        
        field_schemas_cache = {}
        available_fields_by_type = {}
        
        logger.info(f"Iniciando carga masiva de {len(csv_data)} issues al proyecto {project_key}")
        
        for idx, row in enumerate(csv_data, start=1):
            try:
                mapped_issue_type = self._extract_issue_type(row, field_mappings)
                if not mapped_issue_type:
                    mapped_issue_type = 'Story'
                
                csv_issue_type = mapped_issue_type
                
                summary = self._extract_summary(row, field_mappings)
                
                description = row.get('Descripción', row.get('Description', '')).strip()
                assignee = row.get('Asignado', row.get('Assignee', '')).strip() or None
                priority = row.get('Prioridad', row.get('Priority', '')).strip() or None
                labels_str = row.get('Labels', row.get('Etiquetas', '')).strip()
                labels = [l.strip() for l in labels_str.split(',')] if labels_str else None
                
                if not summary:
                    error_msg = 'El campo "Resumen" o "Summary" es requerido.'
                    results['failed'].append({'row': idx, 'error': error_msg})
                    results['error_count'] += 1
                    continue
                
                issue_type = FieldValidator.normalize_issue_type(csv_issue_type, available_types)
                if not issue_type:
                    available_names = ', '.join([it.get('name', '') for it in available_types])
                    error_msg = f'Tipo de issue "{csv_issue_type}" no válido. Tipos disponibles: {available_names}'
                    results['failed'].append({'row': idx, 'error': error_msg, 'summary': summary})
                    results['error_count'] += 1
                    continue
                
                custom_fields, description, priority = self._process_custom_fields(
                    row, field_mappings, default_values, description, priority
                )
                
                # Validación de campos
                if issue_type not in available_fields_by_type:
                    available_fields_metadata = self._fetcher.get_available_fields_metadata(project_key, issue_type, use_cache=True)
                    available_fields_by_type[issue_type] = available_fields_metadata
                else:
                    available_fields_metadata = available_fields_by_type[issue_type]
                
                if custom_fields and available_fields_metadata:
                    valid_custom_fields, filtered_fields = FieldValidator.validate_and_filter_custom_fields(
                        custom_fields, available_fields_metadata, idx
                    )
                    if filtered_fields:
                        custom_fields = valid_custom_fields
                
                # Schemas
                field_schemas = self._get_field_schemas(project_key, issue_type, field_schemas_cache)
                
                issue_result = self._creator.create_issue(
                    project_key=project_key,
                    issue_type=issue_type,
                    summary=summary,
                    description=description if description else None,
                    assignee=assignee,
                    priority=priority,
                    labels=labels,
                    custom_fields=custom_fields if custom_fields else None,
                    field_schemas=field_schemas
                )
                
                if issue_result.get('success'):
                    results['created'].append({
                        'row': idx, 'key': issue_result.get('key'),
                        'summary': summary, 'issue_type': issue_type
                    })
                    results['success_count'] += 1
                    logger.info(f"Fila {idx}: ✅ Issue creado exitosamente: {issue_result.get('key')}")
                else:
                    error_msg = issue_result.get('error', 'Error desconocido')
                    results['failed'].append({'row': idx, 'error': error_msg, 'summary': summary})
                    results['error_count'] += 1
                    logger.error(f"Fila {idx}: ❌ Error al crear issue: {error_msg}")
                    
                    error_lower = error_msg.lower()
                    if any(k in error_lower for k in ['cannot be set', 'not on the appropriate screen', 'unknown field', 'field does not exist']):
                         self._fetcher.invalidate_metadata_cache(f"{project_key}:{issue_type}")
                         if issue_type in available_fields_by_type:
                            del available_fields_by_type[issue_type]
                            
            except Exception as e:
                logger.error(f"Error al procesar fila {idx}: {str(e)}")
                results['failed'].append({'row': idx, 'error': str(e), 'summary': row.get('Resumen', row.get('Summary', 'N/A'))})
                results['error_count'] += 1
        
        results['success'] = results['error_count'] == 0
        logger.info(f"Carga masiva completada: {results['success_count']}/{results['total']} exitosos")
        return results

    def _extract_issue_type(self, row: Dict, field_mappings: Dict) -> Optional[str]:
        """Extrae el tipo de issue de la fila."""
        if field_mappings:
            for csv_field, jira_field in field_mappings.items():
                if jira_field == 'issuetype' and csv_field in row and row[csv_field]:
                    return row[csv_field].strip()
        
        return (
            row.get('Tipo de Issue') or row.get('Tipo') or row.get('tipo de issue') or
            row.get('TIPO DE ISSUE') or row.get('Issue Type') or row.get('issue type') or
            row.get('ISSUE TYPE') or row.get('Issuetype') or None
        )

    def _extract_summary(self, row: Dict, field_mappings: Dict) -> Optional[str]:
        """Extrae el resumen de la fila."""
        if field_mappings:
            for csv_field, jira_field in field_mappings.items():
                if jira_field == 'summary' and csv_field in row:
                    return str(row[csv_field]).strip() if row[csv_field] else None
        
        return row.get('Resumen', row.get('Summary', row.get('Título', ''))).strip()

    def _process_custom_fields(self, row: Dict, field_mappings: Dict, default_values: Dict, 
                             description: str, priority: str):
        """Procesa mapeos y valores por defecto."""
        custom_fields = {}
        mapped_description = None
        mapped_priority = None
        
        if field_mappings:
            for csv_field, jira_field in field_mappings.items():
                if csv_field in row and row[csv_field]:
                    if jira_field == 'issuetype': continue
                    elif jira_field == 'description': mapped_description = row[csv_field]
                    elif jira_field == 'priority': mapped_priority = row[csv_field]
                    elif jira_field in ['summary', 'project', 'assignee', 'labels']: continue
                    else: custom_fields[jira_field] = row[csv_field]
        
        if mapped_description: description = mapped_description.strip() if mapped_description else None
        if mapped_priority: priority = mapped_priority.strip() if mapped_priority else None
        
        if default_values:
            for field, value in default_values.items():
                if field not in custom_fields and field != 'issuetype':
                    custom_fields[field] = value
                    
        return custom_fields, description, priority

    def _get_field_schemas(self, project_key: str, issue_type: str, field_schemas_cache: Dict) -> Optional[Dict]:
        """Obtiene y cachea los esquemas de campos para un tipo de issue."""
        cache_key = f"{project_key}:{issue_type}"
        if cache_key in field_schemas_cache:
            return field_schemas_cache[cache_key]
            
        try:
            url = f"{self._connection.base_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&issuetypeNames={issue_type}&expand=projects.issuetypes.fields"
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
            if response.status_code == 200:
                metadata = response.json()
                projects = metadata.get('projects', [])
                if projects and projects[0].get('issuetypes'):
                    for it in projects[0]['issuetypes']:
                        if it.get('name', '').lower() == issue_type.lower():
                            fields = it.get('fields', {})
                            field_schemas = {}
                            for field_id, field_info in fields.items():
                                field_schemas[field_id] = {
                                    'schema': field_info.get('schema', {}),
                                    'allowedValues': field_info.get('allowedValues', [])
                                }
                            field_schemas_cache[cache_key] = field_schemas
                            return field_schemas
            field_schemas_cache[cache_key] = None
        except Exception:
            field_schemas_cache[cache_key] = None
            
        return None
