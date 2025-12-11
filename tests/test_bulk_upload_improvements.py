"""
Test para las mejoras de carga masiva
Verifica que las nuevas clases funcionan correctamente
"""
import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Importar las clases a testear
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.backend.jira.issue_service import FieldMetadataCache, IssueCreationRateLimiter


class TestFieldMetadataCache(unittest.TestCase):
    """Tests para FieldMetadataCache"""
    
    def setUp(self):
        """Setup antes de cada test"""
        self.cache = FieldMetadataCache(ttl_seconds=2)  # TTL corto para tests
    
    def test_cache_set_and_get(self):
        """Test: Guardar y obtener datos del cache"""
        test_data = {'field1': 'value1', 'field2': 'value2'}
        cache_key = 'test:key'
        
        # Guardar en cache
        self.cache.set(cache_key, test_data)
        
        # Obtener del cache
        result = self.cache.get(cache_key)
        
        self.assertEqual(result, test_data)
    
    def test_cache_expiration(self):
        """Test: Cache expira después del TTL"""
        test_data = {'field1': 'value1'}
        cache_key = 'test:expiration'
        
        # Guardar en cache
        self.cache.set(cache_key, test_data)
        
        # Verificar que está disponible
        self.assertIsNotNone(self.cache.get(cache_key))
        
        # Esperar a que expire (TTL = 2 segundos)
        time.sleep(2.5)
        
        # Verificar que expiró
        self.assertIsNone(self.cache.get(cache_key))
    
    def test_cache_invalidate(self):
        """Test: Invalidar cache manualmente"""
        test_data = {'field1': 'value1'}
        cache_key = 'test:invalidate'
        
        # Guardar en cache
        self.cache.set(cache_key, test_data)
        
        # Verificar que está disponible
        self.assertIsNotNone(self.cache.get(cache_key))
        
        # Invalidar
        self.cache.invalidate(cache_key)
        
        # Verificar que fue eliminado
        self.assertIsNone(self.cache.get(cache_key))
    
    def test_cache_clear(self):
        """Test: Limpiar todo el cache"""
        # Guardar múltiples entradas
        self.cache.set('key1', {'data': 1})
        self.cache.set('key2', {'data': 2})
        self.cache.set('key3', {'data': 3})
        
        # Verificar que están disponibles
        self.assertIsNotNone(self.cache.get('key1'))
        self.assertIsNotNone(self.cache.get('key2'))
        self.assertIsNotNone(self.cache.get('key3'))
        
        # Limpiar todo
        self.cache.clear()
        
        # Verificar que todo fue eliminado
        self.assertIsNone(self.cache.get('key1'))
        self.assertIsNone(self.cache.get('key2'))
        self.assertIsNone(self.cache.get('key3'))
    
    def test_cache_get_nonexistent(self):
        """Test: Obtener clave que no existe"""
        result = self.cache.get('nonexistent:key')
        self.assertIsNone(result)


class TestIssueCreationRateLimiter(unittest.TestCase):
    """Tests para IssueCreationRateLimiter"""
    
    def setUp(self):
        """Setup antes de cada test"""
        self.limiter = IssueCreationRateLimiter(
            base_delay=0.1,  # Delays cortos para tests
            backoff_multiplier=2.0,
            max_delay=1.0
        )
    
    def test_initial_wait(self):
        """Test: Primera espera no debe demorar"""
        start = time.time()
        self.limiter.wait()
        elapsed = time.time() - start
        
        # Primera llamada no debe esperar
        self.assertLess(elapsed, 0.05)
    
    def test_rate_limiting_delay(self):
        """Test: Delay entre requests"""
        # Primera llamada
        self.limiter.wait()
        
        # Segunda llamada debe esperar base_delay
        start = time.time()
        self.limiter.wait()
        elapsed = time.time() - start
        
        # Debe haber esperado al menos base_delay (0.1s)
        self.assertGreaterEqual(elapsed, 0.08)  # Margen de error
    
    def test_backoff_on_errors(self):
        """Test: Backoff exponencial en errores"""
        self.limiter.wait()
        
        # Reportar error
        self.limiter.report_error()
        
        # El delay debe haber aumentado
        self.assertEqual(self.limiter._current_delay, 0.2)  # 0.1 * 2.0
        
        # Reportar otro error
        self.limiter.report_error()
        
        # El delay debe haber aumentado de nuevo
        self.assertEqual(self.limiter._current_delay, 0.4)  # 0.2 * 2.0
    
    def test_backoff_max_delay(self):
        """Test: Delay no excede el máximo"""
        self.limiter.wait()
        
        # Reportar múltiples errores
        for _ in range(10):
            self.limiter.report_error()
        
        # El delay no debe exceder max_delay
        self.assertLessEqual(self.limiter._current_delay, 1.0)
    
    def test_reset_on_success(self):
        """Test: Reset de backoff en éxito"""
        self.limiter.wait()
        
        # Reportar errores
        self.limiter.report_error()
        self.limiter.report_error()
        
        # Verificar que el delay aumentó
        self.assertGreater(self.limiter._current_delay, 0.1)
        
        # Reportar éxito
        self.limiter.report_success()
        
        # El delay debe haberse reseteado
        self.assertEqual(self.limiter._current_delay, 0.1)
    
    def test_consecutive_errors_count(self):
        """Test: Contador de errores consecutivos"""
        # Reportar errores
        self.limiter.report_error()
        self.assertEqual(self.limiter._consecutive_errors, 1)
        
        self.limiter.report_error()
        self.assertEqual(self.limiter._consecutive_errors, 2)
        
        self.limiter.report_error()
        self.assertEqual(self.limiter._consecutive_errors, 3)
        
        # Reportar éxito
        self.limiter.report_success()
        
        # Contador debe resetearse
        self.assertEqual(self.limiter._consecutive_errors, 0)


class TestIntegration(unittest.TestCase):
    """Tests de integración"""
    
    def test_cache_and_limiter_together(self):
        """Test: Cache y rate limiter funcionan juntos"""
        cache = FieldMetadataCache(ttl_seconds=5)
        limiter = IssueCreationRateLimiter(base_delay=0.05)
        
        # Simular flujo de carga masiva
        for i in range(3):
            # Aplicar rate limiting
            limiter.wait()
            
            # Intentar obtener del cache
            data = cache.get('project:type')
            
            if data is None:
                # Simular obtención de metadata
                data = {'field1': 'value1', 'field2': 'value2'}
                cache.set('project:type', data)
            
            # Simular creación de issue
            success = True  # Simular éxito
            
            if success:
                limiter.report_success()
            else:
                limiter.report_error()
        
        # Verificar que el cache tiene datos
        self.assertIsNotNone(cache.get('project:type'))
        
        # Verificar que el rate limiter está en estado normal
        self.assertEqual(limiter._consecutive_errors, 0)


if __name__ == '__main__':
    # Ejecutar tests
    unittest.main(verbosity=2)





