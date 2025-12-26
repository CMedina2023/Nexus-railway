"""
Tests unitarios para el servicio de feedback
"""
import unittest
from unittest.mock import patch, MagicMock
from app.services.feedback_service import FeedbackService


class TestFeedbackService(unittest.TestCase):
    """Tests para FeedbackService"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_repository = MagicMock()
        self.feedback_service = FeedbackService(self.mock_repository)

    def test_create_feedback_success(self):
        """Test creación de feedback exitosa"""
        self.mock_repository.create.return_value = {'id': 1, 'rating': 5}
        
        result = self.feedback_service.create_feedback(
            user_id=1,
            rating=5,
            comment='Great feature!'
        )
        
        self.assertEqual(result['rating'], 5)

    def test_create_feedback_invalid_rating(self):
        """Test creación de feedback con rating inválido"""
        with self.assertRaises(ValueError):
            self.feedback_service.create_feedback(
                user_id=1,
                rating=6,
                comment='Invalid'
            )

    def test_get_feedback_by_id_success(self):
        """Test obtener feedback por ID exitoso"""
        self.mock_repository.get_by_id.return_value = {'id': 1, 'rating': 4}
        
        result = self.feedback_service.get_feedback(1)
        
        self.assertEqual(result['id'], 1)

    def test_get_feedback_by_user(self):
        """Test obtener feedback por usuario"""
        self.mock_repository.get_by_user.return_value = [
            {'id': 1, 'user_id': 1},
            {'id': 2, 'user_id': 1}
        ]
        
        result = self.feedback_service.get_user_feedback(1)
        
        self.assertEqual(len(result), 2)

    def test_calculate_average_rating(self):
        """Test cálculo de rating promedio"""
        self.mock_repository.get_all.return_value = [
            {'rating': 5},
            {'rating': 4},
            {'rating': 3}
        ]
        
        result = self.feedback_service.calculate_average_rating()
        
        self.assertEqual(result, 4.0)

    def test_get_feedback_statistics(self):
        """Test obtener estadísticas de feedback"""
        self.mock_repository.get_all.return_value = [
            {'rating': 5},
            {'rating': 5},
            {'rating': 4},
            {'rating': 3}
        ]
        
        result = self.feedback_service.get_statistics()
        
        self.assertIn('average', result)
        self.assertIn('total', result)

    def test_update_feedback_success(self):
        """Test actualización de feedback exitosa"""
        self.mock_repository.update.return_value = {'id': 1, 'rating': 5}
        
        result = self.feedback_service.update_feedback(1, {'rating': 5})
        
        self.assertEqual(result['rating'], 5)

    def test_delete_feedback_success(self):
        """Test eliminación de feedback exitosa"""
        self.mock_repository.delete.return_value = True
        
        result = self.feedback_service.delete_feedback(1)
        
        self.assertTrue(result)

    def test_get_recent_feedback(self):
        """Test obtener feedback reciente"""
        self.mock_repository.get_recent.return_value = [
            {'id': 3, 'created_at': '2024-01-03'},
            {'id': 2, 'created_at': '2024-01-02'}
        ]
        
        result = self.feedback_service.get_recent_feedback(limit=2)
        
        self.assertEqual(len(result), 2)

    def test_filter_feedback_by_rating(self):
        """Test filtrar feedback por rating"""
        self.mock_repository.get_by_rating.return_value = [
            {'id': 1, 'rating': 5},
            {'id': 2, 'rating': 5}
        ]
        
        result = self.feedback_service.filter_by_rating(5)
        
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
