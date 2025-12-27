import re

class JQLHelper:
    """Utilidades para manipulación de JQL"""
    
    @staticmethod
    def simplify_jql_for_count(jql: str) -> str:
        """
        Simplifica el JQL para approximate-count usando solo variaciones comunes de issuetype.
        Esto ayuda cuando el endpoint tiene problemas con JQLs muy complejos.
        
        Args:
            jql: Query JQL original
            
        Returns:
            str: JQL simplificado
        """
        # Extraer proyecto
        project_match = re.search(r'project\s*=\s*(\w+)', jql)
        if not project_match:
            return jql  # No se puede simplificar sin proyecto
        
        project_key = project_match.group(1)
        
        # Extraer filtros adicionales (después del bloque de issuetypes)
        # Buscar el patrón: ) AND filtros
        filters_match = re.search(r'\)\s*AND\s*(.+)', jql)
        additional_filters = filters_match.group(1) if filters_match else ''
        
        # Determinar si el JQL es para tests Cases, Bugs, o ambos
        has_test_case = any(v in jql for v in ['tests Case', 'test case', 'TestCase', 'Caso de Prueba'])
        has_bug = any(v in jql for v in ['Bug', 'bug', 'BUG', 'Error', 'error', 'Defect', 'defect'])
        
        # Construir JQL simplificado
        issuetype_parts = []
        if has_test_case:
            issuetype_parts.append('issuetype = "tests Case"')
        if has_bug:
            issuetype_parts.append('issuetype = "Bug"')
        
        if not issuetype_parts:
            return jql  # No hay issuetypes conocidos, retornar original
        
        # Construir la parte de issuetypes fuera del f-string para evitar error de sintaxis
        issuetype_clause = ' OR '.join(issuetype_parts)
        simplified = f'project = {project_key} AND ({issuetype_clause})'
        if additional_filters:
            simplified += f' AND {additional_filters}'
        
        return simplified
