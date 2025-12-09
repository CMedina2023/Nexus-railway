"""
Gestión de base de datos
Responsabilidad única: Inicializar y gestionar conexión a base de datos
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from app.core.config import Config

logger = logging.getLogger(__name__)


class Database:
    """
    Clase para gestión de base de datos SQLite
    Responsabilidad única: Gestión de conexión y transacciones
    """
    
    def __init__(self, db_path: str = None):
        """
        Inicializa la conexión a la base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos (default: Config.DATABASE_URL)
        """
        if db_path is None:
            # Extraer ruta de DATABASE_URL (sqlite:///path/to/db.db)
            db_url = Config.DATABASE_URL
            if db_url.startswith('sqlite:///'):
                db_path = db_url.replace('sqlite:///', '')
            else:
                db_path = 'nexus_ai.db'
        
        # Asegurar que el directorio existe
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_path)
        self._init_schema()
    
    def _init_schema(self):
        """Inicializa el esquema de la base de datos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            users_table_sql = '''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'usuario', 'analista_qa')),
                    active INTEGER NOT NULL DEFAULT 1,
                    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                    locked_until TEXT,
                    last_login TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT
                )
            '''
            # Asegurar que la tabla de usuarios soporte el nuevo rol
            self._ensure_users_table_schema(cursor, users_table_sql)
            
            # Tabla de usuarios
            cursor.execute(users_table_sql)
            
            # Tabla de configuración de proyectos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_configs (
                    id TEXT PRIMARY KEY,
                    project_key TEXT UNIQUE NOT NULL,
                    jira_base_url TEXT NOT NULL,
                    shared_email TEXT NOT NULL,
                    shared_token TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    updated_by TEXT,
                    active INTEGER NOT NULL DEFAULT 1
                )
            ''')
            
            # Tabla de configuración personal de Jira por usuario
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_jira_configs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    project_key TEXT NOT NULL,
                    personal_email TEXT NOT NULL,
                    personal_token TEXT NOT NULL,
                    use_personal INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (project_key) REFERENCES project_configs(project_key) ON DELETE CASCADE,
                    UNIQUE(user_id, project_key)
                )
            ''')
            
            # Tabla de historias de usuario generadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    project_key TEXT NOT NULL,
                    area TEXT,
                    story_title TEXT NOT NULL,
                    story_content TEXT NOT NULL,
                    jira_issue_key TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabla de casos de prueba generados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    project_key TEXT NOT NULL,
                    area TEXT,
                    test_case_title TEXT NOT NULL,
                    test_case_content TEXT NOT NULL,
                    jira_issue_key TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabla de reportes creados en Jira
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jira_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    project_key TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    report_title TEXT NOT NULL,
                    report_content TEXT NOT NULL,
                    jira_issue_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabla de cargas masivas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bulk_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    project_key TEXT NOT NULL,
                    upload_type TEXT NOT NULL,
                    total_items INTEGER NOT NULL,
                    successful_items INTEGER NOT NULL DEFAULT 0,
                    failed_items INTEGER NOT NULL DEFAULT 0,
                    upload_details TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Índices para mejorar rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_configs_key ON project_configs(project_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_jira_configs_user ON user_jira_configs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_stories_user ON user_stories(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_stories_project ON user_stories(project_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_cases_user ON test_cases(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_cases_project ON test_cases(project_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jira_reports_user ON jira_reports(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jira_reports_project ON jira_reports(project_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bulk_uploads_user ON bulk_uploads(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bulk_uploads_project ON bulk_uploads(project_key)')
            
            conn.commit()
            conn.close()
            logger.info(f"Esquema de base de datos inicializado en {self.db_path}")
        except Exception as e:
            logger.error(f"Error al inicializar esquema de base de datos: {e}")
            raise

    def _ensure_users_table_schema(self, cursor, users_table_sql: str):
        """
        Verifica y actualiza la tabla de usuarios para soportar nuevos roles.
        Si la tabla existe y no incluye el rol analista_qa en el CHECK,
        se recrea preservando los datos.
        """
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        row = cursor.fetchone()
        if not row:
            return  # La tabla no existe, se creará más adelante

        current_sql = row[0] if isinstance(row, tuple) else row['sql']
        if current_sql and "analista_qa" not in current_sql:
            logger.info("Actualizando tabla users para incluir rol analista_qa")
            cursor.execute("ALTER TABLE users RENAME TO users_old")
            cursor.execute(users_table_sql)
            cursor.execute('''
                INSERT INTO users (
                    id, email, password_hash, role, active,
                    failed_login_attempts, locked_until, last_login,
                    created_at, updated_at, created_by
                )
                SELECT
                    id, email, password_hash,
                    CASE
                        WHEN role IN ('admin', 'usuario', 'analista_qa') THEN role
                        ELSE 'usuario'
                    END as role,
                    active,
                    failed_login_attempts,
                    locked_until,
                    last_login,
                    created_at,
                    updated_at,
                    created_by
                FROM users_old
            ''')
            cursor.execute("DROP TABLE users_old")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtiene una conexión a la base de datos
        
        Returns:
            sqlite3.Connection: Conexión a la base de datos
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
        return conn
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager para gestionar cursores de forma segura
        
        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                result = cursor.fetchall()
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            conn.close()


# Instancia global de la base de datos
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """
    Obtiene la instancia de la base de datos (Singleton)
    
    Returns:
        Database: Instancia de la base de datos
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def init_db():
    """
    Inicializa la base de datos (crea esquema si no existe)
    """
    db = get_db()
    db._init_schema()
    logger.info("Base de datos inicializada correctamente")


def get_db_connection() -> sqlite3.Connection:
    """
    Obtiene una conexión a la base de datos (alias para compatibilidad con repositorios)
    
    Returns:
        sqlite3.Connection: Conexión a la base de datos
    """
    return get_db().get_connection()



