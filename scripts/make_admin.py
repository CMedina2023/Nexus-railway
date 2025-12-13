#!/usr/bin/env python
"""
Script para convertir un usuario en administrador
Uso: python scripts/make_admin.py <email>
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import get_db
from app.database.repositories.user_repository import UserRepository
from app.models.user import User


def make_admin(email: str):
    """
    Convierte un usuario en administrador
    
    Args:
        email: Email del usuario a convertir
    """
    user_repo = UserRepository()  # No necesita argumentos, usa get_db() internamente
    
    # Buscar usuario por email
    user = user_repo.get_by_email(email)
    
    if not user:
        print(f"❌ Error: No se encontró usuario con email: {email}")
        print("\n📋 Usuarios disponibles:")
        list_users()
        sys.exit(1)
    
    if user.role == 'admin':
        print(f"✅ El usuario {email} ya es administrador")
        return
    
    # Actualizar rol
    user.role = 'admin'
    user_repo.update(user)
    
    print(f"✅ Usuario {email} convertido a administrador exitosamente")


def list_users():
    """Lista todos los usuarios en la base de datos"""
    db = get_db()
    
    # Obtener todos los usuarios directamente desde la BD usando get_cursor()
    with db.get_cursor() as cursor:
        cursor.execute("SELECT id, email, role, active, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
    
    if not users:
        print("   No hay usuarios registrados")
        return
    
    print("\n   Email                      | Rol       | Activo | Creado")
    print("   " + "-" * 65)
    for user_row in users:
        # Acceder a los campos (funciona tanto con dict como con sqlite3.Row)
        email = user_row['email']
        role = user_row['role']
        active = "Sí" if user_row['active'] else "No"
        created_at = user_row['created_at'][:10] if user_row['created_at'] else "N/A"
        
        # Formatear email (truncar si es muy largo)
        email_display = email[:25] + "..." if len(email) > 28 else email
        print(f"   {email_display:<28} | {role:<9} | {active:<6} | {created_at}")


def main():
    if len(sys.argv) < 2:
        print("📝 Script para convertir un usuario en administrador")
        print("\nUso:")
        print("  python scripts/make_admin.py <email>")
        print("\nEjemplo:")
        print("  python scripts/make_admin.py admin@example.com")
        print("\nPara listar usuarios:")
        print("  python scripts/make_admin.py --list")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        list_users()
        sys.exit(0)
    
    email = sys.argv[1].strip()
    
    if not email or '@' not in email:
        print("❌ Error: Debes proporcionar un email válido")
        sys.exit(1)
    
    try:
        make_admin(email)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


