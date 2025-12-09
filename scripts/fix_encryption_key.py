"""
Script para verificar y corregir la ENCRYPTION_KEY
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key, find_dotenv

def validate_encryption_key(key: str) -> bool:
    """Valida si una key de Fernet es válida"""
    try:
        if not key:
            return False
        if isinstance(key, str):
            key = key.encode()
        fernet = Fernet(key)
        # Probar que funciona
        test_token = fernet.encrypt(b"test")
        fernet.decrypt(test_token)
        return True
    except Exception:
        return False

def generate_new_key() -> str:
    """Genera una nueva key de Fernet válida"""
    return Fernet.generate_key().decode('utf-8')

def fix_encryption_key():
    """Verifica y corrige la ENCRYPTION_KEY en .env"""
    print("=" * 60)
    print("🔧 VERIFICACIÓN Y CORRECCIÓN DE ENCRYPTION_KEY")
    print("=" * 60)
    
    # Cargar .env
    env_path = find_dotenv()
    if not env_path:
        env_path = BASE_DIR / '.env'
        if not env_path.exists():
            print("❌ Archivo .env no encontrado")
            print("   Ejecuta: python scripts/init_auth.py")
            return False
    
    load_dotenv(env_path)
    
    current_key = os.getenv('ENCRYPTION_KEY', '')
    
    print(f"\n📋 Verificando ENCRYPTION_KEY...")
    print(f"   Archivo: {env_path}")
    
    if not current_key:
        print("   ⚠️  ENCRYPTION_KEY no está configurada")
        generate_new = True
    elif not validate_encryption_key(current_key):
        print(f"   ❌ ENCRYPTION_KEY inválida: {current_key[:20]}...")
        print("   ⚠️  La key actual no es válida para Fernet")
        generate_new = True
    else:
        print("   ✅ ENCRYPTION_KEY es válida")
        print(f"   Key: {current_key[:20]}...")
        return True
    
    if generate_new:
        print("\n🔑 Generando nueva ENCRYPTION_KEY...")
        new_key = generate_new_key()
        
        print(f"\n⚠️  ADVERTENCIA IMPORTANTE:")
        print("   Si ya tienes datos encriptados en la base de datos con la key anterior,")
        print("   NO podrás desencriptarlos con la nueva key.")
        print("   Esto afecta:")
        print("   - Tokens de Jira encriptados")
        print("   - Cualquier dato encriptado previamente")
        print("\n   Opciones:")
        print("   1. Si NO tienes datos importantes encriptados: Continuar (recomendado)")
        print("   2. Si SÍ tienes datos importantes: Cancelar y restaurar la key anterior")
        
        response = input("\n¿Deseas continuar y generar una nueva key? (s/n): ").strip().lower()
        
        if response != 's':
            print("\n❌ Operación cancelada")
            return False
        
        # Actualizar .env
        print(f"\n💾 Actualizando .env con nueva ENCRYPTION_KEY...")
        
        # Leer el archivo completo
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Buscar y reemplazar ENCRYPTION_KEY
        updated = False
        with open(env_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip().startswith('ENCRYPTION_KEY='):
                    f.write(f'ENCRYPTION_KEY={new_key}\n')
                    updated = True
                else:
                    f.write(line)
            
            # Si no existía, agregarla
            if not updated:
                f.write(f'\nENCRYPTION_KEY={new_key}\n')
        
        print(f"   ✅ ENCRYPTION_KEY actualizada")
        print(f"   Nueva key: {new_key[:20]}...")
        print(f"\n⚠️  IMPORTANTE: Si tenías tokens de Jira configurados, necesitarás")
        print("   reconfigurarlos porque la key anterior no puede desencriptarlos.")
        
        return True
    
    return False

if __name__ == '__main__':
    try:
        success = fix_encryption_key()
        if success:
            print("\n" + "=" * 60)
            print("✅ VERIFICACIÓN COMPLETADA")
            print("=" * 60)
            print("\n📋 Próximos pasos:")
            print("1. Reinicia el servidor Flask")
            print("2. Si tenías tokens de Jira configurados, reconfigúralos")
            print("=" * 60)
        else:
            print("\n❌ No se pudo corregir la ENCRYPTION_KEY")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



