"""
Tests unitarios para el generador de historias
"""
import unittest
from unittest.mock import patch, MagicMock
from app.backend.story_generator import StoryGenerator


class TestStoryGenerator(unittest.TestCase):
    """Tests para StoryGenerator"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.story_generator = StoryGenerator()

    @patch('app.backend.story_generator.openai')
    def test_generate_story_success(self, mock_openai):
        """Test generación de historia exitosa"""
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{'message': {'content': 'Generated story'}}]
        }
        
        result = self.story_generator.generate_story('Create a login feature')
        
        self.assertEqual(result, 'Generated story')

    @patch('app.backend.story_generator.openai')
    def test_generate_story_api_error(self, mock_openai):
        """Test generación de historia con error de API"""
        mock_openai.ChatCompletion.create.side_effect = Exception('API Error')
        
        with self.assertRaises(Exception):
            self.story_generator.generate_story('Create a feature')

    def test_generate_story_empty_prompt(self):
        """Test generación de historia con prompt vacío"""
        with self.assertRaises(ValueError):
            self.story_generator.generate_story('')

    def test_generate_story_none_prompt(self):
        """Test generación de historia con prompt None"""
        with self.assertRaises((ValueError, TypeError)):
            self.story_generator.generate_story(None)

    @patch('app.backend.story_generator.openai')
    def test_generate_multiple_stories(self, mock_openai):
        """Test generación de múltiples historias"""
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{'message': {'content': 'Story 1\n---\nStory 2'}}]
        }
        
        result = self.story_generator.generate_stories(['Prompt 1', 'Prompt 2'])
        
        self.assertEqual(len(result), 2)

    @patch('app.backend.story_generator.openai')
    def test_generate_story_with_context(self, mock_openai):
        """Test generación de historia con contexto"""
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{'message': {'content': 'Contextual story'}}]
        }
        
        result = self.story_generator.generate_story_with_context(
            'Create feature',
            context={'project': 'Test Project'}
        )
        
        self.assertIsNotNone(result)

    def test_validate_story_format(self):
        """Test validación de formato de historia"""
        valid_story = "As a user, I want to login, So that I can access my account"
        
        result = self.story_generator.validate_story_format(valid_story)
        
        self.assertTrue(result)

    def test_validate_story_format_invalid(self):
        """Test validación de formato de historia inválido"""
        invalid_story = "This is not a proper user story"
        
        result = self.story_generator.validate_story_format(invalid_story)
        
        self.assertFalse(result)

    @patch('app.backend.story_generator.openai')
    def test_generate_story_with_retry(self, mock_openai):
        """Test generación de historia con reintentos"""
        mock_openai.ChatCompletion.create.side_effect = [
            Exception('Temporary error'),
            {'choices': [{'message': {'content': 'Success on retry'}}]}
        ]
        
        result = self.story_generator.generate_with_retry('Create feature', max_retries=2)
        
        self.assertEqual(result, 'Success on retry')

    @patch('app.backend.story_generator.openai')
    def test_generate_story_max_tokens(self, mock_openai):
        """Test generación de historia con límite de tokens"""
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{'message': {'content': 'Short story'}}]
        }
        
        result = self.story_generator.generate_story('Prompt', max_tokens=100)
        
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
