#!/usr/bin/env bash
# exit on error
set -o errexit

echo "==> Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Instalando Playwright con dependencias del sistema..."
# Instalar chromium con todas las dependencias necesarias
playwright install --with-deps chromium

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
    raise
"

echo "==> Build completado exitosamente"

