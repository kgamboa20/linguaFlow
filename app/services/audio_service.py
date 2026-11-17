import io
import os
import tempfile
import logging
import asyncio
from typing import Dict, Any, Optional
import edge_tts
from gtts import gTTS
import speech_recognition as sr

from app.config import EDGE_TTS_VOICES, SUPPORTED_LANGUAGES
from app.services.translation_service import translation_service

logger = logging.getLogger("linguaflow.audio")

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def generate_tts(self, text: str, lang: str = "es") -> bytes:
        """
        Genera audio MP3 a partir de texto.
        Prioriza las voces neuronales ultra naturales de Edge TTS,
        con fallback a gTTS si ocurre algún inconveniente.
        """
        if not text or not text.strip():
            raise ValueError("El texto para generar audio no puede estar vacío.")

        # Limitar longitud para síntesis de audio si es excesiva
        synthesize_text = text.strip()[:1000]

        # 1. Intentar con Edge TTS (Voz neuronal de alta definición)
        voice = EDGE_TTS_VOICES.get(lang, "es-ES-AlvaroNeural")
        try:
            communicate = edge_tts.Communicate(synthesize_text, voice)
            audio_buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.extend(chunk["data"])
            if len(audio_buffer) > 0:
                return bytes(audio_buffer)
        except Exception as e:
            logger.warning(f"Fallo en Edge TTS ({e}). Intentando fallback con gTTS...")

        # 2. Fallback con Google Text-to-Speech (gTTS)
        def _gtts_generate():
            tts_lang = lang if lang in SUPPORTED_LANGUAGES and lang != "auto" else "es"
            tts = gTTS(text=synthesize_text, lang=tts_lang, slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()

        return await asyncio.to_thread(_gtts_generate)

    def _transcribe_sync(self, audio_bytes: bytes, source_lang: str = "es") -> str:
        """
        Convierte bytes de audio a texto usando reconocimiento de voz.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_path = temp_audio.name
            temp_audio.write(audio_bytes)

        try:
            # speech_recognition requiere AudioFile (WAV o audio decodificable)
            with sr.AudioFile(temp_path) as source:
                # Ajustar para ruido ambiental
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio_data = self.recognizer.record(source)
                
            # Reconocer con Google Speech API (sin API key requerida)
            recognition_lang = "es-ES" if source_lang in ["es", "auto"] else f"{source_lang}-{source_lang.upper()}"
            transcript = self.recognizer.recognize_google(audio_data, language=recognition_lang)
            return transcript
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            logger.error(f"Error en servicio de reconocimiento de voz: {e}")
            raise RuntimeError(f"Error de conexión con servicio STT: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def transcribe_and_translate(
        self,
        audio_bytes: bytes,
        source_lang: str = "auto",
        target_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Procesa el audio, extrae la transcripción en el idioma original
        y genera la traducción simultánea al idioma objetivo.
        """
        effective_source = "es" if source_lang == "auto" else source_lang
        transcribed_text = await asyncio.to_thread(self._transcribe_sync, audio_bytes, effective_source)

        if not transcribed_text:
            return {
                "transcription": "",
                "translated_text": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "message": "No se detectó voz clara en el audio."
            }

        # Traducir la transcripción obtenida
        translation_result = await translation_service.translate_text(
            text=transcribed_text,
            source_lang=source_lang,
            target_lang=target_lang
        )

        return {
            "transcription": transcribed_text,
            "translated_text": translation_result["translated_text"],
            "detected_lang": translation_result["detected_lang"],
            "target_lang": target_lang,
            "message": "Éxito"
        }

audio_service = AudioService()
