"""
Tests unitarios para el servicio de proyectos de Jira
"""
import unittest
from unittest.mock import patch, MagicMock
from app.backend.jira.project_service import ProjectService


class TestProjectService(unittest.TestCase):
    """Tests para ProjectService"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_client = MagicMock()
        self.project_service = ProjectService(self.mock_client)

    def test_get_all_projects_success(self):
        """Test obtener todos los proyectos exitoso"""
        self.mock_client.projects.return_value = [
            MagicMock(key='PROJ1', name='Project 1'),
            MagicMock(key='PROJ2', name='Project 2')
        ]
        
        result = self.project_service.get_all_projects()
        
        self.assertEqual(len(result), 2)

    def test_get_project_by_key_success(self):
        """Test obtener proyecto por key exitoso"""
        self.mock_client.project.return_value = MagicMock(
            key='PROJ1',
            name='Project 1'
        )
        
        result = self.project_service.get_project('PROJ1')
        
        self.assertEqual(result.key, 'PROJ1')

    def test_get_project_not_found(self):
        """Test obtener proyecto no encontrado"""
        self.mock_client.project.side_effect = Exception('Not found')
        
        with self.assertRaises(Exception):
            self.project_service.get_project('INVALID')

    def test_get_project_components(self):
        """Test obtener componentes de proyecto"""
        self.mock_client.project_components.return_value = [
            MagicMock(name='Component 1'),
            MagicMock(name='Component 2')
        ]
        
        result = self.project_service.get_components('PROJ1')
        
        self.assertEqual(len(result), 2)

    def test_get_project_versions(self):
        """Test obtener versiones de proyecto"""
        self.mock_client.project_versions.return_value = [
            MagicMock(name='v1.0'),
            MagicMock(name='v2.0')
        ]
        
        result = self.project_service.get_versions('PROJ1')
        
        self.assertEqual(len(result), 2)

    def test_get_issue_types_for_project(self):
        """Test obtener tipos de issue para proyecto"""
        mock_project = MagicMock()
        mock_project.issueTypes = [
            MagicMock(name='Story'),
            MagicMock(name='Bug')
        ]
        self.mock_client.project.return_value = mock_project
        
        result = self.project_service.get_issue_types('PROJ1')
        
        self.assertEqual(len(result), 2)

    def test_create_project_component(self):
        """Test crear componente de proyecto"""
        self.mock_client.create_component.return_value = MagicMock(
            name='New Component'
        )
        
        result = self.project_service.create_component(
            'PROJ1',
            'New Component'
        )
        
        self.assertIsNotNone(result)

    def test_get_project_roles(self):
        """Test obtener roles de proyecto"""
        self.mock_client.project_roles.return_value = {
            'Developers': MagicMock(),
            'Administrators': MagicMock()
        }
        
        result = self.project_service.get_roles('PROJ1')
        
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
