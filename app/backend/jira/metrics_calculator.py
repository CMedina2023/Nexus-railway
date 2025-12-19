"""
Calculadora de métricas de Jira
Responsabilidad única: Calcular métricas de proyectos e issues
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Estados que representan finalización real (comparación en minúsculas)
FINAL_STATUSES = {
    'done',
    'closed',
    'resolved',
    'finalizado',
    'completado',
    'terminado',
    'liberado',
    'exitoso',
    'listo para produccion',
    'listo para producción'
}


class MetricsCalculator:
    """Calcula métricas de proyectos e issues de Jira"""
    
    def __init__(self):
        """Inicializa la calculadora de métricas"""
        pass
    
    def is_final_status(self, status_name: Optional[str]) -> bool:
        """
        Determina si el estado actual representa una finalización real
        
        Args:
            status_name: Nombre del estado a verificar
            
        Returns:
            bool: True si es un estado final
        """
        if not status_name:
            return False
        return status_name.strip().lower() in FINAL_STATUSES
    
    def calculate_issue_metrics(self, issues: List[Dict], issue_type: str) -> Dict:
        """
        Calcula métricas de avance para un conjunto de issues
        
        Args:
            issues: Lista de issues de Jira
            issue_type: Tipo de issue (para logging)
            
        Returns:
            Dict: Métricas calculadas
        """
        if not issues:
            return {
                'total': 0,
                'by_status': {},
                'by_priority': {},
                'resolved': 0,
                'unresolved': 0,
                'percentage_resolved': 0
            }
        
        metrics = {
            'total': len(issues),
            'by_status': {},
            'by_priority': {},
            'resolved': 0,
            'unresolved': 0,
            'percentage_resolved': 0
        }
        
        for issue in issues:
            # Contar por estado
            status = issue.get('fields', {}).get('status', {}).get('name', 'Sin estado')
            metrics['by_status'][status] = metrics['by_status'].get(status, 0) + 1
            
            # Contar por prioridad
            priority = issue.get('fields', {}).get('priority', {}).get('name', 'Sin prioridad')
            metrics['by_priority'][priority] = metrics['by_priority'].get(priority, 0) + 1
            
            # Contar resueltos vs no resueltos basados en el estado actual
            if self.is_final_status(status):
                metrics['resolved'] += 1
            else:
                metrics['unresolved'] += 1
        
        # Calcular porcentaje de resueltos
        if metrics['total'] > 0:
            metrics['percentage_resolved'] = round((metrics['resolved'] / metrics['total']) * 100, 2)
        
        return metrics
    
    def calculate_general_report_metrics(self, test_cases: List[Dict], bugs: List[Dict]) -> Dict:
        """
        Calcula métricas para el reporte general
        
        Args:
            test_cases: Lista de casos de prueba
            bugs: Lista de bugs
            
        Returns:
            Dict: Métricas del reporte general
        """
        report = {
            'total_test_cases': len(test_cases),
            'successful_test_cases_percentage': 0,
            'real_coverage': 0,
            'total_defects': len(bugs),
            'defect_rate': 0,
            'open_defects': 0,
            'closed_defects': 0,
            'test_cases_by_person': {},
            'defects_by_person': [],
            'bugs_by_severity_open': {}
        }
        
        # Calcular % Successful tests Cases y Real Coverage
        success_statuses = {'exitoso', 'passed', 'done', 'closed', 'resolved', 'completado', 'finalizado'}
        not_executed_statuses = {
            'to do', 'todo', 'backlog', 'open', 'nuevo', 'new', 'pendiente', 'pending',
            'por hacer', 'sin asignar', 'unassigned', 'draft', 'borrador'
        }
        real_coverage_statuses = {
            'exitoso', 'passed', 'done', 'closed', 'resolved', 'completado', 'finalizado',
            'fallado', 'failed', 'fail', 'rejected', 'rechazado',
            'no aplica', 'not applicable', 'n/a', 'na', 'no corresponde'
        }
        
        successful_count = 0
        executed_count = 0
        real_coverage_count = 0
        
        for test_case in test_cases:
            status = test_case.get('fields', {}).get('status', {}).get('name', '').lower().strip()
            
            if status and status not in not_executed_statuses:
                executed_count += 1
                if status in success_statuses:
                    successful_count += 1
            
            if status and status in real_coverage_statuses:
                real_coverage_count += 1
        
        if executed_count > 0:
            report['successful_test_cases_percentage'] = round((successful_count / executed_count) * 100, 2)
        
        if report['total_test_cases'] > 0:
            report['real_coverage'] = round((real_coverage_count / report['total_test_cases']) * 100, 2)
        
        # Defect Rate = (defectos / casos de prueba) * 100
        if report['total_test_cases'] > 0:
            report['defect_rate'] = round((report['total_defects'] / report['total_test_cases']) * 100, 2)
        
        # Open/Closed Defects
        open_bugs = [b for b in bugs if not self.is_final_status(b.get('fields', {}).get('status', {}).get('name', ''))]
        report['open_defects'] = len(open_bugs)
        report['closed_defects'] = report['total_defects'] - report['open_defects']
        
        # Bugs por severidad (solo abiertos)
        for bug in open_bugs:
            priority = bug.get('fields', {}).get('priority', {}).get('name', 'Sin prioridad')
            report['bugs_by_severity_open'][priority] = report['bugs_by_severity_open'].get(priority, 0) + 1
        
        # tests Cases por persona
        for test_case in test_cases:
            assignee = test_case.get('fields', {}).get('assignee')
            assignee_name = assignee.get('displayName', 'Sin asignar') if assignee else 'Sin asignar'
            status = test_case.get('fields', {}).get('status', {}).get('name', 'Sin estado')
            
            if assignee_name not in report['test_cases_by_person']:
                report['test_cases_by_person'][assignee_name] = {
                    'exitoso': 0,
                    'en_progreso': 0,
                    'fallado': 0,
                    'total': 0
                }
            
            person_stats = report['test_cases_by_person'][assignee_name]
            person_stats['total'] += 1
            
            status_lower = status.lower()
            if status_lower in success_statuses:
                person_stats['exitoso'] += 1
            elif 'progreso' in status_lower or 'progress' in status_lower or 'en curso' in status_lower:
                person_stats['en_progreso'] += 1
            elif 'fallado' in status_lower or 'failed' in status_lower or 'error' in status_lower:
                person_stats['fallado'] += 1
        
        # Defects por persona (lista completa con detalles)
        for bug in bugs:
            assignee = bug.get('fields', {}).get('assignee')
            assignee_name = assignee.get('displayName', 'Sin asignar') if assignee else 'Sin asignar'
            status = bug.get('fields', {}).get('status', {}).get('name', 'Sin estado')
            priority = bug.get('fields', {}).get('priority', {}).get('name', 'Sin prioridad')
            summary = bug.get('fields', {}).get('summary', 'Sin resumen')
            key = bug.get('key', '')
            
            report['defects_by_person'].append({
                'key': key,
                'assignee': assignee_name,
                'status': status,
                'summary': summary[:50] + '...' if len(summary) > 50 else summary,
                'severity': priority
            })
        
        return report

