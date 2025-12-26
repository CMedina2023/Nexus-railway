"""
Tests unitarios para rutas de dashboard
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from app.auth.dashboard_routes import dashboard_bp


class TestDashboardRoutes(unittest.TestCase):
    """Tests para rutas de dashboard"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.app = Flask(__name__)
        self.app.register_blueprint(dashboard_bp)
        self.client = self.app.test_client()

    @patch('app.auth.dashboard_routes.require_auth')
    @patch('app.auth.dashboard_routes.MetricsService')
    def test_get_dashboard_metrics(self, mock_metrics, mock_auth):
        """Test obtener métricas del dashboard"""
        mock_metrics.return_value.get_metrics.return_value = {
            'total_stories': 100,
            'completed': 75
        }
        
        response = self.client.get('/dashboard/metrics')
        
        self.assertEqual(response.status_code, 200)

    @patch('app.auth.dashboard_routes.require_auth')
    def test_get_dashboard_unauthorized(self, mock_auth):
        """Test acceso no autorizado al dashboard"""
        mock_auth.side_effect = PermissionError('Unauthorized')
        
        response = self.client.get('/dashboard/metrics')
        
        self.assertEqual(response.status_code, 401)

    @patch('app.auth.dashboard_routes.require_auth')
    @patch('app.auth.dashboard_routes.ChartService')
    def test_get_chart_data(self, mock_chart, mock_auth):
        """Test obtener datos de gráficos"""
        mock_chart.return_value.get_chart_data.return_value = {
            'labels': ['Jan', 'Feb'],
            'data': [10, 20]
        }
        
        response = self.client.get('/dashboard/charts/velocity')
        
        self.assertEqual(response.status_code, 200)

    @patch('app.auth.dashboard_routes.require_auth')
    @patch('app.auth.dashboard_routes.ProjectService')
    def test_get_project_summary(self, mock_project, mock_auth):
        """Test obtener resumen de proyecto"""
        mock_project.return_value.get_summary.return_value = {
            'name': 'Test Project',
            'status': 'Active'
        }
        
        response = self.client.get('/dashboard/projects/1/summary')
        
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
