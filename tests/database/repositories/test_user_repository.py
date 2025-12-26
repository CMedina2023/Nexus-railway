"""
Tests unitarios para repositorios de usuarios
"""
import unittest
from unittest.mock import patch, MagicMock
from app.database.repositories.user_repository import UserRepository


class TestUserRepository(unittest.TestCase):
    """Tests para UserRepository"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_db = MagicMock()
        self.repository = UserRepository(self.mock_db)

    def test_create_user_success(self):
        """Test creación de usuario exitosa"""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': 'hashed'
        }
        
        self.mock_db.execute.return_value.lastrowid = 1
        
        result = self.repository.create(user_data)
        
        self.assertEqual(result, 1)

    def test_get_user_by_id_success(self):
        """Test obtener usuario por ID exitoso"""
        self.mock_db.execute.return_value.fetchone.return_value = {
            'id': 1,
            'username': 'testuser'
        }
        
        result = self.repository.get_by_id(1)
        
        self.assertEqual(result['id'], 1)

    def test_get_user_by_id_not_found(self):
        """Test obtener usuario por ID no encontrado"""
        self.mock_db.execute.return_value.fetchone.return_value = None
        
        result = self.repository.get_by_id(999)
        
        self.assertIsNone(result)

    def test_get_user_by_username_success(self):
        """Test obtener usuario por username exitoso"""
        self.mock_db.execute.return_value.fetchone.return_value = {
            'username': 'testuser'
        }
        
        result = self.repository.get_by_username('testuser')
        
        self.assertEqual(result['username'], 'testuser')

    def test_get_user_by_email_success(self):
        """Test obtener usuario por email exitoso"""
        self.mock_db.execute.return_value.fetchone.return_value = {
            'email': 'test@example.com'
        }
        
        result = self.repository.get_by_email('test@example.com')
        
        self.assertEqual(result['email'], 'test@example.com')

    def test_update_user_success(self):
        """Test actualización de usuario exitosa"""
        update_data = {'email': 'newemail@example.com'}
        
        self.mock_db.execute.return_value.rowcount = 1
        
        result = self.repository.update(1, update_data)
        
        self.assertTrue(result)

    def test_delete_user_success(self):
        """Test eliminación de usuario exitosa"""
        self.mock_db.execute.return_value.rowcount = 1
        
        result = self.repository.delete(1)
        
        self.assertTrue(result)

    def test_get_all_users(self):
        """Test obtener todos los usuarios"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 1, 'username': 'user1'},
            {'id': 2, 'username': 'user2'}
        ]
        
        result = self.repository.get_all()
        
        self.assertEqual(len(result), 2)

    def test_user_exists_by_username(self):
        """Test verificar si usuario existe por username"""
        self.mock_db.execute.return_value.fetchone.return_value = {'id': 1}
        
        result = self.repository.exists_by_username('testuser')
        
        self.assertTrue(result)

    def test_user_not_exists_by_username(self):
        """Test verificar que usuario no existe por username"""
        self.mock_db.execute.return_value.fetchone.return_value = None
        
        result = self.repository.exists_by_username('nonexistent')
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
