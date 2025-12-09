"""
Tests para agent_manager
"""
import unittest
from unittest.mock import Mock, patch

from app.backend.agent_manager import simple_agent_processing, get_download_type


class TestAgentManager(unittest.TestCase):
    """Tests para agent_manager"""
    
    def test_get_download_type_matrix(self):
        """Verifica tipo de descarga para matriz"""
        result = get_download_type("matrix_generator")
        self.assertEqual(result, 'zip')
    
    def test_get_download_type_story(self):
        """Verifica tipo de descarga para historia"""
        result = get_download_type("story_generator")
        self.assertEqual(result, 'docx')
    
    def test_get_download_type_default(self):
        """Verifica tipo de descarga por defecto"""
        result = get_download_type("unknown")
        self.assertEqual(result, 'txt')


if __name__ == '__main__':
    unittest.main()

