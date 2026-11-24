from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, Response, Depends
from typing import Dict, Any
from app.services.audio_service import audio_service
from app.api.routes_auth import get_current_user

router = APIRouter(prefix="/api/audio", tags=["Audio (STT & TTS)"])

@router.get("/tts", summary="Síntesis de voz (Text-to-Speech)")
async def text_to_speech(
    text: str = Query(..., description="Texto que se convertirá a voz", min_length=1),
    lang: str = Query("es", description="Código del idioma para la pronunciación")
):
    """
    Genera y reproduce audio con voces naturales (Edge Neural TTS / gTTS).
    Retorna un flujo de bytes con cabecera audio/mpeg.
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="El parámetro de texto no puede estar vacío.")

    try:
        audio_bytes = await audio_service.generate_tts(text=text, lang=lang)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando síntesis de voz: {str(e)}")

@router.post("/transcribe-translate", summary="Transcripción y Traducción de Audio (Speech-to-Text)")
async def transcribe_and_translate_endpoint(
    audio: UploadFile = File(..., description="Archivo de audio grabado (WAV, MP3, WebM)"),
    source_lang: str = Form("auto", description="Idioma del hablante o 'auto'"),
    target_lang: str = Form("en", description="Idioma al cual traducir la voz"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Recibe un audio capturado del micrófono, extrae la transcripción
    y traduce el contenido en tiempo real. Exclusivo para usuarios autenticados.
    """
    try:
        audio_content = await audio.read()
        if len(audio_content) == 0:
            raise HTTPException(status_code=400, detail="El archivo de audio está vacío.")

        result = await audio_service.transcribe_and_translate(
            audio_bytes=audio_content,
            source_lang=source_lang,
            target_lang=target_lang
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")
