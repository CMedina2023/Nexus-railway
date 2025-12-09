#!/usr/bin/env python
"""
Script para ejecutar todos los tests del sistema de autenticación
Ejecuta: python tests/run_all_tests.py
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == '__main__':
    import unittest
    
    print("=" * 70)
    print("EJECUTANDO TODOS LOS TESTS DEL SISTEMA DE AUTENTICACION")
    print("=" * 70)
    print()
    
    # Cargar y ejecutar los tests
    loader = unittest.TestLoader()
    
    # Tests de protección de rutas
    print("[*] Ejecutando tests de proteccion de rutas...")
    suite1 = loader.loadTestsFromName('tests.test_routes_protection')
    
    # Tests completos del sistema
    print("[*] Ejecutando tests completos del sistema...")
    suite2 = loader.loadTestsFromName('tests.test_complete_auth_system')
    
    # Combinar suites
    suite = unittest.TestSuite([suite1, suite2])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("[OK] TODOS LOS TESTS PASARON EXITOSAMENTE")
        print(f"    Tests ejecutados: {result.testsRun}")
    else:
        print("[ERROR] ALGUNOS TESTS FALLARON")
        print(f"    Tests ejecutados: {result.testsRun}")
        print(f"    Fallos: {len(result.failures)}")
        print(f"    Errores: {len(result.errors)}")
        
        if result.failures:
            print("\n[*] FALLOS:")
            for test, traceback in result.failures:
                print(f"    - {test}")
        
        if result.errors:
            print("\n[*] ERRORES:")
            for test, traceback in result.errors:
                print(f"    - {test}")
    print("=" * 70)
    
    sys.exit(0 if result.wasSuccessful() else 1)

