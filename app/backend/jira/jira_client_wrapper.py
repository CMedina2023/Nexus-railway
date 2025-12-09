"""
Wrapper para JiraClient que usa los servicios especializados
Mantiene compatibilidad hacia atrás mientras usa la nueva arquitectura
"""
import logging
from typing import Dict, List, Optional

from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.issue_service import IssueService
from app.backend.jira.metrics_calculator import MetricsCalculator
from app.core.config import Config

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Cliente para interactuar con la API de Jira
    Usa servicios especializados internamente (SRP, ISP)
    Mantiene la misma interfaz pública para compatibilidad hacia atrás
    """
    
    def __init__(self, base_url: str = None, email: str = None, api_token: str = None):
        """
        Inicializa el cliente Jira con servicios especializados
        
        Args:
            base_url: URL base de Jira (default: Config.JIRA_BASE_URL)
            email: Email de Jira (default: Config.JIRA_EMAIL)
            api_token: Token de API de Jira (default: Config.JIRA_API_TOKEN)
        """
        # Crear conexión
        self._connection = JiraConnection(base_url, email, api_token)
        
        # Crear servicios especializados (inyección de dependencias)
        self._project_service = ProjectService(self._connection)
        self._issue_service = IssueService(self._connection, self._project_service)
        self._metrics_calculator = MetricsCalculator()
        
        # Mantener propiedades públicas para compatibilidad
        self.base_url = self._connection.base_url
        self.auth = self._connection._auth
        self.session = self._connection.session
    
    def test_connection(self) -> Dict:
        """Prueba la conexión con Jira"""
        return self._connection.test_connection()
    
    def get_projects(self) -> List[Dict]:
        """Obtiene la lista de proyectos de Jira"""
        return self._project_service.get_projects()
    
    def get_issue_types(self, project_key: str, filter_types: bool = True) -> List[Dict]:
        """Obtiene los tipos de issue disponibles para un proyecto"""
        return self._project_service.get_issue_types(project_key, filter_types=filter_types)
    
    def get_filter_fields(self, project_key: str, issuetype: str = None, include_all_fields: bool = False) -> Dict:
        """Obtiene los campos disponibles para filtros y sus valores"""
        return self._project_service.get_filter_fields(project_key, issuetype=issuetype, include_all_fields=include_all_fields)
    
    def get_project_fields_for_creation(self, project_key: str, issue_type: str = None, combine_test_cases_and_stories: bool = False) -> Dict:
        """Obtiene los campos disponibles para crear issues en un proyecto"""
        return self._project_service.get_project_fields_for_creation(project_key, issue_type, combine_test_cases_and_stories)
    
    def validate_csv_fields(self, csv_columns: List[str], project_key: str, issue_type: str = None) -> Dict:
        """
        Valida automáticamente las columnas del CSV contra los campos disponibles en Jira
        Retorna sugerencias de mapeo y campos faltantes
        """
        try:
            # Obtener campos disponibles del proyecto
            # Para carga masiva, combinar campos de Test Cases y Stories si no se especifica issue_type
            combine_types = (issue_type is None)
            fields_info = self._project_service.get_project_fields_for_creation(project_key, issue_type, combine_test_cases_and_stories=combine_types)
            
            if not fields_info.get('success', True):  # Si no tiene 'success', asumir éxito
                return {
                    'success': False,
                    'error': fields_info.get('error', 'Error al obtener campos'),
                    'mappings': [],
                    'missing_required': [],
                    'unmapped_csv_columns': [],
                    'required_fields': [],
                    'optional_fields': []
                }
            
            required_fields = fields_info.get('required_fields', [])
            optional_fields = fields_info.get('optional_fields', [])
            all_jira_fields = required_fields + optional_fields
            
            # Normalizar nombres para comparación
            def normalize_name(name: str) -> str:
                """Normaliza un nombre para comparación"""
                import unicodedata
                import re
                name = name.lower()
                name = unicodedata.normalize('NFD', name)
                name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
                name = re.sub(r'[^a-z0-9\s]', '', name)
                name = re.sub(r'\s+', ' ', name).strip()
                return name
            
            # Crear diccionario de campos Jira normalizados
            jira_fields_normalized = {}
            for field in all_jira_fields:
                normalized = normalize_name(field['name'])
                if normalized not in jira_fields_normalized:
                    jira_fields_normalized[normalized] = []
                jira_fields_normalized[normalized].append(field)
            
            # Mapeos sugeridos
            mappings = []
            matched_csv_columns = set()
            matched_jira_fields = set()
            
            # Función para calcular similitud
            def calculate_similarity(str1: str, str2: str) -> float:
                """Calcula similitud entre dos strings (0-1)"""
                norm1 = normalize_name(str1)
                norm2 = normalize_name(str2)
                
                if norm1 == norm2:
                    return 1.0
                
                if norm1 in norm2 or norm2 in norm1:
                    return 0.9
                
                words1 = set(norm1.split())
                words2 = set(norm2.split())
                if words1 and words2:
                    intersection = words1.intersection(words2)
                    union = words1.union(words2)
                    if union:
                        return len(intersection) / len(union)
                
                return 0.0
            
            # Buscar coincidencias para cada columna CSV
            for csv_col in csv_columns:
                csv_col_normalized = normalize_name(csv_col)
                best_match = None
                best_similarity = 0.0
                
                # Filtrar columnas que no deben mapearse
                csv_col_lower = csv_col.lower()
                if csv_col_lower in ['project', 'proyecto', 'project key']:
                    mappings.append({
                        'csv_column': csv_col,
                        'jira_field_id': None,
                        'jira_field_name': None,
                        'jira_field_type': None,
                        'similarity': 0.0,
                        'required': False,
                        'suggested': False,
                        'skip': True
                    })
                    continue
                
                # Buscar en campos Jira
                for jira_field in all_jira_fields:
                    if jira_field['id'] in matched_jira_fields:
                        continue
                    
                    similarity = calculate_similarity(csv_col, jira_field['name'])
                    
                    variations = [
                        csv_col.lower(),
                        csv_col.lower().replace('_', ' '),
                        csv_col.lower().replace('-', ' '),
                        csv_col.lower().replace(' ', ''),
                    ]
                    
                    for variation in variations:
                        var_similarity = calculate_similarity(variation, jira_field['name'])
                        similarity = max(similarity, var_similarity)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = jira_field
                
                # Si la similitud es alta (>0.5), sugerir mapeo
                if best_match and best_similarity > 0.5:
                    mappings.append({
                        'csv_column': csv_col,
                        'jira_field_id': best_match['id'],
                        'jira_field_name': best_match['name'],
                        'jira_field_type': best_match.get('type', 'string'),
                        'similarity': best_similarity,
                        'required': best_match in required_fields,
                        'suggested': True
                    })
                    matched_csv_columns.add(csv_col)
                    matched_jira_fields.add(best_match['id'])
                else:
                    mappings.append({
                        'csv_column': csv_col,
                        'jira_field_id': None,
                        'jira_field_name': None,
                        'jira_field_type': None,
                        'similarity': best_similarity if best_match else 0.0,
                        'required': False,
                        'suggested': False
                    })
            
            # Identificar campos requeridos faltantes
            missing_required = []
            for req_field in required_fields:
                if req_field['id'] not in matched_jira_fields:
                    missing_required.append({
                        'id': req_field['id'],
                        'name': req_field['name'],
                        'type': req_field.get('type', 'string')
                    })
            
            # Identificar columnas CSV sin mapeo
            unmapped_csv_columns = []
            for csv_col in csv_columns:
                if csv_col not in matched_csv_columns:
                    csv_col_lower = csv_col.lower()
                    if csv_col_lower not in ['project', 'proyecto', 'project key', 'priority', 'prioridad']:
                        unmapped_csv_columns.append(csv_col)
            
            return {
                'success': True,
                'mappings': mappings,
                'missing_required': missing_required,
                'unmapped_csv_columns': unmapped_csv_columns,
                'required_fields': [{'id': f['id'], 'name': f['name'], 'type': f.get('type', 'string')} for f in required_fields],
                'optional_fields': [{'id': f['id'], 'name': f['name'], 'type': f.get('type', 'string')} for f in optional_fields]
            }
            
        except Exception as e:
            logger.error(f"Error al validar campos CSV: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'mappings': [],
                'missing_required': [],
                'unmapped_csv_columns': [],
                'required_fields': [],
                'optional_fields': []
            }
    
    def get_project_metrics(self, project_key: str) -> Dict:
        """Obtiene métricas de avance para un proyecto específico"""
        try:
            metrics = {
                'project_key': project_key,
                'test_cases': {},
                'bugs': {},
                'total_issues': 0,
                'general_report': {}
            }
            
            # Obtener casos de prueba (Test Cases)
            test_cases = self._issue_service.get_issues_by_type(project_key, 'Test Case')
            metrics['test_cases'] = self._metrics_calculator.calculate_issue_metrics(test_cases, 'Test Case')
            
            # Obtener bugs
            bugs = self._issue_service.get_issues_by_type(project_key, 'Bug')
            metrics['bugs'] = self._metrics_calculator.calculate_issue_metrics(bugs, 'Bug')
            
            # Total de issues
            all_issues = self._issue_service.get_all_issues(project_key)
            metrics['total_issues'] = len(all_issues)
            
            # Calcular métricas del reporte general
            metrics['general_report'] = self._metrics_calculator.calculate_general_report_metrics(test_cases, bugs)
            
            return metrics
        except Exception as e:
            logger.error(f"Error al obtener métricas del proyecto {project_key}: {str(e)}")
            return {
                'project_key': project_key,
                'error': str(e),
                'test_cases': {},
                'bugs': {},
                'total_issues': 0,
                'general_report': {}
            }
    
    def create_issue(self, project_key: str, issue_type: str, summary: str, description: str = None,
                     assignee: str = None, priority: str = None, labels: List[str] = None) -> Dict:
        """Crea un issue en Jira"""
        return self._issue_service.create_issue(
            project_key=project_key,
            issue_type=issue_type,
            summary=summary,
            description=description,
            assignee=assignee,
            priority=priority,
            labels=labels
        )
    
    def create_issues_from_csv(self, csv_data: List[Dict], project_key: str,
                              field_mappings: Dict = None, default_values: Dict = None,
                              filter_issue_types: bool = True) -> Dict:
        """Crea múltiples issues en Jira desde datos CSV"""
        return self._issue_service.create_issues_from_csv(
            csv_data=csv_data,
            project_key=project_key,
            field_mappings=field_mappings,
            default_values=default_values,
            filter_issue_types=filter_issue_types
        )

