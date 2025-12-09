#!/usr/bin/env python
"""
Script para ver datos de la base de datos
Uso: python scripts/view_db.py [--table <table_name>]
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import get_db


def format_datetime(dt_str: str) -> str:
    """Formatea una fecha ISO a formato legible"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str


def view_table(table_name: str):
    """Muestra los datos de una tabla específica"""
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener todas las filas
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"   La tabla '{table_name}' está vacía")
            return
        
        # Obtener nombres de columnas
        columns = [description[0] for description in cursor.description]
        
        # Mostrar encabezado
        print(f"\n📊 Tabla: {table_name}")
        print(f"   Total de registros: {len(rows)}")
        print("   " + "=" * 80)
        
        # Mostrar columnas
        print(f"   Columnas: {', '.join(columns)}")
        print("   " + "-" * 80)
        
        # Mostrar datos
        for i, row in enumerate(rows, 1):
            print(f"\n   Registro #{i}:")
            for col in columns:
                value = row[col]
                
                # Formatear valores especiales
                if col.endswith('_at') or col == 'last_login' or col == 'locked_until':
                    value = format_datetime(value) if value else "N/A"
                elif col == 'active' or col == 'use_personal':
                    value = "Sí" if value else "No"
                elif col == 'password_hash' or col == 'shared_token' or col == 'personal_token':
                    value = "***HIDDEN***" if value else "N/A"
                elif value is None:
                    value = "NULL"
                
                # Truncar valores largos
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                
                print(f"      {col:<25}: {value}")
    
    except sqlite3.OperationalError as e:
        print(f"❌ Error: La tabla '{table_name}' no existe")
        print(f"   {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def list_tables():
    """Lista todas las tablas en la base de datos"""
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    conn.close()
    
    if not tables:
        print("   No hay tablas en la base de datos")
        return []
    
    table_names = [table[0] for table in tables]
    return table_names


def view_all():
    """Muestra un resumen de todas las tablas"""
    print("\n" + "=" * 80)
    print("📊 VISUALIZACIÓN DE BASE DE DATOS - NEXUS AI")
    print("=" * 80)
    
    tables = list_tables()
    
    if not tables:
        print("\n   No hay tablas en la base de datos")
        return
    
    print(f"\n📋 Tablas encontradas: {len(tables)}")
    for table in tables:
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"   - {table}: {count} registros")
    
    # Mostrar resumen de usuarios
    if 'users' in tables:
        print("\n" + "-" * 80)
        print("👥 RESUMEN DE USUARIOS")
        print("-" * 80)
        
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        role_counts = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE active = 0")
        inactive_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n   Total usuarios: {sum(r[1] for r in role_counts)}")
        print(f"   Activos: {active_count}")
        print(f"   Inactivos: {inactive_count}")
        print(f"\n   Por rol:")
        for role, count in role_counts:
            print(f"      - {role}: {count}")
    
    print("\n💡 Usa --table <nombre> para ver detalles de una tabla específica")
    print("   Ejemplo: python scripts/view_db.py --table users")


def main():
    import sqlite3
    
    if len(sys.argv) > 1 and sys.argv[1] == '--table':
        if len(sys.argv) < 3:
            print("❌ Error: Debes especificar el nombre de la tabla")
            print("\nTablas disponibles:")
            for table in list_tables():
                print(f"   - {table}")
            sys.exit(1)
        
        table_name = sys.argv[2]
        view_table(table_name)
    else:
        view_all()


if __name__ == '__main__':
    main()


