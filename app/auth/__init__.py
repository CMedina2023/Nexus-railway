"""
Módulo de autenticación y autorización
Responsabilidad única: Gestionar autenticación, sesiones y permisos
"""
from app.auth.decorators import login_required, role_required, get_current_user_id, get_current_user_role
from app.auth.user_service import UserService
from app.auth.session_service import SessionService
from app.auth.password_service import PasswordService
from app.auth.encryption_service import EncryptionService

__all__ = [
    'login_required',
    'role_required',
    'get_current_user_id',
    'get_current_user_role',
    'UserService',
    'SessionService',
    'PasswordService',
    'EncryptionService'
]

