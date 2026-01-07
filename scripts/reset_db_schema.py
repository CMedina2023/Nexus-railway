"""
Script de utilidad para reiniciar la base de datos (Eliminar todo y recrear).
Útil para demos o para limpiar el entorno de desarrollo.
"""
import sys
import os
import pathlib
import logging

# Configurar path
BASE_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import Config
from app.database.db import get_db, init_db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_db():
    print("⚠️  ATENCION: ESTO ELIMINARA TODOS LOS DATOS ⚠️")
    confirm = input("¿Estás seguro de que quieres reiniciar la base de datos? (escribe 'SI' para confirmar): ")
    
    if confirm != 'SI':
        print("Operación cancelada.")
        return

    db = get_db()
    
    try:
        if db.is_sqlite:
            # Para SQLite, es más fácil borrar el archivo, pero para mantener la conexión,
            # eliminamos tablas
            logger.info("Eliminando tablas en SQLite...")
            with db.get_connection() as conn:
                cursor = conn.cursor()
                # Desactivar constraints
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                # Obtener lista de tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    if table[0] != 'sqlite_sequence':
                        logger.info(f"Eliminando {table[0]}...")
                        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                
        elif db.is_postgres:
            logger.info("Eliminando esquema public en PostgreSQL...")
            with db.engine.connect() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
                conn.commit()
        
        logger.info("Tablas eliminadas.")
        
        # Regenerar
        logger.info("Regenerando esquema de base de datos...")
        init_db()
        logger.info("✅ Base de datos reiniciada exitosamente con el esquema actual.")
        
    except Exception as e:
        logger.error(f"Error al reiniciar DB: {e}")
        raise

if __name__ == '__main__':
    reset_db()
