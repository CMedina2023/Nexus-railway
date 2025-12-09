"""
Punto de entrada principal de la aplicación Flask
"""
import sys
import pathlib

# Añadir el directorio raíz al path para importaciones correctas
BASE_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from app.core.app import app
from app.core.config import Config

if __name__ == '__main__':
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=True
    )

