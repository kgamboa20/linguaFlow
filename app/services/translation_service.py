import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional
import requests
from langdetect import detect, DetectorFactory
from app.config import SUPPORTED_LANGUAGES, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

# Importación condicional de boto3 para Amazon Translate
try:
    import boto3
    from botocore.config import Config as BotoConfig
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Reproducibilidad en detección de idioma
DetectorFactory.seed = 0
logger = logging.getLogger("linguaflow.translation")

# Mapeo de códigos ISO
LANG_MAP = {
    "zh": "zh-CN",
    "auto": "auto"
}

# Mapeo para MyMemory
LANG_MAP_MYMEMORY = {
    "es": "es-ES", "en": "en-GB", "fr": "fr-FR", "de": "de-DE",
    "it": "it-IT", "pt": "pt-PT", "ru": "ru-RU", "zh": "zh-CN",
    "ja": "ja-JP", "ko": "ko-KR", "ar": "ar-SA", "hi": "hi-IN",
    "nl": "nl-NL", "pl": "pl-PL", "tr": "tr-TR", "uk": "uk-UA",
    "sv": "sv-SE", "el": "el-GR"
}

class TranslationService:
    def __init__(self):
        self.chunk_size = 3500
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        })

        # Inicialización de Amazon Translate (Motor principal)
        self.amazon_client = None
        aws_key = (AWS_ACCESS_KEY_ID or "").strip()
        aws_secret = (AWS_SECRET_ACCESS_KEY or "").strip()
        if BOTO3_AVAILABLE and aws_key and aws_secret:
            try:
                boto_config = BotoConfig(connect_timeout=3, read_timeout=4, retries={'max_attempts': 1})
                self.amazon_client = boto3.client(
                    "translate",
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                    region_name=AWS_REGION,
                    config=boto_config
                )
                logger.info("Motor Amazon Translate configurado con credenciales AWS en región %s.", AWS_REGION)
            except Exception as e:
                self.amazon_client = None
                logger.warning("No se pudo iniciar cliente Amazon Translate: %s. Se usarán motores secundarios.", e)
        else:
            logger.info("Amazon Translate en modo pasivo (sin credenciales AWS explícitas). Motores secundarios activos.")

    def _translate_with_amazon(self, text: str, source_lang: str, target_lang: str) -> Optional[Tuple[str, str]]:
        """Traduce usando Amazon Translate como motor principal oficial."""
        if not self.amazon_client:
            return None

        src = source_lang
        if src == "auto":
            src = self.detect_language(text)

        tgt = target_lang

        # Si el idioma origen y destino son iguales, Amazon Translate arroja ValidationException
        if src == tgt:
            return text, src

        amazon_src = "zh" if src in ("zh", "zh-CN") else src
        amazon_tgt = "zh" if tgt in ("zh", "zh-CN") else tgt

        try:
            response = self.amazon_client.translate_text(
                Text=text,
                SourceLanguageCode=amazon_src,
                TargetLanguageCode=amazon_tgt
            )
            translated = response.get("TranslatedText")
            detected = response.get("SourceLanguageCode", src)
            if translated and translated.strip():
                return translated, detected
        except Exception as e:
            logger.warning("Aviso en Amazon Translate (%s). Alternando automáticamente a motores de respaldo.", e)
            return None
        return None

    def detect_language(self, text: str) -> str:
        """Detecta el código de idioma de un texto como salvaguarda."""
        if not text or len(text.strip()) == 0:
            return "es"
        try:
            detected = detect(text)
            return detected if detected in SUPPORTED_LANGUAGES else "es"
        except Exception:
            return "es"

    def _split_into_chunks(self, text: str) -> List[str]:
        """Divide el texto respetando saltos de línea para textos extensos o documentos."""
        if len(text) <= self.chunk_size:
            return [text]

        paragraphs = text.split("\n")
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p) + 1
            if current_len + p_len > self.chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [p]
                current_len = p_len
            else:
                current_chunk.append(p)
                current_len += p_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _translate_with_engines(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, str]:
        """
        Ejecuta la traducción probando una matriz de motores de alta confiabilidad
        con rotación automática en caso de error o límite de tasa.
        """
        src = LANG_MAP.get(source_lang, source_lang)
        tgt = LANG_MAP.get(target_lang, target_lang)

        # Matriz de endpoints y tokens autorizados sin bloqueos de scraping
        engine_configs = [
            # 1. Google Chrome Extension Engine (Alta velocidad, libre de 429)
            {
                "url": "https://translate.googleapis.com/translate_a/single",
                "params": {"client": "dict-chrome-ex", "sl": src, "tl": tgt, "dt": "t", "q": text},
                "parser": "google_single"
            },
            # 2. Google Android Client Engine
            {
                "url": "https://translate.google.com/translate_a/single",
                "params": {"client": "at", "sl": src, "tl": tgt, "dt": "t", "q": text},
                "parser": "google_single"
            },
            # 3. Google iOS Client Engine
            {
                "url": "https://translate.googleapis.com/translate_a/single",
                "params": {"client": "it", "sl": src, "tl": tgt, "dt": "t", "q": text},
                "parser": "google_single"
            },
            # 4. Google Clients5 Endpoint
            {
                "url": "https://clients5.google.com/translate_a/t",
                "params": {"client": "dict-chrome-ex", "sl": src, "tl": tgt, "q": text},
                "parser": "google_clients5"
            },
            # 5. MyMemory API con email de soporte
            {
                "url": "https://api.mymemory.translated.net/get",
                "params": {
                    "q": text,
                    "langpair": f"{LANG_MAP_MYMEMORY.get(src, 'es-ES' if src == 'auto' else src)}|{LANG_MAP_MYMEMORY.get(tgt, 'en-GB')}",
                    "de": "linguaflow-support@gmail.com"
                },
                "parser": "mymemory"
            }
        ]

        last_error = None

        for eng in engine_configs:
            try:
                resp = self.session.get(eng["url"], params=eng["params"], timeout=6)
                if resp.status_code == 200:
                    parser = eng["parser"]
                    if parser == "google_single":
                        data = resp.json()
                        translated = "".join(part[0] for part in data[0] if part and part[0])
                        detected = data[2] if len(data) > 2 and data[2] else (src if src != "auto" else "es")
                        if translated.strip():
                            return translated, detected

                    elif parser == "google_clients5":
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            item = data[0]
                            translated = item[0] if isinstance(item, list) else str(item)
                            if translated.strip():
                                return translated, (src if src != "auto" else "es")

                    elif parser == "mymemory":
                        data = resp.json()
                        trans = data.get("responseData", {}).get("translatedText")
                        if trans and "MYMEMORY WARNING" not in trans:
                            return trans, (src if src != "auto" else "es")

                logger.debug(f"Motor {eng['url']} devolvió código {resp.status_code}, rotando...")
            except Exception as e:
                last_error = e
                logger.debug(f"Aviso en motor {eng['url']}: {e}. Probando siguiente...")
                continue

        # Si todos fallaron, registrar y devolver el texto original con notificación
        logger.error(f"Todos los motores fallaron para texto '{text[:30]}...'. Error: {last_error}")
        return text, (src if src != "auto" else "es")

    def _translate_sync(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Ejecución síncrona por bloques con autodetección y rotación automática."""
        if not text or not text.strip():
            return {
                "translated_text": "",
                "source_lang": source_lang,
                "detected_lang": source_lang if source_lang != "auto" else "es",
                "target_lang": target_lang
            }

        # Si el idioma origen y destino son idénticos y no auto, retornar sin llamadas de red
        if source_lang != "auto" and source_lang == target_lang:
            return {
                "translated_text": text,
                "source_lang": source_lang,
                "detected_lang": source_lang,
                "target_lang": target_lang
            }

        chunks = self._split_into_chunks(text)
        translated_chunks = []
        detected_lang = source_lang

        for chunk in chunks:
            if not chunk.strip():
                translated_chunks.append(chunk)
                continue

            # 1. Intentar con Amazon Translate como motor principal
            amazon_result = self._translate_with_amazon(chunk, source_lang, target_lang)
            if amazon_result:
                trans_part, det_part = amazon_result
            else:
                # 2. Respaldo a matriz de motores secundarios
                trans_part, det_part = self._translate_with_engines(chunk, source_lang, target_lang)

            translated_chunks.append(trans_part)
            if det_part and det_part != "auto":
                detected_lang = det_part

        full_translation = "\n".join(translated_chunks)

        return {
            "translated_text": full_translation,
            "source_lang": source_lang,
            "detected_lang": detected_lang if detected_lang != "auto" else "es",
            "target_lang": target_lang
        }

    async def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> Dict[str, Any]:
        """Traducción asíncrona segura para el event loop de FastAPI."""
        return await asyncio.to_thread(self._translate_sync, text, source_lang, target_lang)

translation_service = TranslationService()
