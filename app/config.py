import os
from pathlib import Path

# Rutas del Proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "app" / "static"

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
