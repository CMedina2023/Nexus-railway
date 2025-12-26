"""
Tests unitarios para decoradores
"""
import unittest
from unittest.mock import patch, MagicMock
from app.utils.decorators import (
    require_auth,
    cache_result,
    log_execution,
    validate_input
)


class TestDecorators(unittest.TestCase):
    """Tests para decoradores"""

    def test_require_auth_decorator_authenticated(self):
        """Test decorador de autenticación con usuario autenticado"""
        @require_auth
        def protected_function():
            return 'protected_data'
        
        with patch('app.utils.decorators.is_authenticated', return_value=True):
            result = protected_function()
            
            self.assertEqual(result, 'protected_data')

    def test_require_auth_decorator_not_authenticated(self):
        """Test decorador de autenticación sin usuario autenticado"""
        @require_auth
        def protected_function():
            return 'protected_data'
        
        with patch('app.utils.decorators.is_authenticated', return_value=False):
            with self.assertRaises(PermissionError):
                protected_function()

    def test_cache_result_decorator(self):
        """Test decorador de caché"""
        call_count = 0
        
        @cache_result
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = expensive_function(5)
        result2 = expensive_function(5)
        
        self.assertEqual(result1, result2)
        self.assertEqual(call_count, 1)

    def test_log_execution_decorator(self):
        """Test decorador de logging"""
        @log_execution
        def test_function():
            return 'result'
        
        with patch('app.utils.decorators.logger') as mock_logger:
            result = test_function()
            
            self.assertEqual(result, 'result')
            mock_logger.info.assert_called()

    def test_validate_input_decorator_valid(self):
        """Test decorador de validación con entrada válida"""
        @validate_input(lambda x: x > 0)
        def positive_only(x):
            return x * 2
        
        result = positive_only(5)
        
        self.assertEqual(result, 10)

    def test_validate_input_decorator_invalid(self):
        """Test decorador de validación con entrada inválida"""
        @validate_input(lambda x: x > 0)
        def positive_only(x):
            return x * 2
        
        with self.assertRaises(ValueError):
            positive_only(-5)

    def test_timing_decorator(self):
        """Test decorador de medición de tiempo"""
        from app.utils.decorators import timing
        
        @timing
        def slow_function():
            import time
            time.sleep(0.1)
            return 'done'
        
        with patch('app.utils.decorators.logger') as mock_logger:
            result = slow_function()
            
            self.assertEqual(result, 'done')
            mock_logger.info.assert_called()

    def test_retry_decorator(self):
        """Test decorador de reintentos"""
        from app.utils.decorators import retry
        
        attempt_count = 0
        
        @retry(max_attempts=3)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception('Temporary error')
            return 'success'
        
        result = flaky_function()
        
        self.assertEqual(result, 'success')
        self.assertEqual(attempt_count, 2)

    def test_rate_limit_decorator(self):
        """Test decorador de rate limiting"""
        from app.utils.decorators import rate_limit
        
        @rate_limit(calls=2, period=1)
        def limited_function():
            return 'result'
        
        result1 = limited_function()
        result2 = limited_function()
        
        self.assertEqual(result1, 'result')
        self.assertEqual(result2, 'result')

    def test_deprecated_decorator(self):
        """Test decorador de deprecación"""
        from app.utils.decorators import deprecated
        
        @deprecated('Use new_function instead')
        def old_function():
            return 'old_result'
        
        with patch('warnings.warn') as mock_warn:
            result = old_function()
            
            self.assertEqual(result, 'old_result')
            mock_warn.assert_called()


if __name__ == '__main__':
    unittest.main()
