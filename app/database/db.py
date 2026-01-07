"""
Gestión de base de datos
Responsabilidad única: Inicializar y gestionar conexión a base de datos
Soporta SQLite (desarrollo) y PostgreSQL (producción)
"""
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from urllib.parse import urlparse

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool, NullPool

from app.core.config import Config
from app.database.query_adapter import adapt_query, adapt_query_dict

logger = logging.getLogger(__name__)


class Database:
    """
    Clase para gestión de base de datos con soporte SQLite y PostgreSQL
    Responsabilidad única: Gestión de conexión y transacciones
    """
    
    def __init__(self, db_url: str = None):
        """
        Inicializa la conexión a la base de datos
        
        Args:
            db_url: URL de conexión a la base de datos (default: Config.DATABASE_URL)
        """
        if db_url is None:
            db_url = Config.DATABASE_URL
        
        self.db_url = db_url
        self.is_sqlite = db_url.startswith('sqlite:///')
        self.is_postgres = db_url.startswith('postgresql://') or db_url.startswith('postgres://')
        
        # Configurar engine según el tipo de base de datos
        if self.is_sqlite:
            # SQLite: Asegurar que el directorio existe
            db_path = db_url.replace('sqlite:///', '')
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # SQLite con StaticPool para evitar problemas de concurrencia
            self.engine = create_engine(
                db_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False
            )
            
            # Configurar row_factory para retornar diccionarios en SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                import sqlite3
                dbapi_conn.row_factory = sqlite3.Row
            
            logger.info(f"Conectado a SQLite: {db_path}")
            
        elif self.is_postgres:
            # PostgreSQL: Ajustar URL si es necesario (Render usa postgres://)
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
                self.db_url = db_url
            
            # PostgreSQL con pool de conexiones
            self.engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Verificar conexiones antes de usar
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,  # Reciclar conexiones cada hora
                echo=False
            )
            logger.info("Conectado a PostgreSQL")
            
        else:
            raise ValueError(f"Base de datos no soportada: {db_url}")
        
        # Crear session factory
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        ))
        
        # Inicializar esquema
        self._init_schema()
    
    def _init_schema(self):
        """Inicializa el esquema de la base de datos"""
        try:
            with self.engine.connect() as conn:
                # Tabla de usuarios
                if self.is_sqlite:
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
                else:  # PostgreSQL
                    users_table_sql = '''
                        CREATE TABLE IF NOT EXISTS users (
                            id TEXT PRIMARY KEY,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            role TEXT NOT NULL CHECK(role IN ('admin', 'usuario', 'analista_qa')),
                            active INTEGER NOT NULL DEFAULT 1,
                            failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                            locked_until TIMESTAMP,
                            last_login TIMESTAMP,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            created_by TEXT
                        )
                    '''
                
                conn.execute(text(users_table_sql))
                
                # Tabla de configuración de proyectos
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS project_configs (
                        id TEXT PRIMARY KEY,
                        project_key TEXT UNIQUE NOT NULL,
                        jira_base_url TEXT NOT NULL,
                        shared_email TEXT NOT NULL,
                        shared_token TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        created_at {} NOT NULL,
                        updated_at {} NOT NULL,
                        updated_by TEXT,
                        active INTEGER NOT NULL DEFAULT 1
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP', 'TEXT' if self.is_sqlite else 'TIMESTAMP')))
                
                # Tabla de configuración personal de Jira por usuario
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS user_jira_configs (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        project_key TEXT NOT NULL,
                        personal_email TEXT NOT NULL,
                        personal_token TEXT NOT NULL,
                        use_personal INTEGER NOT NULL DEFAULT 0,
                        created_at {} NOT NULL,
                        updated_at {} NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (project_key) REFERENCES project_configs(project_key) ON DELETE CASCADE,
                        UNIQUE(user_id, project_key)
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP', 'TEXT' if self.is_sqlite else 'TIMESTAMP')))
                
                # Tabla de historias de usuario generadas
                if self.is_sqlite:
                    user_stories_sql = '''
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
                            requirement_id TEXT,
                            epic_id TEXT,
                            feature_id TEXT,
                            parent_story_id INTEGER,
                            dependencies TEXT,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            FOREIGN KEY (parent_story_id) REFERENCES user_stories(id)
                        )
                    '''
                else:  # PostgreSQL
                    user_stories_sql = '''
                        CREATE TABLE IF NOT EXISTS user_stories (
                            id SERIAL PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            project_key TEXT NOT NULL,
                            area TEXT,
                            story_title TEXT NOT NULL,
                            story_content TEXT NOT NULL,
                            jira_issue_key TEXT,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            requirement_id TEXT,
                            epic_id TEXT,
                            feature_id TEXT,
                            parent_story_id INTEGER,
                            dependencies TEXT,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            FOREIGN KEY (parent_story_id) REFERENCES user_stories(id)
                        )
                    '''
                
                conn.execute(text(user_stories_sql))
                
                # Tabla de casos de prueba generados
                if self.is_sqlite:
                    test_cases_sql = '''
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
                            requirement_id TEXT,
                            requirement_version TEXT,
                            coverage_status TEXT,
                            approval_status TEXT DEFAULT 'pending',
                            approved_by INTEGER,
                            approved_at TEXT,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    '''
                else:  # PostgreSQL
                    test_cases_sql = '''
                        CREATE TABLE IF NOT EXISTS test_cases (
                            id SERIAL PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            project_key TEXT NOT NULL,
                            area TEXT,
                            test_case_title TEXT NOT NULL,
                            test_case_content TEXT NOT NULL,
                            jira_issue_key TEXT,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            requirement_id TEXT,
                            requirement_version TEXT,
                            coverage_status TEXT,
                            approval_status VARCHAR(20) DEFAULT 'pending',
                            approved_by INTEGER,
                            approved_at TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    '''
                
                conn.execute(text(test_cases_sql))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_test_cases_requirement ON test_cases(requirement_id)'))
                
                # Tabla de reportes creados en Jira
                if self.is_sqlite:
                    jira_reports_sql = '''
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
                    '''
                else:  # PostgreSQL
                    jira_reports_sql = '''
                        CREATE TABLE IF NOT EXISTS jira_reports (
                            id SERIAL PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            project_key TEXT NOT NULL,
                            report_type TEXT NOT NULL,
                            report_title TEXT NOT NULL,
                            report_content TEXT NOT NULL,
                            jira_issue_key TEXT NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    '''
                
                conn.execute(text(jira_reports_sql))
                
                # Tabla de cargas masivas
                if self.is_sqlite:
                    bulk_uploads_sql = '''
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
                    '''
                else:  # PostgreSQL
                    bulk_uploads_sql = '''
                        CREATE TABLE IF NOT EXISTS bulk_uploads (
                            id SERIAL PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            project_key TEXT NOT NULL,
                            upload_type TEXT NOT NULL,
                            total_items INTEGER NOT NULL,
                            successful_items INTEGER NOT NULL DEFAULT 0,
                            failed_items INTEGER NOT NULL DEFAULT 0,
                            upload_details TEXT,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                    '''
                
                conn.execute(text(bulk_uploads_sql))
                
                # Tabla de Epics
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS epics (
                        id VARCHAR(36) PRIMARY KEY,
                        project_key VARCHAR(50) NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'DRAFT',
                        created_at {} NOT NULL,
                        updated_at {} NOT NULL
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP', 'TEXT' if self.is_sqlite else 'TIMESTAMP')))

                # Tabla de Features
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS features (
                        id VARCHAR(36) PRIMARY KEY,
                        project_key VARCHAR(50) NOT NULL,
                        epic_id VARCHAR(36),
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'DRAFT',
                        created_at {} NOT NULL,
                        updated_at {} NOT NULL,
                        FOREIGN KEY (epic_id) REFERENCES epics(id) ON DELETE SET NULL
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP', 'TEXT' if self.is_sqlite else 'TIMESTAMP')))

                # ==========================================
                # NUEVAS TABLAS (Integración Completa)
                # ==========================================

                # 1. Traceability & Requirements
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS requirements (
                        id VARCHAR(36) PRIMARY KEY,
                        project_id VARCHAR(50) NOT NULL,
                        code VARCHAR(50) NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        type VARCHAR(50) NOT NULL,
                        priority VARCHAR(20) NOT NULL,
                        status VARCHAR(20) DEFAULT 'DRAFT',
                        source_document_id VARCHAR(36),
                        created_at {} NOT NULL,
                        updated_at {} NOT NULL
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP', 'TEXT' if self.is_sqlite else 'TIMESTAMP')))

                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS traceability_links (
                        id VARCHAR(36) PRIMARY KEY,
                        source_id VARCHAR(36) NOT NULL,
                        source_type VARCHAR(50) NOT NULL,
                        target_id VARCHAR(36) NOT NULL,
                        target_type VARCHAR(50) NOT NULL,
                        link_type VARCHAR(50) NOT NULL,
                        created_by INTEGER,
                        meta TEXT,
                        created_at {} NOT NULL
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP')))

                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS requirement_coverages (
                        id VARCHAR(36) PRIMARY KEY,
                        requirement_id VARCHAR(36) NOT NULL,
                        test_count INTEGER DEFAULT 0,
                        story_count INTEGER DEFAULT 0,
                        coverage_score FLOAT DEFAULT 0.0,
                        status VARCHAR(20) DEFAULT 'UNCOVERED',
                        last_updated {} NOT NULL,
                        FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP')))

                # 2. Knowledge Base (Context & Documents)
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS project_contexts (
                        id VARCHAR(36) PRIMARY KEY,
                        project_key VARCHAR(50) NOT NULL,
                        summary TEXT,
                        glossary TEXT,
                        business_rules TEXT,
                        tech_constraints TEXT,
                        version INTEGER DEFAULT 1,
                        created_at {} NOT NULL,
                        updated_at {} NOT NULL
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP', 'TEXT' if self.is_sqlite else 'TIMESTAMP')))

                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS project_documents (
                        id VARCHAR(36) PRIMARY KEY,
                        project_key VARCHAR(50) NOT NULL,
                        filename VARCHAR(255) NOT NULL,
                        file_path VARCHAR(512) NOT NULL,
                        file_type VARCHAR(20),
                        status VARCHAR(20) DEFAULT 'pending',
                        content_hash VARCHAR(64),
                        extracted_summary TEXT,
                        error_message TEXT,
                        upload_date {} NOT NULL,
                        processed_at {}
                    )
                '''.format('TEXT' if self.is_sqlite else 'TIMESTAMP', 'TEXT' if self.is_sqlite else 'TIMESTAMP')))

                # 3. Workflows
                if self.is_sqlite:
                    approval_workflows_sql = '''
                        CREATE TABLE IF NOT EXISTS approval_workflows (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            artifact_type VARCHAR(50) NOT NULL,
                            artifact_id INTEGER NOT NULL,
                            current_status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                            requester_id TEXT NOT NULL,
                            reviewer_id TEXT,
                            created_at TEXT,
                            updated_at TEXT,
                            UNIQUE(artifact_type, artifact_id),
                            FOREIGN KEY (requester_id) REFERENCES users(id),
                            FOREIGN KEY (reviewer_id) REFERENCES users(id)
                        )
                    '''
                    approval_history_sql = '''
                        CREATE TABLE IF NOT EXISTS approval_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            workflow_id INTEGER NOT NULL,
                            previous_status VARCHAR(50) NOT NULL,
                            new_status VARCHAR(50) NOT NULL,
                            actor_id TEXT NOT NULL,
                            action VARCHAR(50) NOT NULL,
                            comments TEXT,
                            detailed_snapshot TEXT,
                            created_at TEXT,
                            FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE,
                            FOREIGN KEY (actor_id) REFERENCES users(id)
                        )
                    '''
                else: # PostgreSQL
                    approval_workflows_sql = '''
                        CREATE TABLE IF NOT EXISTS approval_workflows (
                            id SERIAL PRIMARY KEY,
                            artifact_type VARCHAR(50) NOT NULL,
                            artifact_id INTEGER NOT NULL,
                            current_status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                            requester_id TEXT NOT NULL,
                            reviewer_id TEXT,
                            created_at TIMESTAMP,
                            updated_at TIMESTAMP,
                            UNIQUE(artifact_type, artifact_id),
                            FOREIGN KEY (requester_id) REFERENCES users(id),
                            FOREIGN KEY (reviewer_id) REFERENCES users(id)
                        )
                    '''
                    approval_history_sql = '''
                        CREATE TABLE IF NOT EXISTS approval_history (
                            id SERIAL PRIMARY KEY,
                            workflow_id INTEGER NOT NULL,
                            previous_status VARCHAR(50) NOT NULL,
                            new_status VARCHAR(50) NOT NULL,
                            actor_id TEXT NOT NULL,
                            action VARCHAR(50) NOT NULL,
                            comments TEXT,
                            detailed_snapshot JSONB,
                            created_at TIMESTAMP,
                            FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE,
                            FOREIGN KEY (actor_id) REFERENCES users(id)
                        )
                    '''

                conn.execute(text(approval_workflows_sql))
                conn.execute(text(approval_history_sql))

                # CREATE INDEXES for new tables
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_requirements_project ON requirements(project_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_requirements_code ON requirements(code)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_traceability_source ON traceability_links(source_id, source_type)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_project_contexts_key ON project_contexts(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_project_documents_key ON project_documents(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_workflow_status ON approval_workflows(current_status)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_project_configs_key ON project_configs(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_user_jira_configs_user ON user_jira_configs(user_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_user_stories_user ON user_stories(user_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_user_stories_project ON user_stories(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_test_cases_user ON test_cases(user_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_test_cases_project ON test_cases(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_jira_reports_user ON jira_reports(user_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_jira_reports_project ON jira_reports(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_bulk_uploads_user ON bulk_uploads(user_id)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_bulk_uploads_project ON bulk_uploads(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_epics_project ON epics(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_features_project ON features(project_key)'))
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_features_epic ON features(epic_id)'))
                
                conn.commit()
                
            logger.info(f"Esquema de base de datos inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar esquema de base de datos: {e}", exc_info=True)
            raise
    
    def get_connection(self):
        """
        Obtiene una conexión raw a la base de datos (para compatibilidad con código existente)
        
        Returns:
            Connection: Conexión a la base de datos
        """
        return self.engine.raw_connection()
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager para gestionar cursores de forma segura (compatibilidad con código existente)
        
        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                result = cursor.fetchall()
        """
        conn = self.get_connection()
        
        # Crear cursor apropiado según el tipo de BD
        if self.is_postgres:
            # PostgreSQL: Usar RealDictCursor para retornar diccionarios (como SQLite)
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            # SQLite: row_factory ya está configurado en el engine (ver __init__)
            cursor = conn.cursor()
        
        # Crear un wrapper del cursor que adapta las consultas automáticamente
        class CursorWrapper:
            def __init__(self, cursor, is_postgres):
                self._cursor = cursor
                self._is_postgres = is_postgres
            
            def execute(self, query, params=None):
                if params:
                    if isinstance(params, dict):
                        query, params = adapt_query_dict(query, params, self._is_postgres)
                    else:
                        query, params = adapt_query(query, params, self._is_postgres)
                    return self._cursor.execute(query, params)
                return self._cursor.execute(query)
            
            def __getattr__(self, name):
                # Delegar todos los otros métodos al cursor original
                return getattr(self._cursor, name)
        
        wrapped_cursor = CursorWrapper(cursor, self.is_postgres)
        
        try:
            yield wrapped_cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @contextmanager
    def get_session(self):
        """
        Context manager para gestionar sesiones SQLAlchemy
        
        Usage:
            with db.get_session() as session:
                session.execute(text("SELECT * FROM users"))
                session.commit()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Cierra todas las conexiones"""
        self.SessionLocal.remove()
        self.engine.dispose()


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


def get_db_connection():
    """
    Obtiene una conexión a la base de datos (alias para compatibilidad con repositorios)
    
    Returns:
        Connection: Conexión a la base de datos
    """
    return get_db().get_connection()
