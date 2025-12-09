"""
Tests para utilidades de reintentos
"""
import unittest
from unittest.mock import Mock, patch
import time

from app.utils.retry_utils import call_with_retry, retry_with_backoff
from app.utils.exceptions import AIProcessingError


class TestRetryUtils(unittest.TestCase):
    """Tests para utilidades de reintentos"""
    
    def test_call_with_retry_success(self):
        """Verifica que call_with_retry funciona con éxito inmediato"""
        func = Mock(return_value="success")
        result = call_with_retry(func, max_retries=3)
        self.assertEqual(result, "success")
        self.assertEqual(func.call_count, 1)
    
    def test_call_with_retry_failure_then_success(self):
        """Verifica que call_with_retry reintenta en caso de fallo"""
        func = Mock(side_effect=[Exception("Error"), "success"])
        result = call_with_retry(func, max_retries=3)
        self.assertEqual(result, "success")
        self.assertEqual(func.call_count, 2)


if __name__ == '__main__':
    unittest.main()

