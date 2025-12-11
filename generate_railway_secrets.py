#!/usr/bin/env python3
"""
Script para generar las claves necesarias para Railway
Ejecutar: python generate_railway_secrets.py
"""
import secrets
from cryptography.fernet import Fernet

def generate_secret_key(length=32):
    """Genera una SECRET_KEY segura"""
    return secrets.token_hex(length)

def generate_encryption_key():
    """Genera una ENCRYPTION_KEY (Fernet) segura"""
    return Fernet.generate_key().decode()

def main():
    print("=" * 70)
    print("🔐 GENERADOR DE CLAVES PARA RAILWAY DEPLOY")
    print("=" * 70)
    print()
    
    # Generar SECRET_KEY
    secret_key = generate_secret_key()
    print("📌 SECRET_KEY (Flask session):")
    print(f"   {secret_key}")
    print()
    
    # Generar ENCRYPTION_KEY
    encryption_key = generate_encryption_key()
    print("🔑 ENCRYPTION_KEY (Fernet para tokens):")
    print(f"   {encryption_key}")
    print()
    
    print("=" * 70)
    print("📋 INSTRUCCIONES:")
    print("=" * 70)
    print()
    print("1. Ve a tu proyecto en Railway")
    print("2. Selecciona tu servicio web")
    print("3. Ve a 'Variables'")
    print("4. Agrega estas variables:")
    print()
    print(f"   SECRET_KEY={secret_key}")
    print(f"   ENCRYPTION_KEY={encryption_key}")
    print()
    print("5. También necesitas agregar:")
    print("   GOOGLE_API_KEY=tu_google_api_key_aqui")
    print()
    print("6. Opcionalmente (si usas Jira):")
    print("   JIRA_BASE_URL=https://tu-empresa.atlassian.net")
    print("   JIRA_EMAIL=tu-email@empresa.com")
    print("   JIRA_API_TOKEN=tu_jira_token")
    print()
    print("=" * 70)
    print("✅ ¡Listo! Copia y pega estas claves en Railway")
    print("=" * 70)

if __name__ == '__main__':
    main()
