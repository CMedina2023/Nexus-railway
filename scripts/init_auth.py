"""
Script de inicialización del sistema de autenticación
Ejecuta este script para configurar el sistema por primera vez
"""
import os
import sys
import secrets
from pathlib import Path

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from cryptography.fernet import Fernet
from app.database import init_db
from app.auth.user_service import UserService


def generate_secret_key():
    """Genera una SECRET_KEY aleatoria"""
    return secrets.token_hex(32)


def generate_encryption_key():
    """Genera una ENCRYPTION_KEY para Fernet"""
    return Fernet.generate_key().decode('utf-8')


def check_env_file():
    """Verifica y actualiza el archivo .env con las keys necesarias"""
    env_path = BASE_DIR / '.env'
    
    # Leer .env existente si existe
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Generar keys si no existen
    if 'SECRET_KEY' not in env_vars or not env_vars['SECRET_KEY']:
        secret_key = generate_secret_key()
        env_vars['SECRET_KEY'] = secret_key
        print(f"✅ Generada SECRET_KEY: {secret_key[:20]}...")
    
    if 'ENCRYPTION_KEY' not in env_vars or not env_vars['ENCRYPTION_KEY']:
        encryption_key = generate_encryption_key()
        env_vars['ENCRYPTION_KEY'] = encryption_key
        print(f"✅ Generada ENCRYPTION_KEY: {encryption_key[:20]}...")
    
    # Agregar otras variables necesarias con valores por defecto
    defaults = {
        'DATABASE_URL': 'sqlite:///nexus_ai.db',
        'BCRYPT_ROUNDS': '12',
        'SESSION_LIFETIME_HOURS': '8',
        'MAX_LOGIN_ATTEMPTS': '5',
        'LOCKOUT_DURATION_SECONDS': '900',
        'SESSION_COOKIE_SECURE': 'False'
    }
    
    for key, default_value in defaults.items():
        if key not in env_vars:
            env_vars[key] = default_value
    
    # Escribir .env actualizado
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write("# Configuración de Nexus AI\n")
        f.write("# Variables de autenticación y seguridad\n\n")
        f.write(f"SECRET_KEY={env_vars['SECRET_KEY']}\n")
        f.write(f"ENCRYPTION_KEY={env_vars['ENCRYPTION_KEY']}\n\n")
        f.write("# Base de datos\n")
        f.write(f"DATABASE_URL={env_vars['DATABASE_URL']}\n\n")
        f.write("# Seguridad\n")
        f.write(f"BCRYPT_ROUNDS={env_vars['BCRYPT_ROUNDS']}\n")
        f.write(f"SESSION_LIFETIME_HOURS={env_vars['SESSION_LIFETIME_HOURS']}\n")
        f.write(f"MAX_LOGIN_ATTEMPTS={env_vars['MAX_LOGIN_ATTEMPTS']}\n")
        f.write(f"LOCKOUT_DURATION_SECONDS={env_vars['LOCKOUT_DURATION_SECONDS']}\n")
        f.write(f"SESSION_COOKIE_SECURE={env_vars['SESSION_COOKIE_SECURE']}\n\n")
        
        # Mantener otras variables existentes que no sean de seguridad
        f.write("# Otras configuraciones (mantener existentes)\n")
        for key, value in env_vars.items():
            if key not in ['SECRET_KEY', 'ENCRYPTION_KEY', 'DATABASE_URL', 
                          'BCRYPT_ROUNDS', 'SESSION_LIFETIME_HOURS', 
                          'MAX_LOGIN_ATTEMPTS', 'LOCKOUT_DURATION_SECONDS',
                          'SESSION_COOKIE_SECURE']:
                f.write(f"{key}={value}\n")
    
    print(f"✅ Archivo .env actualizado en: {env_path}")
    return env_vars


def init_database():
    """Inicializa la base de datos"""
    try:
        print("\n📦 Inicializando base de datos...")
        init_db()
        print("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        return False


def create_admin_user():
    """Crea un usuario administrador"""
    print("\n👤 Creando usuario administrador...")
    print("Por favor, ingresa los datos del administrador:")
    
    email = input("Email: ").strip()
    if not email:
        print("❌ Email requerido")
        return False
    
    password = input("Contraseña (mínimo 8 caracteres, mayúsculas, minúsculas, números): ").strip()
    if not password:
        print("❌ Contraseña requerida")
        return False
    
    try:
        user_service = UserService()
        admin = user_service.create_user(
            email=email,
            password=password,
            role='admin',
            created_by='system'
        )
        print(f"✅ Usuario admin creado exitosamente:")
        print(f"   - Email: {admin.email}")
        print(f"   - Rol: {admin.role}")
        print(f"   - ID: {admin.id}")
        return True
    except Exception as e:
        print(f"❌ Error al crear usuario admin: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 INICIALIZACIÓN DEL SISTEMA DE AUTENTICACIÓN")
    print("=" * 60)
    
    # Paso 1: Verificar/crear .env
    print("\n📝 Paso 1: Configurando variables de entorno...")
    env_vars = check_env_file()
    
    # Paso 2: Inicializar base de datos
    print("\n📦 Paso 2: Inicializando base de datos...")
    if not init_database():
        print("\n❌ Error en la inicialización. Revisa los errores anteriores.")
        return
    
    # Paso 3: Crear usuario admin
    print("\n👤 Paso 3: Crear usuario administrador...")
    create_admin = input("¿Deseas crear un usuario administrador ahora? (s/n): ").strip().lower()
    
    if create_admin == 's':
        create_admin_user()
    else:
        print("⚠️  Puedes crear un admin más tarde ejecutando:")
        print("   python -c \"from app.auth.user_service import UserService; "
              "UserService().create_user('admin@example.com', 'Password123!', 'admin')\"")
    
    print("\n" + "=" * 60)
    print("✅ INICIALIZACIÓN COMPLETADA")
    print("=" * 60)
    print("\n📋 Próximos pasos:")
    print("1. Inicia el servidor: python run.py")
    print("2. Accede a: http://localhost:5000/auth/login")
    print("3. Inicia sesión con el usuario admin creado")
    print("\n💡 Tip: Puedes probar los endpoints con:")
    print("   - Postman")
    print("   - curl")
    print("   - Python requests")
    print("=" * 60)


if __name__ == '__main__':
    main()



