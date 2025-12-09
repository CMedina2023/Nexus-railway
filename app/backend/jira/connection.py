"""
Servicio de conexión con Jira
Responsabilidad única: Manejar conexión y autenticación con Jira
"""
import requests
import logging
from typing import Dict
from requests.auth import HTTPBasicAuth

from app.core.config import Config

logger = logging.getLogger(__name__)


class JiraConnection:
    """Maneja la conexión y autenticación con Jira"""
    
    def __init__(self, base_url: str = None, email: str = None, api_token: str = None):
        """
        Inicializa la conexión con Jira
        
        Args:
            base_url: URL base de Jira (default: Config.JIRA_BASE_URL)
            email: Email de Jira (default: Config.JIRA_EMAIL)
            api_token: Token de API de Jira (default: Config.JIRA_API_TOKEN)
        """
        self._base_url = (base_url or Config.JIRA_BASE_URL).rstrip('/')
        email = email or Config.JIRA_EMAIL
        api_token = api_token or Config.JIRA_API_TOKEN
        
        self._auth = HTTPBasicAuth(email, api_token)
        self._session = requests.Session()
        self._session.auth = self._auth
        self._session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    @property
    def base_url(self) -> str:
        """URL base de Jira (solo lectura)"""
        return self._base_url
    
    @property
    def session(self) -> requests.Session:
        """Sesión de requests (solo lectura)"""
        return self._session
    
    def test_connection(self) -> Dict:
        """
        Prueba la conexión con Jira
        
        Returns:
            Dict con éxito/error de la conexión
        """
        try:
            url = f"{self._base_url}/rest/api/3/myself"
            response = self._session.get(url, timeout=Config.JIRA_TIMEOUT_SHORT)

            if response.status_code == 200:
                user_data = response.json()
                return {
                    'success': True,
                    'user': user_data.get('displayName', 'Usuario'),
                    'email': user_data.get('emailAddress', '')
                }
            else:
                return {
                    'success': False,
                    'error': f'Error de autenticación: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Error al conectar con Jira: {str(e)}")
            return {
                'success': False,
                'error': f'Error de conexión: {str(e)}'
            }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Método privado para hacer requests a la API de Jira
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint de la API (ej: '/rest/api/3/project')
            **kwargs: Argumentos adicionales para requests
            
        Returns:
            Response object de requests
        """
        url = f"{self._base_url}{endpoint}"
        return self._session.request(method, url, **kwargs)
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Hace una petición GET a Jira"""
        return self._make_request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Hace una petición POST a Jira"""
        return self._make_request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Hace una petición PUT a Jira"""
        return self._make_request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Hace una petición DELETE a Jira"""
        return self._make_request('DELETE', endpoint, **kwargs)

