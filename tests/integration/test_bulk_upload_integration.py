"""
Tests de integración para carga masiva
"""
import unittest
from unittest.mock import patch, MagicMock
from app.services.generation_orchestrator import GenerationOrchestrator
from app.backend.jira.issue_service import IssueService


class TestBulkUploadIntegration(unittest.TestCase):
    """Tests de integración para carga masiva"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.orchestrator = GenerationOrchestrator()
        self.issue_service = IssueService(MagicMock())

    @patch('app.backend.jira.issue_service.JiraClient')
    def test_bulk_upload_complete_flow(self, mock_jira):
        """Test flujo completo de carga masiva"""
        mock_jira.return_value.create_issue.return_value = {'key': 'TEST-1'}
        
        issues = [
            {'project': 'TEST', 'summary': 'Issue 1'},
            {'project': 'TEST', 'summary': 'Issue 2'}
        ]
        
        result = self.issue_service.bulk_create_issues(issues)
        
        self.assertEqual(len(result), 2)

    @patch('app.services.generation_orchestrator.FileManager')
    def test_process_csv_file(self, mock_file_manager):
        """Test procesamiento de archivo CSV"""
        mock_file_manager.return_value.read_csv.return_value = [
            {'title': 'Story 1', 'description': 'Desc 1'},
            {'title': 'Story 2', 'description': 'Desc 2'}
        ]
        
        result = self.orchestrator.process_bulk_file('test.csv')
        
        self.assertEqual(len(result), 2)

    def test_validate_bulk_data(self):
        """Test validación de datos masivos"""
        bulk_data = [
            {'title': 'Valid', 'description': 'Valid desc'},
            {'title': '', 'description': 'Invalid'}
        ]
        
        valid, invalid = self.orchestrator.validate_bulk_data(bulk_data)
        
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 1)

    @patch('app.backend.jira.issue_service.JiraClient')
    def test_bulk_upload_with_errors(self, mock_jira):
        """Test carga masiva con errores parciales"""
        mock_jira.return_value.create_issue.side_effect = [
            {'key': 'TEST-1'},
            Exception('Error'),
            {'key': 'TEST-3'}
        ]
        
        issues = [
            {'project': 'TEST', 'summary': 'Issue 1'},
            {'project': 'TEST', 'summary': 'Issue 2'},
            {'project': 'TEST', 'summary': 'Issue 3'}
        ]
        
        result = self.issue_service.bulk_create_issues(
            issues,
            continue_on_error=True
        )
        
        self.assertEqual(len(result['successful']), 2)
        self.assertEqual(len(result['failed']), 1)

    def test_bulk_upload_progress_tracking(self):
        """Test seguimiento de progreso de carga masiva"""
        progress_callback = MagicMock()
        
        issues = [{'project': 'TEST', 'summary': f'Issue {i}'} for i in range(10)]
        
        self.orchestrator.bulk_upload_with_progress(
            issues,
            callback=progress_callback
        )
        
        self.assertGreater(progress_callback.call_count, 0)


if __name__ == '__main__':
    unittest.main()
