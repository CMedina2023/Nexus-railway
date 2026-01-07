"""
Script para volver atrás (Rollback) todos los cambios de base de datos de los generadores.
Ejecuta los scripts SQL de rollback en el orden correcto para limpiar la base de datos de las nuevas estructuras.
"""
import sys
import pathlib
import logging

# Configurar path
BASE_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import Config
from app.database.db import get_db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rollback_migrations():
    print("⚠️  ATENCIÓN: ESTE SCRIPT ELIMINARÁ TABLAS Y COLUMNAS DE LA SUITE DE GENERADORES ⚠️")
    print("Se revertirán los cambios de: Workflows, Traceability, Knowledge Base, Epics/Features")
    confirm = input("¿Confirmas el rollback? (escribe 'SI' para confirmar): ")
    
    if confirm != 'SI':
        print("Operación cancelada.")
        return

    db = get_db()
    migrations_dir = BASE_DIR / 'migrations'
    
    # Orden de ejecución de rollbacks (Inverso a la creación / dependencias)
    rollback_files = [
        'rollback_workflow_tables.sql',        # Depende de nada (usuario)
        'rollback_test_case_traceability.sql', # Limpia columnas extra
        'rollback_traceability_tables.sql',    # Depende de requirements
        'rollback_knowledge_base_tables.sql',  # Standalone
        'rollback_epic_feature_tables.sql',    # Standalone
        # rollback_user_story_hierarchy no siempre es destructivo o necesario si se borran las tablas
    ]

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for script_name in rollback_files:
                script_path = migrations_dir / script_name
                if not script_path.exists():
                    logger.warning(f"Archivo no encontrado: {script_name}, saltando...")
                    continue
                
                logger.info(f"Ejecutando rollback: {script_name}...")
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Ejecutar script (separando por ; si es necesario, pero cursor.executescript es mejor en sqlite)
                if db.is_sqlite:
                    cursor.executescript(sql_content)
                else:
                    # Postgres no tiene executescript, ejecutamos comando por comando simple o todo el bloque
                    # Aquí asumimos que el SQL es compatible para ejecución directa
                    cursor.execute(sql_content)
            
            conn.commit()
            logger.info("✅ Rollback completado exitosamente.")
            
    except Exception as e:
        logger.error(f"Error durante el rollback: {e}")
        # En caso de error, intentamos rollback de la transacción si está abierta
        try:
            conn.rollback()
        except:
            pass
        raise

if __name__ == '__main__':
    rollback_migrations()
