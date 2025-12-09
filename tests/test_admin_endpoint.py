"""
Script de prueba para verificar el endpoint de administración
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.app import app
from app.database import init_db
from app.database.repositories.user_repository import UserRepository

def test_admin_endpoint():
    """Prueba el endpoint de administración"""
    print("=" * 60)
    print("🔍 PRUEBA DE ENDPOINT DE ADMINISTRACIÓN")
    print("=" * 60)
    
    # Inicializar base de datos
    print("\n1. Inicializando base de datos...")
    try:
        init_db()
        print("   ✅ Base de datos inicializada")
    except Exception as e:
        print(f"   ❌ Error al inicializar BD: {e}")
        return
    
    # Verificar usuarios en BD
    print("\n2. Verificando usuarios en base de datos...")
    try:
        user_repo = UserRepository()
        users = user_repo.get_all(active_only=False)
        print(f"   ✅ Usuarios encontrados: {len(users)}")
        for user in users:
            print(f"      - {user.email} (rol: {user.role}, activo: {user.active})")
    except Exception as e:
        print(f"   ❌ Error al obtener usuarios: {e}")
        return
    
    # Verificar endpoint registrado
    print("\n3. Verificando endpoints registrados...")
    try:
        admin_routes = [r for r in app.url_map.iter_rules() if 'admin' in r.rule]
        print(f"   ✅ Endpoints admin encontrados: {len(admin_routes)}")
        for route in admin_routes:
            print(f"      - {route.rule} -> {route.endpoint} ({', '.join(route.methods)})")
    except Exception as e:
        print(f"   ❌ Error al verificar rutas: {e}")
        return
    
    # Verificar método get_all_filtered
    print("\n4. Verificando método get_all_filtered()...")
    try:
        filtered_users = user_repo.get_all_filtered()
        print(f"   ✅ get_all_filtered() funciona: {len(filtered_users)} usuarios")
        
        # Probar con filtros
        active_users = user_repo.get_all_filtered(active_only=True)
        print(f"   ✅ Filtro active_only=True: {len(active_users)} usuarios")
        
        admin_users = user_repo.get_all_filtered(role='admin')
        print(f"   ✅ Filtro role=admin: {len(admin_users)} usuarios")
    except Exception as e:
        print(f"   ❌ Error en get_all_filtered(): {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)
    print("\nSi todas las pruebas pasaron, el problema puede estar en:")
    print("  1. Autenticación/autorización (verificar que estés logueado como admin)")
    print("  2. JavaScript del frontend (revisar consola del navegador)")
    print("  3. Renderizado del template (verificar que el HTML se cargue)")

if __name__ == '__main__':
    test_admin_endpoint()

