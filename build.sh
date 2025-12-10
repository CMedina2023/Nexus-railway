#!/usr/bin/env bash
# exit on error
set -o errexit

echo "==> Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Instalando Playwright (solo navegador)..."
# Instalar solo el navegador sin dependencias del sistema
# Esto evita el error de permisos en Render
PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium --no-shell

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

