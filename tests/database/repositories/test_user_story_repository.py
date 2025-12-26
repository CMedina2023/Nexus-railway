"""
Tests unitarios para repositorio de historias de usuario
"""
import unittest
from unittest.mock import patch, MagicMock
from app.database.repositories.user_story_repository import UserStoryRepository


class TestUserStoryRepository(unittest.TestCase):
    """Tests para UserStoryRepository"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_db = MagicMock()
        self.repository = UserStoryRepository(self.mock_db)

    def test_create_story_success(self):
        """Test creación de historia exitosa"""
        story_data = {
            'title': 'User login',
            'description': 'As a user...',
            'project_id': 1
        }
        
        self.mock_db.execute.return_value.lastrowid = 1
        
        result = self.repository.create(story_data)
        
        self.assertEqual(result, 1)

    def test_get_story_by_id_success(self):
        """Test obtener historia por ID exitoso"""
        self.mock_db.execute.return_value.fetchone.return_value = {
            'id': 1,
            'title': 'User login'
        }
        
        result = self.repository.get_by_id(1)
        
        self.assertEqual(result['id'], 1)

    def test_get_stories_by_project(self):
        """Test obtener historias por proyecto"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 1, 'project_id': 1},
            {'id': 2, 'project_id': 1}
        ]
        
        result = self.repository.get_by_project(1)
        
        self.assertEqual(len(result), 2)

    def test_update_story_success(self):
        """Test actualización de historia exitosa"""
        update_data = {'title': 'Updated title'}
        
        self.mock_db.execute.return_value.rowcount = 1
        
        result = self.repository.update(1, update_data)
        
        self.assertTrue(result)

    def test_delete_story_success(self):
        """Test eliminación de historia exitosa"""
        self.mock_db.execute.return_value.rowcount = 1
        
        result = self.repository.delete(1)
        
        self.assertTrue(result)

    def test_get_stories_by_status(self):
        """Test obtener historias por estado"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 1, 'status': 'pending'},
            {'id': 2, 'status': 'pending'}
        ]
        
        result = self.repository.get_by_status('pending')
        
        self.assertEqual(len(result), 2)

    def test_bulk_create_stories(self):
        """Test creación masiva de historias"""
        stories = [
            {'title': 'Story 1'},
            {'title': 'Story 2'},
            {'title': 'Story 3'}
        ]
        
        self.mock_db.executemany.return_value.rowcount = 3
        
        result = self.repository.bulk_create(stories)
        
        self.assertEqual(result, 3)

    def test_search_stories_by_keyword(self):
        """Test búsqueda de historias por palabra clave"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 1, 'title': 'User login feature'}
        ]
        
        result = self.repository.search('login')
        
        self.assertEqual(len(result), 1)

    def test_get_stories_count_by_project(self):
        """Test contar historias por proyecto"""
        self.mock_db.execute.return_value.fetchone.return_value = {'count': 10}
        
        result = self.repository.count_by_project(1)
        
        self.assertEqual(result, 10)

    def test_get_recent_stories(self):
        """Test obtener historias recientes"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 3, 'created_at': '2024-01-03'},
            {'id': 2, 'created_at': '2024-01-02'}
        ]
        
        result = self.repository.get_recent(limit=2)
        
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
