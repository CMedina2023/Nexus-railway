import logging
import json
from typing import Dict, List, Optional

from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_fetcher import IssueFetcher
from app.backend.jira.field_validator import FieldValidator
from app.backend.jira.rate_limiter import IssueCreationRateLimiter
from app.core.config import Config

logger = logging.getLogger(__name__)

class IssueCreator:
    """Servicio encargado de la creación de issues en Jira"""
    
    def __init__(self, connection: JiraConnection, project_service: ProjectService, fetcher: IssueFetcher):
        """
        Inicializa el creador de issues.
        
        Args:
            connection: Conexión con Jira.
            project_service: Servicio de proyectos.
            fetcher: Buscador de issues y metadata.
        """
        self._connection = connection
        self._project_service = project_service
        self._fetcher = fetcher
        self._rate_limiter = IssueCreationRateLimiter()

    def create_issue(self, project_key: str, issue_type: str, summary: str, description: str = None,
                     assignee: str = None, priority: str = None, labels: List[str] = None,
                     custom_fields: Dict = None, field_schemas: Dict = None) -> Dict:
        """
        Crea un solo issue en Jira con soporte para campos personalizados y formato ADF.
        
        Args:
            project_key: Clave del proyecto.
            issue_type: Tipo de issue.
            summary: Resumen/Título.
            description: Descripción (Markdown/Texto plano).
            assignee: Email o accountId del asignado.
            priority: Nombre de la prioridad.
            labels: Lista de etiquetas.
            custom_fields: Diccionario de campos personalizados {field_id: value}.
            field_schemas: Metadatos de esquemas para formateo preciso.
            
        Returns:
            Dict con el resultado de la creación.
        """
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
                return self._handle_creation_error(response, url, payload, custom_fields)
                
        except Exception as e:
            logger.error(f"Error al crear issue: {str(e)}")
            self._rate_limiter.report_error()
            return {'success': False, 'error': str(e)}

    def _handle_creation_error(self, response, url, payload, custom_fields) -> Dict:
        """Maneja los errores de respuesta de Jira, incluyendo reintentos ADF."""
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
