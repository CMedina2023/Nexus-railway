from flask import Flask, render_template, request, jsonify, send_file, redirect, Response, stream_with_context
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import io
import zipfile
import logging

from dotenv import load_dotenv
from datetime import timedelta
import json
import pathlib



# Imports de la estructura modular
from app.core.config import Config
from app.backend import story_backend, matrix_backend
from app.backend.agent_manager import simple_agent_processing
from app.utils.file_utils import extract_text_from_file
from app.utils.decorators import validate_file_upload, handle_errors

# Imports de autenticación
from app.auth.routes import auth_bp, init_rate_limiter
from app.auth.decorators import login_required
from app.services.jira.api.routes import jira_bp
from app.services.dashboard.api.routes import dashboard_bp
from app.services.feedback.api.routes import feedback_bp
from app.database import init_db

from app.services.file_manager import FileManager
from app.services.data_transformer import DataTransformer
from app.services.validator import Validator
from app.services.file_generator import FileGenerator
from app.services.generation_orchestrator import GenerationOrchestrator

load_dotenv()

# Obtener la ruta base del proyecto (dos niveles arriba de app/core/)
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

# Inicializar servicios y orquestador (vía Dependency Injection)
from app.core.dependencies import get_file_manager, get_generation_orchestrator
file_manager = get_file_manager(UPLOAD_FOLDER)
orchestrator = get_generation_orchestrator(file_manager)


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
app.register_blueprint(dashboard_bp)
app.register_blueprint(jira_bp)
app.register_blueprint(feedback_bp)
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

def clean_temp_files(filepath):
    """Limpia archivos temporales de forma segura"""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Archivo temporal eliminado: {filepath}")
    except Exception as e:
        logger.warning(f"No se pudo eliminar archivo temporal {filepath}: {e}")


# ============================================================================
# API ENDPOINTS CON MANEJO DE ERRORES
# ============================================================================

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

        # Generar historias usando el orquestador con SSE
        parameters = {
            'role': role,
            'business_context': business_context,
            'story_type': story_type,
            'area': request.form.get('area', 'General')
        }
        
        return Response(
            stream_with_context(orchestrator.stream_generation_pipeline(
                'story', 
                document_text, 
                parameters, 
                output_filename, 
                filepath, 
                simple_agent_processing,
                story_backend
            )),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.error(f"Error en generate_stories: {e}", exc_info=True)
        if filepath:
            clean_temp_files(filepath)
        return jsonify({"error": f"Error en el procesamiento: {str(e)}"}), 500


@app.route('/api/tests/generate', methods=['POST'])
@login_required
@validate_file_upload
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

        # Generar pruebas usando el orquestador con SSE
        parameters = {
            'contexto': context,
            'flujo': flow,
            'test_types': test_types,
            'area': request.form.get('area', 'General')
        }
        
        return Response(
            stream_with_context(orchestrator.stream_generation_pipeline(
                'matrix', 
                text, 
                parameters, 
                'matriz_pruebas', 
                filepath, 
                simple_agent_processing
            )),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.error(f"Error en generate_tests: {e}", exc_info=True)
        if filepath:
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
# CONFIGURACIÓN PARA PRODUCCIÓN
# ============================================================================

if __name__ == '__main__':
    port = Config.FLASK_PORT
    app.run(host=Config.FLASK_HOST, port=port, debug=False)