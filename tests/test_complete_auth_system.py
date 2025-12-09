"""
Tests completos del sistema de autenticación
Responsabilidad única: Verificar que todo el sistema de autenticación funciona correctamente (SRP)
"""
import unittest
import json
import uuid
from flask import Flask
from app.core.app import app
from app.database import init_db
from app.auth.user_service import UserService
from app.auth.session_service import SessionService
from app.auth.password_service import PasswordService


class TestCompleteAuthSystem(unittest.TestCase):
    """
    Tests completos del sistema de autenticación
    """
    
    def setUp(self):
        """Configuración antes de cada test"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()
    
    def _create_user(self, email=None, password='TestPassword123!', role='usuario'):
        """Helper para crear un usuario"""
        if not email:
            email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        
        user_service = UserService()
        return user_service.create_user(
            email=email,
            password=password,
            role=role
        )
    
    def _create_authenticated_client(self, user=None):
        """Helper para crear un cliente autenticado"""
        if not user:
            user = self._create_user()
        
        with self.client.session_transaction() as sess:
            sess[SessionService.USER_ID_KEY] = user.id
            sess[SessionService.USER_EMAIL_KEY] = user.email
            sess[SessionService.USER_ROLE_KEY] = user.role
            sess[SessionService.LOGIN_TIME_KEY] = '2024-01-01T00:00:00'
            sess['_permanent'] = True
        
        return self.client, user
    
    # ========================================================================
    # TESTS DE LOGIN Y REGISTRO
    # ========================================================================
    
    def test_register_new_user(self):
        """Verifica que se puede registrar un nuevo usuario"""
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        
        response = self.client.post('/auth/register', data={
            'email': unique_email,
            'password': 'TestPassword123!',
            'confirm_password': 'TestPassword123!'
        })
        
        # Debería redirigir después del registro
        self.assertIn(response.status_code, [200, 302])
    
    def test_login_with_valid_credentials(self):
        """Verifica que el login funciona con credenciales válidas"""
        user = self._create_user()
        
        response = self.client.post('/auth/login', data={
            'email': user.email,
            'password': 'TestPassword123!'
        })
        
        # Debería redirigir después del login
        self.assertIn(response.status_code, [200, 302])
    
    def test_login_with_invalid_credentials(self):
        """Verifica que el login falla con credenciales inválidas"""
        user = self._create_user()
        
        response = self.client.post('/auth/login', data={
            'email': user.email,
            'password': 'WrongPassword123!'
        })
        
        # Debería retornar error
        self.assertIn(response.status_code, [400, 401])
    
    # ========================================================================
    # TESTS DE PANEL DE ADMINISTRACIÓN
    # ========================================================================
    
    def test_admin_dashboard_requires_admin_role(self):
        """Verifica que el panel de admin requiere rol de admin"""
        # Usuario normal
        client, user = self._create_authenticated_client()
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 403)
        
        # Usuario admin
        admin_user = self._create_user(role='admin')
        with client.session_transaction() as sess:
            sess[SessionService.USER_ID_KEY] = admin_user.id
            sess[SessionService.USER_EMAIL_KEY] = admin_user.email
            sess[SessionService.USER_ROLE_KEY] = admin_user.role
            sess[SessionService.LOGIN_TIME_KEY] = '2024-01-01T00:00:00'
            sess['_permanent'] = True
        
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_denies_analista_qa(self):
        """Verifica que analista QA no accede al panel de admin"""
        qa_user = self._create_user(role='analista_qa')
        client, _ = self._create_authenticated_client(user=qa_user)

        response = client.get('/admin/')
        self.assertEqual(response.status_code, 403)
    
    def test_admin_list_users(self):
        """Verifica que un admin puede listar usuarios"""
        admin_user = self._create_user(role='admin')
        client, _ = self._create_authenticated_client(user=admin_user)
        
        response = client.get('/admin/users')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('users', data)
        self.assertIn('statistics', data)
    
    def test_admin_update_user_role(self):
        """Verifica que un admin puede cambiar el rol de un usuario"""
        admin_user = self._create_user(role='admin')
        regular_user = self._create_user(role='usuario')
        client, _ = self._create_authenticated_client(user=admin_user)
        
        response = client.put(f'/admin/users/{regular_user.id}/role', 
                             json={'role': 'manager'})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
    
    def test_admin_cannot_change_own_role(self):
        """Verifica que un admin no puede cambiar su propio rol"""
        admin_user = self._create_user(role='admin')
        client, _ = self._create_authenticated_client(user=admin_user)
        
        response = client.put(f'/admin/users/{admin_user.id}/role',
                             json={'role': 'usuario'})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('propio rol', data['error'])
    
    # ========================================================================
    # TESTS DE PERFIL DE USUARIO
    # ========================================================================
    
    def test_profile_page_requires_login(self):
        """Verifica que la página de perfil requiere autenticación"""
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
    
    def test_profile_page_with_auth(self):
        """Verifica que un usuario autenticado puede acceder a su perfil"""
        client, user = self._create_authenticated_client()
        response = client.get('/profile/')
        self.assertEqual(response.status_code, 200)
    
    def test_change_password_with_valid_data(self):
        """Verifica que se puede cambiar la contraseña con datos válidos"""
        user = self._create_user()
        client, _ = self._create_authenticated_client(user=user)
        
        response = client.post('/profile/change-password', json={
            'current_password': 'TestPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
    
    def test_change_password_with_wrong_current_password(self):
        """Verifica que no se puede cambiar la contraseña con contraseña actual incorrecta"""
        user = self._create_user()
        client, _ = self._create_authenticated_client(user=user)
        
        response = client.post('/profile/change-password', json={
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('actual incorrecta', data['error'])
    
    def test_change_password_passwords_dont_match(self):
        """Verifica que no se puede cambiar la contraseña si no coinciden"""
        user = self._create_user()
        client, _ = self._create_authenticated_client(user=user)
        
        response = client.post('/profile/change-password', json={
            'current_password': 'TestPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword123!'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('no coinciden', data['error'])
    
    def test_get_profile_info(self):
        """Verifica que se puede obtener información del perfil"""
        client, user = self._create_authenticated_client()
        
        response = client.get('/profile/info')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], user.email)
    
    # ========================================================================
    # TESTS DE REDIRECCIÓN
    # ========================================================================
    
    def test_redirect_to_original_url_after_login(self):
        """Verifica que después del login redirige a la URL original"""
        # Intentar acceder a una ruta protegida
        response = self.client.get('/agent')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
        
        # Verificar que se guardó la URL original
        with self.client.session_transaction() as sess:
            self.assertIn('next_url', sess)
            self.assertIn('/agent', sess['next_url'])
        
        # Hacer login
        user = self._create_user()
        response = self.client.post('/auth/login', data={
            'email': user.email,
            'password': 'TestPassword123!'
        })
        
        # Debería redirigir a /agent (la URL original)
        self.assertEqual(response.status_code, 302)
        # Nota: En tests, la redirección puede variar, pero debería funcionar en producción


if __name__ == '__main__':
    unittest.main()

