#!/usr/bin/env python
"""
Script para ejecutar los tests de protección de rutas
Ejecuta: python tests/run_tests.py
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == '__main__':
    import unittest
    
    # Cargar y ejecutar los tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_routes_protection')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    else:
        print(f"❌ ALGUNOS TESTS FALLARON")
        print(f"   Tests ejecutados: {result.testsRun}")
        print(f"   Fallos: {len(result.failures)}")
        print(f"   Errores: {len(result.errors)}")
    print("=" * 70)
    
    sys.exit(0 if result.wasSuccessful() else 1)

