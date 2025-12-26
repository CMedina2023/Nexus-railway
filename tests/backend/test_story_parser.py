"""
Tests unitarios para el parser de historias
"""
import unittest
from app.backend.story_parser import StoryParser


class TestStoryParser(unittest.TestCase):
    """Tests para StoryParser"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.parser = StoryParser()

    def test_parse_user_story_success(self):
        """Test parseo de historia de usuario exitoso"""
        story = "As a user, I want to login, So that I can access my account"
        
        result = self.parser.parse_user_story(story)
        
        self.assertIn('role', result)
        self.assertIn('action', result)
        self.assertIn('benefit', result)

    def test_parse_user_story_invalid_format(self):
        """Test parseo de historia con formato inválido"""
        story = "This is not a valid user story"
        
        with self.assertRaises(ValueError):
            self.parser.parse_user_story(story)

    def test_extract_acceptance_criteria(self):
        """Test extracción de criterios de aceptación"""
        story = """
        As a user, I want to login
        Acceptance Criteria:
        - Valid credentials should grant access
        - Invalid credentials should show error
        """
        
        result = self.parser.extract_acceptance_criteria(story)
        
        self.assertEqual(len(result), 2)

    def test_parse_story_with_priority(self):
        """Test parseo de historia con prioridad"""
        story = "Priority: High\nAs a user, I want to login"
        
        result = self.parser.parse_story_with_metadata(story)
        
        self.assertEqual(result['priority'], 'High')

    def test_parse_story_with_estimate(self):
        """Test parseo de historia con estimación"""
        story = "Estimate: 5 points\nAs a user, I want to login"
        
        result = self.parser.parse_story_with_metadata(story)
        
        self.assertEqual(result['estimate'], '5 points')

    def test_split_stories_from_text(self):
        """Test división de múltiples historias de un texto"""
        text = """
        Story 1: As a user, I want to login
        ---
        Story 2: As a user, I want to register
        """
        
        result = self.parser.split_stories(text)
        
        self.assertEqual(len(result), 2)

    def test_validate_story_completeness(self):
        """Test validación de completitud de historia"""
        complete_story = {
            'role': 'user',
            'action': 'login',
            'benefit': 'access account'
        }
        
        result = self.parser.validate_completeness(complete_story)
        
        self.assertTrue(result)

    def test_validate_story_incomplete(self):
        """Test validación de historia incompleta"""
        incomplete_story = {
            'role': 'user',
            'action': 'login'
        }
        
        result = self.parser.validate_completeness(incomplete_story)
        
        self.assertFalse(result)

    def test_parse_empty_story(self):
        """Test parseo de historia vacía"""
        with self.assertRaises(ValueError):
            self.parser.parse_user_story('')

    def test_extract_tags_from_story(self):
        """Test extracción de tags de historia"""
        story = "As a user, I want to login #authentication #security"
        
        result = self.parser.extract_tags(story)
        
        self.assertIn('authentication', result)
        self.assertIn('security', result)


if __name__ == '__main__':
    unittest.main()
