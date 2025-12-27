import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class Deduplicator:
    """Utilidades para deduplicación de issues"""
    
    @staticmethod
    def deduplicate_issues(issues: List[Dict], log_tag: str = "DEDUPLICATION") -> List[Dict]:
        """
        Elimina duplicados de una lista de issues priorizando ID, luego Key.
        
        Args:
            issues: Lista de issues a deduplicar
            log_tag: Tag para logging
            
        Returns:
            List[Dict]: Lista de issues únicas
        """
        seen_ids = set()
        unique_issues = []
        issues_without_key = []
        
        for issue in issues:
            # Preferir id (siempre está presente cuando no hay fields)
            issue_id = issue.get('id')
            issue_key = issue.get('key')
            
            # Usar id como identificador principal
            if issue_id:
                issue_id_str = str(issue_id)
                if issue_id_str not in seen_ids:
                    seen_ids.add(issue_id_str)
                    unique_issues.append(issue)
            elif issue_key:
                # Fallback a key si no hay id
                if issue_key not in seen_ids:
                    seen_ids.add(issue_key)
                    unique_issues.append(issue)
            else:
                # Issues sin id ni key - incluirlas para no perder datos, pero trackear
                issues_without_key.append(issue)
                unique_issues.append(issue)
        
        if len(unique_issues) != len(issues):
            logger.warning(f"[{log_tag}] Se encontraron {len(issues) - len(unique_issues)} issues duplicadas (total: {len(issues)}, únicas: {len(unique_issues)})")
            
        if issues_without_key:
             logger.warning(f"[{log_tag}] ⚠️ {len(issues_without_key)} issues sin key/id detectadas.")
             
        return unique_issues
