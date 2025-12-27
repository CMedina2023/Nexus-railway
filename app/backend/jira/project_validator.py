"""
Componente para validaciones relacionadas con proyectos de Jira
"""
import logging
from typing import Dict, List, Optional
from app.backend.jira.project_fetcher import ProjectFetcher
from app.backend.jira.issue_fetcher import TEST_CASE_VARIATIONS, BUG_VARIATIONS

logger = logging.getLogger(__name__)

class ProjectValidator:
    """Componente responsable de las validaciones de negocio"""
    
    def __init__(self, fetcher: ProjectFetcher):
        self._fetcher = fetcher

    def check_user_membership(self, project_key: str, user_email: str) -> Dict:
        """
        Valida si un usuario es asignable (miembro) en un proyecto Jira.
        """
        if not project_key or not user_email:
            return {
                'hasAccess': False,
                'message': 'Faltan project_key o email para validar acceso.'
            }

        users = self._fetcher.search_assignable_users(project_key, user_email)
        
        # Si search_assignable_users retorna None, hubo error
        if users is None:
             return {
                'hasAccess': False,
                # Mensaje genérico, el fetcher ya logueó el error específico
                'message': f"Error al validar permisos en Jira."
            }

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

    def filter_testcases_and_bugs(self, issue_types: List[Dict]) -> List[Dict]:
        """
        Filtra solo tests Cases y Bugs de una lista de tipos de issue.
        Considerado una validación de tipos soportados.
        """
        filtered = []
        seen_ids = set()
        
        for issue_type in issue_types:
            issue_type_id = issue_type.get('id', '')
            issue_type_name = issue_type.get('name', '').strip()
            
            # Evitar duplicados
            if issue_type_id and issue_type_id in seen_ids:
                continue
            
            # Verificar si es tests Case
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
            
            # Solo incluir si es tests Case o Bug
            if is_test_case or is_bug:
                seen_ids.add(issue_type_id)
                filtered.append({
                    'id': issue_type_id,
                    'name': issue_type_name,
                    'description': issue_type.get('description', ''),
                    'iconUrl': issue_type.get('iconUrl', ''),
                    'subtask': issue_type.get('subtask', False)
                })
        
        logger.info(f"[DEBUG] Filtrados {len(filtered)} issuetypes (tests Cases y Bugs) de {len(issue_types)} totales")
        return filtered
