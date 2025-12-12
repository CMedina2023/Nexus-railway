#!/usr/bin/env bash
# exit on error
set -o errexit

# (Playwright eliminado ya que se usa WeasyPrint)

echo "==> Creando directorios necesarios..."
mkdir -p temp_uploads
mkdir -p sessions
mkdir -p backups

echo "==> Inicializando base de datos..."
python -c "
from app.database import init_db
from app.core.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info('Inicializando base de datos...')
    init_db()
    logger.info('Base de datos inicializada correctamente')
except Exception as e:
    logger.error(f'Error inicializando base de datos: {e}')
    # No raise para no detener el build completo
    logger.warning('Continuando a pesar del error...')
"

echo "==> Build completado exitosamente"
