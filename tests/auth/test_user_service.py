"""
Tests unitarios para el servicio de usuarios
"""
import unittest
from unittest.mock import patch, MagicMock
from app.auth.user_service import UserService


class TestUserService(unittest.TestCase):
    """Tests para UserService"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_repository = MagicMock()
        self.user_service = UserService(self.mock_repository)

    def test_create_user_success(self):
        """Test creación de usuario exitosa"""
        self.mock_repository.create.return_value = {'id': 1, 'username': 'test_user'}
        
        result = self.user_service.create_user('test_user', 'password', 'test@example.com')
        
        self.assertEqual(result['username'], 'test_user')
        self.mock_repository.create.assert_called_once()

    def test_create_user_duplicate_username(self):
        """Test creación de usuario con username duplicado"""
        self.mock_repository.create.side_effect = Exception('Duplicate username')
        
        with self.assertRaises(Exception):
            self.user_service.create_user('existing_user', 'password', 'test@example.com')

    def test_get_user_by_id_success(self):
        """Test obtener usuario por ID exitoso"""
        self.mock_repository.get_by_id.return_value = {'id': 1, 'username': 'test_user'}
        
        result = self.user_service.get_user_by_id(1)
        
        self.assertEqual(result['id'], 1)
        self.mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_user_by_id_not_found(self):
        """Test obtener usuario por ID no encontrado"""
        self.mock_repository.get_by_id.return_value = None
        
        result = self.user_service.get_user_by_id(999)
        
        self.assertIsNone(result)

    def test_get_user_by_username_success(self):
        """Test obtener usuario por username exitoso"""
        self.mock_repository.get_by_username.return_value = {'username': 'test_user'}
        
        result = self.user_service.get_user_by_username('test_user')
        
        self.assertEqual(result['username'], 'test_user')

    def test_update_user_success(self):
        """Test actualización de usuario exitosa"""
        self.mock_repository.update.return_value = {'id': 1, 'username': 'updated_user'}
        
        result = self.user_service.update_user(1, {'username': 'updated_user'})
        
        self.assertEqual(result['username'], 'updated_user')

    def test_delete_user_success(self):
        """Test eliminación de usuario exitosa"""
        self.mock_repository.delete.return_value = True
        
        result = self.user_service.delete_user(1)
        
        self.assertTrue(result)
        self.mock_repository.delete.assert_called_once_with(1)

    def test_list_all_users(self):
        """Test listar todos los usuarios"""
        self.mock_repository.get_all.return_value = [
            {'id': 1, 'username': 'user1'},
            {'id': 2, 'username': 'user2'}
        ]
        
        result = self.user_service.list_all_users()
        
        self.assertEqual(len(result), 2)

    def test_validate_user_credentials_success(self):
        """Test validación de credenciales exitosa"""
        self.mock_repository.get_by_username.return_value = {
            'username': 'test_user',
            'password_hash': 'hashed_password'
        }
        
        with patch('app.auth.user_service.check_password_hash', return_value=True):
            result = self.user_service.validate_credentials('test_user', 'password')
            
            self.assertTrue(result)

    def test_validate_user_credentials_failure(self):
        """Test validación de credenciales fallida"""
        self.mock_repository.get_by_username.return_value = {
            'username': 'test_user',
            'password_hash': 'hashed_password'
        }
        
        with patch('app.auth.user_service.check_password_hash', return_value=False):
            result = self.user_service.validate_credentials('test_user', 'wrong_password')
            
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
