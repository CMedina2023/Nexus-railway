"""
Tests unitarios para el servicio de sesiones
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.auth.session_service import SessionService


class TestSessionService(unittest.TestCase):
    """Tests para SessionService"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.session_service = SessionService()

    @patch('app.auth.session_service.session')
    def test_create_session_success(self, mock_session):
        """Test creación de sesión exitosa"""
        user_id = 1
        
        self.session_service.create_session(user_id)
        
        self.assertIn('user_id', mock_session)

    @patch('app.auth.session_service.session')
    def test_get_current_user_success(self, mock_session):
        """Test obtener usuario actual exitoso"""
        mock_session.get.return_value = 1
        
        result = self.session_service.get_current_user()
        
        self.assertEqual(result, 1)

    @patch('app.auth.session_service.session')
    def test_get_current_user_no_session(self, mock_session):
        """Test obtener usuario sin sesión activa"""
        mock_session.get.return_value = None
        
        result = self.session_service.get_current_user()
        
        self.assertIsNone(result)

    @patch('app.auth.session_service.session')
    def test_destroy_session_success(self, mock_session):
        """Test destrucción de sesión exitosa"""
        self.session_service.destroy_session()
        
        mock_session.clear.assert_called_once()

    @patch('app.auth.session_service.session')
    def test_is_authenticated_true(self, mock_session):
        """Test verificación de autenticación positiva"""
        mock_session.get.return_value = 1
        
        result = self.session_service.is_authenticated()
        
        self.assertTrue(result)

    @patch('app.auth.session_service.session')
    def test_is_authenticated_false(self, mock_session):
        """Test verificación de autenticación negativa"""
        mock_session.get.return_value = None
        
        result = self.session_service.is_authenticated()
        
        self.assertFalse(result)

    @patch('app.auth.session_service.session')
    def test_update_session_data(self, mock_session):
        """Test actualización de datos de sesión"""
        self.session_service.update_session_data('key', 'value')
        
        self.assertIn('key', mock_session)

    @patch('app.auth.session_service.session')
    def test_session_timeout_check(self, mock_session):
        """Test verificación de timeout de sesión"""
        old_time = datetime.now() - timedelta(hours=2)
        mock_session.get.return_value = old_time
        
        result = self.session_service.is_session_expired()
        
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
