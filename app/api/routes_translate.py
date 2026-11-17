from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from app.config import SUPPORTED_LANGUAGES
from app.services.translation_service import translation_service

router = APIRouter(prefix="/api", tags=["Traducción"])

class TranslationRequest(BaseModel):
    text: str = Field(..., description="Texto a traducir", min_length=1)
    source_lang: str = Field("auto", description="Código de idioma origen o 'auto'")
    target_lang: str = Field("en", description="Código de idioma destino")

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    detected_lang: str
    target_lang: str
    status: str = "ok"

@router.get("/languages", summary="Obtener idiomas soportados")
async def get_supported_languages() -> Dict[str, str]:
    """Retorna el catálogo completo de idiomas con sus códigos ISO."""
    return SUPPORTED_LANGUAGES

@router.post("/translate", response_model=TranslationResponse, summary="Traducir texto")
async def translate_text_endpoint(req: TranslationRequest):
    """Traduce un fragmento de texto con detección automática opcional."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="El texto a traducir no puede estar vacío.")

    try:
        result = await translation_service.translate_text(
            text=req.text,
            source_lang=req.source_lang,
            target_lang=req.target_lang
        )
        return TranslationResponse(
            original_text=req.text,
            translated_text=result["translated_text"],
            source_lang=result["source_lang"],
            detected_lang=result["detected_lang"],
            target_lang=result["target_lang"],
            status="ok"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de traducción: {str(e)}")
