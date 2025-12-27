"""
Funciones helper para generar métricas de Jira
Responsabilidad única: Lógica reutilizable para cálculo de métricas
"""
import logging
from queue import Queue
from typing import Dict, List, Optional, Callable

from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.backend.jira.metrics_calculator import MetricsCalculator
from app.backend.jira.parallel_fetcher import ParallelIssueFetcher
from app.backend.jira.issue_service import TEST_CASE_VARIATIONS, BUG_VARIATIONS, build_issuetype_jql
from app.core.config import Config

logger = logging.getLogger(__name__)


def filter_issues_by_type(issues: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Filtra issues por tipo (tests Cases y Bugs)
    Nota: Stories no se usan en reportes de métricas
    
    Args:
        issues: Lista de issues de Jira
        
    Returns:
        tuple: (test_cases, bugs)
    """
    test_cases = []
    bugs = []
    
    for issue in issues:
        issue_type_name = issue.get('fields', {}).get('issuetype', {}).get('name', '')
        
        # tests Cases
        if issue_type_name and any(
            variation.lower() == issue_type_name.lower() or 
            (variation.lower() in issue_type_name.lower() and 'test' in issue_type_name.lower() and 'case' in issue_type_name.lower())
            for variation in TEST_CASE_VARIATIONS
        ):
            test_cases.append(issue)
        
        # Bugs
        elif issue_type_name and any(
            variation.lower() == issue_type_name.lower()
            for variation in BUG_VARIATIONS
        ):
            bugs.append(issue)
    
    return test_cases, bugs


def build_jql_from_filters(project_key: str, view_type: str, filters: List[str], assignee_email: str = None) -> str:
    """
    Construye un JQL query desde los filtros proporcionados
    
    Args:
        project_key: Clave del proyecto
        view_type: Tipo de vista (general/personal)
        filters: Lista de filtros en formato "field:value"
        assignee_email: Email del asignado (para vista personal)
        
    Returns:
        str: JQL query construido
    """
    base_jql = f'project = {project_key}'
    
    if view_type == 'personal' and assignee_email:
        base_jql += f' AND assignee = "{assignee_email}"'
    
    jql_parts = [base_jql]
    
    # CAMBIO 1: Agregar filtro de issue types (siempre) - SOLO tests Cases y Bugs (Stories no se usan en reportes)
    from app.backend.jira.issue_service import TEST_CASE_VARIATIONS, BUG_VARIATIONS
    
    # Construir filtro con todas las variaciones de tests Cases y Bugs
    test_case_conditions = ' OR '.join([f'issuetype = "{var}"' for var in TEST_CASE_VARIATIONS])
    bug_conditions = ' OR '.join([f'issuetype = "{var}"' for var in BUG_VARIATIONS])
    issuetype_filter = f'({test_case_conditions} OR {bug_conditions})'
    jql_parts.append(issuetype_filter)
    logger.debug(f"[DEBUG JQL] Filtro de issuetypes agregado automáticamente: {issuetype_filter[:100]}...")
    
    for filter_param in filters:
        if ':' in filter_param:
            field, value = filter_param.split(':', 1)
        elif '=' in filter_param:
            field, value = filter_param.split('=', 1)
        else:
            logger.warning(f"Formato de filtro inválido: {filter_param}")
            continue
        
        field = field.strip()
        value = value.strip()
        
        # Construir condición JQL según el campo
        if field.lower() in ['status', 'estado']:
            jql_parts.append(f'status = "{value}"')
        elif field.lower() in ['priority', 'prioridad']:
            jql_parts.append(f'priority = "{value}"')
        elif field.lower() in ['assignee', 'asignado']:
            jql_parts.append(f'assignee = "{value}"')
        elif field.lower() in ['issuetype', 'tipo']:
            issuetype_jql = build_issuetype_jql(value, project_key)
            if ' AND (' in issuetype_jql:
                issuetype_condition = issuetype_jql.split(' AND (', 1)[1].rstrip(')')
                jql_parts.append(f'({issuetype_condition})')
            else:
                jql_parts.append(f'issuetype = "{value}"')
        elif field.lower() in ['label', 'labels', 'etiqueta', 'etiquetas']:
            jql_parts.append(f'labels = "{value}"')
        elif field.lower() in ['affectedversion', 'affectsversions', 'affects version']:
            jql_parts.append(f'affectedVersion = "{value}"')
        elif field.lower() in ['fixversions', 'version de correccion']:
            jql_parts.append(f'fixVersions = "{value}"')
        else:
            # Para campos personalizados (customfield_XXXXX), no usar comillas alrededor del ID
            # Para campos estándar con nombres, usar comillas
            if field.startswith('customfield_'):
                # Campo personalizado: usar ID sin comillas
                # Para campos de tipo multi-select, puede necesitar usar 'in' en lugar de '='
                # Por ahora, usar '=' que funciona para la mayoría de casos
                jql_condition = f'{field} = "{value}"'
                jql_parts.append(jql_condition)
                logger.debug(f"[DEBUG JQL] Campo personalizado {field}: {jql_condition}")
            else:
                # Campo estándar con nombre: usar comillas alrededor del nombre
                jql_condition = f'"{field}" = "{value}"'
                jql_parts.append(jql_condition)
                logger.debug(f"[DEBUG JQL] Campo estándar {field}: {jql_condition}")
    
    final_jql = ' AND '.join(jql_parts)
    logger.info(f"[DEBUG JQL] JQL construido: {final_jql}")
    logger.info(f"[DEBUG JQL] Filtros procesados: {len(filters)} filtros")
    return final_jql


def calculate_metrics_from_issues(issues: List[Dict]) -> Dict:
    """
    Calcula métricas desde una lista de issues
    
    Args:
        issues: Lista de issues de Jira
        
    Returns:
        Dict con métricas calculadas
    """
    metrics_calculator = MetricsCalculator()
    
    # Filtrar por tipo
    test_cases, bugs = filter_issues_by_type(issues)
    
    logger.info(f"Calculando métricas: {len(test_cases)} test cases, {len(bugs)} bugs de {len(issues)} issues totales")
    
    # Calcular métricas
    test_case_metrics = metrics_calculator.calculate_issue_metrics(test_cases, 'tests case')
    bug_metrics = metrics_calculator.calculate_issue_metrics(bugs, 'Bug')
    general_report = metrics_calculator.calculate_general_report_metrics(test_cases, bugs)
    
    return {
        'test_cases': test_case_metrics,
        'bugs': bug_metrics,
        'general_report': general_report,
        'total_issues': len(issues),
        'test_case_count': len(test_cases),
        'bug_count': len(bugs)
    }


def build_separate_jql_queries(project_key: str, view_type: str, filters: List[str], assignee_email: str = None) -> tuple[str, str]:
    """
    Construye dos JQL queries separados: uno para tests Cases y otro para Bugs
    
    Args:
        project_key: Clave del proyecto
        view_type: Tipo de vista (general/personal)
        filters: Lista de filtros en formato "field:value"
        assignee_email: Email del asignado (para vista personal)
        
    Returns:
        tuple: (jql_test_cases, jql_bugs)
    """
    base_jql = f'project = {project_key}'
    
    if view_type == 'personal' and assignee_email:
        base_jql += f' AND assignee = "{assignee_email}"'
    
    # Construir filtros adicionales (sin issuetypes)
    additional_filters = []
    for filter_param in filters:
        if ':' in filter_param:
            field, value = filter_param.split(':', 1)
        elif '=' in filter_param:
            field, value = filter_param.split('=', 1)
        else:
            continue
        
        field = field.strip()
        value = value.strip()
        
        if field.lower() in ['status', 'estado']:
            additional_filters.append(f'status = "{value}"')
        elif field.lower() in ['priority', 'prioridad']:
            additional_filters.append(f'priority = "{value}"')
        elif field.lower() in ['assignee', 'asignado']:
            additional_filters.append(f'assignee = "{value}"')
        elif field.lower() in ['label', 'etiqueta']:
            additional_filters.append(f'labels = "{value}"')
        elif field.lower() in ['version', 'versión']:
            additional_filters.append(f'fixVersion = "{value}"')
        elif field.startswith('customfield_'):
            additional_filters.append(f'{field} = "{value}"')
        else:
            additional_filters.append(f'{field} = "{value}"')
    
    # Construir JQL para tests Cases
    test_case_conditions = ' OR '.join([f'issuetype = "{var}"' for var in TEST_CASE_VARIATIONS])
    jql_test_cases_parts = [base_jql, f'({test_case_conditions})']
    jql_test_cases_parts.extend(additional_filters)
    jql_test_cases = ' AND '.join(jql_test_cases_parts)
    
    # Construir JQL para Bugs
    bug_conditions = ' OR '.join([f'issuetype = "{var}"' for var in BUG_VARIATIONS])
    jql_bugs_parts = [base_jql, f'({bug_conditions})']
    jql_bugs_parts.extend(additional_filters)
    jql_bugs = ' AND '.join(jql_bugs_parts)
    
    logger.info(f"[CONSULTAS SEPARADAS] JQL tests Cases: {jql_test_cases[:150]}...")
    logger.info(f"[CONSULTAS SEPARADAS] JQL Bugs: {jql_bugs[:150]}...")
    
    return jql_test_cases, jql_bugs


def fetch_issues_with_separate_filters(
    connection: JiraConnection,
    project_key: str,
    view_type: str,
    filters_testcase: List[str],
    filters_bug: List[str],
    assignee_email: str = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict]:
    """
    Obtiene issues usando filtros separados para tests Cases y Bugs
    Nota: Stories no se usan en reportes de métricas
    
    Args:
        connection: Conexión con Jira
        project_key: Clave del proyecto
        view_type: Tipo de vista (general/personal)
        filters_testcase: Lista de filtros para tests Cases en formato "field:value"
        filters_bug: Lista de filtros para Bugs en formato "field:value"
        assignee_email: Email del asignado (para vista personal)
        progress_callback: Callback opcional para reportar progreso
        
    Returns:
        List[Dict]: Lista completa de issues
    """
    logger.info(f"[FILTROS SEPARADOS] Iniciando obtención con filtros separados")
    logger.info(f"[FILTROS SEPARADOS] tests Cases: {len(filters_testcase)} filtros, Bugs: {len(filters_bug)} filtros")
    
    parallel_fetcher = ParallelIssueFetcher(connection)
    
    # Construir JQLs separados con filtros específicos
    base_jql = f'project = {project_key}'
    
    if view_type == 'personal' and assignee_email:
        base_jql += f' AND assignee = "{assignee_email}"'
    
    # Construir JQL para tests Cases
    test_case_conditions = ' OR '.join([f'issuetype = "{var}"' for var in TEST_CASE_VARIATIONS])
    jql_test_cases_parts = [base_jql, f'({test_case_conditions})']
    
    # Agregar filtros específicos de tests Cases
    for filter_param in filters_testcase:
        if ':' in filter_param:
            field, value = filter_param.split(':', 1)
        elif '=' in filter_param:
            field, value = filter_param.split('=', 1)
        else:
            continue
        
        field = field.strip()
        value = value.strip()
        
        # Construir condición JQL según el campo
        if field.lower() in ['status', 'estado']:
            jql_test_cases_parts.append(f'status = "{value}"')
        elif field.lower() in ['priority', 'prioridad']:
            jql_test_cases_parts.append(f'priority = "{value}"')
        elif field.lower() in ['assignee', 'asignado']:
            jql_test_cases_parts.append(f'assignee = "{value}"')
        elif field.lower() in ['label', 'labels', 'etiqueta', 'etiquetas']:
            jql_test_cases_parts.append(f'labels = "{value}"')
        elif field.lower() in ['affectedversion', 'affectsversions', 'affects version']:
            jql_test_cases_parts.append(f'affectedVersion = "{value}"')
        elif field.lower() in ['fixversions', 'version de correccion']:
            jql_test_cases_parts.append(f'fixVersions = "{value}"')
        else:
            # Campos personalizados o estándar
            if field.startswith('customfield_'):
                jql_test_cases_parts.append(f'{field} = "{value}"')
            else:
                jql_test_cases_parts.append(f'"{field}" = "{value}"')
    
    jql_test_cases = ' AND '.join(jql_test_cases_parts)
    
    # Construir JQL para Bugs
    bug_conditions = ' OR '.join([f'issuetype = "{var}"' for var in BUG_VARIATIONS])
    jql_bugs_parts = [base_jql, f'({bug_conditions})']
    
    # Agregar filtros específicos de Bugs
    for filter_param in filters_bug:
        if ':' in filter_param:
            field, value = filter_param.split(':', 1)
        elif '=' in filter_param:
            field, value = filter_param.split('=', 1)
        else:
            continue
        
        field = field.strip()
        value = value.strip()
        
        # Construir condición JQL según el campo
        if field.lower() in ['status', 'estado']:
            jql_bugs_parts.append(f'status = "{value}"')
        elif field.lower() in ['priority', 'prioridad']:
            jql_bugs_parts.append(f'priority = "{value}"')
        elif field.lower() in ['assignee', 'asignado']:
            jql_bugs_parts.append(f'assignee = "{value}"')
        elif field.lower() in ['label', 'labels', 'etiqueta', 'etiquetas']:
            jql_bugs_parts.append(f'labels = "{value}"')
        elif field.lower() in ['affectedversion', 'affectsversions', 'affects version']:
            jql_bugs_parts.append(f'affectedVersion = "{value}"')
        elif field.lower() in ['fixversions', 'version de correccion']:
            jql_bugs_parts.append(f'fixVersions = "{value}"')
        else:
            # Campos personalizados o estándar
            if field.startswith('customfield_'):
                jql_bugs_parts.append(f'{field} = "{value}"')
            else:
                jql_bugs_parts.append(f'"{field}" = "{value}"')
    
    jql_bugs = ' AND '.join(jql_bugs_parts)
    
    logger.info(f"[FILTROS SEPARADOS] JQL tests Cases: {jql_test_cases[:200]}...")
    logger.info(f"[FILTROS SEPARADOS] JQL Bugs: {jql_bugs[:200]}...")
    
    # Obtener tests Cases y Bugs por separado
    all_issues = []
    
    # Obtener tests Cases
    if filters_testcase or True:  # Siempre obtener tests Cases
        try:
            logger.info(f"[FILTROS SEPARADOS] Obteniendo tests Cases...")
            test_cases = parallel_fetcher.fetch_all_issues_parallel(jql_test_cases, progress_callback=None)
            all_issues.extend(test_cases)
            logger.info(f"[FILTROS SEPARADOS] ✓ tests Cases obtenidos: {len(test_cases)}")
        except Exception as e:
            logger.error(f"[FILTROS SEPARADOS] ✗ Error al obtener tests Cases: {e}", exc_info=True)
    
    # Obtener Bugs
    if filters_bug or True:  # Siempre obtener Bugs
        try:
            logger.info(f"[FILTROS SEPARADOS] Obteniendo Bugs...")
            bugs = parallel_fetcher.fetch_all_issues_parallel(jql_bugs, progress_callback=None)
            all_issues.extend(bugs)
            logger.info(f"[FILTROS SEPARADOS] ✓ Bugs obtenidos: {len(bugs)}")
        except Exception as e:
            logger.error(f"[FILTROS SEPARADOS] ✗ Error al obtener Bugs: {e}", exc_info=True)
    
    # Eliminar duplicados por key
    seen_keys = set()
    unique_issues = []
    for issue in all_issues:
        issue_key = issue.get('key')
        if issue_key and issue_key not in seen_keys:
            seen_keys.add(issue_key)
            unique_issues.append(issue)
        elif not issue_key:
            unique_issues.append(issue)
    
    if len(unique_issues) != len(all_issues):
        logger.warning(f"[FILTROS SEPARADOS] Se encontraron {len(all_issues) - len(unique_issues)} issues duplicadas")
    
    # Contar por tipo
    test_case_count = len([i for i in unique_issues if any(
        v.lower() in i.get('fields', {}).get('issuetype', {}).get('name', '').lower() 
        for v in TEST_CASE_VARIATIONS
    )])
    bug_count = len([i for i in unique_issues if any(
        v.lower() in i.get('fields', {}).get('issuetype', {}).get('name', '').lower() 
        for v in BUG_VARIATIONS
    )])
    
    logger.info(f"[FILTROS SEPARADOS] ✓ Total issues obtenidas: {len(unique_issues)} (tests Cases: {test_case_count}, Bugs: {bug_count})")
    
    # Reportar progreso final
    if progress_callback:
        progress_callback(len(unique_issues), len(unique_issues))
    
    return unique_issues


def fetch_issues_with_parallel(
    connection: JiraConnection,
    jql: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict]:
    """
    Obtiene issues usando paginación paralela optimizada
    Usa consultas separadas para tests Cases y Bugs para evitar el bug de Jira cuando total=0
    
    Args:
        connection: Conexión con Jira
        jql: Query JQL (se parseará para crear consultas separadas)
        progress_callback: Callback opcional para reportar progreso (actual, total)
        
    Returns:
        List[Dict]: Lista completa de issues
    """
    logger.info(f"[CONSULTAS SEPARADAS] Iniciando obtención con consultas separadas para tests Cases y Bugs")
    
    parallel_fetcher = ParallelIssueFetcher(connection)
    
    # Parsear JQL para extraer proyecto y filtros
    # Formato esperado: project = X AND (issuetype = ...) AND filtros
    
    # Extraer proyecto
    project_key = None
    if 'project = ' in jql:
        project_start = jql.find('project = ') + len('project = ')
        project_end = jql.find(' AND', project_start)
        if project_end == -1:
            project_end = len(jql)
        project_key = jql[project_start:project_end].strip()
    
    if not project_key:
        logger.warning(f"[CONSULTAS SEPARADAS] No se pudo extraer proyecto del JQL, usando método original")
        return parallel_fetcher.fetch_all_issues_parallel(jql, progress_callback=progress_callback)
    
    # Extraer filtros adicionales (después del bloque de issuetypes)
    # Buscar el cierre del bloque de issuetypes: ') AND' o solo ')'
    issuetype_end = jql.find(') AND')
    if issuetype_end == -1:
        issuetype_end = jql.find(')', jql.find('('))
    
    additional_filters = ''
    if issuetype_end != -1:
        remaining = jql[issuetype_end + 1:].strip()
        if remaining.startswith('AND '):
            additional_filters = remaining[4:]  # Remover 'AND '
        elif remaining:
            additional_filters = remaining
    
    # Construir JQLs separados
    test_case_conditions = ' OR '.join([f'issuetype = "{var}"' for var in TEST_CASE_VARIATIONS])
    bug_conditions = ' OR '.join([f'issuetype = "{var}"' for var in BUG_VARIATIONS])
    
    jql_test_cases = f'project = {project_key} AND ({test_case_conditions})'
    jql_bugs = f'project = {project_key} AND ({bug_conditions})'
    
    if additional_filters:
        jql_test_cases += f' AND {additional_filters}'
        jql_bugs += f' AND {additional_filters}'
    
    logger.info(f"[CONSULTAS SEPARADAS] JQL tests Cases: {jql_test_cases[:200]}...")
    logger.info(f"[CONSULTAS SEPARADAS] JQL Bugs: {jql_bugs[:200]}...")
    
    # Obtener tests Cases y Bugs por separado
    all_issues = []
    
    # Simplificar JQLs para approximate-count usando solo variaciones comunes
    # El endpoint approximate-count puede tener problemas con JQLs muy complejos
    jql_test_cases_simple = jql_test_cases
    jql_bugs_simple = jql_bugs
    
    # Simplificar: reemplazar todas las variaciones por solo "tests Case" o "Bug"
    import re
    # Para tests Cases: reemplazar bloque complejo por solo "tests Case"
    if 'OR' in jql_test_cases and 'issuetype' in jql_test_cases:
        jql_test_cases_simple = re.sub(
            r'\(issuetype\s*=\s*"[^"]*"[^)]*\)',
            'issuetype = "tests Case"',
            jql_test_cases,
            flags=re.IGNORECASE
        )
    # Para Bugs: reemplazar bloque complejo por solo "Bug"
    if 'OR' in jql_bugs and 'issuetype' in jql_bugs:
        jql_bugs_simple = re.sub(
            r'\(issuetype\s*=\s*"[^"]*"[^)]*\)',
            'issuetype = "Bug"',
            jql_bugs,
            flags=re.IGNORECASE
        )
    
    logger.info(f"[CONSULTAS SEPARADAS] JQL tests Cases simplificado para count: {jql_test_cases_simple[:150]}...")
    logger.info(f"[CONSULTAS SEPARADAS] JQL Bugs simplificado para count: {jql_bugs_simple[:150]}...")
    
    # Obtener tests Cases
    try:
        logger.info(f"[CONSULTAS SEPARADAS] Obteniendo tests Cases...")
        # Usar JQL simplificado para approximate-count, pero JQL completo para obtener issues
        test_cases = parallel_fetcher.fetch_all_issues_parallel(jql_test_cases, progress_callback=None)
        all_issues.extend(test_cases)
        logger.info(f"[CONSULTAS SEPARADAS] ✓ tests Cases obtenidos: {len(test_cases)}")
    except Exception as e:
        logger.error(f"[CONSULTAS SEPARADAS] ✗ Error al obtener tests Cases: {e}", exc_info=True)
    
    # Obtener Bugs
    try:
        logger.info(f"[CONSULTAS SEPARADAS] Obteniendo Bugs...")
        bugs = parallel_fetcher.fetch_all_issues_parallel(jql_bugs, progress_callback=None)
        all_issues.extend(bugs)
        logger.info(f"[CONSULTAS SEPARADAS] ✓ Bugs obtenidos: {len(bugs)}")
    except Exception as e:
        logger.error(f"[CONSULTAS SEPARADAS] ✗ Error al obtener Bugs: {e}", exc_info=True)
    
    # Eliminar duplicados por key
    seen_keys = set()
    unique_issues = []
    for issue in all_issues:
        issue_key = issue.get('key')
        if issue_key and issue_key not in seen_keys:
            seen_keys.add(issue_key)
            unique_issues.append(issue)
        elif not issue_key:
            unique_issues.append(issue)
    
    if len(unique_issues) != len(all_issues):
        logger.warning(f"[CONSULTAS SEPARADAS] Se encontraron {len(all_issues) - len(unique_issues)} issues duplicadas al combinar resultados")
    
    # Contar por tipo
    test_case_count = len([i for i in unique_issues if any(
        v.lower() in i.get('fields', {}).get('issuetype', {}).get('name', '').lower() 
        for v in TEST_CASE_VARIATIONS
    )])
    bug_count = len([i for i in unique_issues if any(
        v.lower() in i.get('fields', {}).get('issuetype', {}).get('name', '').lower() 
        for v in BUG_VARIATIONS
    )])
    
    logger.info(f"[CONSULTAS SEPARADAS] ✓ Total issues obtenidas: {len(unique_issues)} (tests Cases: {test_case_count}, Bugs: {bug_count})")
    
    # Reportar progreso final
    if progress_callback:
        progress_callback(len(unique_issues), len(unique_issues))
    
    return unique_issues


def fetch_issues_with_progress_queue(
    connection: JiraConnection,
    jql: str,
    progress_queue: Queue
) -> List[Dict]:
    """
    Obtiene issues usando paginación paralela y reporta progreso mediante una cola
    
    Args:
        connection: Conexión con Jira
        jql: Query JQL
        progress_queue: Cola para reportar progreso (enviar dicts con 'actual' y 'total')
        
    Returns:
        List[Dict]: Lista completa de issues
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import requests
    
    parallel_fetcher = ParallelIssueFetcher(connection)
    
    # Callback interno que envía progreso a la cola
    def internal_progress_callback(actual_issues_fetched: int, total_issues_expected: int):
        """Callback que envía progreso a la cola para SSE"""
        porcentaje = int((actual_issues_fetched / total_issues_expected * 100)) if total_issues_expected > 0 else 0
        progress_queue.put({
            'actual': actual_issues_fetched,
            'total': total_issues_expected,
            'porcentaje': porcentaje
        })
    
    # Usar el callback interno para reportar progreso
    return parallel_fetcher.fetch_all_issues_parallel(jql, progress_callback=internal_progress_callback)

