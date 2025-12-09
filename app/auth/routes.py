"""
Rutas de autenticación
Responsabilidad única: Endpoints de login/logout (SRP)
"""
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, has_request_context
from flask_limiter.util import get_remote_address

from app.auth.user_service import UserService
from app.auth.session_service import SessionService
from app.auth.password_service import PasswordService
from app.utils.exceptions import ValidationError
from app.core.config import Config

logger = logging.getLogger(__name__)

def get_remote_address_safe():
    """Obtiene la dirección remota de forma segura"""
    if has_request_context():
        return get_remote_address()
    return '127.0.0.1'

# Crear Blueprint para rutas de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Inicializar rate limiter (se configurará en app.py)
limiter = None


def init_rate_limiter(app_instance):
    """
    Inicializa el rate limiter con la app Flask
    
    Args:
        app_instance: Instancia de Flask app
    """
    global limiter
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app=app_instance,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    logger.info("Rate limiter inicializado")


def limit_login():
    """Decorador condicional para rate limiting"""
    if limiter:
        return limiter.limit("5 per minute")
    return lambda f: f

@auth_bp.route('/login', methods=['GET', 'POST'])
@limit_login()
def login():
    """
    Endpoint de login
    
    GET: Muestra formulario de login
    POST: Procesa login
    
    ✅ Rate limiting (5 intentos por minuto)
    ✅ Validación de entrada
    ✅ Mensajes genéricos de error
    ✅ Logging de seguridad
    """
    if request.method == 'GET':
        # Si ya está autenticado, redirigir a dashboard
        if SessionService.is_authenticated():
            return redirect(url_for('menu_principal'))
        
        # Mostrar mensaje si fue redirigido desde una ruta protegida
        from flask import session as flask_session
        next_url = flask_session.get('next_url')
        message = None
        if next_url:
            message = "Por favor, inicia sesión para acceder a esta página"
        
        return render_template('auth/login.html', message=message)
    
    # POST: Procesar login
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validación básica
        if not email or not password:
            error_msg = "Email y contraseña son requeridos"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('auth/login.html', error=error_msg), 400
        
        # Autenticar usuario
        user_service = UserService()
        user, message = user_service.authenticate_user(email, password)
        
        if user:
            # Login exitoso: crear sesión
            SessionService.create_session(user)
            logger.info(f"Login exitoso para {email}, redirigiendo")
            
            # Retornar respuesta
            if request.is_json:
                return jsonify({
                    "message": "Login exitoso",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role
                    }
                }), 200
            
            # Redirigir a la URL original si existe, sino al menú principal
            from flask import session as flask_session
            next_url = flask_session.pop('next_url', None)
            
            if next_url and not next_url.endswith('/auth/login'):
                # Validar que la URL es del mismo dominio (seguridad)
                from urllib.parse import urlparse
                parsed_url = urlparse(next_url)
                if parsed_url.netloc == '' or parsed_url.netloc == request.host:
                    logger.info(f"Redirigiendo a URL original: {next_url}")
                    return redirect(next_url)
            
            # Redirigir al menú principal por defecto
            logger.info(f"Redirigiendo a menu_principal")
            return redirect(url_for('menu_principal'))
        else:
            # Login fallido: mensaje genérico (no revelar si usuario existe)
            ip_address = get_remote_address_safe()
            logger.warning(f"Intento de login fallido: {email} desde {ip_address}")
            
            if request.is_json:
                return jsonify({"error": message or "Credenciales inválidas"}), 401
            
            return render_template('auth/login.html', error=message or "Credenciales inválidas"), 401
    
    except ValidationError as e:
        logger.warning(f"Error de validación en login: {e}")
        error_msg = str(e)
        if request.is_json:
            return jsonify({"error": error_msg}), 400
        return render_template('auth/login.html', error=error_msg), 400
    
    except Exception as e:
        logger.error(f"Error inesperado en login: {e}", exc_info=True)
        error_msg = "Error al procesar login. Intenta nuevamente."
        if request.is_json:
            return jsonify({"error": error_msg}), 500
        return render_template('auth/login.html', error=error_msg), 500


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """
    Endpoint de logout
    
    ✅ Destruye sesión
    ✅ Logging de logout
    ✅ Limpia cookies
    """
    if SessionService.is_authenticated():
        user_email = SessionService.get_current_user_email()
        logger.info(f"Logout de usuario: {user_email}")
    
    SessionService.destroy_session()
    
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({"message": "Logout exitoso"}), 200
    
    return redirect(url_for('auth.login'))


def limit_register():
    """Decorador condicional para rate limiting"""
    if limiter:
        return limiter.limit("3 per hour")
    return lambda f: f

@auth_bp.route('/register', methods=['GET', 'POST'])
@limit_register()
def register():
    """
    Endpoint de registro (solo para admins en producción)
    
    GET: Muestra formulario de registro
    POST: Procesa registro
    
    ✅ Rate limiting (3 registros por hora)
    ✅ Validación de datos
    ✅ Hash seguro de contraseña
    """
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # POST: Procesar registro
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        role = data.get('role', 'usuario').strip()
        
        # Validación básica
        if not email or not password:
            error_msg = "Email y contraseña son requeridos"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('auth/register.html', error=error_msg), 400
        
        # Verificar que las contraseñas coincidan
        if password != confirm_password:
            error_msg = "Las contraseñas no coinciden"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('auth/register.html', error=error_msg), 400
        
        # Validar rol (solo admins pueden crear otros admins)
        valid_roles = [r for r in UserService.VALID_ROLES if r != 'admin']
        if role not in valid_roles:
            role = 'usuario'  # Default seguro
        
        # Crear usuario
        user_service = UserService()
        user = user_service.create_user(
            email=email,
            password=password,
            role=role,
            created_by=SessionService.get_current_user_id()  # None si no hay sesión
        )
        
        # Auto-login después de registro
        SessionService.create_session(user)
        
        if request.is_json:
            return jsonify({
                "message": "Usuario creado exitosamente",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role
                }
            }), 201
        
        return redirect(url_for('menu_principal'))
    
    except ValidationError as e:
        logger.warning(f"Error de validación en registro: {e}")
        error_msg = str(e)
        if request.is_json:
            return jsonify({"error": error_msg}), 400
        return render_template('auth/register.html', error=error_msg), 400
    
    except Exception as e:
        logger.error(f"Error inesperado en registro: {e}", exc_info=True)
        error_msg = "Error al crear usuario. Intenta nuevamente."
        if request.is_json:
            return jsonify({"error": error_msg}), 500
        return render_template('auth/register.html', error=error_msg), 500


@auth_bp.route('/session', methods=['GET'])
def get_session():
    """
    Endpoint para obtener información de la sesión actual
    
    ✅ Retorna datos de sesión sin información sensible
    """
    logger.info("[DEBUG] get_session() - Iniciando obtención de sesión")
    try:
        is_authenticated = SessionService.is_authenticated()
        logger.info(f"[DEBUG] get_session() - is_authenticated: {is_authenticated}")
        
        if not is_authenticated:
            logger.info("[DEBUG] get_session() - Usuario no autenticado")
            if request.is_json:
                return jsonify({"authenticated": False}), 200
            return redirect(url_for('auth.login'))
        
        logger.info("[DEBUG] get_session() - Obteniendo información de sesión")
        session_info = SessionService.get_session_info()
        logger.info(f"[DEBUG] get_session() - session_info obtenido: {session_info}")
        
        # Retornar JSON por defecto (las peticiones del frontend esperan JSON)
        # Si es una petición de navegador directa (no AJAX), redirigir al login
        if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
            logger.info("[DEBUG] get_session() - Retornando JSON")
            return jsonify(session_info), 200
        
        # Si es una petición de navegador normal (no AJAX), redirigir al login
        logger.info("[DEBUG] get_session() - Petición no JSON, redirigiendo al login")
        return redirect(url_for('auth.login'))
    
    except Exception as e:
        logger.error(f"[DEBUG] get_session() - Error al obtener sesión: {e}", exc_info=True)
        if request.is_json:
            return jsonify({
                "error": f"Error al obtener sesión: {str(e)}",
                "authenticated": False
            }), 500
        raise

