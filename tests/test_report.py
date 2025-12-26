#!/usr/bin/env python
"""
Script para verificar la estructura de tests y generar estadísticas
"""
import os
from pathlib import Path


def count_test_files(directory):
    """Cuenta archivos de test en un directorio"""
    test_files = list(Path(directory).rglob('test_*.py'))
    return len(test_files)


def count_test_functions(file_path):
    """Cuenta funciones de test en un archivo"""
    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('def test_'):
                    count += 1
    except Exception:
        pass
    return count


def generate_test_report():
    """Genera reporte de tests"""
    base_dir = Path(__file__).parent
    
    modules = {
        'auth': base_dir / 'auth',
        'backend': base_dir / 'backend',
        'backend/jira': base_dir / 'backend' / 'jira',
        'backend/generators': base_dir / 'backend' / 'generators',
        'database': base_dir / 'database',
        'database/repositories': base_dir / 'database' / 'repositories',
        'services': base_dir / 'services',
        'utils': base_dir / 'utils',
        'models': base_dir / 'models',
        'routes': base_dir / 'routes',
        'integration': base_dir / 'integration'
    }
    
    print("=" * 80)
    print("REPORTE DE TESTS UNITARIOS - NEXUS RAILWAY")
    print("=" * 80)
    print()
    
    total_files = 0
    total_tests = 0
    
    for module_name, module_path in modules.items():
        if module_path.exists():
            file_count = count_test_files(module_path)
            test_count = sum(
                count_test_functions(f)
                for f in module_path.rglob('test_*.py')
            )
            
            total_files += file_count
            total_tests += test_count
            
            print(f"📁 {module_name:30} | Archivos: {file_count:3} | Tests: {test_count:4}")
    
    print()
    print("=" * 80)
    print(f"TOTAL: {total_files} archivos de test con {total_tests} tests unitarios")
    print("=" * 80)
    print()
    print("✅ Estructura de tests generada exitosamente")
    print("📊 Objetivo de cobertura: 80%")
    print()
    print("Para ejecutar los tests:")
    print("  pytest")
    print()
    print("Para ver cobertura:")
    print("  pytest --cov=app --cov-report=html")
    print()


if __name__ == '__main__':
    generate_test_report()
