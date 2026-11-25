import os
import sqlite3
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import contextmanager

from app.config import DB_PATH, DATABASE_URL

# Detección de driver PostgreSQL
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger("linguaflow.database")

class DatabaseService:
    def __init__(self, db_path=DB_PATH, database_url=DATABASE_URL):
        self.db_path = str(db_path)
        self.database_url = database_url
        self.is_postgres = bool(
            self.database_url 
            and ("postgres://" in self.database_url or "postgresql://" in self.database_url) 
            and PSYCOPG2_AVAILABLE
        )

        if self.is_postgres:
            logger.info("Modo de base de datos: PostgreSQL en la nube activado.")
        else:
            logger.info("Modo de base de datos: SQLite local (%s).", self.db_path)

        self.init_db()

    def get_connection(self):
        """Crea y retorna una nueva conexión a la base de datos correspondiente."""
        if self.is_postgres:
            conn = psycopg2.connect(
                self.database_url, 
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

    @contextmanager
    def get_cursor(self):
        """Context manager que maneja la conexión, transacción y cursor de forma segura."""
        conn = self.get_connection()
        try:
            if self.is_postgres:
                with conn:
                    with conn.cursor() as cur:
                        yield cur
            else:
                with conn:
                    cur = conn.cursor()
                    yield cur
        finally:
            conn.close()

    def _format_query(self, sql: str) -> str:
        """Adapta la sintaxis de parámetros entre SQLite (?) y PostgreSQL (%s)."""
        if self.is_postgres:
            return sql.replace("?", "%s")
        return sql

    def init_db(self):
        """Inicializa las tablas e índices necesarios para la autenticación y sesiones."""
        try:
            if self.is_postgres:
                with self.get_cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(100) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            salt VARCHAR(255) NOT NULL,
                            full_name VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS sessions (
                            token VARCHAR(255) PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL
                        );
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS password_resets (
                            id SERIAL PRIMARY KEY,
                            token VARCHAR(255) UNIQUE NOT NULL,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            used INTEGER DEFAULT 0
                        );
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (LOWER(username));")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (LOWER(email));")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (token);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_resets_token ON password_resets (token);")
                logger.info("Tablas de PostgreSQL verificadas e inicializadas con éxito.")
            else:
                with self.get_cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                            password_hash TEXT NOT NULL,
                            salt TEXT NOT NULL,
                            full_name TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS sessions (
                            token TEXT PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                        )
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS password_resets (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            token TEXT UNIQUE NOT NULL,
                            user_id INTEGER NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            used INTEGER DEFAULT 0,
                            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                        )
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (token)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_resets_token ON password_resets (token)")
                logger.info("Tablas de SQLite verificadas e inicializadas en %s", self.db_path)
        except Exception as e:
            logger.error("Error al inicializar la base de datos: %s", e)
            raise

    # -------------------------------------------------------------
    # Utilidades de Criptografía y Contraseñas
    # -------------------------------------------------------------
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Genera un hash seguro PBKDF2-HMAC-SHA256 con salt aleatorio."""
        if not salt:
            salt = secrets.token_hex(16)
        
        salt_bytes = salt.encode("utf-8")
        pwd_bytes = password.encode("utf-8")
        pwd_hash = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000).hex()
        return pwd_hash, salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verifica una contraseña contra el hash almacenado usando tiempo constante."""
        calculated_hash, _ = DatabaseService.hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, stored_hash)

    # -------------------------------------------------------------
    # Métodos de Usuario
    # -------------------------------------------------------------
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Busca un usuario por su identificador primario."""
        sql = "SELECT id, username, email, full_name, created_at FROM users WHERE id = ?"
        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql), (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            if isinstance(data.get("created_at"), datetime):
                data["created_at"] = data["created_at"].isoformat()
            return data

    def get_user_by_username_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Busca un usuario por su nombre de usuario o correo electrónico (incluyendo hashes)."""
        clean_id = identifier.strip().lower()
        sql = """
            SELECT id, username, email, password_hash, salt, full_name, created_at 
            FROM users 
            WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)
        """
        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql), (clean_id, clean_id))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            if isinstance(data.get("created_at"), datetime):
                data["created_at"] = data["created_at"].isoformat()
            return data

    def create_user(
        self, 
        username: str, 
        email: str, 
        password: str, 
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra un nuevo usuario en la base de datos con contraseña cifrada.
        Lanza ValueError si el usuario o email ya están registrados.
        """
        username_clean = username.strip()
        email_clean = email.strip().lower()
        full_name_clean = full_name.strip() if full_name else username_clean

        # Validar si ya existe
        existing = self.get_user_by_username_or_email(username_clean)
        if existing:
            if existing["username"].lower() == username_clean.lower():
                raise ValueError("El nombre de usuario ya está registrado.")
            if existing["email"].lower() == email_clean.lower():
                raise ValueError("El correo electrónico ya está registrado.")

        existing_email = self.get_user_by_username_or_email(email_clean)
        if existing_email:
            raise ValueError("El correo electrónico ya está registrado.")

        # Cifrar contraseña
        pwd_hash, salt = self.hash_password(password)

        with self.get_cursor() as cur:
            if self.is_postgres:
                sql = """
                    INSERT INTO users (username, email, password_hash, salt, full_name)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """
                cur.execute(sql, (username_clean, email_clean, pwd_hash, salt, full_name_clean))
                row = cur.fetchone()
                user_id = row["id"]
                created_at = row["created_at"]
                if isinstance(created_at, datetime):
                    created_at = created_at.isoformat()
            else:
                sql = """
                    INSERT INTO users (username, email, password_hash, salt, full_name)
                    VALUES (?, ?, ?, ?, ?)
                """
                cur.execute(sql, (username_clean, email_clean, pwd_hash, salt, full_name_clean))
                user_id = cur.lastrowid
                created_at = datetime.utcnow().isoformat()

        return {
            "id": user_id,
            "username": username_clean,
            "email": email_clean,
            "full_name": full_name_clean,
            "created_at": created_at
        }

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Valida las credenciales de un usuario existente.
        Retorna el diccionario del usuario sin campos sensibles si es válido, o None si no coincide.
        """
        user_row = self.get_user_by_username_or_email(username_or_email)
        if not user_row:
            return None

        if not self.verify_password(password, user_row["password_hash"], user_row["salt"]):
            return None

        return {
            "id": user_row["id"],
            "username": user_row["username"],
            "email": user_row["email"],
            "full_name": user_row["full_name"],
            "created_at": user_row["created_at"]
        }

    # -------------------------------------------------------------
    # Manejo de Sesiones / Tokens
    # -------------------------------------------------------------
    def create_session(self, user_id: int, duration_days: int = 30) -> str:
        """Crea una sesión persistente con token criptográfico seguro."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=duration_days)

        sql = """
            INSERT INTO sessions (token, user_id, expires_at)
            VALUES (?, ?, ?)
        """
        param_expires = expires_at if self.is_postgres else expires_at.isoformat()

        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql), (token, user_id, param_expires))

        return token

    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Obtiene el usuario vinculado a un token activo y no expirado."""
        if not token:
            return None

        now = datetime.utcnow()
        param_now = now if self.is_postgres else now.isoformat()

        sql = """
            SELECT u.id, u.username, u.email, u.full_name, u.created_at, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ?
        """
        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql), (token, param_now))
            row = cur.fetchone()
            if row:
                created_at = row["created_at"]
                if isinstance(created_at, datetime):
                    created_at = created_at.isoformat()
                return {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "created_at": created_at
                }
            return None

    def delete_session(self, token: str) -> bool:
        """Cierra la sesión eliminando el token especificado."""
        if not token:
            return False

        sql = "DELETE FROM sessions WHERE token = ?"
        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql), (token,))
            return cur.rowcount > 0

    # -------------------------------------------------------------
    # Recuperación de Cuenta y Contraseña
    # -------------------------------------------------------------
    def create_password_reset(self, user_id: int, duration_hours: int = 24) -> str:
        """Genera un token seguro para recuperación de contraseña."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        param_expires = expires_at if self.is_postgres else expires_at.isoformat()

        # Invalidar tokens anteriores no usados
        sql_invalidate = "UPDATE password_resets SET used = 1 WHERE user_id = ? AND used = 0"
        sql_insert = "INSERT INTO password_resets (token, user_id, expires_at, used) VALUES (?, ?, ?, 0)"

        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql_invalidate), (user_id,))
            cur.execute(self._format_query(sql_insert), (token, user_id, param_expires))

        return token

    def verify_password_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica si un token de recuperación es válido y vigente."""
        if not token:
            return None

        now = datetime.utcnow()
        param_now = now if self.is_postgres else now.isoformat()

        sql = """
            SELECT pr.token, pr.user_id, pr.expires_at, pr.used, u.id, u.username, u.email, u.full_name
            FROM password_resets pr
            JOIN users u ON pr.user_id = u.id
            WHERE pr.token = ? AND pr.used = 0 AND pr.expires_at > ?
        """
        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql), (token, param_now))
            row = cur.fetchone()
            if row:
                return dict(row)
            return None

    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Restablece la contraseña de un usuario mediante su token y revoca sesiones anteriores."""
        reset_info = self.verify_password_reset_token(token)
        if not reset_info:
            return False

        user_id = reset_info["user_id"]
        pwd_hash, salt = self.hash_password(new_password)

        sql_update_user = "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?"
        sql_mark_used = "UPDATE password_resets SET used = 1 WHERE token = ?"
        sql_delete_sessions = "DELETE FROM sessions WHERE user_id = ?"

        with self.get_cursor() as cur:
            cur.execute(self._format_query(sql_update_user), (pwd_hash, salt, user_id))
            cur.execute(self._format_query(sql_mark_used), (token,))
            cur.execute(self._format_query(sql_delete_sessions), (user_id,))

        return True

# Instancia singleton del servicio de base de datos
db_service = DatabaseService()
