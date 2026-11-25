import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional
import requests
from langdetect import detect, DetectorFactory
from app.config import (
    SUPPORTED_LANGUAGES,
    AZURE_TRANSLATOR_KEY,
    AZURE_TRANSLATOR_REGION,
    AZURE_TRANSLATOR_ENDPOINT
)

# Reproducibilidad en detección de idioma
DetectorFactory.seed = 0
logger = logging.getLogger("linguaflow.translation")

# Mapeo de códigos ISO generales
LANG_MAP = {
    "zh": "zh-CN",
    "auto": "auto"
}

# Mapeo de códigos ISO para Microsoft Translator (Azure)
LANG_MAP_AZURE = {
    "zh": "zh-Hans",
    "zh-CN": "zh-Hans"
}

# Mapeo inverso de detección de Azure a códigos internos
REVERSE_LANG_MAP_AZURE = {
    "zh-hans": "zh",
    "zh-hant": "zh",
    "pt-pt": "pt",
    "pt-br": "pt",
    "en-us": "en",
    "en-gb": "en",
    "es-es": "es"
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

        # Configuración de Microsoft Translator (Azure Cognitive Services - Motor principal)
        self.azure_key = (AZURE_TRANSLATOR_KEY or "").strip()
        self.azure_region = (AZURE_TRANSLATOR_REGION or "global").strip()
        self.azure_endpoint = (AZURE_TRANSLATOR_ENDPOINT or "https://api.cognitive.microsofttranslator.com").strip().rstrip("/")

        if self.azure_key:
            logger.info("Motor Microsoft Translator (Azure) activo (Región: %s, Endpoint: %s).", self.azure_region, self.azure_endpoint)
        else:
            logger.info("Microsoft Translator (Azure) en modo pasivo (sin AZURE_TRANSLATOR_KEY). Motores secundarios activos.")

    def _translate_with_azure(self, text: str, source_lang: str, target_lang: str) -> Optional[Tuple[str, str]]:
        """Traduce usando Microsoft Translator (Azure) como motor principal oficial."""
        if not self.azure_key:
            return None

        tgt = LANG_MAP_AZURE.get(target_lang, target_lang)

        # Si el idioma origen está definido y no es auto
        src = None
        if source_lang and source_lang != "auto":
            src = LANG_MAP_AZURE.get(source_lang, source_lang)
            if src == tgt:
                return text, source_lang

        # Construir endpoint y parámetros de Azure Translator v3.0
        url = f"{self.azure_endpoint}/translate"
        params = {
            "api-version": "3.0",
            "to": tgt
        }
        if src:
            params["from"] = src

        headers = {
            "Ocp-Apim-Subscription-Key": self.azure_key,
            "Content-Type": "application/json; charset=UTF-8"
        }
        if self.azure_region and self.azure_region.lower() != "global":
            headers["Ocp-Apim-Subscription-Region"] = self.azure_region

        body = [{"Text": text}]

        try:
            resp = self.session.post(url, params=params, headers=headers, json=body, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                    translations = item.get("translations", [])
                    if translations and len(translations) > 0:
                        translated_text = translations[0].get("text", "")

                        # Idioma detectado automáticamente por Azure si fue auto
                        detected = source_lang if source_lang != "auto" else "es"
                        if "detectedLanguage" in item:
                            detected_azure = item["detectedLanguage"].get("language", "")
                            detected = REVERSE_LANG_MAP_AZURE.get(detected_azure.lower(), detected_azure)

                        if translated_text and translated_text.strip():
                            return translated_text, detected
            else:
                logger.warning(
                    "Azure Translator devolvió estado %s: %s. Alternando automáticamente a motores de respaldo.",
                    resp.status_code, resp.text[:120]
                )
                return None
        except Exception as e:
            logger.warning("Error de conexión con Microsoft Translator Azure (%s). Alternando a motores de respaldo.", e)
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

            # 1. Intentar con Microsoft Translator (Azure) como motor principal
            azure_result = self._translate_with_azure(chunk, source_lang, target_lang)
            if azure_result:
                trans_part, det_part = azure_result
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
