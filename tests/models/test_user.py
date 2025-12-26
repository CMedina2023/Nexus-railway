"""
Tests unitarios para modelos - User
"""
import unittest
from app.models.user import User


class TestUserModel(unittest.TestCase):
    """Tests para el modelo User"""

    def test_create_user_instance(self):
        """Test creación de instancia de usuario"""
        user = User(
            id=1,
            username='testuser',
            email='test@example.com'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')

    def test_user_to_dict(self):
        """Test conversión de usuario a diccionario"""
        user = User(id=1, username='testuser', email='test@example.com')
        
        user_dict = user.to_dict()
        
        self.assertIsInstance(user_dict, dict)
        self.assertEqual(user_dict['username'], 'testuser')

    def test_user_from_dict(self):
        """Test creación de usuario desde diccionario"""
        user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        user = User.from_dict(user_data)
        
        self.assertEqual(user.username, 'testuser')

    def test_user_repr(self):
        """Test representación de usuario"""
        user = User(id=1, username='testuser', email='test@example.com')
        
        repr_str = repr(user)
        
        self.assertIn('testuser', repr_str)

    def test_user_equality(self):
        """Test igualdad de usuarios"""
        user1 = User(id=1, username='testuser', email='test@example.com')
        user2 = User(id=1, username='testuser', email='test@example.com')
        
        self.assertEqual(user1, user2)

    def test_user_hash(self):
        """Test hash de usuario"""
        user = User(id=1, username='testuser', email='test@example.com')
        
        hash_value = hash(user)
        
        self.assertIsInstance(hash_value, int)

    def test_user_validation(self):
        """Test validación de usuario"""
        user = User(id=1, username='testuser', email='test@example.com')
        
        is_valid = user.validate()
        
        self.assertTrue(is_valid)

    def test_user_invalid_email(self):
        """Test usuario con email inválido"""
        with self.assertRaises(ValueError):
            User(id=1, username='testuser', email='invalid-email')


if __name__ == '__main__':
    unittest.main()
