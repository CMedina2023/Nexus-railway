"""
Test simple para verificar la lógica de Cache y Rate Limiter
Sin dependencias externas
"""
import time
from datetime import datetime, timedelta


# ============================================================================
# Copias simplificadas de las clases para testing independiente
# ============================================================================

class FieldMetadataCache:
    """Cache con TTL para metadata de campos"""
    
    def __init__(self, ttl_seconds=300):
        self._cache = {}
        self._ttl_seconds = ttl_seconds
    
    def get(self, cache_key):
        if cache_key not in self._cache:
            return None
        
        cached_item = self._cache[cache_key]
        timestamp = cached_item.get('timestamp')
        data = cached_item.get('data')
        
        if timestamp and datetime.now() - timestamp > timedelta(seconds=self._ttl_seconds):
            del self._cache[cache_key]
            return None
        
        return data
    
    def set(self, cache_key, data):
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def invalidate(self, cache_key):
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    def clear(self):
        self._cache.clear()


class IssueCreationRateLimiter:
    """Rate limiter con backoff exponencial"""
    
    def __init__(self, base_delay=0.5, backoff_multiplier=1.5, max_delay=5.0):
        self._base_delay = base_delay
        self._backoff_multiplier = backoff_multiplier
        self._max_delay = max_delay
        self._current_delay = base_delay
        self._consecutive_errors = 0
        self._last_request_time = None
    
    def wait(self):
        if self._last_request_time is None:
            self._last_request_time = time.time()
            return
        
        elapsed = time.time() - self._last_request_time
        required_delay = self._current_delay
        
        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def report_success(self):
        self._consecutive_errors = 0
        self._current_delay = self._base_delay
    
    def report_error(self):
        self._consecutive_errors += 1
        self._current_delay = min(
            self._current_delay * self._backoff_multiplier,
            self._max_delay
        )


# ============================================================================
# Tests
# ============================================================================

def test_cache_basic():
    """Test básico de cache"""
    print("\n[TEST] Cache básico...")
    cache = FieldMetadataCache(ttl_seconds=2)
    
    # Guardar datos
    test_data = {'field1': 'value1', 'field2': 'value2'}
    cache.set('test:key', test_data)
    
    # Recuperar datos
    result = cache.get('test:key')
    assert result == test_data, "Cache debe retornar los datos guardados"
    print("✅ Cache básico funciona")


def test_cache_expiration():
    """Test de expiración de cache"""
    print("\n[TEST] Expiración de cache...")
    cache = FieldMetadataCache(ttl_seconds=1)
    
    # Guardar datos
    cache.set('test:expiration', {'data': 'test'})
    
    # Verificar que está disponible
    assert cache.get('test:expiration') is not None, "Cache debe estar disponible"
    
    # Esperar a que expire
    print("  Esperando 1.5 segundos para que expire...")
    time.sleep(1.5)
    
    # Verificar que expiró
    assert cache.get('test:expiration') is None, "Cache debe haber expirado"
    print("✅ Expiración de cache funciona")


def test_cache_invalidation():
    """Test de invalidación manual"""
    print("\n[TEST] Invalidación de cache...")
    cache = FieldMetadataCache(ttl_seconds=10)
    
    # Guardar datos
    cache.set('test:invalidate', {'data': 'test'})
    
    # Verificar que está disponible
    assert cache.get('test:invalidate') is not None, "Cache debe estar disponible"
    
    # Invalidar
    cache.invalidate('test:invalidate')
    
    # Verificar que fue eliminado
    assert cache.get('test:invalidate') is None, "Cache debe haber sido invalidado"
    print("✅ Invalidación de cache funciona")


def test_rate_limiter_basic():
    """Test básico de rate limiter"""
    print("\n[TEST] Rate limiter básico...")
    limiter = IssueCreationRateLimiter(base_delay=0.1, backoff_multiplier=2.0, max_delay=1.0)
    
    # Primera llamada no debe esperar
    start = time.time()
    limiter.wait()
    elapsed = time.time() - start
    assert elapsed < 0.05, "Primera llamada no debe esperar"
    
    # Segunda llamada debe esperar base_delay
    start = time.time()
    limiter.wait()
    elapsed = time.time() - start
    assert elapsed >= 0.08, f"Segunda llamada debe esperar ~0.1s (esperó {elapsed:.3f}s)"
    print("✅ Rate limiter básico funciona")


def test_rate_limiter_backoff():
    """Test de backoff exponencial"""
    print("\n[TEST] Backoff exponencial...")
    limiter = IssueCreationRateLimiter(base_delay=0.1, backoff_multiplier=2.0, max_delay=1.0)
    
    limiter.wait()
    
    # Reportar errores y verificar backoff
    limiter.report_error()
    assert limiter._current_delay == 0.2, f"Delay debe ser 0.2, es {limiter._current_delay}"
    
    limiter.report_error()
    assert limiter._current_delay == 0.4, f"Delay debe ser 0.4, es {limiter._current_delay}"
    
    limiter.report_error()
    assert limiter._current_delay == 0.8, f"Delay debe ser 0.8, es {limiter._current_delay}"
    
    # Verificar límite máximo
    for _ in range(5):
        limiter.report_error()
    assert limiter._current_delay <= 1.0, f"Delay no debe exceder 1.0, es {limiter._current_delay}"
    
    print("✅ Backoff exponencial funciona")


def test_rate_limiter_reset():
    """Test de reset después de éxito"""
    print("\n[TEST] Reset de rate limiter...")
    limiter = IssueCreationRateLimiter(base_delay=0.1, backoff_multiplier=2.0, max_delay=1.0)
    
    limiter.wait()
    
    # Reportar errores
    limiter.report_error()
    limiter.report_error()
    assert limiter._current_delay > 0.1, "Delay debe haber aumentado"
    
    # Reportar éxito
    limiter.report_success()
    assert limiter._current_delay == 0.1, "Delay debe haberse reseteado"
    assert limiter._consecutive_errors == 0, "Contador de errores debe resetearse"
    
    print("✅ Reset de rate limiter funciona")


def test_integration():
    """Test de integración: Cache + Rate Limiter"""
    print("\n[TEST] Integración Cache + Rate Limiter...")
    cache = FieldMetadataCache(ttl_seconds=5)
    limiter = IssueCreationRateLimiter(base_delay=0.05, backoff_multiplier=1.5, max_delay=1.0)
    
    # Simular carga masiva de 5 issues
    for i in range(5):
        # Aplicar rate limiting
        limiter.wait()
        
        # Intentar obtener metadata del cache
        metadata = cache.get('RB:Test Case')
        
        if metadata is None:
            # Simular obtención de metadata de Jira
            metadata = {
                'customfield_10533': {'name': 'Campo 1', 'operations': ['set']},
                'customfield_10568': {'name': 'Campo 2', 'operations': ['set']}
            }
            cache.set('RB:Test Case', metadata)
            print(f"  Issue {i+1}: Metadata obtenida de Jira y guardada en cache")
        else:
            print(f"  Issue {i+1}: Metadata obtenida del cache (cache hit)")
        
        # Simular creación exitosa
        limiter.report_success()
    
    # Verificar que el cache tiene datos
    assert cache.get('RB:Test Case') is not None, "Cache debe tener metadata"
    
    # Verificar que el rate limiter está en estado normal
    assert limiter._consecutive_errors == 0, "No debe haber errores consecutivos"
    
    print("✅ Integración funciona correctamente")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("=" * 70)
    print("TESTS DE MEJORAS DE CARGA MASIVA")
    print("=" * 70)
    
    tests = [
        test_cache_basic,
        test_cache_expiration,
        test_cache_invalidation,
        test_rate_limiter_basic,
        test_rate_limiter_backoff,
        test_rate_limiter_reset,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FALLÓ: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTADOS: {passed} tests pasaron, {failed} tests fallaron")
    print("=" * 70)
    
    if failed == 0:
        print("✅ ¡TODOS LOS TESTS PASARON!")
        return 0
    else:
        print("❌ Algunos tests fallaron")
        return 1


if __name__ == '__main__':
    exit(run_all_tests())


