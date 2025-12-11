"""
Script para verificar la conexión a la base de datos
Prueba tanto SQLite como PostgreSQL
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.db import get_db
from app.core.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        logger.info(f"Probando conexión a: {Config.DATABASE_URL}")
        
        db = get_db()
        
        logger.info(f"Tipo de base de datos: {'PostgreSQL' if db.is_postgres else 'SQLite'}")
        logger.info(f"Ruta/URL: {db.db_url}")
        
        # Probar una consulta simple
        with db.get_cursor() as cursor:
            if db.is_sqlite:
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()
                logger.info(f"SQLite version: {version[0]}")
            else:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                logger.info(f"PostgreSQL version: {version[0]}")
            
            # Verificar que las tablas existen
            if db.is_sqlite:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            else:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            
            tables = cursor.fetchall()
            logger.info(f"Tablas encontradas: {len(tables)}")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        logger.info("✅ Conexión exitosa!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al conectar: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

