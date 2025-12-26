"""
Tests unitarios para utilidades de reintentos
"""
import unittest
from unittest.mock import patch, MagicMock
from app.utils.retry_utils import RetryUtils


class TestRetryUtils(unittest.TestCase):
    """Tests para RetryUtils"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.retry_utils = RetryUtils()

    def test_retry_success_first_attempt(self):
        """Test reintento exitoso en primer intento"""
        mock_func = MagicMock(return_value='success')
        
        result = self.retry_utils.retry(mock_func, max_attempts=3)
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 1)

    def test_retry_success_after_failures(self):
        """Test reintento exitoso después de fallos"""
        mock_func = MagicMock(side_effect=[
            Exception('Error 1'),
            Exception('Error 2'),
            'success'
        ])
        
        result = self.retry_utils.retry(mock_func, max_attempts=3)
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_max_attempts_exceeded(self):
        """Test reintento con máximo de intentos excedido"""
        mock_func = MagicMock(side_effect=Exception('Persistent error'))
        
        with self.assertRaises(Exception):
            self.retry_utils.retry(mock_func, max_attempts=3)

    def test_retry_with_exponential_backoff(self):
        """Test reintento con backoff exponencial"""
        mock_func = MagicMock(side_effect=[
            Exception('Error'),
            'success'
        ])
        
        with patch('time.sleep') as mock_sleep:
            result = self.retry_utils.retry_with_backoff(
                mock_func,
                max_attempts=3,
                backoff_factor=2
            )
            
            self.assertEqual(result, 'success')
            mock_sleep.assert_called()

    def test_retry_with_custom_exception(self):
        """Test reintento con excepción personalizada"""
        mock_func = MagicMock(side_effect=ValueError('Custom error'))
        
        with self.assertRaises(ValueError):
            self.retry_utils.retry(
                mock_func,
                max_attempts=2,
                catch_exceptions=(ValueError,)
            )

    def test_retry_with_callback(self):
        """Test reintento con callback en cada intento"""
        mock_func = MagicMock(side_effect=[Exception('Error'), 'success'])
        mock_callback = MagicMock()
        
        result = self.retry_utils.retry_with_callback(
            mock_func,
            callback=mock_callback,
            max_attempts=3
        )
        
        self.assertEqual(result, 'success')
        mock_callback.assert_called()

    def test_retry_with_timeout(self):
        """Test reintento con timeout"""
        mock_func = MagicMock(return_value='success')
        
        result = self.retry_utils.retry_with_timeout(
            mock_func,
            timeout=5,
            max_attempts=3
        )
        
        self.assertEqual(result, 'success')

    def test_retry_decorator_success(self):
        """Test decorador de reintento exitoso"""
        @self.retry_utils.retry_decorator(max_attempts=3)
        def test_function():
            return 'success'
        
        result = test_function()
        
        self.assertEqual(result, 'success')

    def test_retry_with_jitter(self):
        """Test reintento con jitter"""
        mock_func = MagicMock(side_effect=[Exception('Error'), 'success'])
        
        with patch('random.uniform', return_value=0.5):
            with patch('time.sleep'):
                result = self.retry_utils.retry_with_jitter(
                    mock_func,
                    max_attempts=3
                )
                
                self.assertEqual(result, 'success')

    def test_retry_async_function(self):
        """Test reintento de función asíncrona"""
        async def async_func():
            return 'async_success'
        
        result = self.retry_utils.retry_async(async_func, max_attempts=3)
        
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
