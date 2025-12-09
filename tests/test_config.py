"""
Tests para el módulo de configuración
"""
import unittest
import os
from unittest.mock import patch

from app.core.config import Config


class TestConfig(unittest.TestCase):
    """Tests para la clase Config"""
    
    def test_config_attributes_exist(self):
        """Verifica que todos los atributos de configuración existen"""
        self.assertTrue(hasattr(Config, 'GOOGLE_API_KEY'))
        self.assertTrue(hasattr(Config, 'GEMINI_MODEL'))
        self.assertTrue(hasattr(Config, 'JIRA_BASE_URL'))
        self.assertTrue(hasattr(Config, 'UPLOAD_FOLDER'))
    
    def test_get_max_content_length(self):
        """Verifica que get_max_content_length retorna bytes correctos"""
        result = Config.get_max_content_length()
        expected = Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self.assertEqual(result, expected)
    
    def test_default_values(self):
        """Verifica valores por defecto"""
        # Estos valores deberían estar presentes incluso sin .env
        self.assertIsNotNone(Config.GEMINI_MODEL)
        self.assertIsNotNone(Config.UPLOAD_FOLDER)


if __name__ == '__main__':
    unittest.main()

