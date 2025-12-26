"""
Tests de integración para generación de historias
"""
import unittest
from unittest.mock import patch, MagicMock
from app.backend.story_generator import StoryGenerator
from app.backend.story_parser import StoryParser
from app.services.generation_orchestrator import GenerationOrchestrator


class TestStoryGenerationIntegration(unittest.TestCase):
    """Tests de integración para generación de historias"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.generator = StoryGenerator()
        self.parser = StoryParser()
        self.orchestrator = GenerationOrchestrator()

    @patch('app.backend.story_generator.openai')
    def test_generate_and_parse_story(self, mock_openai):
        """Test generación y parseo de historia"""
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{
                'message': {
                    'content': 'As a user, I want to login, So that I can access my account'
                }
            }]
        }
        
        generated = self.generator.generate_story('Create login feature')
        parsed = self.parser.parse_user_story(generated)
        
        self.assertIn('role', parsed)
        self.assertIn('action', parsed)

    @patch('app.backend.story_generator.openai')
    def test_complete_story_generation_pipeline(self, mock_openai):
        """Test pipeline completo de generación de historias"""
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{
                'message': {
                    'content': 'As a user, I want to login'
                }
            }]
        }
        
        result = self.orchestrator.orchestrate_story_generation('Login feature')
        
        self.assertIsNotNone(result)

    @patch('app.backend.story_generator.openai')
    @patch('app.services.file_manager.FileManager')
    def test_generate_and_save_stories(self, mock_file, mock_openai):
        """Test generación y guardado de historias"""
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{
                'message': {
                    'content': 'As a user, I want to login'
                }
            }]
        }
        mock_file.return_value.save.return_value = True
        
        result = self.orchestrator.orchestrate_and_save(
            'Login feature',
            'stories.txt'
        )
        
        self.assertTrue(result)

    def test_validate_generated_stories(self):
        """Test validación de historias generadas"""
        stories = [
            'As a user, I want to login',
            'Invalid story format',
            'As a admin, I want to manage users'
        ]
        
        valid_stories = [
            s for s in stories
            if self.parser.validate_story_format(s)
        ]
        
        self.assertGreater(len(valid_stories), 0)


if __name__ == '__main__':
    unittest.main()
