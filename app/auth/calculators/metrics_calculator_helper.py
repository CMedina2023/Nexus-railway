"""
Módulo para el cálculo de métricas de issues de Jira.
Responsabilidad: Procesar colecciones de issues para extraer KPIs y reportes.
"""
import logging
from typing import Dict, List, Tuple
from app.backend.jira.metrics_calculator import MetricsCalculator as CoreMetricsCalculator
from app.backend.jira.issue_service import TEST_CASE_VARIATIONS, BUG_VARIATIONS

logger = logging.getLogger(__name__)

class MetricsCalculatorHelper:
    """Clase para filtrar issues y calcular métricas."""

    def __init__(self):
        self.core_calculator = CoreMetricsCalculator()

    def filter_issues_by_type(self, issues: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filtra issues por tipo (Test Cases y Bugs).
        
        Args:
            issues: Lista de issues de Jira.
            
        Returns:
            Tuple: (test_cases, bugs)
        """
        test_cases = []
        bugs = []
        
        for issue in issues:
            issue_type_name = issue.get('fields', {}).get('issuetype', {}).get('name', '')
            if not issue_type_name:
                continue

            # Check Test Cases
            if any(var.lower() == issue_type_name.lower() or 
                  (var.lower() in issue_type_name.lower() and 'test' in issue_type_name.lower() and 'case' in issue_type_name.lower())
                  for var in TEST_CASE_VARIATIONS):
                test_cases.append(issue)
            # Check Bugs
            elif any(var.lower() == issue_type_name.lower() for var in BUG_VARIATIONS):
                bugs.append(issue)
        
        return test_cases, bugs

    def calculate_metrics_from_issues(self, issues: List[Dict]) -> Dict:
        """
        Calcula métricas completas desde una lista de issues.
        
        Args:
            issues: Lista de issues de Jira.
            
        Returns:
            Dict: Diccionario con métricas calculadas.
        """
        test_cases, bugs = self.filter_issues_by_type(issues)
        
        logger.info(f"Calculando métricas: {len(test_cases)} test cases, {len(bugs)} bugs de {len(issues)} issues totales")
        
        test_case_metrics = self.core_calculator.calculate_issue_metrics(test_cases, 'test case')
        bug_metrics = self.core_calculator.calculate_issue_metrics(bugs, 'Bug')
        general_report = self.core_calculator.calculate_general_report_metrics(test_cases, bugs)
        
        return {
            'test_cases': test_case_metrics,
            'bugs': bug_metrics,
            'general_report': general_report,
            'total_issues': len(issues),
            'test_case_count': len(test_cases),
            'bug_count': len(bugs)
        }
