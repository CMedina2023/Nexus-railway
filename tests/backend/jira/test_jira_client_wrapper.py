"""
Tests unitarios para el cliente de Jira
"""
import unittest
from unittest.mock import patch, MagicMock
from app.backend.jira.jira_client_wrapper import JiraClientWrapper


class TestJiraClientWrapper(unittest.TestCase):
    """Tests para JiraClientWrapper"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_jira = MagicMock()
        self.client = JiraClientWrapper(self.mock_jira)

    def test_create_issue_success(self):
        """Test creación de issue exitosa"""
        self.mock_jira.create_issue.return_value = {'key': 'TEST-123'}
        
        result = self.client.create_issue({
            'project': 'TEST',
            'summary': 'Test issue',
            'issuetype': {'name': 'Story'}
        })
        
        self.assertEqual(result['key'], 'TEST-123')

    def test_create_issue_error(self):
        """Test creación de issue con error"""
        self.mock_jira.create_issue.side_effect = Exception('Jira API Error')
        
        with self.assertRaises(Exception):
            self.client.create_issue({'project': 'TEST'})

    def test_get_issue_success(self):
        """Test obtener issue exitoso"""
        self.mock_jira.issue.return_value = MagicMock(key='TEST-123')
        
        result = self.client.get_issue('TEST-123')
        
        self.assertEqual(result.key, 'TEST-123')

    def test_get_issue_not_found(self):
        """Test obtener issue no encontrado"""
        self.mock_jira.issue.side_effect = Exception('Issue not found')
        
        with self.assertRaises(Exception):
            self.client.get_issue('INVALID-999')

    def test_update_issue_success(self):
        """Test actualización de issue exitosa"""
        mock_issue = MagicMock()
        self.mock_jira.issue.return_value = mock_issue
        
        self.client.update_issue('TEST-123', {'summary': 'Updated summary'})
        
        mock_issue.update.assert_called_once()

    def test_search_issues_success(self):
        """Test búsqueda de issues exitosa"""
        self.mock_jira.search_issues.return_value = [
            MagicMock(key='TEST-1'),
            MagicMock(key='TEST-2')
        ]
        
        result = self.client.search_issues('project=TEST')
        
        self.assertEqual(len(result), 2)

    def test_get_projects_success(self):
        """Test obtener proyectos exitoso"""
        self.mock_jira.projects.return_value = [
            MagicMock(key='PROJ1'),
            MagicMock(key='PROJ2')
        ]
        
        result = self.client.get_projects()
        
        self.assertEqual(len(result), 2)

    def test_add_comment_success(self):
        """Test agregar comentario exitoso"""
        mock_issue = MagicMock()
        self.mock_jira.issue.return_value = mock_issue
        
        self.client.add_comment('TEST-123', 'Test comment')
        
        self.mock_jira.add_comment.assert_called_once()

    def test_get_transitions_success(self):
        """Test obtener transiciones exitoso"""
        self.mock_jira.transitions.return_value = [
            {'id': '1', 'name': 'To Do'},
            {'id': '2', 'name': 'In Progress'}
        ]
        
        result = self.client.get_transitions('TEST-123')
        
        self.assertEqual(len(result), 2)

    def test_transition_issue_success(self):
        """Test transición de issue exitosa"""
        mock_issue = MagicMock()
        self.mock_jira.issue.return_value = mock_issue
        
        self.client.transition_issue('TEST-123', '2')
        
        self.mock_jira.transition_issue.assert_called_once()


if __name__ == '__main__':
    unittest.main()
