"""
Script para inicializar las tablas del dashboard con permisos por rol

Este script crea las tablas necesarias para el sistema de dashboard:
- user_stories: Historias de usuario generadas
- test_cases: Casos de prueba generados
- jira_reports: Reportes creados en Jira
- bulk_uploads: Cargas masivas realizadas

Uso:
    python scripts/init_dashboard_tables.py
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Inicializa las tablas del dashboard"""
    try:
        logger.info("=" * 60)
        logger.info("Inicializando tablas del dashboard...")
        logger.info("=" * 60)
        
        # Inicializar base de datos (crea tablas si no existen)
        init_db()
        
        logger.info("")
        logger.info("✅ Tablas del dashboard inicializadas correctamente")
        logger.info("")
        logger.info("Tablas creadas:")
        logger.info("  - user_stories: Historias de usuario generadas")
        logger.info("  - test_cases: Casos de prueba generados")
        logger.info("  - jira_reports: Reportes creados en Jira")
        logger.info("  - bulk_uploads: Cargas masivas realizadas")
        logger.info("")
        logger.info("Índices creados para optimizar consultas:")
        logger.info("  - idx_user_stories_user")
        logger.info("  - idx_user_stories_project")
        logger.info("  - idx_test_cases_user")
        logger.info("  - idx_test_cases_project")
        logger.info("  - idx_jira_reports_user")
        logger.info("  - idx_jira_reports_project")
        logger.info("  - idx_bulk_uploads_user")
        logger.info("  - idx_bulk_uploads_project")
        logger.info("")
        logger.info("=" * 60)
        logger.info("Sistema de permisos por rol listo para usar")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error al inicializar tablas: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())













