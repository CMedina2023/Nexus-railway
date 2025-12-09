#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependencias de Python
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Playwright y sus dependencias
playwright install chromium
playwright install-deps chromium

# Crear directorios necesarios
mkdir -p temp_uploads
mkdir -p sessions
mkdir -p backups

# Inicializar la base de datos
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
    raise
"

echo "Build completado exitosamente"

