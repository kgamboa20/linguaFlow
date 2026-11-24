import sqlite3
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.config import DB_PATH

logger = logging.getLogger("linguaflow.database")

class DatabaseService:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos SQLite con fábrica de filas."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Inicializa las tablas necesarias para autenticación si no existen."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de Usuarios
            cursor.execute("""
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

            # Tabla de Sesiones Activas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # Índices de búsqueda rápida
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
            
            conn.commit()
            logger.info("Base de datos SQLite inicializada correctamente en %s", self.db_path)

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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, full_name, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_username_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Busca un usuario por su nombre de usuario o correo electrónico (incluyendo hashes)."""
        clean_id = identifier.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, email, password_hash, salt, full_name, created_at 
                FROM users 
                WHERE LOWER(username) = ? OR LOWER(email) = ?
                """,
                (clean_id, clean_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

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

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, salt, full_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username_clean, email_clean, pwd_hash, salt, full_name_clean)
            )
            user_id = cursor.lastrowid
            conn.commit()

        return {
            "id": user_id,
            "username": username_clean,
            "email": email_clean,
            "full_name": full_name_clean,
            "created_at": datetime.utcnow().isoformat()
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

        # Excluir hash y salt del retorno
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

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (token, user_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (token, user_id, expires_at.isoformat())
            )
            conn.commit()

        return token

    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Obtiene el usuario vinculado a un token activo y no expirado."""
        if not token:
            return None

        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.email, u.full_name, u.created_at, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (token, now)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "created_at": row["created_at"]
                }
            return None

    def delete_session(self, token: str) -> bool:
        """Cierra la sesión eliminando el token especificado."""
        if not token:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return cursor.rowcount > 0

# Instancia singleton del servicio de base de datos
db_service = DatabaseService()
