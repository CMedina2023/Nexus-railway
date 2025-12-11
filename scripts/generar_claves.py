"""
Script para generar claves secretas para Nexus AI
Uso: python scripts/generar_claves.py
"""
import secrets
from cryptography.fernet import Fernet

def main():
    print("=" * 70)
    print(" " * 15 + "GENERADOR DE CLAVES SECRETAS - NEXUS AI")
    print("=" * 70)
    print()
    
    # Generar SECRET_KEY
    secret_key = secrets.token_hex(32)
    print("🔑 SECRET_KEY (para Flask):")
    print("-" * 70)
    print(secret_key)
    print()
    
    # Generar ENCRYPTION_KEY
    encryption_key = Fernet.generate_key().decode()
    print("🔐 ENCRYPTION_KEY (para encriptar tokens):")
    print("-" * 70)
    print(encryption_key)
    print()
    
    print("=" * 70)
    print("📋 INSTRUCCIONES PARA RENDER:")
    print("=" * 70)
    print()
    print("1. Ve a Render.com → Tu Web Service → Environment Variables")
    print()
    print("2. Agrega estas variables de entorno:")
    print()
    print("   Variable: SECRET_KEY")
    print(f"   Value: {secret_key}")
    print()
    print("   Variable: ENCRYPTION_KEY")
    print(f"   Value: {encryption_key}")
    print()
    print("=" * 70)
    print("⚠️  IMPORTANTE - SEGURIDAD:")
    print("=" * 70)
    print("• Guarda estas claves en un lugar SEGURO (gestor de contraseñas)")
    print("• NO las compartas ni las subas a GitHub")
    print("• NO las incluyas en el código fuente")
    print("• Genera claves DIFERENTES para desarrollo y producción")
    print("=" * 70)
    print()
    
    # Guardar en archivo (opcional)
    respuesta = input("¿Deseas guardar estas claves en un archivo temporal? (s/n): ")
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        with open('claves_temporales.txt', 'w') as f:
            f.write("CLAVES SECRETAS - NEXUS AI\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write(f"ENCRYPTION_KEY={encryption_key}\n")
            f.write("\n" + "=" * 70 + "\n")
            f.write("⚠️  ELIMINA ESTE ARCHIVO DESPUÉS DE COPIAR LAS CLAVES\n")
            f.write("⚠️  NO SUBAS ESTE ARCHIVO A GITHUB\n")
        
        print()
        print("✅ Claves guardadas en: claves_temporales.txt")
        print("⚠️  RECUERDA: Elimina este archivo después de copiar las claves")
    
    print()
    print("✅ ¡Listo! Usa estas claves en Render")
    print()

if __name__ == '__main__':
    main()







