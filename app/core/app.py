from flask import Flask, render_template, request, jsonify, send_file, redirect, Response
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import io
import csv
import zipfile
import logging
import base64
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from typing import Dict
import time
from playwright.sync_api import sync_playwright

# Imports de la estructura modular
from app.core.config import Config
from app.backend import story_backend, matrix_backend, jira_backend
from app.backend.jira_backend import JiraClient
from app.backend.agent_manager import simple_agent_processing
from app.utils.file_utils import extract_text_from_file
from app.utils.matrix_utils import extract_matrix_data
from app.utils.decorators import validate_file_upload, handle_errors, validate_required_params

# Imports de autenticación
from app.auth.routes import auth_bp, init_rate_limiter
from app.auth.decorators import login_required, get_current_user_id
from app.auth.session_service import SessionService
from app.auth.user_service import UserService
from app.services.jira_token_manager import JiraTokenManager
from app.backend.jira.connection import JiraConnection
from app.backend.jira.project_service import ProjectService
from app.database import init_db

# Imports de repositorios para historial de actividades
from app.database.repositories.user_story_repository import UserStoryRepository
from app.database.repositories.test_case_repository import TestCaseRepository
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.database.repositories.bulk_upload_repository import BulkUploadRepository
from app.models.user_story import UserStory
from app.models.test_case import TestCase
from app.models.jira_report import JiraReport
from app.models.bulk_upload import BulkUpload

load_dotenv()

# Obtener la ruta base del proyecto (dos niveles arriba de app/core/)
import pathlib
BASE_DIR = pathlib.Path(__file__).parent.parent.parent

app = Flask(__name__, 
            template_folder=str(BASE_DIR / 'templates'),
            static_folder=str(BASE_DIR / 'static'))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN MEJORADA PARA PRODUCCIÓN
# ============================================================================

# Configuración del directorio temporal para las subidas (relativo al directorio raíz del proyecto)
UPLOAD_FOLDER = str(BASE_DIR / Config.UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.get_max_content_length()

# Asegurar que el directorio de subidas existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD Y AUTENTICACIÓN
# ============================================================================

# Secret key para sesiones y CSRF (requerido para Flask-WTF y Flask-Session)
if not Config.SECRET_KEY:
    logger.warning(
        "SECRET_KEY no está configurada. Genera una con: "
        "python -c \"import secrets; print(secrets.token_hex(32))\""
    )
    # Generar una key temporal para desarrollo (NUNCA usar en producción)
    import secrets
    Config.SECRET_KEY = secrets.token_hex(32)
    logger.warning("Usando SECRET_KEY temporal generada. Configura SECRET_KEY en .env para producción")

app.config['SECRET_KEY'] = Config.SECRET_KEY

# Configuración de sesiones seguras
app.config['SESSION_TYPE'] = 'filesystem'  # Usar sistema de archivos para sesiones
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Firmar cookies de sesión
app.config['SESSION_KEY_PREFIX'] = 'nexus_ai:'
app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE  # Solo HTTPS en producción
app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=Config.SESSION_LIFETIME_HOURS)

# Inicializar Flask-Session
session_store_path = str(BASE_DIR / 'sessions')
if not os.path.exists(session_store_path):
    os.makedirs(session_store_path)
app.config['SESSION_FILE_DIR'] = session_store_path

Session(app)

# Inicializar protección CSRF
csrf = CSRFProtect(app)


# Hacer disponible csrf_token en todos los templates
@app.context_processor
def inject_csrf_token():
    """Inyecta la función csrf_token en todos los templates"""
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=lambda: generate_csrf())

# Inicializar base de datos
try:
    init_db()
    logger.info("Base de datos inicializada correctamente")
except Exception as e:
    logger.error(f"Error al inicializar base de datos: {e}")

# Inicializar rate limiter
init_rate_limiter(app)

# Registrar Blueprints de autenticación
app.register_blueprint(auth_bp)
from app.auth.project_config_routes import project_config_bp
app.register_blueprint(project_config_bp)
from app.auth.metrics_routes import metrics_bp
app.register_blueprint(metrics_bp)
from app.auth.personal_token_routes import personal_token_bp
app.register_blueprint(personal_token_bp)
from app.auth.admin_routes import admin_bp
app.register_blueprint(admin_bp)
from app.auth.profile_routes import profile_bp
app.register_blueprint(profile_bp)
from app.auth.dashboard_routes import dashboard_bp
app.register_blueprint(dashboard_bp)
logger.info("Blueprints de autenticación registrados")


# ============================================================================
# MANEJO GLOBAL DE ERRORES PARA DEVOLVER JSON
# ============================================================================

@app.errorhandler(403)
def forbidden(error):
    """
    Manejador de error 403 (Forbidden)
    Retorna página de error o JSON según el tipo de request
    """
    if request.path.startswith('/api/'):
        return jsonify({
            "error": "No autorizado",
            "status": "forbidden"
        }), 403
    # Para páginas, retornar HTML simple
    return f"""
    <html>
        <head><title>403 - Prohibido</title></head>
        <body>
            <h1>403 - Acceso Prohibido</h1>
            <p>No tienes permisos para acceder a esta página.</p>
            <a href="/">Volver al inicio</a>
        </body>
    </html>
    """, 403

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint no encontrado"}), 404
    # ✅ Respuesta simple sin template
    return f"""
    <html>
        <head><title>404 - Página no encontrada</title></head>
        <body>
            <h1>404 - Página no encontrada</h1>
            <p>La página que buscas no existe.</p>
            <a href="/">Volver al inicio</a>
        </body>
    </html>
    """, 404


@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Error interno del servidor"}), 500
    return f"""
    <html>
        <head><title>500 - Error interno</title></head>
        <body>
            <h1>500 - Error interno del servidor</h1>
            <p>Ha ocurrido un error interno.</p>
            <a href="/">Volver al inicio</a>
        </body>
    </html>
    """, 500


@app.errorhandler(Exception)
def handle_exception(e):
    # No manejar excepciones HTTP de Werkzeug (403, 404, etc.) - ya tienen sus manejadores
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        # Dejar que Flask maneje las excepciones HTTP normalmente
        raise e
    
    logger.error(f"Error no manejado: {e}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({"error": "Error interno del servidor"}), 500
    return f"""
    <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error</h1>
            <p>Ha ocurrido un error inesperado.</p>
            <a href="/">Volver al inicio</a>
        </body>
    </html>
    """, 500


# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@app.route('/')
@login_required
def menu_principal():
    """
    Página principal del sistema (requiere autenticación)
    
    ✅ Protegida con @login_required
    ✅ Muestra información del usuario en el sidebar
    """
    from app.auth.session_service import SessionService
    
    # Obtener información del usuario actual
    user_info = {
        'email': SessionService.get_current_user_email(),
        'role': SessionService.get_current_user_role(),
        'user_id': SessionService.get_current_user_id()
    }
    
    return render_template('index.html', user_info=user_info)


@app.route('/infografia')
def infografia():
    return render_template('Infografia.html')




@app.route('/overview')
@login_required
def overview():
    """
    Redirige a la página de infografía (requiere autenticación)
    
    ✅ Protegida con @login_required
    """
    return redirect('/infografia')


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def analyze_document_content(document_text):
    """Analiza el contenido del documento para determinar qué se puede generar"""
    text_lower = document_text.lower()

    # Palabras clave para historias de usuario
    story_keywords = ['como', 'quiero', 'para', 'usuario', 'historia', 'requerimiento',
                      'funcionalidad', 'feature', 'user story', 'criterio de aceptación']

    # Palabras clave para matriz de pruebas
    matrix_keywords = ['prueba', 'test', 'caso', 'escenario', 'validación', 'verificación',
                       'matriz', 'matrix', 'test case', 'condición', 'resultado esperado']

    story_score = sum(1 for keyword in story_keywords if keyword in text_lower)
    matrix_score = sum(1 for keyword in matrix_keywords if keyword in text_lower)

    # Umbrales para determinar qué se puede generar
    can_generate_stories = story_score >= 2 or len(document_text) > 100
    can_generate_matrix = matrix_score >= 2 or len(document_text) > 100

    return {
        "can_generate_stories": can_generate_stories,
        "can_generate_matrix": can_generate_matrix,
        "story_keywords_found": story_score,
        "matrix_keywords_found": matrix_score,
        "document_length": len(document_text)
    }


def clean_temp_files(filepath):
    """Limpia archivos temporales de forma segura"""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Archivo temporal eliminado: {filepath}")
    except Exception as e:
        logger.warning(f"No se pudo eliminar archivo temporal {filepath}: {e}")


def clean_matrix_data(matrix_data):
    """Limpia y normaliza los datos de la matriz de pruebas"""
    cleaned_data = []

    if not matrix_data:
        return cleaned_data

    # Si es un string, intentar parsearlo como JSON
    if isinstance(matrix_data, str):
        try:
            matrix_data = json.loads(matrix_data)
        except json.JSONDecodeError:
            logger.error("Los datos de matriz son un string pero no es JSON válido")
            return cleaned_data

    # Si es un diccionario, buscar la lista de casos de prueba
    if isinstance(matrix_data, dict):
        # Buscar claves que contengan la lista de casos
        matrix_keys = ['matrix', 'test_cases', 'cases', 'test_cases_list', 'data']
        for key in matrix_keys:
            if key in matrix_data and isinstance(matrix_data[key], list):
                matrix_data = matrix_data[key]
                logger.info(f"Encontrados datos en clave: {key}")
                break
        else:
            # Si es un diccionario de caso individual, convertirlo a lista
            if any(k in matrix_data for k in ['id_caso_prueba', 'titulo_caso_prueba', 'Descripcion', 'id', 'title']):
                matrix_data = [matrix_data]
                logger.info("Convertido diccionario de caso individual a lista")
            else:
                # Buscar recursivamente en valores del diccionario
                for key, value in matrix_data.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        matrix_data = value
                        logger.info(f"Encontrados datos en clave recursiva: {key}")
                        break
                else:
                    logger.warning("No se pudo encontrar lista de casos en el diccionario")
                    return cleaned_data

    # Asegurarse de que es una lista
    if not isinstance(matrix_data, list):
        matrix_data = [matrix_data]

    for item in matrix_data:
        if isinstance(item, dict):
            # Limpiar y normalizar el item
            cleaned_item = {}
            for key, value in item.items():
                # Normalizar claves
                normalized_key = key.lower().replace(' ', '_').replace('-', '_')

                # Limpiar valores (especialmente arrays que deben ser strings)
                if isinstance(value, list):
                    if normalized_key in ['pasos', 'steps', 'resultado_esperado', 'expected_results']:
                        value = '\n'.join([f"{i + 1}. {step}" if normalized_key in ['pasos', 'steps'] else f"- {step}"
                                           for i, step in enumerate(value)])
                    else:
                        value = ', '.join(str(v) for v in value)
                elif value is None:
                    value = ""

                cleaned_item[normalized_key] = value

            # Asegurar campos mínimos
            if 'id_caso_prueba' not in cleaned_item:
                cleaned_item['id_caso_prueba'] = f"TC{len(cleaned_data) + 1:03d}"

            cleaned_data.append(cleaned_item)
        else:
            logger.warning(f"Elemento ignorado en clean_matrix_data: {type(item)} - {str(item)[:100]}")

    return cleaned_data


def generate_proper_csv(matrix_data):
    """Genera CSV correctamente formateado para casos de prueba"""

    if not matrix_data:
        return "id_caso_prueba,titulo_caso_prueba,Descripcion,Precondiciones\nTC001,No hay datos,No se generaron casos de prueba,\"\""

    # Definir el orden de columnas esperado
    expected_columns = [
        "id_caso_prueba", "titulo_caso_prueba", "Descripcion", "Precondiciones",
        "Tipo_de_prueba", "Nivel_de_prueba", "Tipo_de_ejecucion", "Pasos",
        "Resultado_esperado", "Categoria", "Ambiente", "Ciclo", "issuetype",
        "Prioridad", "historia_de_usuario"
    ]

    # Encontrar todas las claves presentes en los datos
    all_keys = set()
    for item in matrix_data:
        if isinstance(item, dict):
            all_keys.update(item.keys())

    # Ordenar las claves: primero las esperadas, luego las adicionales
    fieldnames = []
    for col in expected_columns:
        if col in all_keys:
            fieldnames.append(col)
            all_keys.remove(col)

    # Añadir las claves adicionales
    fieldnames.extend(sorted(all_keys))

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    # Escribir headers
    writer.writeheader()

    # Escribir datos
    for row in matrix_data:
        if isinstance(row, dict):
            # Asegurar que todas las claves estén presentes
            complete_row = {key: row.get(key, "") for key in fieldnames}
            writer.writerow(complete_row)

    return output.getvalue()


def clean_story_text(story_text):
    """Limpia el texto de la historia removiendo formato excesivo"""
    # Remover bloques de código ```
    story_text = story_text.replace('```json', '').replace('```', '')

    # Remover caracteres de escape excesivos
    story_text = story_text.replace('\\n', '\n').replace('\\"', '"')

    # Remover líneas de separación excesivas (sin usar re)
    story_text = story_text.replace('╔════════════════════════════════════════════════════════════════════════════════',
                                    '')
    story_text = story_text.replace('════════════════════════════════════════════════════════════════════════════════',
                                    '')
    # Remover JSON escapes
    story_text = story_text.replace('\"', '"')

    # Limpiar espacios y saltos de línea múltiples (usando replace en lugar de re)
    story_text = story_text.strip()
    while '\n\n\n' in story_text:
        story_text = story_text.replace('\n\n\n', '\n\n')

    return story_text


def split_story_text_into_individual_stories(story_text):
    """Divide un texto que contiene múltiples historias en historias individuales"""
    
    if not story_text or not isinstance(story_text, str):
        return []
    
    # Patrones para detectar el inicio de una nueva historia
    # Patrón 1: "HISTORIA #" seguido de número
    pattern1 = r'(?=HISTORIA\s*#\s*\d+)'
    # Patrón 2: "HISTORIA NO FUNCIONAL #" seguido de número
    pattern2 = r'(?=HISTORIA\s+NO\s+FUNCIONAL\s*#\s*\d+)'
    # Patrón 3: Líneas con "════════════" seguidas de "HISTORIA"
    pattern3 = r'(?=╔════════════.*?HISTORIA)'
    
    # Intentar dividir por el patrón más común
    stories = []
    
    # Buscar todas las ocurrencias de "HISTORIA #" (con diferentes variaciones)
    # Patrón más flexible: busca "HISTORIA" seguido de "#" y número, o "HISTORIA #" seguido de número
    pattern = r'HISTORIA\s*#\s*\d+|HISTORIA\s+NO\s+FUNCIONAL\s*#\s*\d+|HISTORIA\s+#\s*\d+'
    matches = list(re.finditer(pattern, story_text, re.IGNORECASE | re.MULTILINE))
    
    if len(matches) > 1:
        # Hay múltiples historias, dividir el texto
        for i, match in enumerate(matches):
            start_pos = match.start()
            # El final es el inicio de la siguiente historia, o el final del texto
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(story_text)
            story = story_text[start_pos:end_pos].strip()
            if story and len(story) > 50:  # Validar que tenga contenido mínimo
                stories.append(story)
        logger.info(f"Divididas {len(stories)} historias individuales del texto usando patrón 'HISTORIA #'")
    elif len(matches) == 1:
        # Solo una coincidencia, pero puede haber más historias con otro formato
        # Intentar buscar por separadores de líneas "═"
        parts = re.split(r'\n\s*═{20,}\s*\n', story_text)
        if len(parts) > 1:
            stories = [p.strip() for p in parts if p.strip() and len(p.strip()) > 50]
            logger.info(f"Divididas {len(stories)} historias por separadores de líneas '═'")
        else:
            # Solo una historia en el texto
            stories = [story_text.strip()]
            logger.info("Una historia encontrada en el texto")
    else:
        # No se encontró el patrón "HISTORIA #", intentar dividir por otros separadores
        # Buscar por bloques grandes separados por líneas de "═"
        parts = re.split(r'\n\s*═{20,}\s*\n', story_text)
        if len(parts) > 1:
            stories = [p.strip() for p in parts if p.strip() and len(p.strip()) > 50]
            logger.info(f"Divididas {len(stories)} historias por separadores de líneas '═'")
        else:
            # Buscar por patrones alternativos: bloques que empiezan con "COMO:", "QUIERO:", "PARA:"
            # Esto puede indicar múltiples historias
            como_matches = list(re.finditer(r'^\s*COMO\s*:', story_text, re.IGNORECASE | re.MULTILINE))
            if len(como_matches) > 1:
                for i, match in enumerate(como_matches):
                    start_pos = match.start()
                    end_pos = como_matches[i + 1].start() if i + 1 < len(como_matches) else len(story_text)
                    story = story_text[start_pos:end_pos].strip()
                    if story and len(story) > 50:
                        stories.append(story)
                logger.info(f"Divididas {len(stories)} historias usando patrón 'COMO:'")
            else:
                # Si no hay separadores claros, tratar todo como una historia
                stories = [story_text.strip()] if story_text.strip() else []
                logger.info("Texto tratado como una sola historia (sin separadores detectados)")
    
    return stories


def extract_stories_from_result(result):
    """Extrae las historias de usuario del resultado del agente"""
    stories = []

    if isinstance(result, dict):
        # Caso 1: El resultado está anidado en 'result.stories' o 'result.story'
        if 'result' in result and isinstance(result['result'], dict):
            result_data = result['result']
            if 'stories' in result_data and isinstance(result_data['stories'], list):
                # Si la lista tiene un solo elemento que es un string largo, puede contener múltiples historias
                if len(result_data['stories']) == 1 and isinstance(result_data['stories'][0], str):
                    # Intentar dividir el string en múltiples historias
                    split_stories = split_story_text_into_individual_stories(result_data['stories'][0])
                    if len(split_stories) > 1:
                        stories = split_stories
                        logger.info(f"Historias encontradas en 'result.stories' (divididas de 1 string): {len(stories)}")
                    else:
                        stories = result_data['stories']
                        logger.info(f"Historias encontradas en clave 'result.stories': {len(stories)}")
                else:
                    # Lista con múltiples elementos o elementos no-string
                    stories = result_data['stories']
                    logger.info(f"Historias encontradas en clave 'result.stories': {len(stories)}")
            # También buscar en 'result.story' (singular) que puede contener texto con múltiples historias
            elif 'story' in result_data and isinstance(result_data['story'], str):
                stories = split_story_text_into_individual_stories(result_data['story'])
                logger.info(f"Historias extraídas de 'result.story': {len(stories)}")
            # Buscar cualquier clave que contenga 'story' en el nombre dentro de result
            elif isinstance(result_data, dict):
                for key in result_data.keys():
                    if 'story' in key.lower() and isinstance(result_data[key], str):
                        stories = split_story_text_into_individual_stories(result_data[key])
                        if stories:
                            logger.info(f"Historias extraídas de 'result.{key}': {len(stories)}")
                            break

        # Caso 2: Buscar directamente en el diccionario (sin 'result')
        if not stories:
            if 'stories' in result and isinstance(result['stories'], list):
                # Si la lista tiene un solo elemento que es un string largo, puede contener múltiples historias
                if len(result['stories']) == 1 and isinstance(result['stories'][0], str):
                    # Intentar dividir el string en múltiples historias
                    split_stories = split_story_text_into_individual_stories(result['stories'][0])
                    if len(split_stories) > 1:
                        stories = split_stories
                        logger.info(f"Historias encontradas en 'stories' (divididas de 1 string): {len(stories)}")
                    else:
                        stories = result['stories']
                        logger.info(f"Historias encontradas en clave 'stories': {len(stories)}")
                else:
                    # Lista con múltiples elementos o elementos no-string
                    stories = result['stories']
                    logger.info(f"Historias encontradas en clave 'stories': {len(stories)}")
            elif 'story' in result and isinstance(result['story'], str):
                stories = split_story_text_into_individual_stories(result['story'])
                logger.info(f"Historias extraídas de clave 'story': {len(stories)}")

        # Caso 3: Buscar en cualquier otra clave que pueda contener historias
        if not stories:
            for key, value in result.items():
                if isinstance(value, list) and value:
                    # Verificar si el primer elemento parece ser una historia
                    first_item = value[0]
                    if isinstance(first_item, str) and any(
                            marker in first_item.lower() for marker in ['como', 'quiero', 'para', 'historia']):
                        stories = value
                        logger.info(f"Historias encontradas en clave '{key}': {len(stories)}")
                        break
                # También buscar en valores string que puedan contener múltiples historias
                elif isinstance(value, str) and any(
                        marker in value.lower() for marker in ['historia #', 'historia#', 'como', 'quiero', 'para']):
                    # Puede ser un string con múltiples historias
                    split_stories = split_story_text_into_individual_stories(value)
                    if split_stories:
                        stories = split_stories
                        logger.info(f"Historias extraídas de clave '{key}': {len(split_stories)}")
                        break

    # Si es una lista directamente, usarla
    elif isinstance(result, list):
        stories = result
        logger.info(f"Resultado es lista directa de historias: {len(stories)}")

    # Si es un string, intentar dividirlo en historias individuales
    elif isinstance(result, str):
        stories = split_story_text_into_individual_stories(result)
        logger.info(f"Historias extraídas de string: {len(stories)}")

    # Limpiar las historias (remover formato JSON si es necesario)
    cleaned_stories = []
    for story in stories:
        if isinstance(story, str):
            # Remover marcas de código y formato excesivo
            cleaned_story = clean_story_text(story)
            # Si después de limpiar sigue siendo una historia válida
            if cleaned_story and len(cleaned_story.strip()) > 50:
                cleaned_stories.append(cleaned_story)
        else:
            # Si no es string, convertirlo a string
            story_str = str(story)
            if story_str and len(story_str.strip()) > 50:
                cleaned_stories.append(story_str)

    logger.info(f"Total de historias finales después de limpieza: {len(cleaned_stories)}")
    return cleaned_stories


# ============================================================================
# FUNCIONES AUXILIARES PARA PROCESAMIENTO
# ============================================================================

def validate_stories(stories_content):
    """
    Valida y filtra historias válidas usando normalización y validación de estructura.
    
    Args:
        stories_content: Lista de historias a validar
        
    Returns:
        Tuple[List[str], Optional[str]]: (historias válidas, mensaje de error si hay)
    """
    from app.services.story_normalizer import StoryNormalizer
    
    if not stories_content or len(stories_content) == 0:
        return None, "No se generaron historias de usuario"
    
    # Filtrar historias vacías o muy cortas
    filtered = [s for s in stories_content if s and s.strip() and len(s.strip()) > Config.MIN_RESPONSE_LENGTH]
    
    if not filtered:
        return None, "Todas las historias generadas están vacías o son inválidas"
    
    # Normalizar y validar estructura completa
    normalizer = StoryNormalizer()
    valid_stories = normalizer.normalize_and_validate(filtered)
    
    if not valid_stories:
        return None, "Todas las historias generadas tienen estructura incompleta (faltan componentes requeridos)"
    
    logger.info(f"Validadas {len(valid_stories)} historias completas de {len(filtered)} historias iniciales")
    
    return valid_stories, None


def validate_test_cases(cleaned_matrix_data):
    """Valida y filtra casos de prueba válidos"""
    if not cleaned_matrix_data or len(cleaned_matrix_data) == 0:
        return None, "No se generaron casos de prueba"
    
    valid_cases = []
    for case in cleaned_matrix_data:
        if isinstance(case, dict):
            has_title = case.get('titulo_caso_prueba', '').strip()
            has_desc = case.get('Descripcion', '').strip()
            if has_title or has_desc:
                valid_cases.append(case)
    
    if not valid_cases:
        return None, "Todos los casos de prueba generados están vacíos"
    
    return valid_cases, None


def process_story_generation(result, output_filename, filepath):
    """Procesa la generación de historias de usuario"""
    # Extraer historias
    logger.debug(f"Contenido de result: {result}")
    stories_content = extract_stories_from_result(result)
    logger.info(f"Historias extraídas: {len(stories_content)} elementos")
    
    # Validar historias
    valid_stories, error_msg = validate_stories(stories_content)
    if error_msg:
        logger.error(error_msg)
        clean_temp_files(filepath)
        return None, {
            "error": "No se pudieron generar historias de usuario. El documento puede ser demasiado grande o no contener información suficiente. Intenta con un documento más pequeño o más detallado."
        }
    
    # Crear archivos HTML y CSV
    logger.info("Paso 3: Creando archivos HTML y CSV...")
    
    # Generar HTML
    html_content = story_backend.generate_html_document(valid_stories)
    html_filename = f"{output_filename}.html"
    html_filepath = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generar CSV para Jira
    csv_content = story_backend.generate_jira_csv(valid_stories)
    csv_filename = f"{output_filename}.csv"
    csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
        f.write(csv_content)
    
    story_count = len(valid_stories)
    story_word = "historia" if story_count == 1 else "historias"
    
    return {
        "status": "success",
        "message": f"Historias generadas exitosamente: {story_count} {story_word}",
        "download_url": f"/download/{html_filename}",
        "filename": html_filename,
        "stories_count": story_count,
        "csv_filename": csv_filename
    }, None


def process_matrix_generation(result, output_filename, filepath):
    """Procesa la generación de matriz de pruebas"""
    # Obtener datos de matriz
    logger.debug(f"Contenido de result: {result}")
    matrix_data = extract_matrix_data(result)
    
    if matrix_data:
        logger.debug(f"matrix_data tipo: {type(matrix_data)}, longitud: {len(matrix_data)}")
    
    # Limpiar y validar
    cleaned_matrix_data = clean_matrix_data(matrix_data) if matrix_data else []
    logger.info(f"Datos limpios: {len(cleaned_matrix_data)} elementos")
    
    # Validar casos
    valid_cases, error_msg = validate_test_cases(cleaned_matrix_data)
    if error_msg:
        logger.error(f"No hay datos válidos: {error_msg}")
        clean_temp_files(filepath)
        return None, {
            "error": "No se pudieron generar casos de prueba. El documento puede ser demasiado grande, el procesamiento puede haber sido interrumpido por timeout, o el documento no contiene información suficiente. Intenta con un documento más pequeño o más detallado."
        }
    
    # Crear ZIP
    zip_filename = f"{output_filename}.zip"
    zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    csv_content = generate_proper_csv(valid_cases)
    json_content = json.dumps(valid_cases, ensure_ascii=False, indent=2)
    
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"{output_filename}.json", json_content)
        zip_file.writestr(f"{output_filename}.csv", csv_content)
    
    logger.info(f"Archivo ZIP creado con {len(valid_cases)} casos de prueba")
    
    case_count = len(valid_cases)
    case_word = "caso" if case_count == 1 else "casos"
    
    return {
        "status": "success",
        "message": f"Matriz de pruebas generada exitosamente con {case_count} {case_word}",
        "download_url": f"/download/{zip_filename}",
        "filename": zip_filename,
        "test_cases_count": case_count
    }, None


def process_both_generation(document_text, parameters, output_filename, filepath):
    """Procesa la generación de historias y matriz de pruebas"""
    logger.info("Generando ambos: historias y matriz de pruebas")
    
    # Generar historias
    logger.info("Paso 1: Generando historias de usuario...")
    stories_result = simple_agent_processing('story', document_text, parameters)
    
    if isinstance(stories_result, dict) and "error" in stories_result:
        logger.error(f"Error al generar historias: {stories_result['error']}")
        clean_temp_files(filepath)
        return None, {"error": f"Error al generar historias: {stories_result['error']}"}
    
    # Validar historias
    stories_content = extract_stories_from_result(stories_result)
    logger.info(f"Historias extraídas: {len(stories_content)} elementos")
    
    valid_stories, error_msg = validate_stories(stories_content)
    if error_msg:
        logger.error(error_msg)
        clean_temp_files(filepath)
        return None, {
            "error": "No se pudieron generar historias de usuario. El documento puede ser demasiado grande o no contener información suficiente."
        }
    
    # Generar matriz
    logger.info("Paso 2: Generando matriz de pruebas...")
    matrix_result = simple_agent_processing('matrix', document_text, parameters)
    
    if isinstance(matrix_result, dict) and "error" in matrix_result:
        logger.error(f"Error al generar matriz: {matrix_result['error']}")
        clean_temp_files(filepath)
        return None, {"error": f"Error al generar matriz: {matrix_result['error']}"}
    
    # Extraer y validar matriz
    matrix_data = extract_matrix_data(matrix_result)
    cleaned_matrix_data = clean_matrix_data(matrix_data) if matrix_data else []
    logger.info(f"Datos de matriz limpios: {len(cleaned_matrix_data)} elementos")
    
    valid_cases, error_msg = validate_test_cases(cleaned_matrix_data)
    if error_msg:
        logger.error(error_msg)
        clean_temp_files(filepath)
        return None, {
            "error": "No se pudieron generar casos de prueba. El documento puede ser demasiado grande o no contener información suficiente."
        }
    
    # Crear archivos
    logger.info("Paso 3: Creando archivos...")
    
    # Generar HTML para historias
    html_content = story_backend.generate_html_document(valid_stories)
    stories_html_filename = f"{output_filename}_historias.html"
    stories_html_filepath = os.path.join(app.config['UPLOAD_FOLDER'], stories_html_filename)
    with open(stories_html_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generar CSV para historias (Jira)
    stories_csv_content = story_backend.generate_jira_csv(valid_stories)
    stories_csv_filename = f"{output_filename}_historias.csv"
    stories_csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], stories_csv_filename)
    with open(stories_csv_filepath, 'w', encoding='utf-8', newline='') as f:
        f.write(stories_csv_content)
    
    # CSV y JSON para matriz
    matrix_csv_content = generate_proper_csv(valid_cases)
    json_content = json.dumps(valid_cases, ensure_ascii=False, indent=2)
    
    # ZIP con todos los archivos
    zip_filename = f"{output_filename}_completo.zip"
    zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(stories_html_filepath, stories_html_filename)
        zip_file.write(stories_csv_filepath, stories_csv_filename)
        zip_file.writestr(f"{output_filename}_matriz.json", json_content)
        zip_file.writestr(f"{output_filename}_matriz.csv", matrix_csv_content)
    
    # Limpiar archivo temporal
    clean_temp_files(filepath)
    
    story_count = len(valid_stories)
    story_word = "historia" if story_count == 1 else "historias"
    case_count = len(valid_cases)
    case_word = "caso" if case_count == 1 else "casos"
    
    logger.info(f"Proceso completado: {story_count} {story_word} y {case_count} {case_word}")
    
    return {
        "status": "success",
        "message": f"✅ Generación completada: {story_count} {story_word} de usuario y {case_count} {case_word} de prueba",
        "download_url": f"/download/{zip_filename}",
        "filename": zip_filename,
        "stories_count": story_count,
        "test_cases_count": case_count
    }, None


# ============================================================================
# API ENDPOINTS CON MANEJO DE ERRORES
# ============================================================================

# [REMOVED] Endpoint /api/agent/process - Obsoleto
# Este endpoint era usado por el "Generador AI" antiguo que ha sido reemplazado
# por los generadores especializados: /api/stories/generate y /api/tests/generate


@app.route('/api/matrix', methods=['POST'])
@login_required
@validate_file_upload
@handle_errors("Error al generar matriz de pruebas", status_code=500)
def generate_matrix():
    filepath = None
    try:
        logger.info("Iniciando generación de matriz de pruebas")

        file = request.files['file']

        # Obtener parámetros del formulario, incluyendo el nuevo campo 'historia' y 'types'
        context = request.form.get('contexto', '')
        flow = request.form.get('flujo', '')
        historia = request.form.get('historia', '')  # AÑADIDO: Obtiene la historia de usuario
        types = request.form.getlist('types')  # AÑADIDO: Obtiene los tipos de prueba
        if not types:  # Si types está vacío, usar funcional por defecto
            types = ['funcional']
            logger.warning("No se especificaron tipos de prueba, usando 'funcional' por defecto")
        output_filename = request.form.get('output_filename', 'matriz_de_prueba')

        logger.info(f"Procesando archivo: {file.filename}")
        logger.info(f"Contexto: {len(context)} caracteres")
        logger.info(f"Flujo: {len(flow)} caracteres")
        logger.info(f"Historia de Usuario: {len(historia)} caracteres")
        logger.info(f"Tipos de prueba: {types}")

        # Guardar archivo temporal
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extraer texto
        logger.info("Extrayendo texto del archivo")
        text = extract_text_from_file(filepath)
        logger.info(f"Texto extraído: {len(text)} caracteres")

        # Generar matriz
        logger.info("Generando matriz de pruebas")
        # Se pasan los nuevos argumentos 'historia' y 'types'
        result = matrix_backend.generar_matriz_test(context, flow, historia, text, types)
        logger.info(f"Resultado: {result['status']}")

        clean_temp_files(filepath)

        if result['status'] == 'success':
            matrix_data = result['matrix']
            logger.info(f"Matriz generada con {len(matrix_data)} casos de prueba")

            # Crear ZIP con archivos
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                # JSON
                json_content = matrix_backend.save_to_json_buffer(matrix_data)
                zip_file.writestr(f"{output_filename}.json", json_content)

                # CSV
                csv_content = matrix_backend.save_to_csv_buffer(matrix_data)
                zip_file.writestr(f"{output_filename}.csv", csv_content)

            zip_buffer.seek(0)
            logger.info("Archivo ZIP creado exitosamente")

            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name=f"{output_filename}.zip",
                mimetype='application/zip'
            )
        else:
            logger.error(f"Error en la generación: {result['message']}")
            return jsonify({"error": result['message']}), 500

    except Exception as e:
        logger.error(f"Error en generate_matrix: {e}", exc_info=True)
        clean_temp_files(filepath)
        return jsonify({"error": f"Error en el procesamiento: {str(e)}"}), 500


@app.route('/api/stories/generate', methods=['POST'])
@login_required
@validate_file_upload
@handle_errors("Error al generar historias de usuario", status_code=500)
def generate_stories():
    """Endpoint para generar historias de usuario con campos específicos"""
    filepath = None
    try:
        logger.info("Iniciando generación de historias de usuario")

        file = request.files['file']
        
        # Obtener parámetros del formulario
        role = request.form.get('role', 'Usuario')
        story_type = request.form.get('story_type', 'funcionalidad')
        business_context = request.form.get('business_context', '')
        # output_filename ya no es necesario, se genera automáticamente
        output_filename = 'historias_usuario'

        logger.info(f"Procesando archivo: {file.filename}")
        logger.info(f"Rol: {role}, Tipo: {story_type}, Contexto: {len(business_context)} caracteres")

        # Guardar archivo temporal
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extraer texto
        logger.info("Extrayendo texto del archivo")
        document_text = extract_text_from_file(filepath)
        logger.info(f"Texto extraído: {len(document_text)} caracteres")

        # Generar historias usando story_backend
        logger.info("Generando historias de usuario...")
        parameters = {
            'role': role,
            'business_context': business_context,
            'story_type': story_type
        }
        
        result = simple_agent_processing('story', document_text, parameters)
        
        # Procesar resultado y generar archivos
        result_data, error = process_story_generation(result, output_filename, filepath)
        
        if error:
            return jsonify(error), 500
        
        # Obtener historias parseadas para vista previa
        valid_stories = extract_stories_from_result(result)
        validated_stories, _ = validate_stories(valid_stories)
        
        # Convertir historias a formato estructurado para vista previa
        stories_dict = story_backend.parse_stories_to_dict(validated_stories)
        
        # Generar HTML y CSV para descarga opcional
        html_content = story_backend.generate_html_document(validated_stories)
        csv_content = story_backend.generate_jira_csv(validated_stories)
        
        # Obtener conteo de historias
        stories_count = len(validated_stories)
        logger.info(f"Historias generadas: {stories_count}")
        
        # Guardar en base de datos local para historial de actividades
        try:
            user_id = get_current_user_id()
            # Obtener el área del formulario (Finanzas, RRHH, TI, etc.)
            area = request.form.get('area', 'UNKNOWN')
            # project_key es el proyecto de Jira (puede ser vacío si no se sube a Jira)
            project_key = request.form.get('project_key', '')
            
            # Crear UN SOLO registro con todas las historias
            story_repo = UserStoryRepository()
            story_title = f"Generación de {stories_count} historias de usuario - {area}"
            
            user_story = UserStory(
                user_id=user_id,
                project_key=project_key,  # Proyecto de Jira (puede estar vacío)
                area=area,  # Área que solicitó la generación (Finanzas, RRHH, etc.)
                story_title=story_title,
                story_content=json.dumps(validated_stories, ensure_ascii=False),  # Todas las historias juntas
                jira_issue_key=None  # Se actualizará cuando se suba a Jira
            )
            story_repo.create(user_story)
            
            logger.info(f"Historias guardadas en BD local: 1 registro con {stories_count} historias para user_id={user_id}, área={area}")
        except Exception as e:
            logger.error(f"Error al guardar historias en BD local: {e}", exc_info=True)
            # No fallar la operación si falla el guardado en BD local
        
        # Retornar JSON con datos para vista previa
        return jsonify({
            "status": "success",
            "message": f"Historias generadas exitosamente: {stories_count} historias",
            "stories": stories_dict,
            "stories_count": stories_count,
            "html_content": html_content,
            "csv_content": csv_content
        }), 200

    except Exception as e:
        logger.error(f"Error en generate_stories: {e}", exc_info=True)
        clean_temp_files(filepath)
        return jsonify({"error": f"Error en el procesamiento: {str(e)}"}), 500


@app.route('/api/tests/generate', methods=['POST'])
@login_required
@validate_file_upload
@handle_errors("Error al generar casos de prueba", status_code=500)
def generate_tests():
    """Endpoint para generar casos de prueba con campos específicos y retornar vista previa"""
    filepath = None
    try:
        logger.info("Iniciando generación de casos de prueba")

        file = request.files['file']
        
        # Obtener parámetros del formulario
        context = request.form.get('contexto', '')
        flow = request.form.get('flujo', '')
        test_types = request.form.getlist('test_types')
        if not test_types:
            test_types = ['funcional', 'no_funcional']
        # output_filename ya no es necesario, se genera automáticamente

        logger.info(f"Procesando archivo: {file.filename}")
        logger.info(f"Contexto: {len(context)} caracteres, Flujo: {len(flow)} caracteres")
        logger.info(f"Tipos de prueba: {test_types}")

        # Guardar archivo temporal
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extraer texto
        logger.info("Extrayendo texto del archivo")
        text = extract_text_from_file(filepath)
        logger.info(f"Texto extraído: {len(text)} caracteres")

        # Generar matriz usando matrix_backend
        logger.info("Generando matriz de pruebas...")
        result = matrix_backend.generar_matriz_test(context, flow, '', text, test_types)
        logger.info(f"Resultado: {result['status']}")

        clean_temp_files(filepath)

        if result['status'] == 'success':
            matrix_data = result['matrix']
            test_cases_count = len(matrix_data)
            logger.info(f"Matriz generada con {test_cases_count} casos de prueba")

            # Convertir casos de prueba a formato estructurado para vista previa
            test_cases_dict = matrix_backend.parse_test_cases_to_dict(matrix_data)
            logger.info(f"Casos parseados para vista previa: {len(test_cases_dict)} casos")
            if test_cases_dict:
                logger.info(f"Primer caso parseado: {test_cases_dict[0]}")
            else:
                logger.warning("⚠️ parse_test_cases_to_dict retornó array vacío!")
            
            # Generar HTML y CSV para descarga opcional
            html_content = matrix_backend.generate_test_cases_html_document(matrix_data)
            csv_content = matrix_backend.generate_jira_csv_for_test_cases(matrix_data)
            
            # Guardar en base de datos local para historial de actividades
            try:
                user_id = get_current_user_id()
                # Obtener el área del formulario (Finanzas, RRHH, TI, etc.)
                area = request.form.get('area', 'UNKNOWN')
                # project_key es el proyecto de Jira (puede ser vacío si no se sube a Jira)
                project_key = request.form.get('project_key', '')
                
                # Crear UN SOLO registro con todos los casos de prueba
                test_case_repo = TestCaseRepository()
                test_case_title = f"Generación de {test_cases_count} casos de prueba - {area}"
                
                test_case_obj = TestCase(
                    user_id=user_id,
                    project_key=project_key,  # Proyecto de Jira (puede estar vacío)
                    area=area,  # Área que solicitó la generación (Finanzas, RRHH, etc.)
                    test_case_title=test_case_title,
                    test_case_content=json.dumps(matrix_data, ensure_ascii=False),  # Todos los casos juntos
                    jira_issue_key=None  # Se actualizará cuando se suba a Jira
                )
                test_case_repo.create(test_case_obj)
                
                logger.info(f"Casos de prueba guardados en BD local: 1 registro con {test_cases_count} casos para user_id={user_id}, área={area}")
            except Exception as e:
                logger.error(f"Error al guardar casos de prueba en BD local: {e}", exc_info=True)
                # No fallar la operación si falla el guardado en BD local
            
            # Retornar JSON con datos para vista previa
            return jsonify({
                "status": "success",
                "message": f"Casos de prueba generados exitosamente: {test_cases_count} casos",
                "test_cases": test_cases_dict,
                "test_cases_count": test_cases_count,
                "html_content": html_content,
                "csv_content": csv_content
            }), 200
        else:
            logger.error(f"Error en la generación: {result['message']}")
            return jsonify({"error": result['message']}), 500

    except Exception as e:
        logger.error(f"Error en generate_tests: {e}", exc_info=True)
        clean_temp_files(filepath)
        return jsonify({"error": f"Error en el procesamiento: {str(e)}"}), 500


@app.route('/api/story', methods=['POST'])
@login_required
@validate_file_upload
@handle_errors("Error al generar historias de usuario", status_code=500)
def generate_and_download_story():
    filepath = None
    try:
        logger.info("Iniciando generación de historias")

        file = request.files['file']

        # Obtener parámetros
        role = request.form.get('role', 'Usuario')
        story_type = request.form.get('story_type', 'funcionalidad')
        output_filename = request.form.get('output_filename', 'historias_generadas')
        business_context = request.form.get('business_context', '')  # ✅ Ahora sí lo capturamos

        logger.info(
            f"Archivo: {file.filename}, Rol: {role}, Tipo: {story_type}, Contexto: {len(business_context)} caracteres")

        # Guardar archivo temporal
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extraer texto
        text = extract_text_from_file(filepath)
        logger.info(f"Documento con {len(text)} caracteres")

        # Procesar según tamaño
        if len(text) > Config.LARGE_DOCUMENT_THRESHOLD:
            logger.info("Usando procesamiento avanzado para documento grande")
            result = story_backend.process_large_document(text, role, story_type, business_context)

            if result['status'] == 'success':
                stories = [result['story']]
            else:
                raise Exception(result['message'])
        else:
            logger.info("Usando procesamiento por chunks")
            chunks = story_backend.split_document_into_chunks(text)
            logger.info(f"Dividido en {len(chunks)} chunks")

            stories = []
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"Procesando chunk {i}/{len(chunks)}")
                result = story_backend.generate_story_from_chunk(chunk, role, story_type, business_context)
                if result['status'] == 'success':
                    stories.append(result['story'])
                else:
                    raise Exception(result['message'])

        clean_temp_files(filepath)

        # Generar HTML y CSV
        logger.info("Creando archivos HTML y CSV")
        html_content = story_backend.generate_html_document(stories)
        csv_content = story_backend.generate_jira_csv(stories)
        
        # Guardar HTML
        html_filename = f"{output_filename}.html"
        html_filepath = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Guardar CSV
        csv_filename = f"{output_filename}.csv"
        csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
        with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)
        
        logger.info("Proceso completado exitosamente")
        
        # Retornar HTML como archivo principal
        return send_file(
            html_filepath,
            as_attachment=True,
            download_name=html_filename,
            mimetype='text/html'
        )

    except Exception as e:
        logger.error(f"Error en generate_story: {e}", exc_info=True)
        clean_temp_files(filepath)
        return jsonify({"error": f"Error en el procesamiento: {str(e)}"}), 500


# Añadir este endpoint para descargas
@app.route('/download/<filename>')
@login_required
@handle_errors("Error al descargar archivo", status_code=500)
def download_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({"error": "Archivo no encontrado"}), 404
    except Exception as e:
        logger.error(f"Error descargando archivo: {e}")
        return jsonify({"error": "Error al descargar el archivo"}), 500


# ============================================================================
# ENDPOINTS PARA JIRA
# ============================================================================

@app.route('/api/jira/test-connection', methods=['GET'])
@login_required
@handle_errors("Error al probar conexión con Jira", status_code=500)
def jira_test_connection():
    """Prueba la conexión con Jira"""
    try:
        client = jira_backend.JiraClient()
        result = client.test_connection()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error al probar conexión con Jira: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/jira/projects', methods=['GET'])
@login_required
def jira_get_projects():
    """Obtiene la lista de proyectos de Jira"""
    try:
        # Obtener configuración de Jira del usuario
        from app.services.jira_token_manager import JiraTokenManager
        from app.auth.decorators import get_current_user_id
        from app.auth.user_service import UserService
        from app.database.repositories.project_config_repository import ProjectConfigRepository
        
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado", "projects": []}), 401
        
        # Obtener todas las configuraciones de proyectos disponibles
        project_config_repo = ProjectConfigRepository()
        all_configs = project_config_repo.get_all(active_only=True)
        
        if not all_configs:
            # Fallback: usar variables de entorno si no hay configuraciones en BD
            from app.core.config import Config
            if Config.JIRA_BASE_URL and Config.JIRA_EMAIL and Config.JIRA_API_TOKEN:
                from app.backend.jira.connection import JiraConnection
                from app.backend.jira.project_service import ProjectService
                
                connection = JiraConnection(
                    base_url=Config.JIRA_BASE_URL,
                    email=Config.JIRA_EMAIL,
                    api_token=Config.JIRA_API_TOKEN
                )
                project_service = ProjectService(connection)
                projects = project_service.get_projects()
                return jsonify({"success": True, "projects": projects})
            
            return jsonify({"success": False, "error": "No hay configuración de Jira disponible", "projects": []}), 400
        
        # Usar la primera configuración disponible para obtener proyectos
        first_config = all_configs[0]
        token_manager = JiraTokenManager()
        
        try:
            jira_config = token_manager.get_token_for_user(user, first_config.project_key)
        except Exception as e:
            logger.warning(f"Error al obtener token para proyecto {first_config.project_key}: {e}")
            # Intentar con variables de entorno como fallback
            from app.core.config import Config
            if Config.JIRA_BASE_URL and Config.JIRA_EMAIL and Config.JIRA_API_TOKEN:
                jira_config = type('JiraConfig', (), {
                    'base_url': Config.JIRA_BASE_URL,
                    'email': Config.JIRA_EMAIL,
                    'token': Config.JIRA_API_TOKEN
                })()
            else:
                raise
        
        from app.backend.jira.connection import JiraConnection
        from app.backend.jira.project_service import ProjectService
        
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        project_service = ProjectService(connection)
        projects = project_service.get_projects()
        
        return jsonify({"success": True, "projects": projects})
    except Exception as e:
        logger.error(f"Error al obtener proyectos de Jira: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e), "projects": []}), 500


@app.route('/api/jira/validate-project-access', methods=['POST'])
@login_required
def jira_validate_project_access():
    """
    Valida si el usuario tiene acceso (membresía) al proyecto de Jira indicado.
    Admin y Analista QA bypass; Usuario valida en Jira.
    """
    try:
        data = request.get_json() or {}
        project_key = (data.get('project_key') or data.get('projectKey') or '').strip()
        requested_email = (data.get('email') or '').strip()
        role = SessionService.get_current_user_role() or 'usuario'
        session_email = SessionService.get_current_user_email() or ''

        if not project_key:
            return jsonify({'hasAccess': False, 'message': 'project_key es requerido'}), 400

        if role in ['admin', 'analista_qa']:
            return jsonify({'hasAccess': True, 'message': 'Acceso permitido por rol'}), 200

        user = UserService().get_user_by_id(get_current_user_id())
        if not user:
            return jsonify({'hasAccess': False, 'message': 'Usuario no encontrado'}), 401

        try:
            jira_config = JiraTokenManager().get_token_for_user(user, project_key)
        except Exception as e:
            return jsonify({'hasAccess': False, 'message': str(e)}), 400

        # Validar membresía del usuario autenticado (no del dueño del token compartido)
        target_email = (requested_email or session_email or '').strip()
        # Blindaje: solo permitir validar el email de la sesión, ignorar otro input
        if session_email:
            target_email = session_email

        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        project_service = ProjectService(connection)
        membership = project_service.check_user_membership(project_key, target_email)
        return jsonify(membership), 200

    except Exception as e:
        logger.error(f"Error al validar acceso a proyecto Jira: {e}", exc_info=True)
        return jsonify({'hasAccess': False, 'message': f'Error al validar permisos: {str(e)}'}), 500


@app.route('/api/jira/project/<project_key>/filter-fields', methods=['GET'])
@login_required
def jira_get_filter_fields(project_key):
    """Obtiene los campos disponibles para filtros y sus valores"""
    try:
        # Obtener parámetro opcional issuetype de query string
        issuetype = request.args.get('issuetype', None)
        if issuetype:
            logger.info(f"[DEBUG] Filtrando campos por issuetype: {issuetype}")
        
        # Obtener parámetro include_all_fields (para carga masiva)
        include_all_fields = request.args.get('include_all_fields', 'false').lower() == 'true'
        if include_all_fields:
            logger.info(f"[DEBUG] Modo carga masiva: incluyendo todos los campos (incluso sin valores permitidos)")
        
        jira = JiraClient()
        result = jira.get_filter_fields(project_key, issuetype=issuetype, include_all_fields=include_all_fields)
        
        # Formatear respuesta según lo que espera el frontend
        # El frontend espera: { success: true, fields: { available_fields: [...], field_values: {...} } }
        
        # Construir available_fields con los campos estándar y personalizados
        available_fields = []
        field_values = {}
        
        # Obtener custom_field_values temprano para usarlo en campos estándar
        custom_field_values = result.get('custom_field_values', {})
        
        logger.info(f"[DEBUG] ===== INICIO PROCESAMIENTO FILTROS =====")
        logger.info(f"[DEBUG] custom_field_values recibido: {len(custom_field_values)} campos")
        logger.info(f"[DEBUG] Claves en custom_field_values: {list(custom_field_values.keys())}")
        if 'affectsVersions' in custom_field_values:
            logger.info(f"[DEBUG] affectsVersions encontrado con {len(custom_field_values['affectsVersions'])} valores")
        else:
            logger.warning(f"[DEBUG] affectsVersions NO encontrado en custom_field_values")
        
        # Agregar status si tiene valores
        if result.get('status'):
            available_fields.append({
                'id': 'status',
                'name': 'Estado',
                'type': 'select',
                'custom': False
            })
            field_values['status'] = result.get('status', [])
        
        # Agregar priority si tiene valores
        if result.get('priority'):
            available_fields.append({
                'id': 'priority',
                'name': 'Prioridad',
                'type': 'select',
                'custom': False
            })
            field_values['priority'] = result.get('priority', [])
        
        # Agregar assignee (aunque no tenga valores predefinidos, es un campo válido)
        available_fields.append({
            'id': 'assignee',
            'name': 'Asignado',
            'type': 'text',
            'custom': False
        })
        field_values['assignee'] = result.get('assignee', [])
        
        # Agregar labels (campo común)
        available_fields.append({
            'id': 'labels',
            'name': 'Etiqueta',
            'type': 'text',
            'custom': False
        })
        field_values['labels'] = []
        
        # Agregar campos adicionales estándar
        standard_fields = [
            {'id': 'reporter', 'name': 'Reportado por', 'type': 'text'},
            {'id': 'fixVersions', 'name': 'Versión de Corrección', 'type': 'select'},
            {'id': 'affectsVersions', 'name': 'Affects Version', 'type': 'select'},
            {'id': 'components', 'name': 'Componentes', 'type': 'select'},
            {'id': 'created', 'name': 'Fecha de Creación', 'type': 'date'},
            {'id': 'updated', 'name': 'Fecha de Actualización', 'type': 'date'},
            {'id': 'resolution', 'name': 'Resolución', 'type': 'select'}
        ]
        
        all_fields = result.get('all_fields', [])
        
        for field_info in standard_fields:
            field_id = field_info['id']
            # Obtener valores desde custom_field_values si existen (para affectsVersions y otros)
            field_vals = custom_field_values.get(field_id, [])
            
            # Para affectsVersions, agregarlo directamente si tiene valores, aunque no esté en all_fields
            if field_id == 'affectsVersions':
                logger.info(f"[DEBUG] ===== PROCESANDO AFFECTSVERSIONS EN APP.PY =====")
                logger.info(f"[DEBUG] Valores encontrados en custom_field_values: {field_vals}")
                logger.info(f"[DEBUG] Cantidad de valores: {len(field_vals) if field_vals else 0}")
                logger.info(f"[DEBUG] Todos los campos en custom_field_values: {list(custom_field_values.keys())}")
                
                if field_vals and len(field_vals) > 0:
                    logger.info(f"[DEBUG] ✓ Agregando affectsVersions directamente con {len(field_vals)} valores")
                    logger.info(f"[DEBUG] Valores: {field_vals[:5]}...")
                    available_fields.append({
                        'id': field_id,
                        'name': field_info['name'],
                        'type': field_info['type'],
                        'custom': False
                    })
                    field_values[field_id] = field_vals
                    logger.info(f"[DEBUG] affectsVersions agregado a available_fields y field_values")
                else:
                    logger.warning(f"[DEBUG] ✗ affectsVersions NO tiene valores - omitiendo")
                    logger.warning(f"[DEBUG] custom_field_values contiene: {list(custom_field_values.keys())}")
                    if 'affectsVersions' in custom_field_values:
                        logger.warning(f"[DEBUG] affectsVersions está en custom_field_values pero está vacío")
                    else:
                        logger.warning(f"[DEBUG] affectsVersions NO está en custom_field_values")
                logger.info(f"[DEBUG] ===== FIN PROCESAMIENTO AFFECTSVERSIONS EN APP.PY =====")
                continue
            
            # Para otros campos estándar, verificar si están en all_fields
            if any(f.get('id') == field_id for f in all_fields):
                # Solo agregar campos estándar que tienen valores o son de tipo text/date
                if field_info['type'] in ['text', 'date'] or field_vals:
                    available_fields.append({
                        'id': field_id,
                        'name': field_info['name'],
                        'type': field_info['type'],
                        'custom': False
                    })
                    field_values[field_id] = field_vals if field_vals else []
        
        # Agregar campos personalizados del proyecto
        custom_fields = result.get('custom_fields', [])
        # custom_field_values ya está definido arriba
        
        logger.info(f"[DEBUG] Procesando {len(custom_fields)} campos personalizados")
        logger.info(f"[DEBUG] Diccionario custom_field_values tiene {len(custom_field_values)} campos")
        
        for custom_field in custom_fields:
            field_id = custom_field.get('id', '')
            field_name = custom_field.get('name', '')
            field_type = custom_field.get('type', 'string')
            allowed_values = custom_field.get('allowedValues', [])
            
            logger.debug(f"[DEBUG] Procesando campo personalizado: {field_id} ({field_name})")
            
            # Si no hay allowedValues en el campo, intentar obtenerlos del diccionario
            if not allowed_values:
                allowed_values = custom_field_values.get(field_id, [])
            
            # FILTRO: Solo incluir campos que tienen valores permitidos (lista desplegable)
            # EXCEPCIÓN: Si include_all_fields=true (carga masiva), incluir todos los campos
            if not include_all_fields:
                if not allowed_values or len(allowed_values) == 0:
                    logger.debug(f"[DEBUG] Campo personalizado {field_id} ({field_name}) omitido - no tiene valores permitidos")
                    continue
            else:
                # En modo carga masiva, incluir campos aunque no tengan valores permitidos
                if not allowed_values or len(allowed_values) == 0:
                    logger.debug(f"[DEBUG] Campo personalizado {field_id} ({field_name}) incluido (modo carga masiva) - sin valores permitidos")
            
            logger.debug(f"[DEBUG] Campo personalizado {field_id} ({field_name}) tiene {len(allowed_values) if allowed_values else 0} valores permitidos")
            
            # Determinar el tipo de input según el schema y si tiene valores permitidos
            if allowed_values and len(allowed_values) > 0:
                input_type = 'select'  # Si tiene valores, será select
            else:
                # Si no tiene valores, determinar el tipo según el schema
                if field_type in ['date', 'datetime']:
                    input_type = 'date'
                elif field_type in ['number', 'integer', 'float']:
                    input_type = 'number'
                elif field_type in ['text', 'string']:
                    input_type = 'text'
                else:
                    input_type = 'text'  # Por defecto, texto
            
            available_fields.append({
                'id': field_id,
                'name': field_name,
                'type': input_type,
                'custom': True
            })
            # Usar los valores permitidos (puede estar vacío en modo carga masiva)
            field_values[field_id] = allowed_values if allowed_values else []
        
        logger.info(f"[DEBUG] Campos de filtro disponibles: {len(available_fields)} total")
        
        return jsonify({
            'success': True,
            'fields': {
                'available_fields': available_fields,
                'field_values': field_values
            }
        })
    except Exception as e:
        logger.error(f"Error al obtener campos de filtros: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'fields': {
                'available_fields': [],
                'field_values': {}
            }
        }), 500

@app.route('/api/jira/project/<project_key>/metrics', methods=['GET'])
@login_required
def jira_get_project_metrics(project_key):
    """Obtiene métricas de avance para un proyecto específico (compatibilidad hacia atrás)"""
    # Usar la nueva ruta que tiene la lógica correcta de filtrado por rol
    from app.auth.metrics_routes import get_project_metrics
    return get_project_metrics(project_key)


@app.route('/api/jira/project/<project_key>/fields', methods=['GET'])
@login_required
def jira_get_project_fields(project_key):
    """Obtiene los campos disponibles para crear issues en un proyecto"""
    try:
        
        issue_type = request.args.get('issue_type', None)
        client = jira_backend.JiraClient()
        
        fields_info = client.get_project_fields_for_creation(project_key, issue_type)
        
        if fields_info.get('success'):
            return jsonify({
                "success": True,
                "required_fields": fields_info.get('required_fields', []),
                "optional_fields": fields_info.get('optional_fields', []),
                "issue_type": fields_info.get('issue_type', '')
            })
        else:
            return jsonify({
                "success": False,
                "error": fields_info.get('error', 'Error al obtener campos')
            }), 400
            
    except Exception as e:
        logger.error(f"Error al obtener campos del proyecto: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/jira/validate-csv-fields', methods=['POST'])
@login_required
def jira_validate_csv_fields():
    """Valida automáticamente las columnas del CSV contra los campos de Jira"""
    try:
        
        data = request.get_json()
        csv_columns = data.get('csv_columns', [])
        project_key = data.get('project_key')
        issue_type = data.get('issue_type', None)
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        if not csv_columns:
            return jsonify({"success": False, "error": "No se proporcionaron columnas del CSV"}), 400
        
        client = jira_backend.JiraClient()
        validation_result = client.validate_csv_fields(csv_columns, project_key, issue_type)
        
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"Error al validar campos CSV: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "mappings": [],
            "missing_required": [],
            "unmapped_csv_columns": [],
            "required_fields": [],
            "optional_fields": []
        }), 500


@app.route('/api/jira/validate-test-case-fields', methods=['POST'])
@login_required
def jira_validate_test_case_fields():
    """Valida que el proyecto tenga los campos necesarios para crear Test Cases"""
    try:
        data = request.get_json()
        project_key = data.get('project_key', '').strip()
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        # Obtener configuración de Jira del usuario
        from app.services.jira_token_manager import JiraTokenManager
        from app.auth.decorators import get_current_user_id
        from app.auth.user_service import UserService
        
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 401
        
        token_manager = JiraTokenManager()
        jira_config = token_manager.get_token_for_user(user, project_key)
        
        # Crear conexión y servicios
        from app.backend.jira.connection import JiraConnection
        from app.backend.jira.project_service import ProjectService
        
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        project_service = ProjectService(connection)
        
        # Obtener campos del proyecto para Test Case
        fields_info = project_service.get_project_fields_for_creation(project_key, issue_type='Test Case')
        
        if not fields_info.get('success', True):
            return jsonify({
                "success": False,
                "error": fields_info.get('error', 'Error al obtener campos del proyecto'),
                "missing_fields": [],
                "available_fields": []
            }), 400
        
        # Campos requeridos (estándar y custom)
        required_fields = {
            'summary': ['summary', 'Summary', 'Resumen'],
            'description': ['description', 'Description', 'Descripción'],
            'priority': ['priority', 'Priority', 'Prioridad'],
            'issuetype': ['issuetype', 'Issue Type', 'Tipo de Issue'],
            'assignee': ['assignee', 'Assignee', 'Asignado'],
            'pasos': ['pasos', 'Pasos', 'Test Steps', 'Steps', 'Pasos de Prueba'],
            'resultado_esperado': ['resultado esperado', 'Resultado Esperado', 'Expected Result', 'Expected Results', 'Resultado'],
            'tipo_prueba': ['tipo de prueba', 'Tipo de Prueba', 'Test Type', 'Tipo Prueba'],
            'nivel_prueba': ['nivel de prueba', 'Nivel de Prueba', 'Test Level', 'Nivel Prueba'],
            'ambiente': ['ambiente', 'Ambiente', 'Environment', 'Entorno'],
            'tipo_ejecucion': ['tipo de ejecución', 'Tipo de Ejecución', 'Execution Type', 'Tipo Ejecución'],
            'ciclo': ['ciclo', 'Ciclo', 'Cycle', 'Test Cycle'],
            'precondiciones': ['precondiciones', 'Precondiciones', 'Preconditions', 'Precondición']
        }
        
        # Normalizar nombres para comparación
        def normalize_name(name: str) -> str:
            """Normaliza un nombre para comparación"""
            import unicodedata
            import re
            name = name.lower()
            name = unicodedata.normalize('NFD', name)
            name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
            name = re.sub(r'[^a-z0-9\s]', '', name)
            name = re.sub(r'\s+', ' ', name).strip()
            return name
        
        # Obtener todos los campos disponibles (required + optional)
        all_fields = fields_info.get('required_fields', []) + fields_info.get('optional_fields', [])
        
        # Crear diccionario de campos normalizados
        available_fields_normalized = {}
        for field in all_fields:
            field_name = field.get('name', '')
            normalized = normalize_name(field_name)
            if normalized not in available_fields_normalized:
                available_fields_normalized[normalized] = []
            available_fields_normalized[normalized].append({
                'name': field_name,
                'id': field.get('id', ''),
                'type': field.get('type', ''),
                'required': field.get('required', False)
            })
        
        # Validar cada campo requerido
        missing_fields = []
        found_fields = {}
        
        for field_key, possible_names in required_fields.items():
            found = False
            for possible_name in possible_names:
                normalized = normalize_name(possible_name)
                if normalized in available_fields_normalized:
                    found_fields[field_key] = available_fields_normalized[normalized][0]
                    found = True
                    break
            
            if not found:
                missing_fields.append({
                    'field': field_key,
                    'possible_names': possible_names
                })
        
        # Preparar respuesta
        if missing_fields:
            return jsonify({
                "success": False,
                "error": "El proyecto no cuenta con todos los campos necesarios",
                "missing_fields": missing_fields,
                "found_fields": {k: v['name'] for k, v in found_fields.items()},
                "message": "Por favor, configura los campos faltantes en el proyecto de Jira antes de continuar."
            }), 400
        else:
            return jsonify({
                "success": True,
                "message": "Todos los campos necesarios están disponibles en el proyecto",
                "found_fields": {k: v['name'] for k, v in found_fields.items()}
            }), 200
        
    except Exception as e:
        logger.error(f"Error al validar campos de Test Case: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "missing_fields": [],
            "found_fields": {}
        }), 500


@app.route('/api/jira/get-test-case-field-values', methods=['POST'])
@login_required
def get_test_case_field_values():
    """Obtiene los valores permitidos para campos select de Test Cases"""
    try:
        data = request.get_json()
        project_key = data.get('project_key', '').strip()
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        # Obtener configuración de Jira del usuario
        from app.services.jira_token_manager import JiraTokenManager
        from app.auth.decorators import get_current_user_id
        from app.auth.user_service import UserService
        
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 401
        
        token_manager = JiraTokenManager()
        jira_config = token_manager.get_token_for_user(user, project_key)
        
        # Crear conexión y servicios
        from app.backend.jira.connection import JiraConnection
        from app.backend.jira.project_service import ProjectService
        
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        project_service = ProjectService(connection)
        
        # Obtener campos del proyecto para Test Case
        fields_info = project_service.get_project_fields_for_creation(project_key, issue_type='Test Case')
        
        if not fields_info.get('success', True):
            return jsonify({
                "success": False,
                "error": fields_info.get('error', 'Error al obtener campos del proyecto'),
                "field_values": {}
            }), 400
        
        # Normalizar nombres para comparación
        def normalize_name(name: str) -> str:
            import unicodedata
            import re
            name = name.lower()
            name = unicodedata.normalize('NFD', name)
            name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
            name = re.sub(r'[^a-z0-9\s]', '', name)
            name = re.sub(r'\s+', ' ', name).strip()
            return name
        
        # Campos select que necesitamos
        select_fields = {
            'tipo_prueba': ['tipo de prueba', 'Tipo de Prueba', 'Test Type', 'Tipo Prueba'],
            'nivel_prueba': ['nivel de prueba', 'Nivel de Prueba', 'Test Level', 'Nivel Prueba'],
            'tipo_ejecucion': ['tipo de ejecución', 'Tipo de Ejecución', 'Execution Type', 'Tipo Ejecución'],
            'ambiente': ['ambiente', 'Ambiente', 'Environment', 'Entorno']
        }
        
        # Obtener todos los campos disponibles
        all_fields = fields_info.get('required_fields', []) + fields_info.get('optional_fields', [])
        
        # Buscar campos y extraer sus allowedValues
        field_values = {}
        
        for field_key, possible_names in select_fields.items():
            field_found = False
            for field in all_fields:
                field_name = field.get('name', '')
                normalized = normalize_name(field_name)
                
                # Verificar si coincide con alguno de los nombres posibles
                for possible_name in possible_names:
                    if normalized == normalize_name(possible_name):
                        field_found = True
                        # Obtener allowedValues del campo
                        allowed_values = field.get('allowedValues', [])
                        values_list = []
                        
                        if allowed_values and len(allowed_values) > 0:
                            for av in allowed_values:
                                if isinstance(av, dict):
                                    # Extraer el valor más apropiado
                                    value = av.get('value', av.get('name', av.get('label', '')))
                                    if value:
                                        values_list.append({
                                            'value': str(value),
                                            'id': av.get('id'),
                                            'name': av.get('name', value)
                                        })
                                elif isinstance(av, str):
                                    values_list.append({
                                        'value': av,
                                        'name': av
                                    })
                            
                            field_values[field_key] = {
                                'field_name': field_name,
                                'field_id': field.get('id', ''),
                                'values': values_list,
                                'exists': True,
                                'has_values': True
                            }
                        else:
                            # Campo existe pero no tiene valores configurados
                            field_values[field_key] = {
                                'field_name': field_name,
                                'field_id': field.get('id', ''),
                                'values': [],
                                'exists': True,
                                'has_values': False
                            }
                        break
                
                if field_found:
                    break
            
            if not field_found:
                # Campo no existe en el proyecto
                field_values[field_key] = {
                    'field_name': '',
                    'field_id': '',
                    'values': [],
                    'exists': False,
                    'has_values': False
                }
        
        return jsonify({
            "success": True,
            "field_values": field_values
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener valores de campos: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "field_values": {}
        }), 500


@app.route('/api/jira/validate-user', methods=['POST'])
@login_required
def jira_validate_user():
    """Valida si un email tiene cuenta en Jira y retorna su accountId"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({"valid": False, "error": "Email no proporcionado"}), 400
        
        # Validar formato de email básico
        if '@' not in email:
            return jsonify({"valid": False, "error": "Formato de email inválido"}), 400
        
        # Obtener configuración de Jira del usuario
        from app.services.jira_token_manager import JiraTokenManager
        from app.auth.decorators import get_current_user_id
        from app.auth.user_service import UserService
        
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"valid": False, "error": "Usuario no encontrado"}), 401
        
        token_manager = JiraTokenManager()
        # Usar el primer proyecto disponible para validar (o un proyecto por defecto)
        # En este caso, necesitamos un project_key, pero para validar usuario no es necesario
        # Usaremos la conexión directamente
        from app.backend.jira.connection import JiraConnection
        from app.database.repositories.project_config_repository import ProjectConfigRepository
        
        # Obtener configuración de Jira (usaremos la primera disponible o una por defecto)
        project_config_repo = ProjectConfigRepository()
        all_configs = project_config_repo.get_all(active_only=True)
        
        if not all_configs:
            # Fallback: usar variables de entorno si no hay configuraciones en BD
            from app.core.config import Config
            if Config.JIRA_BASE_URL and Config.JIRA_EMAIL and Config.JIRA_API_TOKEN:
                connection = JiraConnection(
                    base_url=Config.JIRA_BASE_URL,
                    email=Config.JIRA_EMAIL,
                    api_token=Config.JIRA_API_TOKEN
                )
            else:
                return jsonify({"valid": False, "error": "No hay configuración de Jira disponible"}), 400
        else:
            # Usar la primera configuración disponible
            first_config = all_configs[0]
            try:
                jira_config = token_manager.get_token_for_user(user, first_config.project_key)
                connection = JiraConnection(
                    base_url=jira_config.base_url,
                    email=jira_config.email,
                    api_token=jira_config.token
                )
            except Exception as e:
                logger.warning(f"Error al obtener token para proyecto {first_config.project_key}: {e}")
                # Fallback: usar variables de entorno
                from app.core.config import Config
                if Config.JIRA_BASE_URL and Config.JIRA_EMAIL and Config.JIRA_API_TOKEN:
                    connection = JiraConnection(
                        base_url=Config.JIRA_BASE_URL,
                        email=Config.JIRA_EMAIL,
                        api_token=Config.JIRA_API_TOKEN
                    )
                else:
                    return jsonify({"valid": False, "error": f"Error al obtener configuración de Jira: {str(e)}"}), 400
        
        from app.backend.jira.issue_service import IssueService
        issue_service = IssueService(connection, None)
        
        # Buscar usuario por email
        account_id = issue_service.get_user_account_id_by_email(email)
        
        if account_id:
            return jsonify({
                "valid": True,
                "accountId": account_id,
                "email": email
            }), 200
        else:
            return jsonify({
                "valid": False,
                "error": "Este correo no tiene cuenta en Jira"
            }), 200  # 200 porque es una respuesta válida (usuario no encontrado)
            
    except Exception as e:
        logger.error(f"Error al validar usuario de Jira: {e}", exc_info=True)
        return jsonify({"valid": False, "error": f"Error al validar usuario: {str(e)}"}), 500


@app.route('/api/stories/upload-to-jira', methods=['POST'])
@login_required
def upload_stories_to_jira():
    """Sube historias de usuario directamente a Jira"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        stories = data.get('stories', [])
        project_key = data.get('project_key', '').strip()
        assignee_email = data.get('assignee_email', '').strip() or None
        
        if not stories or len(stories) == 0:
            return jsonify({"success": False, "error": "No se proporcionaron historias para subir"}), 400
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        # Obtener configuración de Jira del usuario
        from app.services.jira_token_manager import JiraTokenManager
        from app.auth.decorators import get_current_user_id
        from app.auth.user_service import UserService
        
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 401
        
        token_manager = JiraTokenManager()
        jira_config = token_manager.get_token_for_user(user, project_key)
        
        # Crear conexión y servicios
        from app.backend.jira.connection import JiraConnection
        from app.backend.jira.project_service import ProjectService
        from app.backend.jira.issue_service import IssueService
        
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        project_service = ProjectService(connection)
        issue_service = IssueService(connection, project_service)
        
        # Validar asignado si se proporciona
        assignee_account_id = None
        if assignee_email:
            assignee_account_id = issue_service.get_user_account_id_by_email(assignee_email)
            if not assignee_account_id:
                return jsonify({
                    "success": False,
                    "error": f"El correo {assignee_email} no tiene cuenta en Jira"
                }), 400
        
        # Convertir historias a formato CSV para usar create_issues_from_csv
        csv_data = []
        for story in stories:
            csv_row = {
                'Summary': story.get('summary', 'Sin título'),
                'Description': story.get('description', ''),
                'Issuetype': story.get('issuetype', 'Story'),
                'Priority': story.get('priority', 'Medium')
            }
            if assignee_account_id:
                # Para CSV, necesitamos el email, pero luego se convertirá a accountId
                csv_row['Asignado'] = assignee_email
            csv_data.append(csv_row)
        
        # Crear issues en Jira
        # Usar field_mappings para mapear correctamente
        field_mappings = {
            'Summary': 'summary',
            'Description': 'description',
            'Issuetype': 'issuetype',
            'Priority': 'priority'
        }
        if assignee_email:
            field_mappings['Asignado'] = 'assignee'
        
        # Crear issues usando el método existente
        # filter_issue_types=False para aceptar todos los tipos (incluyendo Story)
        results = issue_service.create_issues_from_csv(
            csv_data=csv_data,
            project_key=project_key,
            field_mappings=field_mappings,
            default_values={},
            filter_issue_types=False
        )
        
        # Calcular distribución de tipos de issue
        issue_types_distribution = {}
        for created in results.get('created', []):
            issue_type = created.get('issue_type', 'Unknown')
            issue_types_distribution[issue_type] = issue_types_distribution.get(issue_type, 0) + 1
        
        results['issue_types_distribution'] = issue_types_distribution
        
        # Generar archivo TXT de resumen (igual que carga masiva y casos de prueba)
        txt_content = generate_stories_upload_summary_txt(results, project_key, len(stories))
        txt_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
        txt_filename = f"stories_upload_{project_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        if results['success_count'] > 0:
            message = f"Se crearon {results['success_count']} de {results['total']} historias exitosamente"
            if results['error_count'] > 0:
                message += f". {results['error_count']} historias fallaron."
            
            return jsonify({
                "success": True,
                "message": message,
                "results": results,
                "txt_content": txt_base64,
                "txt_filename": txt_filename
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"No se pudo crear ninguna historia. Errores: {len(results['failed'])}",
                "results": results,
                "txt_content": txt_base64,
                "txt_filename": txt_filename
            }), 400
            
    except Exception as e:
        logger.error(f"Error al subir historias a Jira: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tests/upload-to-jira', methods=['POST'])
@login_required
def upload_test_cases_to_jira():
    """Sube casos de prueba directamente a Jira"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        test_cases = data.get('test_cases', [])
        project_key = data.get('project_key', '').strip()
        assignee_email = data.get('assignee_email', '').strip() or None
        
        # Valores de campos select desde el modal
        tipo_prueba_value = data.get('tipo_prueba', '').strip()
        nivel_prueba_value = data.get('nivel_prueba', '').strip()
        tipo_ejecucion_value = data.get('tipo_ejecucion', '').strip()
        ambiente_value = data.get('ambiente', '').strip()
        
        if not test_cases or len(test_cases) == 0:
            return jsonify({"success": False, "error": "No se proporcionaron casos de prueba para subir"}), 400
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        # Obtener configuración de Jira del usuario
        from app.services.jira_token_manager import JiraTokenManager
        from app.auth.decorators import get_current_user_id
        from app.auth.user_service import UserService
        
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 401
        
        token_manager = JiraTokenManager()
        jira_config = token_manager.get_token_for_user(user, project_key)
        
        # Crear conexión y servicios
        from app.backend.jira.connection import JiraConnection
        from app.backend.jira.project_service import ProjectService
        from app.backend.jira.issue_service import IssueService
        
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        project_service = ProjectService(connection)
        issue_service = IssueService(connection, project_service)
        
        # Validar asignado si se proporciona
        assignee_account_id = None
        if assignee_email:
            assignee_account_id = issue_service.get_user_account_id_by_email(assignee_email)
            if not assignee_account_id:
                return jsonify({
                    "success": False,
                    "error": f"El correo {assignee_email} no tiene cuenta en Jira"
                }), 400
        
        # Obtener nombres reales de campos de Jira para mapeo correcto
        fields_info = project_service.get_project_fields_for_creation(project_key, issue_type='Test Case')
        if not fields_info.get('success', True):
            logger.warning(f"No se pudieron obtener campos del proyecto para mapeo: {fields_info.get('error', 'Error desconocido')}")
            fields_info = {'required_fields': [], 'optional_fields': []}
        
        # Normalizar nombres para comparación
        def normalize_name(name: str) -> str:
            """Normaliza un nombre para comparación"""
            import unicodedata
            import re
            name = name.lower()
            name = unicodedata.normalize('NFD', name)
            name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
            name = re.sub(r'[^a-z0-9\s]', '', name)
            name = re.sub(r'\s+', ' ', name).strip()
            return name
        
        # Mapeo de campos internos a posibles nombres en Jira
        field_mapping_config = {
            'pasos': ['pasos', 'Pasos', 'Test Steps', 'Steps', 'Pasos de Prueba'],
            'resultado_esperado': ['resultado esperado', 'Resultado Esperado', 'Expected Result', 'Expected Results', 'Resultado'],
            'tipo_prueba': ['tipo de prueba', 'Tipo de Prueba', 'Test Type', 'Tipo Prueba'],
            'nivel_prueba': ['nivel de prueba', 'Nivel de Prueba', 'Test Level', 'Nivel Prueba'],
            'ambiente': ['ambiente', 'Ambiente', 'Environment', 'Entorno'],
            'tipo_ejecucion': ['tipo de ejecución', 'Tipo de Ejecución', 'Execution Type', 'Tipo Ejecución'],
            'ciclo': ['ciclo', 'Ciclo', 'Cycle', 'Test Cycle'],
            'precondiciones': ['precondiciones', 'Precondiciones', 'Preconditions', 'Precondición']
        }
        
        # Obtener todos los campos disponibles
        all_fields = fields_info.get('required_fields', []) + fields_info.get('optional_fields', [])
        
        # Crear diccionario de campos normalizados con sus IDs y nombres reales
        jira_field_names = {}
        jira_field_ids = {}  # Mapeo de nombre normalizado a ID del campo
        for field in all_fields:
            field_name = field.get('name', '')
            field_id = field.get('id', '')
            normalized = normalize_name(field_name)
            if normalized not in jira_field_names:
                jira_field_names[normalized] = {
                    'name': field_name,
                    'id': field_id
                }
                # También crear mapeo inverso: nombre real -> ID
                jira_field_ids[field_name] = field_id
        
        # Mapear campos internos a IDs y nombres reales de Jira
        internal_to_jira = {}  # Mapeo: internal_key -> {'name': nombre_real, 'id': field_id}
        for internal_key, possible_names in field_mapping_config.items():
            for possible_name in possible_names:
                normalized = normalize_name(possible_name)
                if normalized in jira_field_names:
                    field_info = jira_field_names[normalized]
                    internal_to_jira[internal_key] = {
                        'name': field_info['name'],
                        'id': field_info['id']
                    }
                    break
        
        # Convertir casos de prueba a formato CSV para usar create_issues_from_csv
        csv_data = []
        for test_case in test_cases:
            # Obtener raw_data para extraer campos personalizados
            raw_data = test_case.get('raw_data', {})
            
            # Construir descripción básica solo con Descripción (sin campos personalizados que van a sus campos)
            descripcion_basica = raw_data.get('Descripcion', '')
            if not descripcion_basica:
                # Si no hay descripción en raw_data, usar la del test_case pero limpiarla
                descripcion_completa = test_case.get('description', '')
                # Extraer solo la parte de "Descripción:" si existe
                if '* Descripción:' in descripcion_completa:
                    descripcion_basica = descripcion_completa.split('* Descripción:')[1].split('*')[0].strip()
                else:
                    descripcion_basica = descripcion_completa
            
            csv_row = {
                'Summary': test_case.get('summary', 'Sin título'),
                'Description': descripcion_basica,  # Solo descripción básica, sin campos personalizados
                'Issuetype': test_case.get('issuetype', 'Test Case'),
                'Priority': test_case.get('priority', 'Medium')
            }
            
            # Mapear campos personalizados a nombres reales de Jira (usar el nombre para el CSV)
            if 'pasos' in internal_to_jira:
                pasos = raw_data.get('Pasos', [])
                if pasos:
                    if isinstance(pasos, list):
                        pasos_text = '\n'.join([f"{i+1}. {paso}" for i, paso in enumerate(pasos) if paso])
                    else:
                        pasos_text = str(pasos)
                    csv_row[internal_to_jira['pasos']['name']] = pasos_text
            
            if 'resultado_esperado' in internal_to_jira:
                resultado_esperado = raw_data.get('Resultado_esperado', [])
                if resultado_esperado:
                    if isinstance(resultado_esperado, list):
                        resultado_text = '\n'.join([f"• {res}" for res in resultado_esperado if res])
                    else:
                        resultado_text = str(resultado_esperado)
                    csv_row[internal_to_jira['resultado_esperado']['name']] = resultado_text
            
            if 'precondiciones' in internal_to_jira:
                precondiciones = raw_data.get('Precondiciones', '')
                if precondiciones:
                    csv_row[internal_to_jira['precondiciones']['name']] = precondiciones
            
            if 'tipo_prueba' in internal_to_jira:
                # Usar valor del modal si existe, sino usar valor de raw_data, sino usar valor por defecto
                tipo_prueba = tipo_prueba_value or raw_data.get('Tipo_de_prueba', '') or 'Funcional'
                if tipo_prueba:
                    csv_row[internal_to_jira['tipo_prueba']['name']] = tipo_prueba
            
            if 'nivel_prueba' in internal_to_jira:
                # Usar valor del modal si existe, sino usar valor de raw_data, sino usar valor por defecto
                nivel_prueba = nivel_prueba_value or raw_data.get('Nivel_de_prueba', '') or 'UAT'
                if nivel_prueba:
                    csv_row[internal_to_jira['nivel_prueba']['name']] = nivel_prueba
            
            if 'ambiente' in internal_to_jira:
                # Usar valor del modal si existe, sino usar valor de raw_data, sino usar valor por defecto
                ambiente = ambiente_value or raw_data.get('Ambiente', '') or 'QA'
                if ambiente:
                    csv_row[internal_to_jira['ambiente']['name']] = ambiente
            
            if 'tipo_ejecucion' in internal_to_jira:
                # Usar valor del modal si existe, sino usar valor de raw_data
                tipo_ejecucion = tipo_ejecucion_value or raw_data.get('Tipo_de_ejecucion', '')
                if tipo_ejecucion:
                    csv_row[internal_to_jira['tipo_ejecucion']['name']] = tipo_ejecucion
            
            if 'ciclo' in internal_to_jira:
                ciclo = raw_data.get('Ciclo', '')
                if ciclo:
                    csv_row[internal_to_jira['ciclo']['name']] = ciclo
            
            if assignee_account_id:
                csv_row['Asignado'] = assignee_email
            
            csv_data.append(csv_row)
        
        # Crear issues en Jira
        field_mappings = {
            'Summary': 'summary',
            'Description': 'description',
            'Issuetype': 'issuetype',
            'Priority': 'priority'
        }
        
        # Agregar mapeos de campos personalizados
        # El mapeo debe ser: nombre_en_csv -> id_del_campo_en_jira
        for internal_key, field_info in internal_to_jira.items():
            jira_field_name = field_info['name']
            jira_field_id = field_info['id']
            # Mapear el nombre del campo en el CSV al ID del campo en Jira
            field_mappings[jira_field_name] = jira_field_id
        
        if assignee_email:
            field_mappings['Asignado'] = 'assignee'
        
        # Crear issues usando el método existente
        # filter_issue_types=False para aceptar todos los tipos (incluyendo Test Case)
        results = issue_service.create_issues_from_csv(
            csv_data=csv_data,
            project_key=project_key,
            field_mappings=field_mappings,
            default_values={},
            filter_issue_types=False
        )
        
        # Calcular distribución de tipos de issue
        issue_types_distribution = {}
        for created in results.get('created', []):
            issue_type = created.get('issue_type', 'Unknown')
            issue_types_distribution[issue_type] = issue_types_distribution.get(issue_type, 0) + 1
        
        results['issue_types_distribution'] = issue_types_distribution
        
        # Generar archivo TXT con resumen (similar a carga masiva)
        txt_content = generate_test_cases_upload_summary_txt(results, project_key, len(test_cases))
        txt_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
        txt_filename = f"test_cases_upload_{project_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Preparar mensaje de respuesta
        created_count = len(results.get('created', []))
        failed_count = len(results.get('failed', []))
        
        if created_count > 0:
            message = f"Se crearon {created_count} caso(s) de prueba exitosamente"
            if failed_count > 0:
                message += f" ({failed_count} fallaron)"
            
            return jsonify({
                "success": True,
                "message": message,
                "results": results,
                "txt_content": txt_base64,
                "txt_filename": txt_filename
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"No se pudo crear ningún caso de prueba. Errores: {failed_count}",
                "results": results,
                "txt_content": txt_base64,
                "txt_filename": txt_filename
            }), 400
            
    except Exception as e:
        logger.error(f"Error al subir casos de prueba a Jira: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/jira/upload-csv', methods=['POST'])
@login_required
def jira_upload_csv():
    """Procesa un archivo CSV y crea issues en Jira usando mapeos configurados"""
    try:
        
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No se proporcionó ningún archivo"}), 400
        
        file = request.files['file']
        project_key = request.form.get('project_key')
        field_mappings = request.form.get('field_mappings')  # JSON string con mapeos
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        if file.filename == '':
            return jsonify({"success": False, "error": "El archivo está vacío"}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({"success": False, "error": "El archivo debe ser un CSV"}), 400

        # Configuración Jira y validación de acceso según rol
        current_role = SessionService.get_current_user_role() or 'usuario'
        user = UserService().get_user_by_id(get_current_user_id())
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 401

        try:
            jira_config = JiraTokenManager().get_token_for_user(user, project_key)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )

        if current_role == 'usuario':
            session_email = SessionService.get_current_user_email() or ''
            membership = ProjectService(connection).check_user_membership(project_key, session_email)
            if not membership.get('hasAccess'):
                return jsonify({
                    "success": False,
                    "error": membership.get('message', "No tienes acceso a este proyecto. Contacta al administrador del proyecto en Jira.")
                }), 403
        
        # Leer el CSV con detección automática de encoding
        try:
            file.stream.seek(0)
            file_content = file.stream.read()
            file.stream.seek(0)
            
            # Lista de encodings a probar (en orden de preferencia)
            # Agregar más encodings comunes para español y Windows
            encodings_to_try = [
                'utf-8-sig',  # UTF-8 con BOM
                'utf-8',      # UTF-8 estándar
                'latin-1',     # ISO-8859-1 (compatible con todos los bytes)
                'cp1252',     # Windows-1252 (común en Windows)
                'windows-1252', # Windows-1252 alternativo
                'iso-8859-1',  # ISO-8859-1
                'cp850',       # DOS Latin-1
                'mac-roman',   # Mac Roman
            ]
            
            csv_data = None
            csv_reader = None
            successful_encoding = None
            
            # Primero intentar con errors='strict' para preservar caracteres especiales
            for encoding in encodings_to_try:
                try:
                    file.stream.seek(0)
                    stream = io.TextIOWrapper(file.stream, encoding=encoding, errors='strict')
                    csv_reader = csv.DictReader(stream)
                    # Intentar leer al menos una fila para validar
                    csv_data = list(csv_reader)
                    
                    # Validar que se leyeron datos correctamente
                    if csv_data and len(csv_data) > 0:
                        # Verificar que las columnas no estén vacías o corruptas
                        first_row = csv_data[0]
                        if first_row and any(first_row.values()):
                            successful_encoding = encoding
                            logger.info(f"CSV leído exitosamente con encoding: {encoding}, {len(csv_data)} filas")
                            break
                except (UnicodeDecodeError, UnicodeError) as e:
                    logger.debug(f"Error con encoding {encoding} (strict): {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Error inesperado con encoding {encoding}: {e}")
                    continue
            
            # Si no funcionó con strict, intentar con errors='ignore' (mejor que 'replace' para preservar caracteres)
            if csv_data is None or successful_encoding is None:
                logger.warn("Intentando lectura con manejo de errores más permisivo (ignore)...")
                for encoding in ['utf-8', 'latin-1', 'cp1252', 'windows-1252']:
                    try:
                        file.stream.seek(0)
                        stream = io.TextIOWrapper(file.stream, encoding=encoding, errors='ignore')
                        csv_reader = csv.DictReader(stream)
                        csv_data = list(csv_reader)
                        if csv_data and len(csv_data) > 0:
                            successful_encoding = encoding
                            logger.info(f"CSV leído con encoding {encoding} usando errors='ignore', {len(csv_data)} filas")
                            break
                    except Exception as e:
                        logger.debug(f"Error con encoding {encoding} y errors='ignore': {e}")
                        continue
            
            # Último recurso: usar 'replace' solo si todo lo demás falla
            if csv_data is None or successful_encoding is None:
                logger.warn("Último intento con errors='replace' (puede perder algunos caracteres)...")
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        file.stream.seek(0)
                        stream = io.TextIOWrapper(file.stream, encoding=encoding, errors='replace')
                        csv_reader = csv.DictReader(stream)
                        csv_data = list(csv_reader)
                        if csv_data and len(csv_data) > 0:
                            successful_encoding = encoding
                            logger.warn(f"CSV leído con encoding {encoding} usando errors='replace' (algunos caracteres pueden perderse), {len(csv_data)} filas")
                            break
                    except Exception as e:
                        logger.debug(f"Error con encoding {encoding} y errors='replace': {e}")
                        continue
            
            if csv_data is None or successful_encoding is None:
                raise Exception("No se pudo leer el CSV con ningún encoding conocido. El archivo puede estar corrupto o usar un encoding no estándar. Intenta guardar el archivo como UTF-8.")
            
            # Logging para debug: mostrar las columnas detectadas y primeras filas
            if csv_reader.fieldnames:
                logger.info(f"Columnas detectadas en CSV: {csv_reader.fieldnames}")
            
            # Logging adicional: mostrar qué valores tiene la columna de tipo
            if csv_data:
                logger.info(f"Total de filas leídas: {len(csv_data)}")
                for idx, row in enumerate(csv_data[:3], 1):  # Mostrar primeras 3 filas
                    tipo_raw = row.get('Tipo de Issue') or row.get('Tipo') or row.get('tipo de issue') or row.get('TIPO DE ISSUE')
                    logger.info(f"Fila {idx} - Valores de tipo encontrados: 'Tipo de Issue'={repr(row.get('Tipo de Issue'))}, 'Tipo'={repr(row.get('Tipo'))}, raw={repr(tipo_raw)}")
                    logger.info(f"Fila {idx} - Todas las claves del row: {list(row.keys())}")
                    logger.info(f"Fila {idx} - Primera fila completa: {dict(row)}")
        except Exception as e:
            logger.error(f"Error al leer CSV: {e}", exc_info=True)
            return jsonify({"success": False, "error": f"Error al leer el archivo CSV: {str(e)}"}), 400
        
        if not csv_data:
            return jsonify({"success": False, "error": "El archivo CSV está vacío o no tiene datos válidos"}), 400
        
        # Parsear field_mappings y default_values
        field_mappings = {}
        default_values = {}
        field_mappings = {}
        try:
            if request.form.get('field_mappings'):
                field_mappings_raw = json.loads(request.form.get('field_mappings'))
                # Transformar el mapeo: el frontend envía objetos con jira_field_id, necesitamos solo el ID
                for csv_field, jira_field_data in field_mappings_raw.items():
                    if isinstance(jira_field_data, dict) and 'jira_field_id' in jira_field_data:
                        field_mappings[csv_field] = jira_field_data['jira_field_id']
                    elif isinstance(jira_field_data, str):
                        # Si ya es un string (ID), usarlo directamente
                        field_mappings[csv_field] = jira_field_data
            if request.form.get('default_values'):
                default_values = json.loads(request.form.get('default_values'))
        except json.JSONDecodeError as e:
            logger.warning(f"Error al parsear mapeos o valores por defecto: {e}")
        
        # Crear issues en Jira usando la conexión del usuario (o compartida)
        client = jira_backend.JiraClient(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        # filter_issue_types=False para aceptar Test Cases, Bugs y Stories
        results = client.create_issues_from_csv(csv_data, project_key, field_mappings, default_values, filter_issue_types=False)
        
        # Calcular distribución de tipos de issue para métricas
        issue_types_distribution = {}
        for created in results.get('created', []):
            issue_type = created.get('issue_type', 'Unknown')
            issue_types_distribution[issue_type] = issue_types_distribution.get(issue_type, 0) + 1
        
        # Agregar distribución de tipos al resultado
        results['issue_types_distribution'] = issue_types_distribution
        
        # Generar archivo TXT con el resumen (siempre, incluso si hay errores)
        txt_content = generate_upload_summary_txt(file.filename, results, project_key)
        
        # Retornar el contenido del TXT como base64 para descarga
        txt_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
        
        # Guardar en base de datos local para historial de actividades
        try:
            user_id = get_current_user_id()
            upload_type = 'csv_upload'  # Tipo genérico para carga CSV
            
            bulk_upload = BulkUpload(
                user_id=user_id,
                project_key=project_key,
                upload_type=upload_type,
                total_items=results['total'],
                successful_items=results['success_count'],
                failed_items=results['error_count'],
                upload_details=json.dumps({
                    'filename': file.filename,
                    'created_keys': [c.get('key') for c in results.get('created', [])],
                    'failed_summaries': [f.get('summary') for f in results.get('failed', [])],
                    'issue_types_distribution': issue_types_distribution  # Agregar distribución de tipos para gráficas
                }, ensure_ascii=False)
            )
            upload_repo = BulkUploadRepository()
            upload_repo.create(bulk_upload)
            
            logger.info(f"Carga masiva guardada en BD local: {results['success_count']}/{results['total']} para user_id={user_id}")
        except Exception as e:
            logger.error(f"Error al guardar carga masiva en BD local: {e}", exc_info=True)
            # No fallar la operación si falla el guardado en BD local
        
        if results['success_count'] > 0:
            message = f"Se crearon {results['success_count']} de {results['total']} issues exitosamente"
            if results['error_count'] > 0:
                message += f". {results['error_count']} issues fallaron."
            
            return jsonify({
                "success": True,
                "message": message,
                "results": results,
                "txt_content": txt_base64,
                "txt_filename": file.filename.replace('.csv', '').replace('.CSV', '') + '.txt'
            })
        else:
            return jsonify({
                "success": False,
                "error": f"No se pudo crear ningún issue. Errores: {len(results['failed'])}",
                "results": results,
                "txt_content": txt_base64,
                "txt_filename": file.filename.replace('.csv', '').replace('.CSV', '') + '.txt'
            }), 400
            
    except Exception as e:
        logger.error(f"Error al procesar CSV para Jira: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


def generate_stories_upload_summary_txt(results: Dict, project_key: str, total_stories: int) -> str:
    """Genera el contenido del archivo TXT con el resumen de la carga de historias"""
    
    # Fecha y hora actual
    now = datetime.now()
    fecha_hora = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Construir el contenido del TXT (igual que carga masiva)
    lines = []
    lines.append(f"Procesado: {fecha_hora}")
    lines.append(f"Archivo: Historias de Usuario")
    lines.append("--------------------------------------------------")
    
    # Listar historias creadas exitosamente
    for idx, created in enumerate(results.get('created', []), start=1):
        row_num = created.get('row', idx)
        key = created.get('key', 'N/A')
        summary = created.get('summary', 'Sin resumen')
        lines.append(f"{idx}. [OK] {summary} --> {key}")
    
    # Listar errores si los hay
    if results.get('failed'):
        lines.append("")
        for failed in results.get('failed', []):
            row_num = failed.get('row', '?')
            error = failed.get('error', 'Error desconocido')
            summary = failed.get('summary', 'Sin resumen')
            lines.append(f"[ERROR] Fila {row_num}: {summary} --> Error: {error}")
    
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Resumen del procesamiento de Historias de Usuario:")
    lines.append(f"  [OK] Exitos: {results.get('success_count', 0)}")
    lines.append(f"  [ERROR] Errores: {results.get('error_count', 0)}")
    lines.append(f"  [OK] Total de registros: {results.get('total', 0)}")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("Query para buscar en Jira")
    lines.append("")
    
    # Generar query JQL si hay historias creadas
    created_keys = [c.get('key') for c in results.get('created', []) if c.get('key')]
    if created_keys:
        # Ordenar keys para obtener el primero y último
        sorted_keys = sorted(created_keys)
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        lines.append(f'PROJECT = {project_key} and key <= "{last_key}" and key >= "{first_key}"')
    else:
        lines.append(f'PROJECT = {project_key}')
    
    return '\n'.join(lines)


def generate_test_cases_upload_summary_txt(results: Dict, project_key: str, total_cases: int) -> str:
    """Genera el contenido del archivo TXT con el resumen de la carga de casos de prueba"""
    
    # Fecha y hora actual
    now = datetime.now()
    fecha_hora = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Construir el contenido del TXT (igual que carga masiva)
    lines = []
    lines.append(f"Procesado: {fecha_hora}")
    lines.append(f"Archivo: Casos de Prueba")
    lines.append("--------------------------------------------------")
    
    # Listar casos creados exitosamente
    for idx, created in enumerate(results.get('created', []), start=1):
        row_num = created.get('row', idx)
        key = created.get('key', 'N/A')
        summary = created.get('summary', 'Sin resumen')
        lines.append(f"{idx}. [OK] {summary} --> {key}")
    
    # Listar errores si los hay
    if results.get('failed'):
        lines.append("")
        for failed in results.get('failed', []):
            row_num = failed.get('row', '?')
            error = failed.get('error', 'Error desconocido')
            summary = failed.get('summary', 'Sin resumen')
            lines.append(f"[ERROR] Fila {row_num}: {summary} --> Error: {error}")
    
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Resumen del procesamiento de Casos de Prueba:")
    lines.append(f"  [OK] Exitos: {results.get('success_count', 0)}")
    lines.append(f"  [ERROR] Errores: {results.get('error_count', 0)}")
    lines.append(f"  [OK] Total de registros: {total_cases}")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("Query para buscar en Jira")
    lines.append("")
    
    # Generar query JQL si hay casos creados
    created_keys = [c.get('key') for c in results.get('created', []) if c.get('key')]
    if created_keys:
        # Ordenar keys para obtener el primero y último
        sorted_keys = sorted(created_keys)
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        lines.append(f'PROJECT = {project_key} and key <= "{last_key}" and key >= "{first_key}"')
    else:
        lines.append(f'PROJECT = {project_key}')
    
    return '\n'.join(lines)


def generate_upload_summary_txt(csv_filename: str, results: Dict, project_key: str) -> str:
    """Genera el contenido del archivo TXT con el resumen de la carga"""
    
    # Obtener nombre base del archivo (sin extensión)
    base_filename = csv_filename.replace('.csv', '').replace('.CSV', '')
    
    # Fecha y hora actual
    now = datetime.now()
    fecha_hora = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Construir el contenido del TXT
    lines = []
    lines.append(f"Procesado: {fecha_hora}")
    lines.append(f"Archivo: {csv_filename}")
    lines.append("--------------------------------------------------")
    
    # Listar issues creados exitosamente
    for idx, created in enumerate(results.get('created', []), start=1):
        row_num = created.get('row', idx)
        key = created.get('key', 'N/A')
        summary = created.get('summary', 'Sin resumen')
        lines.append(f"{idx}. [OK] {summary} --> {key}")
    
    # Listar errores si los hay
    if results.get('failed'):
        lines.append("")
        for failed in results.get('failed', []):
            row_num = failed.get('row', '?')
            error = failed.get('error', 'Error desconocido')
            summary = failed.get('summary', 'Sin resumen')
            lines.append(f"[ERROR] Fila {row_num}: {summary} --> Error: {error}")
    
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Resumen del procesamiento de {csv_filename}:")
    lines.append(f"  [OK] Exitos: {results.get('success_count', 0)}")
    lines.append(f"  [ERROR] Errores: {results.get('error_count', 0)}")
    lines.append(f"  [OK] Total de registros: {results.get('total', 0)}")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("Query para buscar en Jira")
    lines.append("")
    
    # Generar query JQL si hay issues creados
    created_keys = [c.get('key') for c in results.get('created', []) if c.get('key')]
    if created_keys:
        # Ordenar keys para obtener el primero y último
        sorted_keys = sorted(created_keys)
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        lines.append(f'PROJECT = {project_key} and key <= "{last_key}" and key >= "{first_key}"')
    else:
        lines.append(f'PROJECT = {project_key}')
    
    return '\n'.join(lines)


@app.route('/api/jira/download-report', methods=['POST'])
@login_required
def jira_download_report():
    """Genera y descarga un reporte de Jira en formato PDF usando Playwright"""
    try:
        
        data = request.get_json()
        project_key = data.get('project_key')
        format_type = data.get('format', 'pdf')
        chart_images = data.get('chart_images', {})
        table_data = data.get('table_data', {})
        active_widgets = data.get('active_widgets', [])
        widget_chart_images = data.get('widget_chart_images', {})
        widget_data = data.get('widget_data', {})
        filters = data.get('filters', {})  # Filtros aplicados en el frontend
        
        if not project_key:
            return jsonify({"success": False, "error": "No se proporcionó la clave del proyecto"}), 400
        
        if format_type != 'pdf':
            return jsonify({"success": False, "error": "Formato no soportado. Use 'pdf'"}), 400
        
        # Construir reporte desde los datos del frontend (ya incluyen filtros aplicados)
        # Si no hay datos del frontend, obtener métricas básicas
        if table_data and (table_data.get('test_cases_by_person') or table_data.get('defects_by_person')):
            # Usar datos del frontend que ya tienen filtros aplicados
            report = {
                'total_test_cases': sum(item.get('total', 0) for item in table_data.get('test_cases_by_person', [])),
                'total_defects': len(table_data.get('defects_by_person', []))
            }
        else:
            # Fallback: obtener métricas básicas del proyecto
            try:
                client = jira_backend.JiraClient()
                metrics = client.get_project_metrics(project_key)
                if not metrics.get('general_report'):
                    return jsonify({"success": False, "error": "No se pudieron obtener las métricas del proyecto"}), 400
                report = metrics['general_report']
            except Exception as e:
                logger.error(f"Error al obtener métricas para PDF: {e}", exc_info=True)
                # Crear reporte básico si falla
                report = {
                    'total_test_cases': 0,
                    'total_defects': 0
                }
        
        # Limitar datos a solo los primeros 20 registros para cada tabla
        items_per_page = 20
        
        # Procesar tabla de test cases: solo primeros 20 registros
        test_cases_paginated = []
        test_cases_total = 0
        test_cases_totals = {
            'exitoso': 0,
            'en_progreso': 0,
            'fallado': 0,
            'total': 0
        }
        if table_data.get('test_cases_by_person'):
            test_cases_total = len(table_data['test_cases_by_person'])
            test_cases_paginated = table_data['test_cases_by_person'][:items_per_page]
            # Calcular totales de TODOS los registros (no solo los mostrados)
            for item in table_data['test_cases_by_person']:
                test_cases_totals['exitoso'] += item.get('exitoso', 0) or 0
                test_cases_totals['en_progreso'] += item.get('en_progreso', 0) or 0
                test_cases_totals['fallado'] += item.get('fallado', 0) or 0
                test_cases_totals['total'] += item.get('total', 0) or 0
        
        # Calcular información de paginación para test cases
        test_cases_pagination = {
            'current_page': 1,
            'total_items': test_cases_total,
            'items_per_page': items_per_page,
            'total_pages': (test_cases_total + items_per_page - 1) // items_per_page if test_cases_total > 0 else 0,
            'start_item': 1 if test_cases_total > 0 else 0,
            'end_item': min(items_per_page, test_cases_total) if test_cases_total > 0 else 0
        }
        
        # Procesar tabla de defectos: solo primeros 20 registros
        defects_paginated = []
        defects_total = 0
        if table_data.get('defects_by_person'):
            defects_total = len(table_data['defects_by_person'])
            defects_paginated = table_data['defects_by_person'][:items_per_page]
        
        # Calcular información de paginación para defectos
        defects_pagination = {
            'current_page': 1,
            'total_items': defects_total,
            'items_per_page': items_per_page,
            'total_pages': (defects_total + items_per_page - 1) // items_per_page if defects_total > 0 else 0,
            'start_item': 1 if defects_total > 0 else 0,
            'end_item': min(items_per_page, defects_total) if defects_total > 0 else 0
        }
        
        # Renderizar HTML del reporte
        html_content = render_template('jira_report.html', 
                                     project_key=project_key,
                                     report=report,
                                     chart_images=chart_images,
                                     test_cases_data=test_cases_paginated,
                                     test_cases_totals=test_cases_totals,
                                     test_cases_pagination=test_cases_pagination,
                                     defects_data=defects_paginated,
                                     defects_pagination=defects_pagination,
                                     active_widgets=active_widgets,
                                     widget_chart_images=widget_chart_images,
                                     widget_data=widget_data,
                                     date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Generar PDF usando Playwright
        logger.info(f"Iniciando generación de PDF para proyecto {project_key}")
        
        with sync_playwright() as p:
            logger.info("Lanzando navegador Chromium...")
            
            # Configuración del navegador con opciones adicionales para Windows
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            logger.info("Navegador lanzado, creando nueva página...")
            page = browser.new_page()
            
            # Configurar timeout más corto
            page.set_default_timeout(30000)  # 30 segundos
            
            # Cargar el HTML en la página
            logger.info("Cargando contenido HTML...")
            try:
                page.set_content(html_content, wait_until='domcontentloaded', timeout=15000)
            except Exception as load_error:
                logger.warning(f"Advertencia al cargar contenido: {load_error}")
                # Intentar con un método más simple
                page.set_content(html_content)
            
            # Esperar a que los gráficos se rendericen (si hay imágenes)
            if chart_images:
                logger.info("Esperando a que se carguen las imágenes...")
                page.wait_for_timeout(1500)  # Esperar 1.5 segundos para que las imágenes se carguen
            else:
                page.wait_for_timeout(500)  # Esperar medio segundo para renderizado básico
            
            # Generar PDF en formato landscape para que quepa en una sola página
            logger.info("Generando PDF...")
            pdf_buffer = page.pdf(
                format='A4',
                landscape=True,
                print_background=True,
                margin={'top': '10mm', 'right': '10mm', 'bottom': '10mm', 'left': '10mm'},
                prefer_css_page_size=False
            )
            
            logger.info(f"PDF generado exitosamente, tamaño: {len(pdf_buffer)} bytes")
            browser.close()
            
            # Guardar reporte en base de datos local para métricas por usuario
            try:
                user_id = get_current_user_id()
                report_repo = JiraReportRepository()
                
                # Crear registro del reporte descargado
                jira_report = JiraReport(
                    user_id=user_id,
                    project_key=project_key,
                    report_type='pdf_report',  # Tipo específico para reportes PDF descargados
                    report_title=f'Reporte PDF - {project_key}',
                    report_content=json.dumps({
                        'total_test_cases': report.get('total_test_cases', 0),
                        'total_defects': report.get('total_defects', 0),
                        'filters': filters,
                        'active_widgets': active_widgets,
                        'generated_at': datetime.now().isoformat()
                    }, ensure_ascii=False),
                    jira_issue_key='N/A'  # Reportes PDF son locales, no se suben a Jira
                )
                report_repo.create(jira_report)
                logger.info(f"Reporte PDF guardado en BD local para user_id={user_id}, proyecto={project_key}")
            except Exception as e:
                logger.error(f"Error al guardar reporte PDF en BD local: {e}", exc_info=True)
                # No fallar la operación si falla el guardado en BD local
            
            return Response(
                pdf_buffer,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename=reporte_jira_{project_key}_{datetime.now().strftime("%Y%m%d")}.pdf'
                }
            )
            
    except ImportError as ie:
        logger.error(f"ImportError - Playwright no está instalado: {ie}", exc_info=True)
        return jsonify({"success": False, "error": "Playwright no está instalado. Instala con: pip install playwright && playwright install chromium"}), 500
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error al generar reporte de Jira con Playwright: {error_msg}", exc_info=True)
        
        # Mensajes de error más específicos
        if "Target page, context or browser has been closed" in error_msg:
            error_msg = "El navegador se cerró inesperadamente. Intenta nuevamente."
        elif "Executable doesn't exist" in error_msg or "Failed to launch" in error_msg:
            error_msg = "Chromium no está instalado. Ejecuta: playwright install chromium"
        elif "timeout" in error_msg.lower():
            error_msg = "Tiempo de espera agotado al generar el PDF. Intenta con menos datos."
        
        return jsonify({"success": False, "error": error_msg}), 500


@app.route('/api/metrics/download-report', methods=['POST'])
@login_required
def metrics_download_report():
    """Genera y descarga un reporte de métricas en formato PDF usando Playwright"""
    try:
        
        data = request.get_json()
        selected_types = data.get('selected_types', [])
        generator_metrics = data.get('generator_metrics', {})
        jira_metrics = data.get('jira_metrics', {})
        chart_images = data.get('chart_images', {})
        
        if not selected_types:
            return jsonify({"success": False, "error": "No se seleccionaron tipos de métricas"}), 400
        
        # Renderizar HTML del reporte de métricas
        html_content = render_template('metrics_report.html', 
                                     selected_types=selected_types,
                                     generator_metrics=generator_metrics,
                                     jira_metrics=jira_metrics,
                                     chart_images=chart_images,
                                     date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Generar PDF usando Playwright
        logger.info("Iniciando generación de PDF de métricas")
        
        with sync_playwright() as p:
            logger.info("Lanzando navegador Chromium...")
            
            # Configuración del navegador con opciones adicionales para Windows
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            logger.info("Navegador lanzado, creando nueva página...")
            page = browser.new_page()
            
            # Configurar timeout más corto
            page.set_default_timeout(30000)  # 30 segundos
            
            # Cargar el HTML en la página
            logger.info("Cargando contenido HTML...")
            try:
                page.set_content(html_content, wait_until='domcontentloaded', timeout=15000)
            except Exception as load_error:
                logger.warning(f"Advertencia al cargar contenido: {load_error}")
                # Intentar con un método más simple
                page.set_content(html_content)
            
            # Esperar a que los gráficos se rendericen (si hay imágenes)
            if chart_images:
                logger.info("Esperando a que se carguen las imágenes...")
                page.wait_for_timeout(1500)
            else:
                page.wait_for_timeout(500)  # Esperar medio segundo para renderizado básico
            
            # Generar PDF en formato landscape
            logger.info("Generando PDF...")
            pdf_buffer = page.pdf(
                format='A4',
                landscape=True,
                print_background=True,
                margin={'top': '10mm', 'right': '10mm', 'bottom': '10mm', 'left': '10mm'},
                prefer_css_page_size=False
            )
            
            logger.info(f"PDF generado exitosamente, tamaño: {len(pdf_buffer)} bytes")
            browser.close()
            
            return Response(
                pdf_buffer,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename=metricas_nexus_ai_{datetime.now().strftime("%Y%m%d")}.pdf'
                }
            )
            
    except ImportError as ie:
        logger.error(f"ImportError - Playwright no está instalado: {ie}", exc_info=True)
        return jsonify({"success": False, "error": "Playwright no está instalado. Instala con: pip install playwright && playwright install chromium"}), 500
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error al generar reporte de métricas con Playwright: {error_msg}", exc_info=True)
        
        # Mensajes de error más específicos
        if "Target page, context or browser has been closed" in error_msg:
            error_msg = "El navegador se cerró inesperadamente. Intenta nuevamente."
        elif "Executable doesn't exist" in error_msg or "Failed to launch" in error_msg:
            error_msg = "Chromium no está instalado. Ejecuta: playwright install chromium"
        elif "timeout" in error_msg.lower():
            error_msg = "Tiempo de espera agotado al generar el PDF. Intenta con menos datos."
        
        return jsonify({"success": False, "error": error_msg}), 500


@app.route('/api/jira/download-template', methods=['GET'])
@login_required
def jira_download_template():
    """Descarga una plantilla CSV de ejemplo para carga masiva (requiere autenticación)"""
    try:
        
        # Obtener project_key de los parámetros (opcional)
        project_key = request.args.get('project_key', None)
        
        # Valores por defecto si no se proporciona project_key
        story_type = 'Story'
        test_case_type = 'Test Case'
        bug_type = 'Bug'
        
        # Si se proporciona project_key, obtener los tipos reales del proyecto
        if project_key:
            try:
                client = jira_backend.JiraClient()
                issue_types = client.get_issue_types(project_key)
                
                if issue_types:
                    # Buscar los tipos más comunes
                    type_names = [it.get('name', '') for it in issue_types]
                    
                    # Buscar Story
                    for name in type_names:
                        if 'story' in name.lower():
                            story_type = name
                            break
                    
                    # Buscar Test Case
                    for name in type_names:
                        if 'test' in name.lower() and 'case' in name.lower():
                            test_case_type = name
                            break
                        elif 'test case' in name.lower():
                            test_case_type = name
                            break
                    
                    # Buscar Bug
                    for name in type_names:
                        if 'bug' in name.lower():
                            bug_type = name
                            break
            except Exception as e:
                logger.warning(f"No se pudieron obtener tipos de issue del proyecto {project_key}: {e}")
                # Continuar con valores por defecto
        
        # Crear el contenido del CSV de ejemplo
        output = io.StringIO()
        fieldnames = ['Tipo de Issue', 'Resumen', 'Descripción', 'Prioridad', 'Labels']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        # Agregar ejemplos con los tipos reales del proyecto
        writer.writerow({
            'Tipo de Issue': story_type,
            'Resumen': 'Ejemplo de historia de usuario',
            'Descripción': 'Esta es una descripción de ejemplo para una historia de usuario',
            'Prioridad': 'High',
            'Labels': 'ejemplo,historia'
        })
        writer.writerow({
            'Tipo de Issue': test_case_type,
            'Resumen': 'Ejemplo de caso de prueba',
            'Descripción': 'Esta es una descripción de ejemplo para un caso de prueba',
            'Prioridad': 'Medium',
            'Labels': 'ejemplo,prueba'
        })
        writer.writerow({
            'Tipo de Issue': bug_type,
            'Resumen': 'Ejemplo de bug',
            'Descripción': 'Esta es una descripción de ejemplo para un bug',
            'Prioridad': 'High',
            'Labels': 'ejemplo,bug'
        })
        
        # Convertir a bytes
        csv_bytes = output.getvalue().encode('utf-8-sig')  # UTF-8 con BOM para Excel
        output.close()
        
        # Crear respuesta
        return send_file(
            io.BytesIO(csv_bytes),
            mimetype='text/csv',
            as_attachment=True,
            download_name='plantilla_carga_masiva_jira.csv'
        )
        
    except Exception as e:
        logger.error(f"Error al generar plantilla CSV: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# FEEDBACK - Endpoints para gestionar feedback de usuarios
# ============================================================================



@app.route('/api/feedback/validate-project', methods=['POST'])
@login_required
@handle_errors("Error al validar proyecto", status_code=500)
def feedback_validate_project():
    """
    Valida que el proyecto seleccionado sea válido para feedback
    """
    try:
        from app.services.feedback_service import FeedbackService
        from app.utils.exceptions import ValidationError
        from app.auth.user_service import UserService
        
        data = request.get_json()
        project_key = data.get('project_key', '').strip()
        
        if not project_key:
            return jsonify({
                "success": False,
                "error": "Debe proporcionar una clave de proyecto"
            }), 400
        
        # Obtener usuario actual
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "Usuario no encontrado"
            }), 400
        
        # Obtener configuración de Jira del usuario
        token_manager = JiraTokenManager()
        
        try:
            jira_config = token_manager.get_token_for_user(user, project_key)
        except Exception as e:
            logger.warning(f"No se pudo obtener configuración de Jira: {e}")
            return jsonify({
                "success": False,
                "error": "No se encontró configuración de Jira para este proyecto"
            }), 400
        
        # Crear conexión
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        # Validar proyecto
        feedback_service = FeedbackService(connection)
        is_valid = feedback_service.validate_project(project_key)
        
        return jsonify({
            "success": True,
            "valid": is_valid,
            "message": f"Proyecto '{project_key}' validado correctamente"
        })
        
    except ValidationError as e:
        return jsonify({
            "success": False,
            "valid": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error al validar proyecto: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/feedback/submit', methods=['POST'])
@login_required
@handle_errors("Error al enviar feedback", status_code=500)
def feedback_submit():
    """
    Envía feedback creando un issue (Bug o Task) en Jira
    """
    try:
        from app.services.feedback_service import FeedbackService
        from app.utils.exceptions import ValidationError
        from app.auth.user_service import UserService
        
        data = request.get_json()
        
        # Extraer datos
        project_key = data.get('project_key', '').strip()
        issue_type = data.get('issue_type', '').strip()
        summary = data.get('summary', '').strip()
        description = data.get('description', '').strip()
        
        # Validar datos requeridos
        if not all([project_key, issue_type, summary, description]):
            return jsonify({
                "success": False,
                "error": "Todos los campos son obligatorios"
            }), 400
        
        # Obtener usuario actual
        user_service = UserService()
        user_id = get_current_user_id()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "Usuario no encontrado"
            }), 400
        
        user_email = user.email
        
        # Obtener configuración de Jira del usuario
        token_manager = JiraTokenManager()
        
        try:
            jira_config = token_manager.get_token_for_user(user, project_key)
        except Exception as e:
            logger.warning(f"No se pudo obtener configuración de Jira: {e}")
            return jsonify({
                "success": False,
                "error": "No se encontró configuración de Jira para este proyecto"
            }), 400
        
        # Crear conexión
        connection = JiraConnection(
            base_url=jira_config.base_url,
            email=jira_config.email,
            api_token=jira_config.token
        )
        
        # Crear feedback
        feedback_service = FeedbackService(connection)
        result = feedback_service.create_feedback_issue(
            project_key=project_key,
            issue_type=issue_type,
            summary=summary,
            description=description,
            user_email=user_email
        )
        
        logger.info(f"Feedback enviado por usuario {user_email}: {result.get('issue_key')}")
        
        return jsonify(result)
        
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error al enviar feedback: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Error al enviar feedback: {str(e)}"
        }), 500


# ============================================================================
# CONFIGURACIÓN PARA PRODUCCIÓN
# ============================================================================

if __name__ == '__main__':
    port = Config.FLASK_PORT
    app.run(host=Config.FLASK_HOST, port=port, debug=False)