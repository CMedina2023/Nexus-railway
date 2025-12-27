"""
Componente para gestión y caché de datos de proyectos
"""
import logging
from typing import Dict, List, Optional, Set
from app.backend.jira.project_fetcher import ProjectFetcher
from app.backend.jira.project_validator import ProjectValidator
from app.backend.jira.issue_fetcher import TEST_CASE_VARIATIONS, STORY_VARIATIONS

logger = logging.getLogger(__name__)

class ProjectCache:
    """Componente que gestiona la obtención de datos, aplicando estrategias de recuperación"""
    
    def __init__(self, fetcher: ProjectFetcher, validator: ProjectValidator):
        self._fetcher = fetcher
        self._validator = validator

    def get_projects(self) -> List[Dict]:
        """Obtiene y formatea la lista de proyectos"""
        projects = self._fetcher.fetch_projects()
        if not projects:
            return []
            
        formatted_projects = []
        for project in projects:
            formatted_projects.append({
                'key': project.get('key', ''),
                'name': project.get('name', ''),
                'id': project.get('id', ''),
                'projectTypeKey': project.get('projectTypeKey', ''),
                'avatarUrls': project.get('avatarUrls', {})
            })
        return formatted_projects

    def get_issue_types(self, project_key: str, use_createmeta: bool = False, filter_types: bool = True) -> List[Dict]:
        """
        Obtiene los tipos de issue disponibles para un proyecto
        Estrategia híbrida: Escenario 1 (Proyecto) vs Escenario 2 (Global)
        """
        # ESCENARIO 1: Intentar con la API de proyecto (rápido)
        project_data = self._fetcher.fetch_project_issue_types(project_key)
        
        if project_data:
            issue_types = project_data.get('issueTypes', [])
            logger.info(f"[DEBUG] Endpoint de proyecto retornó {len(issue_types)} issuetypes")
            
            # ESCENARIO 2: Si hay exactamente 100, puede haber más (límite de Jira)
            if len(issue_types) == 100:
                logger.info(f"[DEBUG] Detectado límite de 100 issuetypes, consultando endpoint global...")
                global_types = self._fetcher.fetch_global_issue_types()
                
                if global_types:
                    issue_types = global_types
                    logger.info(f"[DEBUG] Usando {len(issue_types)} issuetypes del endpoint global")
                else:
                    logger.warning(f"[DEBUG] No se pudieron obtener issuetypes globales, usando los del proyecto")
            
            # Filtrar solo tests Cases y Bugs si filter_types es True
            if filter_types:
                filtered_types = self._validator.filter_testcases_and_bugs(issue_types)
                logger.info(f"[DEBUG] Total de issuetypes filtrados (tests Cases y Bugs): {len(filtered_types)}")
                return filtered_types
            else:
                logger.info(f"[DEBUG] Retornando todos los {len(issue_types)} issuetypes sin filtrar")
                return issue_types
        else:
            return []

    def get_filter_fields(self, project_key: str, issuetype: str = None, include_all_fields: bool = False) -> Dict:
        """Obtiene los campos disponibles para filtros y sus valores"""
        fields_data = {
            'status': [],
            'priority': [],
            'assignee': [],
            'all_fields': [],
            'custom_fields': []
        }
        
        # 1. Obtener estados
        statuses_data = self._fetcher.fetch_project_statuses(project_key)
        if statuses_data:
            all_statuses = set()
            for status_category in statuses_data:
                # Filtrar por issuetype si se especifica
                if issuetype:
                    category_name = status_category.get('name', '').lower()
                    issuetype_lower = issuetype.lower()
                    issue_types_in_category = [it.get('name', '').lower() for it in status_category.get('issuetypes', [])]
                    
                    if (issuetype_lower not in category_name and 
                        category_name not in issuetype_lower and
                        not any(issuetype_lower in it or it in issuetype_lower for it in issue_types_in_category)):
                        continue
                
                for status in status_category.get('statuses', []):
                    all_statuses.add(status.get('name', ''))
            
            fields_data['status'] = sorted(list(all_statuses))
            if issuetype:
                logger.info(f"[DEBUG] Estados filtrados para {issuetype}: {len(fields_data['status'])} estados")

        # 2. Obtener prioridades
        priorities = self._fetcher.fetch_priorities()
        if priorities:
            fields_data['priority'] = [p.get('name', '') for p in priorities]

        # 3. Obtener versiones (custom_field_values init)
        custom_field_values = {}
        project_versions = []
        versions_data = self._fetcher.fetch_project_versions(project_key)
        
        if versions_data:
            for version in versions_data:
                version_name = version.get('name', '')
                if version_name:
                    project_versions.append(version_name)
            
            logger.info(f"[DEBUG] Versiones del proyecto obtenidas: {len(project_versions)} versiones")
            custom_field_values['affectsVersions'] = set(project_versions)
            custom_field_values['fixVersions'] = set(project_versions)

        # 4. Obtener todos los campos y valores permitidos
        all_fields = self._fetcher.fetch_all_fields()
        
        if all_fields:
            # Obtener metadatos para valores permitidos
            # Utilizar createmeta para inferir valores
            createmeta_data = self._fetcher.fetch_createmeta(project_key)
            
            if createmeta_data:
                projects = createmeta_data.get('projects', [])
                if projects:
                    project_meta = projects[0]
                    issue_types_meta = project_meta.get('issuetypes', [])
                    
                    logger.info(f"[DEBUG] Procesando {len(issue_types_meta)} tipos de issues desde createmeta para valores")
                    
                    for it_meta in issue_types_meta:
                        it_name = it_meta.get('name', 'Unknown')
                        
                        # Filtro por tipo de issue
                        if issuetype:
                            it_lower = it_name.lower()
                            q_lower = issuetype.lower()
                            if q_lower not in it_lower and it_lower not in q_lower:
                                continue

                        fields = it_meta.get('fields', {})
                        for field_id, field_info in fields.items():
                            is_custom = field_id.startswith('customfield_')
                            is_affects = field_id == 'affectsVersions'
                            
                            if not is_custom and not is_affects:
                                continue

                            allowed_values = field_info.get('allowedValues', [])
                            if allowed_values:
                                if field_id not in custom_field_values:
                                    custom_field_values[field_id] = set()
                                
                                for value in allowed_values:
                                    extracted = self._extract_value_from_option(value)
                                    if extracted:
                                        custom_field_values[field_id].add(extracted)

            # Filtrar y construir respuesta final de campos
            filterable_fields = []
            custom_fields = []
            
            for field in all_fields:
                field_id = field.get('id', '')
                field_name = field.get('name', '')
                field_type = field.get('schema', {}).get('type', '')
                field_custom = field.get('custom', False)
                
                if field_id in ['status', 'priority', 'assignee', 'labels', 'fixVersions', 'affectsVersions', 'components', 'reporter', 'created', 'updated', 'resolution']:
                    filterable_fields.append({
                        'id': field_id, 'name': field_name, 'type': field_type, 'custom': False
                    })
                elif field_custom:
                    allowed_values_list = sorted(list(custom_field_values.get(field_id, [])))
                    if not include_all_fields:
                        if not allowed_values_list:
                            continue
                    
                    c_field = {
                        'id': field_id, 'name': field_name, 'type': field_type, 'custom': True,
                        'allowedValues': allowed_values_list
                    }
                    custom_fields.append(c_field)
                    filterable_fields.append(c_field)
            
            fields_data['all_fields'] = filterable_fields
            fields_data['custom_fields'] = custom_fields
            fields_data['custom_field_values'] = {k: sorted(list(v)) for k, v in custom_field_values.items()}
            
        return fields_data

    def _extract_value_from_option(self, value):
        """Helper para extraer valor de opciones de Jira"""
        if isinstance(value, dict):
            if 'value' in value: return str(value['value'])
            if 'name' in value: return str(value['name'])
            if 'label' in value: return str(value['label'])
            if 'id' in value: return str(value['id'])
            if 'key' in value: return str(value['key'])
            # Fallback
            for k in value.keys():
                if isinstance(value[k], (str, int, float)):
                    return str(value[k])
            return str(value)
        return str(value)

    def get_project_fields_for_creation(self, project_key: str, issue_type: str = None, combine_test_cases_and_stories: bool = False) -> Dict:
        """Obtiene campos para creación usando createmeta"""
        # Solicitar createmeta
        # Si issue_type está definido, optimizamos. 
        # Pero la lógica original usaba issue_typeNames param?
        # Revisando original: Si issue_type, usaba &issuetypeNames={issue_type}
        
        createmeta_data = self._fetcher.fetch_createmeta(project_key, issue_type if issue_type else None)
        
        if not createmeta_data:
            return {'success': False, 'error': 'Error al conectar con Jira', 'fields': {}, 'required_fields': [], 'optional_fields': []}
            
        projects = createmeta_data.get('projects', [])
        if not projects:
             return {'success': False, 'error': 'No se encontró el proyecto', 'fields': {}, 'required_fields': [], 'optional_fields': []}
             
        project = projects[0]
        issue_types = project.get('issuetypes', [])
        
        if not issue_types:
             return {'success': False, 'error': 'No se encontraron tipos de issues', 'fields': {}, 'required_fields': [], 'optional_fields': []}

        # Lógica de selección de campos
        if issue_type:
            selected_type = next((it for it in issue_types if it.get('name', '').lower() == issue_type.lower()), issue_types[0])
            fields = selected_type.get('fields', {})
            issue_type_name = selected_type.get('name', '')
            issue_type_id = selected_type.get('id', '')
        elif combine_test_cases_and_stories:
            # Lógica combinada
            all_fields = {}
            target_types = []
            
            for it in issue_types:
                it_name = it.get('name', '').lower()
                is_tc = any(v.lower() == it_name or (v.lower() in it_name and 'test' in it_name and 'case' in it_name) for v in TEST_CASE_VARIATIONS)
                is_story = any(v.lower() == it_name or (v.lower() in it_name and 'story' in it_name) for v in STORY_VARIATIONS)
                if is_tc or is_story:
                    target_types.append(it)
            
            if not target_types:
                target_types = [issue_types[0]]
            
            for it in target_types:
                type_fields = it.get('fields', {})
                for fid, finfo in type_fields.items():
                    if fid not in all_fields:
                        all_fields[fid] = finfo
                    else:
                        existing = all_fields[fid]
                        if not existing.get('allowedValues') and finfo.get('allowedValues'):
                            all_fields[fid] = finfo
                        if not existing.get('required') and finfo.get('required'):
                            all_fields[fid] = finfo
            
            fields = all_fields
            issue_type_name = 'tests Cases & Stories'
            issue_type_id = None
        else:
            selected_type = issue_types[0]
            fields = selected_type.get('fields', {})
            issue_type_name = selected_type.get('name', '')
            issue_type_id = selected_type.get('id', '')

        # Formatear
        formatted_fields = {}
        required_fields = []
        optional_fields = []
        
        for field_id, field_info in fields.items():
            if field_id == 'project': continue
            
            f_data = {
                'id': field_id,
                'name': field_info.get('name', field_id),
                'required': field_info.get('required', False),
                'type': field_info.get('schema', {}).get('type', 'string'),
                'allowedValues': field_info.get('allowedValues', [])
            }
            formatted_fields[field_id] = f_data
            if f_data['required']: required_fields.append(f_data)
            else: optional_fields.append(f_data)
            
        return {
            'success': True,
            'fields': formatted_fields,
            'required_fields': required_fields,
            'optional_fields': optional_fields,
            'issue_type': issue_type_name,
            'issue_type_id': issue_type_id
        }
