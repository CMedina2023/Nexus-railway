"""
Tests unitarios para modelos - UserStory
"""
import unittest
from app.models.user_story import UserStory


class TestUserStoryModel(unittest.TestCase):
    """Tests para el modelo UserStory"""

    def test_create_user_story_instance(self):
        """Test creación de instancia de historia de usuario"""
        story = UserStory(
            id=1,
            title='User login',
            description='As a user, I want to login'
        )
        
        self.assertEqual(story.title, 'User login')

    def test_user_story_to_dict(self):
        """Test conversión de historia a diccionario"""
        story = UserStory(
            id=1,
            title='User login',
            description='As a user, I want to login'
        )
        
        story_dict = story.to_dict()
        
        self.assertIsInstance(story_dict, dict)
        self.assertEqual(story_dict['title'], 'User login')

    def test_user_story_from_dict(self):
        """Test creación de historia desde diccionario"""
        story_data = {
            'id': 1,
            'title': 'User login',
            'description': 'As a user, I want to login'
        }
        
        story = UserStory.from_dict(story_data)
        
        self.assertEqual(story.title, 'User login')

    def test_user_story_validation(self):
        """Test validación de historia de usuario"""
        story = UserStory(
            id=1,
            title='User login',
            description='As a user, I want to login'
        )
        
        is_valid = story.validate()
        
        self.assertTrue(is_valid)

    def test_user_story_empty_title(self):
        """Test historia con título vacío"""
        with self.assertRaises(ValueError):
            UserStory(id=1, title='', description='Description')

    def test_user_story_add_acceptance_criteria(self):
        """Test agregar criterios de aceptación"""
        story = UserStory(id=1, title='Login', description='User login')
        
        story.add_acceptance_criteria('Valid credentials grant access')
        
        self.assertEqual(len(story.acceptance_criteria), 1)

    def test_user_story_set_priority(self):
        """Test establecer prioridad"""
        story = UserStory(id=1, title='Login', description='User login')
        
        story.set_priority('High')
        
        self.assertEqual(story.priority, 'High')

    def test_user_story_estimate_points(self):
        """Test establecer estimación en puntos"""
        story = UserStory(id=1, title='Login', description='User login')
        
        story.set_estimate(5)
        
        self.assertEqual(story.estimate, 5)


if __name__ == '__main__':
    unittest.main()
