import logging
import json
import time
from typing import Dict, List, Optional

from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_fetcher import IssueFetcher
from app.backend.jira.field_validator import FieldValidator
from app.core.config import Config

logger = logging.getLogger(__name__)

class IssueCreationRateLimiter:
    """
    Rate limiter con backoff exponencial para creación de issues
    Previene throttling de Jira API
    """
    
    def __init__(self, base_delay: float = None, backoff_multiplier: float = None, max_delay: float = None):
        self._base_delay = base_delay or Config.JIRA_CREATE_ISSUE_DELAY_SECONDS
        self._backoff_multiplier = backoff_multiplier or Config.JIRA_CREATE_ISSUE_BACKOFF_MULTIPLIER
        self._max_delay = max_delay or Config.JIRA_CREATE_ISSUE_MAX_DELAY_SECONDS
        self._current_delay = self._base_delay
        self._consecutive_errors = 0
        self._last_request_time = None
        logger.info(f"RateLimiter inicializado: base_delay={self._base_delay}s, backoff={self._backoff_multiplier}x, max={self._max_delay}s")
    
    def wait(self) -> None:
        if self._last_request_time is None:
            self._last_request_time = time.time()
            return
        
        elapsed = time.time() - self._last_request_time
        required_delay = self._current_delay
        
        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            logger.debug(f"Rate limiting: esperando {wait_time:.2f}s (delay actual: {self._current_delay:.2f}s)")
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def report_success(self) -> None:
        if self._consecutive_errors > 0:
            logger.info(f"Request exitoso después de {self._consecutive_errors} errores, reseteando backoff")
        self._consecutive_errors = 0
        self._current_delay = self._base_delay
    
    def report_error(self) -> None:
        self._consecutive_errors += 1
        old_delay = self._current_delay
        self._current_delay = min(
            self._current_delay * self._backoff_multiplier,
            self._max_delay
        )
        logger.warning(
            f"Error #{self._consecutive_errors} detectado, "
            f"incrementando delay: {old_delay:.2f}s → {self._current_delay:.2f}s"
        )

class IssueCreator:
    """Servicio encargado de la creación de issues en Jira"""
    
    def __init__(self, connection: JiraConnection, project_service: ProjectService, fetcher: IssueFetcher):
        self._connection = connection
        self._project_service = project_service
        self._fetcher = fetcher
        self._rate_limiter = IssueCreationRateLimiter()

    def create_issue(self, project_key: str, issue_type: str, summary: str, description: str = None,
                     assignee: str = None, priority: str = None, labels: List[str] = None,
                     custom_fields: Dict = None, field_schemas: Dict = None) -> Dict:
        """Crea un issue en Jira"""
        self._rate_limiter.wait()
        
        try:
            url = f"{self._connection.base_url}/rest/api/3/issue"
            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "issuetype": {"name": issue_type}
                }
            }
            
            if description:
                payload["fields"]["description"] = FieldValidator.format_description_to_adf(description)
            
            if assignee:
                assignee = assignee.strip()
                if '@' in assignee:
                    account_id = self._fetcher.get_user_account_id_by_email(assignee)
                    if account_id:
                        payload["fields"]["assignee"] = {"accountId": account_id}
                    else:
                        logger.warning(f"No se pudo encontrar accountId para el email: {assignee}. El issue se creará sin asignado.")
                else:
                    payload["fields"]["assignee"] = {"accountId": assignee}
            
            if priority:
                priority_str = str(priority).strip() if priority else None
                if priority_str:
                    payload["fields"]["priority"] = {"name": priority_str}
            
            if labels:
                payload["fields"]["labels"] = labels
            
            if custom_fields:
                filtered_custom_fields = {}
                for k, v in custom_fields.items():
                    if k in ['issuetype', 'summary', 'description', 'project', 'assignee', 'priority', 'labels']:
                        logger.warning(f"Campo del sistema '{k}' encontrado en custom_fields, será ignorado")
                        continue
                    
                    if field_schemas and k in field_schemas:
                        field_info = field_schemas[k]
                        field_schema = field_info.get('schema', {})
                        allowed_values = field_info.get('allowedValues', [])
                        formatted_value = FieldValidator.format_field_value_by_type(k, str(v) if v else '', field_schema, allowed_values)
                        filtered_custom_fields[k] = formatted_value
                        logger.debug(f"Campo '{k}' formateado: {v} -> {formatted_value}")
                    else:
                        formatted_value = FieldValidator.format_field_value_by_type(k, str(v) if v else '', None, None)
                        filtered_custom_fields[k] = formatted_value
                
                if filtered_custom_fields:
                    payload["fields"].update(filtered_custom_fields)
            
            logger.debug(f"[DEBUG] Payload para crear issue: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = self._connection.session.post(url, json=payload, timeout=Config.JIRA_TIMEOUT_LONG)
            
            if response.status_code == 201:
                issue_data = response.json()
                self._rate_limiter.report_success()
                return {
                    'success': True,
                    'key': issue_data.get('key'),
                    'id': issue_data.get('id'),
                    'self': issue_data.get('self')
                }
            else:
                error_text = response.text
                error_json = {}
                errors = {}
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_json = response.json()
                        errors = error_json.get('errors', {})
                        error_messages = error_json.get('errorMessages', [])
                        logger.error(f"Error al crear issue: {response.status_code}")
                        if error_messages: logger.error(f"Mensajes de error: {error_messages}")
                        if errors:
                            for field_id, error_msg in errors.items():
                                logger.error(f"  - Campo '{field_id}': {error_msg}")
                except Exception as e:
                    logger.warning(f"No se pudo parsear la respuesta de error como JSON: {e}")
                
                # Reintento con ADF si es necesario
                adf_fields = []
                for field_id, error_msg in errors.items():
                    if 'atlassian document' in str(error_msg).lower() or 'adf' in str(error_msg).lower():
                        adf_fields.append(field_id)
                        logger.warning(f"Campo '{field_id}' requiere formato ADF: {error_msg}")
                
                if adf_fields and custom_fields:
                    logger.info(f"Detectados {len(adf_fields)} campo(s) que requieren ADF: {adf_fields}. Reintentando con formato ADF...")
                    for field_id in adf_fields:
                        if field_id in custom_fields:
                            original_value = custom_fields[field_id]
                            if isinstance(original_value, str):
                                custom_fields[field_id] = FieldValidator.format_description_to_adf(original_value)
                    
                    for field_id in adf_fields:
                        if field_id in custom_fields:
                            payload["fields"][field_id] = custom_fields[field_id]
                    
                    logger.info(f"Reintentando creación de issue con campos ADF corregidos...")
                    response = self._connection.session.post(url, json=payload, timeout=Config.JIRA_TIMEOUT_LONG)
                    
                    if response.status_code == 201:
                        issue_data = response.json()
                        logger.info(f"Issue creado exitosamente después de convertir campos a ADF: {issue_data.get('key')}")
                        self._rate_limiter.report_success()
                        return {
                            'success': True,
                            'key': issue_data.get('key'),
                            'id': issue_data.get('id'),
                            'self': issue_data.get('self')
                        }
                    else:
                        retry_error_text = response.text
                        logger.error(f"Error al crear issue después de reintento con ADF: {response.status_code} - {retry_error_text}")
                        self._rate_limiter.report_error()
                
                error_summary = []
                if errors:
                    for field_id, error_msg in errors.items():
                        error_summary.append(f"Campo '{field_id}': {error_msg}")
                
                error_message = f"Error {response.status_code}"
                if error_summary:
                    error_message += f" - {'; '.join(error_summary)}"
                elif error_text:
                    error_message += f" - {error_text[:200]}"
                
                logger.error(f"Error final al crear issue: {error_message}")
                self._rate_limiter.report_error()
                return {'success': False, 'error': error_message}
                
        except Exception as e:
            logger.error(f"Error al crear issue: {str(e)}")
            self._rate_limiter.report_error()
            return {'success': False, 'error': str(e)}

    def create_issues_from_csv(self, csv_data: List[Dict], project_key: str, 
                               field_mappings: Dict = None, default_values: Dict = None,
                               filter_issue_types: bool = True) -> Dict:
        """Crea múltiples issues en Jira desde datos CSV"""
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
                mapped_issue_type = None
                if field_mappings:
                    for csv_field, jira_field in field_mappings.items():
                        if jira_field == 'issuetype' and csv_field in row and row[csv_field]:
                            mapped_issue_type = row[csv_field].strip()
                            break
                
                if not mapped_issue_type:
                    csv_issue_type_raw = (
                        row.get('Tipo de Issue') or row.get('Tipo') or row.get('tipo de issue') or
                        row.get('TIPO DE ISSUE') or row.get('Issue Type') or row.get('issue type') or
                        row.get('ISSUE TYPE') or row.get('Issuetype') or None
                    )
                    if csv_issue_type_raw:
                        mapped_issue_type = csv_issue_type_raw.strip()
                
                if not mapped_issue_type:
                    mapped_issue_type = 'Story'
                
                csv_issue_type = mapped_issue_type
                
                summary = None
                if field_mappings:
                    for csv_field, jira_field in field_mappings.items():
                        if jira_field == 'summary' and csv_field in row:
                            summary = str(row[csv_field]).strip() if row[csv_field] else None
                            break
                
                if not summary:
                    summary = row.get('Resumen', row.get('Summary', row.get('Título', ''))).strip()
                
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
                field_schemas = None
                cache_key = f"{project_key}:{issue_type}"
                if cache_key not in field_schemas_cache:
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
                                            schema = field_info.get('schema', {})
                                            allowed_values = field_info.get('allowedValues', [])
                                            field_schemas[field_id] = {
                                                'schema': schema,
                                                'allowedValues': allowed_values
                                            }
                                        field_schemas_cache[cache_key] = field_schemas
                                        break
                        if cache_key not in field_schemas_cache:
                            field_schemas_cache[cache_key] = None
                    except Exception:
                        field_schemas_cache[cache_key] = None
                else:
                    field_schemas = field_schemas_cache[cache_key]
                
                issue_result = self.create_issue(
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
                         self._fetcher.invalidate_metadata_cache(cache_key)
                         if issue_type in available_fields_by_type:
                            del available_fields_by_type[issue_type]
                            
            except Exception as e:
                logger.error(f"Error al procesar fila {idx}: {str(e)}")
                results['failed'].append({'row': idx, 'error': str(e), 'summary': row.get('Resumen', row.get('Summary', 'N/A'))})
                results['error_count'] += 1
        
        results['success'] = results['error_count'] == 0
        logger.info(f"Carga masiva completada: {results['success_count']}/{results['total']} exitosos")
        return results
