"""
Script de prueba rápida del sistema de autenticación
Ejecuta este script después de iniciar el servidor (python run.py)
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_login():
    """Prueba el sistema de login"""
    session = requests.Session()
    
    print("=" * 60)
    print("🧪 PRUEBA DEL SISTEMA DE AUTENTICACIÓN")
    print("=" * 60)
    
    # 1. Login
    print("\n1️⃣  Login...")
    email = input("   Email: ").strip() or "admin@test.com"
    password = input("   Password: ").strip() or "Admin123!"
    
    try:
        response = session.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login exitoso!")
            print(f"   Usuario: {data.get('user', {}).get('email')}")
            print(f"   Rol: {data.get('user', {}).get('role')}")
        else:
            print(f"   ❌ Error: {response.json().get('error', 'Error desconocido')}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Error: No se puede conectar al servidor.")
        print("   Asegúrate de que el servidor esté corriendo (python run.py)")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # 2. Ver sesión
    print("\n2️⃣  Ver sesión actual...")
    try:
        response = session.get(f"{BASE_URL}/auth/session", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Sesión activa:")
            print(f"   - Usuario ID: {data.get('user_id')}")
            print(f"   - Email: {data.get('email')}")
            print(f"   - Rol: {data.get('role')}")
            print(f"   - Autenticado: {data.get('is_authenticated')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Listar proyectos
    print("\n3️⃣  Listar proyectos configurados...")
    try:
        response = session.get(f"{BASE_URL}/api/projects/list", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            print(f"   ✅ Proyectos encontrados: {len(projects)}")
            for project in projects[:5]:  # Mostrar máximo 5
                print(f"   - {project.get('project_key')} ({project.get('jira_base_url')})")
            if len(projects) > 5:
                print(f"   ... y {len(projects) - 5} más")
        else:
            print(f"   ⚠️  {response.json().get('error', 'No hay proyectos configurados')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Logout
    print("\n4️⃣  Logout...")
    try:
        response = session.post(f"{BASE_URL}/auth/logout", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Logout exitoso")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == '__main__':
    test_login()



