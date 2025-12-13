#!/usr/bin/env python3
"""
Wrapper para iniciar Gunicorn en Railway
Lee el puerto de la variable PORT y ejecuta Gunicorn
"""
import os
import sys
import warnings

# Silenciar advertencias de GLib en Windows
os.environ['G_MESSAGES_DEBUG'] = ''
warnings.filterwarnings('ignore', category=UserWarning, module='weasyprint')

# Obtener el puerto de la variable de entorno
port = os.getenv('PORT', '8000')

# Configuración de Gunicorn
gunicorn_config = [
    'gunicorn',
    '-w', '2',  # 2 workers
    '-k', 'eventlet',  # worker class eventlet (async)
    '--timeout', '300',  # timeout de 5 minutos
    '--graceful-timeout', '30',  # graceful timeout de 30 segundos
    '-b', f'0.0.0.0:{port}',  # bind a todas las interfaces en el puerto de Railway
    'run:app'  # módulo:aplicación
]

# Ejecutar Gunicorn
os.execvp('gunicorn', gunicorn_config)
