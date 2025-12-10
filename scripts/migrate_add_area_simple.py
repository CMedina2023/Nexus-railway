"""
Script de migración simple para agregar campo 'area' a las tablas user_stories y test_cases
"""
import sqlite3
import os

# Ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'nexus_ai.db')

def migrate_add_area_field():
    """Agrega el campo 'area' a las tablas user_stories y test_cases si no existe"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Base de datos no encontrada en {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔄 Iniciando migración: Agregar campo 'area'...")
        print(f"📁 Base de datos: {DB_PATH}")
        
        # Verificar si el campo 'area' ya existe en user_stories
        cursor.execute("PRAGMA table_info(user_stories)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'area' not in columns:
            print("  ➕ Agregando campo 'area' a tabla 'user_stories'...")
            cursor.execute("ALTER TABLE user_stories ADD COLUMN area TEXT")
            print("  ✅ Campo 'area' agregado a 'user_stories'")
        else:
            print("  ℹ️  Campo 'area' ya existe en 'user_stories'")
        
        # Verificar si el campo 'area' ya existe en test_cases
        cursor.execute("PRAGMA table_info(test_cases)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'area' not in columns:
            print("  ➕ Agregando campo 'area' a tabla 'test_cases'...")
            cursor.execute("ALTER TABLE test_cases ADD COLUMN area TEXT")
            print("  ✅ Campo 'area' agregado a 'test_cases'")
        else:
            print("  ℹ️  Campo 'area' ya existe en 'test_cases'")
        
        conn.commit()
        print("\n✅ Migración completada exitosamente")
        print("🔄 Reinicia el servidor para aplicar los cambios")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"\n❌ Error en la migración: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_add_area_field()







