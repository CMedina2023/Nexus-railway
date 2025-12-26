"""
Tests unitarios para el calculador de métricas de Jira
"""
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from app.backend.jira.metrics_calculator import MetricsCalculator


class TestMetricsCalculator(unittest.TestCase):
    """Tests para MetricsCalculator"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.calculator = MetricsCalculator()

    def test_calculate_velocity_success(self):
        """Test cálculo de velocidad exitoso"""
        sprints = [
            {'completed_points': 20},
            {'completed_points': 25},
            {'completed_points': 30}
        ]
        
        result = self.calculator.calculate_velocity(sprints)
        
        self.assertEqual(result, 25)

    def test_calculate_velocity_empty_sprints(self):
        """Test cálculo de velocidad con sprints vacíos"""
        result = self.calculator.calculate_velocity([])
        
        self.assertEqual(result, 0)

    def test_calculate_cycle_time(self):
        """Test cálculo de cycle time"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)
        
        result = self.calculator.calculate_cycle_time(start_date, end_date)
        
        self.assertEqual(result, 9)

    def test_calculate_lead_time(self):
        """Test cálculo de lead time"""
        created_date = datetime(2024, 1, 1)
        completed_date = datetime(2024, 1, 15)
        
        result = self.calculator.calculate_lead_time(created_date, completed_date)
        
        self.assertEqual(result, 14)

    def test_calculate_throughput(self):
        """Test cálculo de throughput"""
        completed_issues = [
            {'completed_date': datetime(2024, 1, 1)},
            {'completed_date': datetime(2024, 1, 2)},
            {'completed_date': datetime(2024, 1, 3)}
        ]
        
        result = self.calculator.calculate_throughput(completed_issues, days=7)
        
        self.assertGreater(result, 0)

    def test_calculate_defect_rate(self):
        """Test cálculo de tasa de defectos"""
        total_issues = 100
        defects = 10
        
        result = self.calculator.calculate_defect_rate(total_issues, defects)
        
        self.assertEqual(result, 10.0)

    def test_calculate_defect_rate_zero_issues(self):
        """Test cálculo de tasa de defectos con cero issues"""
        result = self.calculator.calculate_defect_rate(0, 0)
        
        self.assertEqual(result, 0)

    def test_calculate_sprint_burndown(self):
        """Test cálculo de burndown de sprint"""
        total_points = 50
        daily_progress = [5, 10, 8, 12, 15]
        
        result = self.calculator.calculate_sprint_burndown(total_points, daily_progress)
        
        self.assertEqual(len(result), 5)
        self.assertEqual(result[-1], 0)

    def test_calculate_story_points_distribution(self):
        """Test cálculo de distribución de story points"""
        stories = [
            {'points': 1},
            {'points': 2},
            {'points': 3},
            {'points': 5},
            {'points': 8}
        ]
        
        result = self.calculator.calculate_points_distribution(stories)
        
        self.assertIn(1, result)
        self.assertIn(8, result)

    def test_calculate_average_resolution_time(self):
        """Test cálculo de tiempo promedio de resolución"""
        issues = [
            {'resolution_time': 5},
            {'resolution_time': 10},
            {'resolution_time': 15}
        ]
        
        result = self.calculator.calculate_average_resolution_time(issues)
        
        self.assertEqual(result, 10)


if __name__ == '__main__':
    unittest.main()
