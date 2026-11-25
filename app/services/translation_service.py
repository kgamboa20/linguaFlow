import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional
import requests
from langdetect import detect, DetectorFactory
from app.config import (
    SUPPORTED_LANGUAGES,
    DEEPL_API_KEY,
    DEEPL_API_ENDPOINT
)

# Reproducibilidad en detección de idioma
DetectorFactory.seed = 0
logger = logging.getLogger("linguaflow.translation")

# Mapeo de códigos ISO generales
LANG_MAP = {
    "zh": "zh-CN",
    "auto": "auto"
}

# Mapeo de códigos ISO destino para DeepL API
LANG_MAP_DEEPL_TARGET = {
    "en": "EN-US",
    "pt": "PT-PT",
    "zh": "ZH",
    "es": "ES",
    "fr": "FR",
    "de": "DE",
    "it": "IT",
    "ru": "RU",
    "ja": "JA",
    "ko": "KO",
    "ar": "AR",
    "nl": "NL",
    "pl": "PL",
    "tr": "TR",
    "uk": "UK",
    "sv": "SV",
    "el": "EL"
}

# Idiomas origen soportados oficialmente por DeepL
DEEPL_SUPPORTED_SOURCES = {
    "es", "en", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
    "ar", "nl", "pl", "tr", "uk", "sv", "el"
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

        # Configuración de DeepL API (DeepL API Free & Pro - Motor principal)
        self.deepl_key = (DEEPL_API_KEY or "").strip()
        self.deepl_endpoint = (DEEPL_API_ENDPOINT or "https://api-free.deepl.com/v2/translate").strip()

        if self.deepl_key:
            tier = "Free" if ":fx" in self.deepl_key or "api-free" in self.deepl_endpoint else "Pro"
            logger.info("Motor DeepL API (%s) activo exitosamente (Endpoint: %s).", tier, self.deepl_endpoint)
        else:
            logger.info("DeepL API en modo pasivo (sin DEEPL_API_KEY). Motores secundarios activos.")

    def _translate_with_deepl(self, text: str, source_lang: str, target_lang: str) -> Optional[Tuple[str, str]]:
        """Traduce usando DeepL API Free / Pro como motor principal oficial."""
        if not self.deepl_key:
            return None

        clean_tgt = target_lang.lower().strip()
        deepl_tgt = LANG_MAP_DEEPL_TARGET.get(clean_tgt)
        if not deepl_tgt:
            # Idiomas no soportados nativamente por DeepL (ej. Hindi 'hi') van a motores de respaldo
            return None

        clean_src = source_lang.lower().strip() if source_lang else "auto"
        if clean_src != "auto" and clean_src == clean_tgt:
            return text, clean_src

        headers = {
            "Authorization": f"DeepL-Auth-Key {self.deepl_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "text": [text],
            "target_lang": deepl_tgt
        }

        # Si el origen es un idioma soportado por DeepL y no es auto
        if clean_src != "auto" and clean_src in DEEPL_SUPPORTED_SOURCES:
            payload["source_lang"] = clean_src.upper()

        try:
            resp = self.session.post(self.deepl_endpoint, headers=headers, json=payload, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                translations = data.get("translations", [])
                if translations and len(translations) > 0:
                    item = translations[0]
                    translated_text = item.get("text", "")
                    detected_deepl = item.get("detected_source_language", clean_src if clean_src != "auto" else "es")
                    detected = detected_deepl.lower()
                    if translated_text and translated_text.strip():
                        return translated_text, detected
            else:
                logger.warning(
                    "DeepL API devolvió código %s (%s). Alternando automáticamente a motores de respaldo.",
                    resp.status_code, resp.text[:120]
                )
                return None
        except Exception as e:
            logger.warning("Error de conexión con DeepL API (%s). Alternando a motores de respaldo.", e)
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

            # 1. Intentar con DeepL API como motor principal
            deepl_result = self._translate_with_deepl(chunk, source_lang, target_lang)
            if deepl_result:
                trans_part, det_part = deepl_result
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
