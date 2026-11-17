import asyncio
import logging
from typing import Dict, Any, List
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from app.config import SUPPORTED_LANGUAGES

# Asegurar reproducibilidad en detección de idioma
DetectorFactory.seed = 0
logger = logging.getLogger("linguaflow.translation")

class TranslationService:
    def __init__(self):
        self.chunk_size = 4000  # Límite seguro para evitar truncamiento por petición

    def detect_language(self, text: str) -> str:
        """Detecta el código de idioma de un texto."""
        if not text or len(text.strip()) == 0:
            return "es"
        try:
            detected = detect(text)
            return detected if detected in SUPPORTED_LANGUAGES else "es"
        except Exception as e:
            logger.warning(f"Error detectando idioma: {e}. Fallback a 'es'.")
            return "es"

    def _split_into_chunks(self, text: str) -> List[str]:
        """Divide el texto respetando párrafos o saltos de línea."""
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

    def _translate_sync(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Ejecución síncrona de la traducción con deep-translator."""
        if not text or not text.strip():
            return {
                "translated_text": "",
                "source_lang": source_lang,
                "detected_lang": source_lang if source_lang != "auto" else "es",
                "target_lang": target_lang
            }

        detected_lang = source_lang
        if source_lang == "auto":
            detected_lang = self.detect_language(text)

        # Si el idioma origen y destino son el mismo, devolver directo
        if detected_lang == target_lang:
            return {
                "translated_text": text,
                "source_lang": source_lang,
                "detected_lang": detected_lang,
                "target_lang": target_lang
            }

        chunks = self._split_into_chunks(text)
        translated_chunks = []

        translator = GoogleTranslator(source=source_lang, target=target_lang)

        for chunk in chunks:
            if not chunk.strip():
                translated_chunks.append(chunk)
                continue
            translated = translator.translate(chunk)
            translated_chunks.append(translated if translated else chunk)

        full_translation = "\n".join(translated_chunks)

        return {
            "translated_text": full_translation,
            "source_lang": source_lang,
            "detected_lang": detected_lang,
            "target_lang": target_lang
        }

    async def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> Dict[str, Any]:
        """Traducción asíncrona segura para el event loop de FastAPI."""
        return await asyncio.to_thread(self._translate_sync, text, source_lang, target_lang)

translation_service = TranslationService()
