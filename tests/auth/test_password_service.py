"""
Tests unitarios para el servicio de contraseñas
"""
import unittest
from unittest.mock import patch, MagicMock
from app.auth.password_service import PasswordService


class TestPasswordService(unittest.TestCase):
    """Tests para PasswordService"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.password_service = PasswordService()

    @patch('app.auth.password_service.generate_password_hash')
    def test_hash_password_success(self, mock_hash):
        """Test hash de contraseña exitoso"""
        mock_hash.return_value = 'hashed_password'
        
        result = self.password_service.hash_password('test_password')
        
        self.assertEqual(result, 'hashed_password')
        mock_hash.assert_called_once_with('test_password')

    @patch('app.auth.password_service.check_password_hash')
    def test_verify_password_success(self, mock_check):
        """Test verificación de contraseña exitosa"""
        mock_check.return_value = True
        
        result = self.password_service.verify_password('hashed', 'password')
        
        self.assertTrue(result)
        mock_check.assert_called_once_with('hashed', 'password')

    @patch('app.auth.password_service.check_password_hash')
    def test_verify_password_failure(self, mock_check):
        """Test verificación de contraseña fallida"""
        mock_check.return_value = False
        
        result = self.password_service.verify_password('hashed', 'wrong_password')
        
        self.assertFalse(result)

    def test_hash_empty_password(self):
        """Test hash de contraseña vacía"""
        with self.assertRaises((ValueError, TypeError)):
            self.password_service.hash_password('')

    def test_hash_none_password(self):
        """Test hash de contraseña None"""
        with self.assertRaises((ValueError, TypeError)):
            self.password_service.hash_password(None)

    @patch('app.auth.password_service.generate_password_hash')
    def test_hash_long_password(self, mock_hash):
        """Test hash de contraseña muy larga"""
        long_password = 'a' * 1000
        mock_hash.return_value = 'hashed_long'
        
        result = self.password_service.hash_password(long_password)
        
        self.assertIsNotNone(result)

    @patch('app.auth.password_service.generate_password_hash')
    def test_hash_special_characters(self, mock_hash):
        """Test hash de contraseña con caracteres especiales"""
        special_password = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        mock_hash.return_value = 'hashed_special'
        
        result = self.password_service.hash_password(special_password)
        
        self.assertIsNotNone(result)

    @patch('app.auth.password_service.check_password_hash')
    def test_verify_password_case_sensitive(self, mock_check):
        """Test verificación de contraseña es case-sensitive"""
        mock_check.return_value = False
        
        result = self.password_service.verify_password('hashed', 'Password')
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
