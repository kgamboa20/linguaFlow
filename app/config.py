import os
from pathlib import Path

# Rutas del Proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", BASE_DIR / "uploads"))
STATIC_DIR = BASE_DIR / "app" / "static"
DB_PATH = Path(os.environ.get("DB_PATH", BASE_DIR / "linguaflow.db"))

# Variables de Entorno y Producción
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")

# Conexión a Base de Datos (PostgreSQL en la Nube / SQLite en local)
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Normalización para compatibilidad con librerías modernas de Python
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configuración de DeepL API (DeepL API Free & Pro)
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", os.environ.get("DEEPL_AUTH_KEY", "")).strip()
DEEPL_API_ENDPOINT = os.environ.get("DEEPL_API_ENDPOINT", "").strip().rstrip("/")
# Si la key termina en :fx o no se especifica endpoint, se usa por defecto la API Free
if not DEEPL_API_ENDPOINT:
    if DEEPL_API_KEY.endswith(":fx"):
        DEEPL_API_ENDPOINT = "https://api-free.deepl.com/v2/translate"
    else:
        DEEPL_API_ENDPOINT = "https://api-free.deepl.com/v2/translate" if not DEEPL_API_KEY else "https://api.deepl.com/v2/translate"

# Configuración de Correo Electrónico (SMTP)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "no-reply@linguaflow.com")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "LinguaFlow")
SMTP_TLS = os.environ.get("SMTP_TLS", "true").lower() in ("true", "1", "yes")
APP_URL = os.environ.get("APP_URL", "http://localhost:8000")

# Asegurar existencia del directorio de uploads
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Límite de tamaño de archivo (15 MB)
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024

# Catálogo de Idiomas soportados (Código ISO 639-1 y nombre para la UI)
SUPPORTED_LANGUAGES = {
    "auto": "Detectar idioma automáticamente",
    "es": "Español",
    "en": "Inglés",
    "fr": "Francés",
    "de": "Alemán",
    "it": "Italiano",
    "pt": "Portugués",
    "ru": "Ruso",
    "zh": "Chino (Simplificado)",
    "ja": "Japonés",
    "ko": "Coreano",
    "ar": "Árabe",
    "hi": "Hindi",
    "nl": "Neerlandés",
    "pl": "Polaco",
    "tr": "Turco",
    "uk": "Ucraniano",
    "sv": "Sueco",
    "el": "Griego"
}

# Voces neuronales de alta fidelidad para Edge TTS (con fallback a gTTS)
EDGE_TTS_VOICES = {
    "es": "es-ES-AlvaroNeural",
    "en": "en-US-JennyNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
    "ru": "ru-RU-DmitryNeural",
    "zh": "zh-CN-YunxiNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
    "ar": "ar-SA-HamedNeural",
    "hi": "hi-IN-MadhurNeural",
    "nl": "nl-NL-MaartenNeural",
    "pl": "pl-PL-MarekNeural",
    "tr": "tr-TR-AhmetNeural",
    "uk": "uk-UA-OstapNeural",
    "sv": "sv-SE-MattiasNeural",
    "el": "el-GR-NestorasNeural"
}
