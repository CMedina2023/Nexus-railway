"""
Tests unitarios para rutas de autenticación
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from app.auth.routes import auth_bp


class TestAuthRoutes(unittest.TestCase):
    """Tests para rutas de autenticación"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.app = Flask(__name__)
        self.app.register_blueprint(auth_bp)
        self.client = self.app.test_client()

    @patch('app.auth.routes.UserService')
    def test_login_success(self, mock_user_service):
        """Test login exitoso"""
        mock_user_service.return_value.authenticate.return_value = {
            'id': 1,
            'username': 'testuser'
        }
        
        response = self.client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, 200)

    def test_login_missing_credentials(self):
        """Test login con credenciales faltantes"""
        response = self.client.post('/auth/login', json={
            'username': 'testuser'
        })
        
        self.assertEqual(response.status_code, 400)

    @patch('app.auth.routes.UserService')
    def test_login_invalid_credentials(self, mock_user_service):
        """Test login con credenciales inválidas"""
        mock_user_service.return_value.authenticate.return_value = None
        
        response = self.client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 401)

    @patch('app.auth.routes.UserService')
    def test_register_success(self, mock_user_service):
        """Test registro exitoso"""
        mock_user_service.return_value.create_user.return_value = {
            'id': 1,
            'username': 'newuser'
        }
        
        response = self.client.post('/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, 201)

    def test_register_duplicate_username(self):
        """Test registro con username duplicado"""
        with patch('app.auth.routes.UserService') as mock_service:
            mock_service.return_value.create_user.side_effect = Exception('Duplicate')
            
            response = self.client.post('/auth/register', json={
                'username': 'existinguser',
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            self.assertEqual(response.status_code, 400)

    @patch('app.auth.routes.SessionService')
    def test_logout_success(self, mock_session_service):
        """Test logout exitoso"""
        response = self.client.post('/auth/logout')
        
        self.assertEqual(response.status_code, 200)

    @patch('app.auth.routes.SessionService')
    def test_get_current_user(self, mock_session_service):
        """Test obtener usuario actual"""
        mock_session_service.return_value.get_current_user.return_value = 1
        
        with patch('app.auth.routes.UserService') as mock_user_service:
            mock_user_service.return_value.get_user_by_id.return_value = {
                'id': 1,
                'username': 'testuser'
            }
            
            response = self.client.get('/auth/me')
            
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
