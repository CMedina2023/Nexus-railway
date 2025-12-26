"""
Tests unitarios para el servicio de issues de Jira
"""
import unittest
from unittest.mock import patch, MagicMock
from app.backend.jira.issue_service import IssueService


class TestIssueService(unittest.TestCase):
    """Tests para IssueService"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_client = MagicMock()
        self.issue_service = IssueService(self.mock_client)

    def test_create_story_success(self):
        """Test creación de historia exitosa"""
        self.mock_client.create_issue.return_value = {'key': 'STORY-1'}
        
        result = self.issue_service.create_story('TEST', 'User login', 'As a user...')
        
        self.assertEqual(result['key'], 'STORY-1')

    def test_create_bug_success(self):
        """Test creación de bug exitoso"""
        self.mock_client.create_issue.return_value = {'key': 'BUG-1'}
        
        result = self.issue_service.create_bug('TEST', 'Login fails', 'Steps to reproduce...')
        
        self.assertEqual(result['key'], 'BUG-1')

    def test_create_test_case_success(self):
        """Test creación de caso de prueba exitoso"""
        self.mock_client.create_issue.return_value = {'key': 'TEST-1'}
        
        result = self.issue_service.create_test_case('TEST', 'Verify login', 'Test steps...')
        
        self.assertEqual(result['key'], 'TEST-1')

    def test_bulk_create_issues_success(self):
        """Test creación masiva de issues exitosa"""
        self.mock_client.create_issue.side_effect = [
            {'key': 'TEST-1'},
            {'key': 'TEST-2'},
            {'key': 'TEST-3'}
        ]
        
        issues = [
            {'project': 'TEST', 'summary': 'Issue 1'},
            {'project': 'TEST', 'summary': 'Issue 2'},
            {'project': 'TEST', 'summary': 'Issue 3'}
        ]
        
        result = self.issue_service.bulk_create_issues(issues)
        
        self.assertEqual(len(result), 3)

    def test_bulk_create_issues_partial_failure(self):
        """Test creación masiva con fallos parciales"""
        self.mock_client.create_issue.side_effect = [
            {'key': 'TEST-1'},
            Exception('API Error'),
            {'key': 'TEST-3'}
        ]
        
        issues = [
            {'project': 'TEST', 'summary': 'Issue 1'},
            {'project': 'TEST', 'summary': 'Issue 2'},
            {'project': 'TEST', 'summary': 'Issue 3'}
        ]
        
        result = self.issue_service.bulk_create_issues(issues, continue_on_error=True)
        
        self.assertEqual(len(result['successful']), 2)
        self.assertEqual(len(result['failed']), 1)

    def test_validate_issue_fields_success(self):
        """Test validación de campos de issue exitosa"""
        issue_data = {
            'project': 'TEST',
            'summary': 'Valid issue',
            'issuetype': {'name': 'Story'}
        }
        
        result = self.issue_service.validate_issue_fields(issue_data)
        
        self.assertTrue(result)

    def test_validate_issue_fields_missing_required(self):
        """Test validación con campos requeridos faltantes"""
        issue_data = {
            'project': 'TEST'
        }
        
        with self.assertRaises(ValueError):
            self.issue_service.validate_issue_fields(issue_data)

    def test_get_issue_by_key_success(self):
        """Test obtener issue por key exitoso"""
        self.mock_client.get_issue.return_value = MagicMock(key='TEST-123')
        
        result = self.issue_service.get_issue_by_key('TEST-123')
        
        self.assertEqual(result.key, 'TEST-123')

    def test_update_issue_status_success(self):
        """Test actualización de estado de issue exitosa"""
        self.mock_client.transition_issue.return_value = True
        
        result = self.issue_service.update_issue_status('TEST-123', 'In Progress')
        
        self.assertTrue(result)

    def test_add_attachment_to_issue(self):
        """Test agregar adjunto a issue"""
        self.mock_client.add_attachment.return_value = {'id': 'attach-1'}
        
        result = self.issue_service.add_attachment('TEST-123', 'file.pdf')
        
        self.assertEqual(result['id'], 'attach-1')


if __name__ == '__main__':
    unittest.main()
