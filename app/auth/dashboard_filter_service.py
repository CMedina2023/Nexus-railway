import logging
import json
from collections import defaultdict
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DashboardFilterService:
    """
    Servicio que encapsula la lógica de filtrado de datos para el dashboard
    basándose en el rol del usuario (Admin vs Otros).
    """

    @staticmethod
    def get_filtered_items(user: Any, repo: Any, limit: Optional[int] = None) -> List[Any]:
        # ... (código existente)
        if user.role == 'admin':
            items = repo.get_all(limit=limit)
            logger.info(f"Admin {user.email} consultó todos los registros de {repo.__class__.__name__}")
        else:
            items = repo.get_by_user_id(user.id, limit=limit)
            logger.info(f"Usuario {user.email} consultó sus registros de {repo.__class__.__name__}")
        return items

    @staticmethod
    def get_activity_metrics(user: Any, repos: Dict[str, Any]) -> Dict[str, Any]:
        # ... (código existente)
        is_admin = user.role == 'admin'
        
        if is_admin:
            metrics = {
                "stories_generated": repos['story'].count_all(),
                "test_cases_generated": repos['test_case'].count_all(),
                "reports_created": repos['report'].count_all(),
                "bulk_uploads_performed": repos['upload'].count_all(),
                "view_type": "global"
            }
            logger.info(f"Admin {user.email} consultó métricas globales")
        else:
            metrics = {
                "stories_generated": repos['story'].count_by_user(user.id),
                "test_cases_generated": repos['test_case'].count_by_user(user.id),
                "reports_created": repos['report'].count_by_user(user.id),
                "bulk_uploads_performed": repos['upload'].count_by_user(user.id),
                "view_type": "personal"
            }
            logger.info(f"Usuario {user.email} consultó sus métricas personales")
            
        return metrics

    @staticmethod
    def get_dashboard_summary(user: Any, repos: Dict[str, Any]) -> Dict[str, Any]:
        # ... (código existente)
        is_admin = user.role == 'admin'
        
        if is_admin:
            summary = {
                "total_stories": repos['story'].count_all(),
                "total_test_cases": repos['test_case'].count_all(),
                "total_reports": repos['report'].count_all(),
                "total_bulk_uploads": repos['upload'].count_all(),
                "recent_stories": [s.to_dict() for s in repos['story'].get_all(limit=5)],
                "recent_test_cases": [tc.to_dict() for tc in repos['test_case'].get_all(limit=5)],
                "recent_reports": [r.to_dict() for r in repos['report'].get_all(limit=5)],
                "recent_bulk_uploads": [u.to_dict() for u in repos['upload'].get_all(limit=5)],
                "view_type": "global"
            }
        else:
            summary = {
                "total_stories": repos['story'].count_by_user(user.id),
                "total_test_cases": repos['test_case'].count_by_user(user.id),
                "total_reports": repos['report'].count_by_user(user.id),
                "total_bulk_uploads": repos['upload'].count_by_user(user.id),
                "recent_stories": [s.to_dict() for s in repos['story'].get_by_user_id(user.id, limit=5)],
                "recent_test_cases": [tc.to_dict() for tc in repos['test_case'].get_by_user_id(user.id, limit=5)],
                "recent_reports": [r.to_dict() for r in repos['report'].get_by_user_id(user.id, limit=5)],
                "recent_bulk_uploads": [u.to_dict() for u in repos['upload'].get_by_user_id(user.id, limit=5)],
                "view_type": "personal"
            }
            
        return summary

    @staticmethod
    def get_complex_metrics(user: Any, repos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene métricas complejas con historial y distribución, filtradas por rol (Admin ve TODO).
        """
        is_admin = user.role == 'admin'
        
        # 1. Obtener datos según rol
        if is_admin:
            stories = repos['story'].get_all()
            test_cases = repos['test_case'].get_all()
            reports_all = repos['report'].get_all()
            uploads = repos['upload'].get_all()
            total_stories = repos['story'].count_all()
            total_test_cases = repos['test_case'].count_all()
        else:
            stories = repos['story'].get_by_user_id(user.id)
            test_cases = repos['test_case'].get_by_user_id(user.id)
            reports_all = repos['report'].get_by_user_id(user.id)
            uploads = repos['upload'].get_by_user_id(user.id)
            total_stories = repos['story'].count_by_user(user.id)
            total_test_cases = repos['test_case'].count_by_user(user.id)

        # 2. PROCESAR MÉTRICAS DEL GENERADOR
        history = []
        for story in stories:
            history.append(DashboardFilterService._format_history_item(story, 'stories', 'story_content'))
        for tc in test_cases:
            history.append(DashboardFilterService._format_history_item(tc, 'testCases', 'test_case_content'))
        
        history.sort(key=lambda x: x['date'] or '', reverse=True)
        
        generator_metrics = {
            'stories': total_stories,
            'testCases': total_test_cases,
            'history': history,
            'view_type': 'global' if is_admin else 'personal'
        }

        # 3. PROCESAR MÉTRICAS DE JIRA
        reports = [r for r in reports_all if r.report_type != 'metrics']
        reports_by_project = defaultdict(lambda: {'count': 0, 'name': '', 'lastDate': None})
        reports_history = []
        
        for r in reports:
            key = r.project_key
            reports_by_project[key]['count'] += 1
            reports_by_project[key]['name'] = key
            if r.created_at:
                date_iso = r.created_at.isoformat()
                if not reports_by_project[key]['lastDate'] or date_iso > reports_by_project[key]['lastDate']:
                    reports_by_project[key]['lastDate'] = r.created_at.strftime('%Y-%m-%d')
                reports_history.append({
                    'project_key': key,
                    'created_at': date_iso,
                    'timestamp': r.created_at.timestamp() * 1000
                })
        
        reports_history.sort(key=lambda x: x['created_at'], reverse=True)
        last_report_date = max((r.created_at for r in reports if r.created_at), default=None)
        
        # Cargas masivas
        total_items_uploaded = sum(u.successful_items or 0 for u in uploads)
        uploads_by_project = defaultdict(lambda: {'count': 0, 'name': '', 'itemsCount': 0, 'lastDate': None, 'issueTypesDistribution': {}})
        issue_types_distribution = defaultdict(int)
        uploads_history = []
        
        for u in uploads:
            key = u.project_key
            uploads_by_project[key]['count'] += 1
            uploads_by_project[key]['name'] = key
            uploads_by_project[key]['itemsCount'] += u.successful_items or 0
            if u.created_at:
                date_iso = u.created_at.isoformat()
                if not uploads_by_project[key]['lastDate'] or date_iso > uploads_by_project[key]['lastDate']:
                    uploads_by_project[key]['lastDate'] = u.created_at.strftime('%Y-%m-%d')
                
                # Detalles y distribución
                try:
                    details = json.loads(u.upload_details) if isinstance(u.upload_details, str) else u.upload_details
                    if details and 'issue_types_distribution' in details:
                        for itype, count in details['issue_types_distribution'].items():
                            issue_types_distribution[itype] += count
                            uploads_by_project[key]['issueTypesDistribution'][itype] = \
                                uploads_by_project[key]['issueTypesDistribution'].get(itype, 0) + count
                except:
                    details = {}

                uploads_history.append({
                    'project_key': key,
                    'itemsCount': u.successful_items or 0,
                    'created_at': date_iso,
                    'timestamp': u.created_at.timestamp() * 1000,
                    'upload_details': details
                })
        
        uploads_history.sort(key=lambda x: x['created_at'], reverse=True)

        return {
            'success': True,
            'generator_metrics': generator_metrics,
            'jira_metrics': {
                'reports': {
                    'count': len(reports),
                    'byProject': dict(reports_by_project),
                    'lastDate': last_report_date.strftime('%Y-%m-%d') if last_report_date else None,
                    'history': reports_history
                },
                'uploads': {
                    'count': len(uploads),
                    'itemsCount': total_items_uploaded,
                    'byProject': dict(uploads_by_project),
                    'issueTypesDistribution': dict(issue_types_distribution),
                    'history': uploads_history
                }
            }
        }

    @staticmethod
    def _format_history_item(item: Any, type_name: str, content_attr: str) -> Dict[str, Any]:
        """Helper para formatear ítems del historial"""
        try:
            content = getattr(item, content_attr)
            data = json.loads(content) if isinstance(content, str) else content
            count = len(data) if isinstance(data, list) else 1
        except:
            count = 1
            
        return {
            'type': type_name,
            'count': count,
            'area': item.area or 'Sin área',
            'date': item.created_at.isoformat() if item.created_at else None
        }
