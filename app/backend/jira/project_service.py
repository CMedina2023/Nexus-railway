"""
Servicio para operaciones relacionadas con proyectos de Jira
Responsabilidad única: Gestionar información y configuración de proyectos
"""
import logging
from typing import Dict, List, Optional

from app.backend.jira.connection import JiraConnection
from app.core.config import Config

logger = logging.getLogger(__name__)


class ProjectService:
    """Servicio para operaciones relacionadas con proyectos de Jira"""
    
    def __init__(self, connection: JiraConnection):
        """
        Inicializa el servicio de proyectos
        
        Args:
            connection: Conexión con Jira (inyección de dependencias)
        """
        self._connection = connection
    
    def get_projects(self) -> List[Dict]:
        """
        Obtiene la lista de proyectos de Jira
        
        Returns:
            List[Dict]: Lista de proyectos formateados
        """
        try:
            url = f"{self._connection.base_url}/rest/api/3/project"
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                projects = response.json()
                # Formatear proyectos para el frontend
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
            else:
                logger.error(f"Error al obtener proyectos: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error al obtener proyectos: {str(e)}")
            return []
    
    def _get_global_issue_types(self) -> List[Dict]:
        """
        Obtiene todos los tipos de issue del sistema usando el endpoint global
        (sin límite de 100)
        
        Returns:
            List[Dict]: Lista de todos los tipos de issue del sistema
        """
        try:
            url = f"{self._connection.base_url}/rest/api/3/issuetype"
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                all_types = response.json()
                logger.info(f"[DEBUG] Endpoint global retornó {len(all_types)} issuetypes del sistema")
                return all_types
            else:
                logger.warning(f"Error al obtener issuetypes globales: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.warning(f"Error al obtener issuetypes globales: {str(e)}")
            return []
    
    def _filter_testcases_and_bugs(self, issue_types: List[Dict]) -> List[Dict]:
        """
        Filtra solo Test Cases y Bugs de una lista de tipos de issue
        
        Args:
            issue_types: Lista de tipos de issue a filtrar
            
        Returns:
            List[Dict]: Lista filtrada con solo Test Cases y Bugs
        """
        from app.backend.jira.issue_service import TEST_CASE_VARIATIONS, BUG_VARIATIONS
        
        filtered = []
        seen_ids = set()
        
        for issue_type in issue_types:
            issue_type_id = issue_type.get('id', '')
            issue_type_name = issue_type.get('name', '').strip()
            
            # Evitar duplicados
            if issue_type_id and issue_type_id in seen_ids:
                continue
            
            # Verificar si es Test Case
            is_test_case = any(
                variation.lower() == issue_type_name.lower() or
                (variation.lower() in issue_type_name.lower() and 
                 'test' in issue_type_name.lower() and 'case' in issue_type_name.lower())
                for variation in TEST_CASE_VARIATIONS
            )
            
            # Verificar si es Bug
            is_bug = any(
                variation.lower() == issue_type_name.lower()
                for variation in BUG_VARIATIONS
            )
            
            # Solo incluir si es Test Case o Bug
            if is_test_case or is_bug:
                seen_ids.add(issue_type_id)
                filtered.append({
                    'id': issue_type_id,
                    'name': issue_type_name,
                    'description': issue_type.get('description', ''),
                    'iconUrl': issue_type.get('iconUrl', ''),
                    'subtask': issue_type.get('subtask', False)
                })
        
        logger.info(f"[DEBUG] Filtrados {len(filtered)} issuetypes (Test Cases y Bugs) de {len(issue_types)} totales")
        return filtered
    
    def get_issue_types(self, project_key: str, use_createmeta: bool = False, filter_types: bool = True) -> List[Dict]:
        """
        Obtiene los tipos de issue disponibles para un proyecto
        
        Estrategia híbrida:
        - Escenario 1 (< 100): Usa endpoint de proyecto (rápido)
        - Escenario 2 (≥ 100): Usa endpoint global (completo)
        
        Args:
            project_key: Clave del proyecto
            use_createmeta: Si es True, usa createmeta API (más lento pero obtiene todos los issuetypes)
            filter_types: Si es True, filtra solo Test Cases y Bugs. Si es False, retorna todos los tipos.
            
        Returns:
            List[Dict]: Lista de tipos de issue (filtrados o todos según filter_types)
        """
        try:
            # ESCENARIO 1: Intentar con la API de proyecto (rápido)
            url = f"{self._connection.base_url}/rest/api/3/project/{project_key}"
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)
            
            if response.status_code == 200:
                project_data = response.json()
                issue_types = project_data.get('issueTypes', [])
                
                logger.info(f"[DEBUG] Endpoint de proyecto retornó {len(issue_types)} issuetypes")
                
                # ESCENARIO 2: Si hay exactamente 100, puede haber más (límite de Jira)
                # Consultar endpoint global para obtener TODOS los issuetypes
                if len(issue_types) == 100:
                    logger.info(f"[DEBUG] Detectado límite de 100 issuetypes, consultando endpoint global...")
                    global_types = self._get_global_issue_types()
                    
                    if global_types:
                        # Usar los tipos globales (sin límite)
                        issue_types = global_types
                        logger.info(f"[DEBUG] Usando {len(issue_types)} issuetypes del endpoint global")
                    else:
                        logger.warning(f"[DEBUG] No se pudieron obtener issuetypes globales, usando los del proyecto")
                
                # Filtrar solo Test Cases y Bugs si filter_types es True
                if filter_types:
                    filtered_types = self._filter_testcases_and_bugs(issue_types)
                    logger.info(f"[DEBUG] Total de issuetypes filtrados (Test Cases y Bugs): {len(filtered_types)}")
                    return filtered_types
                else:
                    logger.info(f"[DEBUG] Retornando todos los {len(issue_types)} issuetypes sin filtrar")
                    return issue_types
            else:
                logger.error(f"Error al obtener tipos de issue: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error al obtener tipos de issue para {project_key}: {str(e)}")
            return []
    
    def get_filter_fields(self, project_key: str, issuetype: str = None, include_all_fields: bool = False) -> Dict:
        """
        Obtiene los campos disponibles para filtros y sus valores
        
        Args:
            project_key: Clave del proyecto
            issuetype: Tipo de issue opcional para filtrar campos específicos (ej: "Test Case", "Bug")
            include_all_fields: Si es True, incluye todos los campos incluso sin valores permitidos (para carga masiva)
            
        Returns:
            Dict: Campos disponibles para filtros con estructura:
                {
                    'status': [...],
                    'priority': [...],
                    'assignee': [...],
                    'all_fields': [...],  # Lista de todos los campos disponibles
                    'custom_fields': [...]  # Lista de campos personalizados
                }
        """
        try:
            fields_data = {
                'status': [],
                'priority': [],
                'assignee': [],
                'all_fields': [],
                'custom_fields': []
            }
            
            # Obtener estados disponibles
            try:
                status_url = f"{self._connection.base_url}/rest/api/3/project/{project_key}/statuses"
                status_response = self._connection.session.get(status_url, timeout=Config.JIRA_TIMEOUT_SHORT)
                
                if status_response.status_code == 200:
                    statuses_data = status_response.json()
                    all_statuses = set()
                    
                    for status_category in statuses_data:
                        # Si se especificó un issuetype, filtrar por ese tipo
                        if issuetype:
                            # Comparar de forma flexible
                            category_name = status_category.get('name', '').lower()
                            issuetype_lower = issuetype.lower()
                            
                            # Verificar si el nombre de la categoría contiene el issuetype o viceversa
                            # O si el issuetype está en la lista de tipos de issues de la categoría
                            issue_types_in_category = [it.get('name', '').lower() 
                                                      for it in status_category.get('issuetypes', [])]
                            
                            if (issuetype_lower not in category_name and 
                                category_name not in issuetype_lower and
                                not any(issuetype_lower in it or it in issuetype_lower 
                                       for it in issue_types_in_category)):
                                continue
                        
                        for status in status_category.get('statuses', []):
                            all_statuses.add(status.get('name', ''))
                    
                    fields_data['status'] = sorted(list(all_statuses))
                    if issuetype:
                        logger.info(f"[DEBUG] Estados filtrados para {issuetype}: {len(fields_data['status'])} estados")
            except Exception as e:
                logger.warning(f"Error al obtener estados: {str(e)}")
            
            # Obtener prioridades disponibles
            try:
                priority_url = f"{self._connection.base_url}/rest/api/3/priority"
                priority_response = self._connection.session.get(priority_url, timeout=Config.JIRA_TIMEOUT_SHORT)
                
                if priority_response.status_code == 200:
                    priorities = priority_response.json()
                    fields_data['priority'] = [p.get('name', '') for p in priorities]
            except Exception as e:
                logger.warning(f"Error al obtener prioridades: {str(e)}")
            
            # Inicializar custom_field_values antes de obtener datos
            custom_field_values = {}
            
            # Obtener versiones del proyecto para affectsVersions y fixVersions
            project_versions = []
            try:
                versions_url = f"{self._connection.base_url}/rest/api/3/project/{project_key}/versions"
                versions_response = self._connection.session.get(versions_url, timeout=Config.JIRA_TIMEOUT_SHORT)
                
                if versions_response.status_code == 200:
                    versions_data = versions_response.json()
                    # Extraer nombres de las versiones (pueden estar archivadas o no liberadas)
                    for version in versions_data:
                        version_name = version.get('name', '')
                        if version_name:
                            project_versions.append(version_name)
                    
                    logger.info(f"[DEBUG] Versiones del proyecto obtenidas: {len(project_versions)} versiones")
                    if project_versions:
                        logger.info(f"[DEBUG] Primeras versiones: {project_versions[:5]}")
                    
                    # Agregar versiones a custom_field_values para affectsVersions y fixVersions
                    custom_field_values['affectsVersions'] = set(project_versions)
                    custom_field_values['fixVersions'] = set(project_versions)
                    
                    logger.info(f"[DEBUG] ✓ Versiones agregadas a affectsVersions y fixVersions: {len(project_versions)} versiones")
                else:
                    logger.warning(f"Error al obtener versiones del proyecto: {versions_response.status_code} - {versions_response.text}")
            except Exception as e:
                logger.error(f"Error al obtener versiones del proyecto: {str(e)}", exc_info=True)
            
            # Obtener TODOS los campos disponibles en Jira
            try:
                fields_url = f"{self._connection.base_url}/rest/api/3/field"
                fields_response = self._connection.session.get(fields_url, timeout=Config.JIRA_TIMEOUT_SHORT)
                
                if fields_response.status_code == 200:
                    all_fields = fields_response.json()
                    
                    # Obtener valores permitidos de campos usando createmeta
                    # Esto nos da información sobre los valores posibles para campos personalizados
                    # NOTA: custom_field_values ya está inicializado arriba con las versiones del proyecto
                    try:
                        createmeta_url = f"{self._connection.base_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes.fields"
                        createmeta_response = self._connection.session.get(createmeta_url, timeout=Config.JIRA_TIMEOUT_LONG)
                        
                        if createmeta_response.status_code == 200:
                            createmeta_data = createmeta_response.json()
                            projects = createmeta_data.get('projects', [])
                            
                            if projects:
                                project = projects[0]
                                issue_types = project.get('issuetypes', [])
                                
                                # Recopilar valores permitidos de todos los tipos de issues
                                logger.info(f"[DEBUG] Procesando {len(issue_types)} tipos de issues desde createmeta")
                                if issuetype:
                                    logger.info(f"[DEBUG] Filtrando campos para issuetype específico: {issuetype}")
                                
                                for issue_type in issue_types:
                                    issue_type_name = issue_type.get('name', 'Unknown')
                                    
                                    # Si se especificó un issuetype, solo procesar ese tipo
                                    if issuetype:
                                        # Comparar de forma flexible (case-insensitive, variaciones)
                                        issue_type_lower = issue_type_name.lower()
                                        issuetype_lower = issuetype.lower()
                                        
                                        # Verificar coincidencia exacta o parcial
                                        if (issuetype_lower not in issue_type_lower and 
                                            issue_type_lower not in issuetype_lower):
                                            logger.debug(f"[DEBUG] Saltando tipo de issue: {issue_type_name} (no coincide con {issuetype})")
                                            continue
                                    
                                    fields = issue_type.get('fields', {})
                                    logger.debug(f"[DEBUG] Procesando tipo de issue: {issue_type_name}, campos: {len(fields)}")
                                    
                                    for field_id, field_info in fields.items():
                                        # Procesar campos personalizados (customfield_) y affectsVersions
                                        is_custom_field = field_id.startswith('customfield_')
                                        is_affects_version = field_id == 'affectsVersions'
                                        
                                        if not is_custom_field and not is_affects_version:
                                            continue
                                        
                                        field_name = field_info.get('name', 'Unknown')
                                        
                                        # Log específico para affectsVersions
                                        if is_affects_version:
                                            logger.info(f"[DEBUG] ===== ENCONTRADO AFFECTSVERSIONS EN CREATEMETA =====")
                                            logger.info(f"[DEBUG] Campo ID: {field_id}")
                                            logger.info(f"[DEBUG] Campo Nombre: {field_name}")
                                            logger.info(f"[DEBUG] Issue Type: {issue_type_name}")
                                        
                                        # Obtener información del schema del campo
                                        schema = field_info.get('schema', {})
                                        field_type = schema.get('type', '')
                                        
                                        if is_affects_version:
                                            logger.info(f"[DEBUG] Schema Type: {field_type}")
                                            logger.info(f"[DEBUG] Schema: {schema}")
                                        
                                        # Verificar si es un campo que puede tener opciones
                                        is_option_field = field_type in ['option', 'array'] or schema.get('items') == 'option'
                                        
                                        # Obtener allowedValues si existe
                                        allowed_values = field_info.get('allowedValues', [])
                                        
                                        if is_affects_version:
                                            logger.info(f"[DEBUG] allowedValues encontrados: {len(allowed_values)} valores")
                                            if allowed_values:
                                                logger.info(f"[DEBUG] Primer valor de ejemplo: {allowed_values[0]}")
                                        
                                        if allowed_values:
                                            if field_id not in custom_field_values:
                                                custom_field_values[field_id] = set()
                                            
                                            logger.debug(f"[DEBUG] Extrayendo {len(allowed_values)} valores del campo {field_id} ({field_name})")
                                            
                                            # Extraer valores según el tipo de campo
                                            for idx, value in enumerate(allowed_values):
                                                extracted_value = None
                                                
                                                if isinstance(value, dict):
                                                    logger.debug(f"[DEBUG] Valor {idx} es objeto: {value}")
                                                    # Para campos tipo option, obtener el valor más apropiado
                                                    # Prioridad: value > name > label > id > key
                                                    if 'value' in value:
                                                        extracted_value = str(value['value'])
                                                        logger.debug(f"[DEBUG] Extraído desde 'value': {extracted_value}")
                                                    elif 'name' in value:
                                                        extracted_value = str(value['name'])
                                                        logger.debug(f"[DEBUG] Extraído desde 'name': {extracted_value}")
                                                    elif 'label' in value:
                                                        extracted_value = str(value['label'])
                                                        logger.debug(f"[DEBUG] Extraído desde 'label': {extracted_value}")
                                                    elif 'id' in value:
                                                        extracted_value = str(value['id'])
                                                        logger.debug(f"[DEBUG] Extraído desde 'id': {extracted_value}")
                                                    elif 'key' in value:
                                                        extracted_value = str(value['key'])
                                                        logger.debug(f"[DEBUG] Extraído desde 'key': {extracted_value}")
                                                    else:
                                                        # Si es un objeto pero no tiene los campos esperados, intentar cualquier clave
                                                        logger.debug(f"[DEBUG] Objeto sin campos conocidos, buscando cualquier valor...")
                                                        for key in value.keys():
                                                            if isinstance(value[key], (str, int, float)):
                                                                extracted_value = str(value[key])
                                                                logger.debug(f"[DEBUG] Extraído desde clave '{key}': {extracted_value}")
                                                                break
                                                        
                                                        # Si aún no hay valor, convertir el objeto completo
                                                        if not extracted_value:
                                                            extracted_value = str(value)
                                                            logger.debug(f"[DEBUG] Convertido objeto completo a string: {extracted_value}")
                                                else:
                                                    extracted_value = str(value)
                                                    logger.debug(f"[DEBUG] Valor {idx} es primitivo: {extracted_value}")
                                                
                                                if extracted_value:
                                                    custom_field_values[field_id].add(extracted_value)
                                                    logger.debug(f"[DEBUG] Valor agregado al set: {extracted_value}")
                                            
                                            logger.debug(f"[DEBUG] Total de valores únicos extraídos para {field_name}: {len(custom_field_values[field_id])}")
                                            if is_affects_version:
                                                logger.info(f"[DEBUG] Total valores únicos extraídos para affectsVersions: {len(custom_field_values[field_id])}")
                                                logger.info(f"[DEBUG] Valores extraídos: {sorted(list(custom_field_values[field_id]))[:10]}...")
                                                logger.info(f"[DEBUG] ===== FIN PROCESAMIENTO AFFECTSVERSIONS =====")
                                        
                                        # Si el campo tiene schema pero no tiene allowedValues directamente,
                                        # podría ser un campo que necesita búsqueda adicional
                                        elif is_option_field:
                                            logger.debug(f"[DEBUG] Campo {field_id} es tipo option pero no tiene allowedValues en createmeta")
                                            if is_affects_version:
                                                logger.warning(f"[DEBUG] affectsVersions es tipo option pero NO tiene allowedValues en createmeta")
                                
                                logger.info(f"[DEBUG] Valores de campos personalizados recopilados: {len(custom_field_values)} campos con valores")
                                for field_id, values in custom_field_values.items():
                                    logger.debug(f"[DEBUG] Campo {field_id}: {len(values)} valores")
                    except Exception as e:
                        logger.warning(f"Error al obtener valores de campos desde createmeta: {str(e)}")
                    
                    # Filtrar campos que son útiles para filtros
                    filterable_fields = []
                    custom_fields = []
                    
                    for field in all_fields:
                        field_id = field.get('id', '')
                        field_name = field.get('name', '')
                        field_type = field.get('schema', {}).get('type', '')
                        field_custom = field.get('custom', False)
                        
                        # Incluir campos estándar conocidos y campos personalizados
                        if field_id in ['status', 'priority', 'assignee', 'labels', 'fixVersions', 'affectsVersions', 'components', 'reporter', 'created', 'updated', 'resolution']:
                            filterable_fields.append({
                                'id': field_id,
                                'name': field_name,
                                'type': field_type,
                                'custom': False
                            })
                        elif field_custom:
                            # Campos personalizados
                            allowed_values_list = sorted(list(custom_field_values.get(field_id, [])))
                            
                            # FILTRO: Solo incluir campos que tienen lista desplegable (valores permitidos)
                            # EXCEPCIÓN: Si include_all_fields=True (carga masiva), incluir todos los campos
                            if not include_all_fields:
                                if not allowed_values_list or len(allowed_values_list) == 0:
                                    logger.debug(f"[DEBUG] Campo personalizado {field_id} ({field_name}) omitido - no tiene valores permitidos")
                                    continue
                            else:
                                # En modo carga masiva, incluir campos aunque no tengan valores permitidos
                                if not allowed_values_list or len(allowed_values_list) == 0:
                                    logger.debug(f"[DEBUG] Campo personalizado {field_id} ({field_name}) incluido (modo carga masiva) - sin valores permitidos")
                            
                            logger.debug(f"[DEBUG] Campo personalizado encontrado: {field_id} ({field_name}) con {len(allowed_values_list) if allowed_values_list else 0} valores")
                            
                            custom_fields.append({
                                'id': field_id,
                                'name': field_name,
                                'type': field_type,
                                'custom': True,
                                'allowedValues': allowed_values_list if allowed_values_list else []
                            })
                            filterable_fields.append({
                                'id': field_id,
                                'name': field_name,
                                'type': field_type,
                                'custom': True,
                                'allowedValues': allowed_values_list if allowed_values_list else []
                            })
                    
                    fields_data['all_fields'] = filterable_fields
                    fields_data['custom_fields'] = custom_fields
                    fields_data['custom_field_values'] = {k: sorted(list(v)) for k, v in custom_field_values.items()}
                    logger.info(f"[DEBUG] Campos obtenidos para filtros: {len(filterable_fields)} total, {len(custom_fields)} personalizados")
                    logger.info(f"[DEBUG] custom_field_values retornado: {len(fields_data['custom_field_values'])} campos")
                    logger.info(f"[DEBUG] Claves en custom_field_values retornado: {list(fields_data['custom_field_values'].keys())}")
                    if 'affectsVersions' in fields_data['custom_field_values']:
                        logger.info(f"[DEBUG] ✓ affectsVersions en respuesta con {len(fields_data['custom_field_values']['affectsVersions'])} valores")
                        logger.info(f"[DEBUG] Valores de affectsVersions: {fields_data['custom_field_values']['affectsVersions'][:5]}...")
                    else:
                        logger.warning(f"[DEBUG] ✗ affectsVersions NO está en custom_field_values retornado")
            except Exception as e:
                logger.warning(f"Error al obtener todos los campos: {str(e)}")
            
            return fields_data
        except Exception as e:
            logger.error(f"Error al obtener campos de filtro para {project_key}: {str(e)}")
            return {'status': [], 'priority': [], 'assignee': [], 'all_fields': [], 'custom_fields': []}
    
    def get_project_fields_for_creation(self, project_key: str, issue_type: str = None, combine_test_cases_and_stories: bool = False) -> Dict:
        """
        Obtiene los campos disponibles para crear un issue en un proyecto
        
        Args:
            project_key: Clave del proyecto
            issue_type: Tipo de issue (opcional)
            combine_test_cases_and_stories: Si es True y issue_type es None, combina campos de Test Cases y Stories (para carga masiva)
            
        Returns:
            Dict: Campos disponibles para creación
        """
        try:
            if issue_type:
                url = f"{self._connection.base_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&issuetypeNames={issue_type}&expand=projects.issuetypes.fields"
            else:
                url = f"{self._connection.base_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes.fields"
            
            response = self._connection.session.get(url, timeout=Config.JIRA_TIMEOUT_LONG)
            
            if response.status_code == 200:
                metadata = response.json()
                projects = metadata.get('projects', [])
                
                if not projects:
                    return {
                        'success': False,
                        'error': 'No se encontró el proyecto',
                        'fields': {},
                        'required_fields': [],
                        'optional_fields': []
                    }
                
                project = projects[0]
                issue_types = project.get('issuetypes', [])
                
                if not issue_types:
                    return {
                        'success': False,
                        'error': 'No se encontraron tipos de issues en el proyecto',
                        'fields': {},
                        'required_fields': [],
                        'optional_fields': []
                    }
                
                # Si se especificó un tipo, buscar ese
                if issue_type:
                    selected_type = None
                    for it in issue_types:
                        if it.get('name', '').lower() == issue_type.lower():
                            selected_type = it
                            break
                    
                    if not selected_type:
                        selected_type = issue_types[0]
                    
                    fields = selected_type.get('fields', {})
                elif combine_test_cases_and_stories:
                    # COMBINAR campos de Test Cases y Stories específicamente (para carga masiva)
                    from app.backend.jira.issue_service import TEST_CASE_VARIATIONS, STORY_VARIATIONS
                    
                    all_fields = {}
                    logger.info(f"[DEBUG] Combinando campos de Test Cases y Stories para carga masiva")
                    
                    target_types = []
                    for it in issue_types:
                        issue_type_name = it.get('name', '')
                        issue_type_lower = issue_type_name.lower()
                        
                        # Verificar si es Test Case
                        is_test_case = any(
                            variation.lower() == issue_type_lower or 
                            (variation.lower() in issue_type_lower and 'test' in issue_type_lower and 'case' in issue_type_lower)
                            for variation in TEST_CASE_VARIATIONS
                        )
                        
                        # Verificar si es Story
                        is_story = any(
                            variation.lower() == issue_type_lower or
                            (variation.lower() in issue_type_lower and 'story' in issue_type_lower)
                            for variation in STORY_VARIATIONS
                        )
                        
                        if is_test_case or is_story:
                            target_types.append(it)
                            logger.info(f"[DEBUG] Tipo incluido: '{issue_type_name}' ({'Test Case' if is_test_case else 'Story'})")
                    
                    if not target_types:
                        logger.warning(f"[DEBUG] No se encontraron Test Cases ni Stories, usando el primer tipo disponible")
                        target_types = [issue_types[0]]
                    
                    # Combinar campos de los tipos seleccionados
                    for it in target_types:
                        issue_type_name = it.get('name', '')
                        type_fields = it.get('fields', {})
                        logger.info(f"[DEBUG] Tipo '{issue_type_name}': {len(type_fields)} campos")
                        
                        for field_id, field_info in type_fields.items():
                            # Si el campo ya existe, mantener el que tiene más información
                            if field_id not in all_fields:
                                all_fields[field_id] = field_info
                            else:
                                # Si el campo existente no tiene allowedValues pero el nuevo sí, actualizar
                                existing = all_fields[field_id]
                                if not existing.get('allowedValues') and field_info.get('allowedValues'):
                                    all_fields[field_id] = field_info
                                # Si el campo existente no es required pero el nuevo sí, actualizar
                                if not existing.get('required', False) and field_info.get('required', False):
                                    all_fields[field_id] = field_info
                    
                    fields = all_fields
                    selected_type = None  # No hay un tipo específico cuando se combinan
                    logger.info(f"[DEBUG] Total de campos únicos combinados de Test Cases y Stories: {len(fields)}")
                else:
                    # Comportamiento original: usar el primer tipo si no se especifica
                    selected_type = issue_types[0]
                    fields = selected_type.get('fields', {})
                
                # Log para debugging
                logger.info(f"[DEBUG] Campos obtenidos de Jira para {project_key}: {list(fields.keys())[:10]}... (total: {len(fields)})")
                
                # Formatear campos para el frontend y separar en requeridos y opcionales
                formatted_fields = {}
                required_fields = []
                optional_fields = []
                
                for field_id, field_info in fields.items():
                    # Excluir solo project porque ya se selecciona en el paso 1
                    # issuetype SÍ debe estar disponible para mapear
                    if field_id == 'project':
                        continue
                    
                    field_data = {
                        'id': field_id,
                        'name': field_info.get('name', field_id),
                        'required': field_info.get('required', False),
                        'type': field_info.get('schema', {}).get('type', 'string'),
                        'allowedValues': field_info.get('allowedValues', [])
                    }
                    
                    formatted_fields[field_id] = field_data
                    
                    # Separar en requeridos y opcionales
                    if field_info.get('required', False):
                        required_fields.append(field_data)
                    else:
                        optional_fields.append(field_data)
                
                # Log para debugging
                logger.info(f"[DEBUG] Campos requeridos encontrados: {len(required_fields)}")
                logger.info(f"[DEBUG] Campos opcionales encontrados: {len(optional_fields)}")
                logger.info(f"[DEBUG] IDs de campos requeridos: {[f['id'] for f in required_fields[:5]]}")
                
                # Determinar el issue_type para el return
                if selected_type:
                    issue_type_name = selected_type.get('name', '')
                    issue_type_id = selected_type.get('id', '')
                elif combine_test_cases_and_stories:
                    issue_type_name = 'Test Cases & Stories'
                    issue_type_id = None
                else:
                    issue_type_name = issue_types[0].get('name', '') if issue_types else ''
                    issue_type_id = issue_types[0].get('id', '') if issue_types else None
                
                return {
                    'success': True,
                    'fields': formatted_fields,
                    'required_fields': required_fields,
                    'optional_fields': optional_fields,
                    'issue_type': issue_type_name,
                    'issue_type_id': issue_type_id
                }
            else:
                logger.error(f"Error al obtener campos de creación: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Error al obtener campos: {response.status_code}',
                    'fields': {},
                    'required_fields': [],
                    'optional_fields': []
                }
        except Exception as e:
            logger.error(f"Error al obtener campos de creación para {project_key}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fields': {},
                'required_fields': [],
                'optional_fields': []
            }

    def check_user_membership(self, project_key: str, user_email: str) -> Dict:
        """
        Valida si un usuario es asignable (miembro) en un proyecto Jira.
        Se apoya en el endpoint de Jira: /rest/api/3/user/assignable/search?project=KEY
        """
        try:
            if not project_key or not user_email:
                return {
                    'hasAccess': False,
                    'message': 'Faltan project_key o email para validar acceso.'
                }

            url = f"{self._connection.base_url}/rest/api/3/user/assignable/search"
            params = {
                'project': project_key,
                'query': user_email,
                'maxResults': 200
            }
            response = self._connection.session.get(url, params=params, timeout=Config.JIRA_TIMEOUT_SHORT)

            if response.status_code != 200:
                logger.error(f"Error al validar membresía en {project_key}: {response.status_code} - {response.text}")
                return {
                    'hasAccess': False,
                    'message': f"Jira respondió {response.status_code} al validar permisos."
                }

            users = response.json() or []
            logger.info(f"[JiraMembership] project={project_key} query_email={user_email} results={len(users)}")
            user_email_lower = user_email.lower()

            # Validar por coincidencia exacta de email (case-insensitive)
            has_access = any(
                user_email_lower == (u.get('emailAddress') or '').lower()
                for u in users
            )

            return {
                'hasAccess': has_access,
                'message': 'Acceso confirmado al proyecto' if has_access else 'El usuario no forma parte del proyecto en Jira.'
            }
        except Exception as e:
            logger.error(f"Error al validar membresía en proyecto {project_key}: {e}", exc_info=True)
            return {
                'hasAccess': False,
                'message': f'Error al validar permisos: {str(e)}'
            }

