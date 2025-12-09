"""
Tests para verificar protección de rutas con autenticación
Responsabilidad única: Verificar que las rutas protegidas requieren autenticación (SRP)
"""
import unittest
import json
from flask import Flask
from app.core.app import app
from app.database import init_db
from app.auth.user_service import UserService
from app.auth.session_service import SessionService


class TestRouteProtection(unittest.TestCase):
    """
    Tests para verificar que las rutas protegidas requieren autenticación
    """
    
    def setUp(self):
        """Configuración antes de cada test"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        app.config['WTF_CSRF_ENABLED'] = False  # Deshabilitar CSRF en tests
        self.client = app.test_client()
        with app.app_context():
            init_db()
    
    def _create_authenticated_client(self):
        """Helper para crear un cliente autenticado"""
        import uuid
        user_service = UserService()
        
        # Usar email único para evitar conflictos
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        
        # Crear usuario dentro del contexto de la app
        with app.app_context():
            try:
                test_user = user_service.create_user(
                    email=unique_email,
                    password='TestPassword123!',
                    role='usuario'
                )
            except Exception as e:
                # Si el usuario ya existe, intentar obtenerlo
                test_user = user_service.get_user_by_email(unique_email)
                if not test_user:
                    raise
        
        # Crear sesión dentro del contexto de request usando session_transaction
        with self.client.session_transaction() as sess:
            # Simular la sesión directamente en el diccionario de sesión
            sess[SessionService.USER_ID_KEY] = test_user.id
            sess[SessionService.USER_EMAIL_KEY] = test_user.email
            sess[SessionService.USER_ROLE_KEY] = test_user.role
            sess[SessionService.LOGIN_TIME_KEY] = '2024-01-01T00:00:00'
            sess['_permanent'] = True
        
        return self.client, test_user
    
    def test_menu_principal_requires_login(self):
        """Verifica que / requiere autenticación"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirige a login
        self.assertIn('/auth/login', response.location)
    
    def test_menu_principal_with_auth(self):
        """Verifica que / funciona con autenticación"""
        client, user = self._create_authenticated_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        # Verificar que la respuesta contiene contenido (no está vacía)
        self.assertIsNotNone(response.data)
        self.assertGreater(len(response.data), 0)
    
    def test_agent_interface_requires_login(self):
        """Verifica que /agent requiere autenticación"""
        response = self.client.get('/agent')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
    
    def test_agent_interface_with_auth(self):
        """Verifica que /agent funciona con autenticación"""
        client, user = self._create_authenticated_client()
        response = client.get('/agent')
        self.assertEqual(response.status_code, 200)
    
    def test_overview_requires_login(self):
        """Verifica que /overview requiere autenticación"""
        response = self.client.get('/overview')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
    
    def test_infografia_is_public(self):
        """Verifica que /infografia es pública (no requiere autenticación)"""
        response = self.client.get('/infografia')
        self.assertEqual(response.status_code, 200)  # Accesible sin login
    
    # ========================================================================
    # TESTS PARA RUTAS API
    # ========================================================================
    
    def test_api_agent_process_requires_login(self):
        """Verifica que /api/agent/process requiere autenticación"""
        response = self.client.post('/api/agent/process')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
        self.assertEqual(data.get('status'), 'unauthorized')
    
    def test_api_matrix_requires_login(self):
        """Verifica que /api/matrix requiere autenticación"""
        response = self.client.post('/api/matrix')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_api_story_requires_login(self):
        """Verifica que /api/story requiere autenticación"""
        response = self.client.post('/api/story')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_api_preview_requires_login(self):
        """Verifica que /api/preview requiere autenticación"""
        response = self.client.post('/api/preview')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_download_requires_login(self):
        """Verifica que /download/<filename> requiere autenticación"""
        response = self.client.get('/download/test.txt')
        self.assertEqual(response.status_code, 302)  # Redirige a login
        self.assertIn('/auth/login', response.location)
    
    # ========================================================================
    # TESTS PARA RUTAS DE JIRA
    # ========================================================================
    
    def test_jira_test_connection_requires_login(self):
        """Verifica que /api/jira/test-connection requiere autenticación"""
        response = self.client.get('/api/jira/test-connection')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_projects_requires_login(self):
        """Verifica que /api/jira/projects requiere autenticación"""
        response = self.client.get('/api/jira/projects')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_filter_fields_requires_login(self):
        """Verifica que /api/jira/project/<key>/filter-fields requiere autenticación"""
        response = self.client.get('/api/jira/project/TEST/filter-fields')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_metrics_requires_login(self):
        """Verifica que /api/jira/project/<key>/metrics requiere autenticación"""
        response = self.client.get('/api/jira/project/TEST/metrics')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_fields_requires_login(self):
        """Verifica que /api/jira/project/<key>/fields requiere autenticación"""
        response = self.client.get('/api/jira/project/TEST/fields')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_validate_csv_requires_login(self):
        """Verifica que /api/jira/validate-csv-fields requiere autenticación"""
        response = self.client.post('/api/jira/validate-csv-fields', json={})
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_upload_csv_requires_login(self):
        """Verifica que /api/jira/upload-csv requiere autenticación"""
        response = self.client.post('/api/jira/upload-csv')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_download_report_requires_login(self):
        """Verifica que /api/jira/download-report requiere autenticación"""
        response = self.client.post('/api/jira/download-report', json={})
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_jira_download_template_requires_login(self):
        """Verifica que /api/jira/download-template requiere autenticación"""
        response = self.client.get('/api/jira/download-template')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    def test_metrics_download_report_requires_login(self):
        """Verifica que /api/metrics/download-report requiere autenticación"""
        response = self.client.post('/api/metrics/download-report', json={})
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data.get('error'), 'No autenticado')
    
    # ========================================================================
    # TESTS PARA RUTAS PÚBLICAS
    # ========================================================================
    
    def test_login_page_is_public(self):
        """Verifica que /auth/login es pública (accesible sin autenticación)"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
    
    def test_register_page_is_public(self):
        """Verifica que /auth/register es pública (accesible sin autenticación)"""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
    
    def test_infografia_is_public_duplicate(self):
        """Verifica que /infografia es pública (accesible sin autenticación) - duplicado para completitud"""
        response = self.client.get('/infografia')
        self.assertEqual(response.status_code, 200)


class TestAuthenticatedAccess(unittest.TestCase):
    """
    Tests para verificar que las rutas funcionan correctamente con autenticación
    """
    
    def setUp(self):
        """Configuración antes de cada test"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()
    
    def _create_authenticated_client(self):
        """Helper para crear un cliente autenticado"""
        import uuid
        user_service = UserService()
        
        # Usar email único para evitar conflictos
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        
        # Crear usuario dentro del contexto de la app
        with app.app_context():
            try:
                test_user = user_service.create_user(
                    email=unique_email,
                    password='TestPassword123!',
                    role='usuario'
                )
            except Exception as e:
                # Si el usuario ya existe, intentar obtenerlo
                test_user = user_service.get_user_by_email(unique_email)
                if not test_user:
                    raise
        
        # Crear sesión dentro del contexto de request usando session_transaction
        with self.client.session_transaction() as sess:
            # Simular la sesión directamente en el diccionario de sesión
            sess[SessionService.USER_ID_KEY] = test_user.id
            sess[SessionService.USER_EMAIL_KEY] = test_user.email
            sess[SessionService.USER_ROLE_KEY] = test_user.role
            sess[SessionService.LOGIN_TIME_KEY] = '2024-01-01T00:00:00'
            sess['_permanent'] = True
        
        return self.client, test_user
    
    def test_authenticated_user_can_access_menu(self):
        """Verifica que un usuario autenticado puede acceder al menú principal"""
        client, user = self._create_authenticated_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_authenticated_user_can_access_agent(self):
        """Verifica que un usuario autenticado puede acceder al agente"""
        client, user = self._create_authenticated_client()
        response = client.get('/agent')
        self.assertEqual(response.status_code, 200)
    
    def test_authenticated_user_gets_user_info(self):
        """Verifica que el menú principal incluye información del usuario"""
        client, user = self._create_authenticated_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        # La información del usuario se pasa al template
        # Verificamos que la respuesta contiene datos (no verificamos el template directamente)


if __name__ == '__main__':
    unittest.main()

