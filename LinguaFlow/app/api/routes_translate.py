from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from app.config import SUPPORTED_LANGUAGES
from app.services.translation_service import translation_service
from app.api.routes_auth import get_optional_user

router = APIRouter(prefix="/api", tags=["Traducción"])

GUEST_CHAR_LIMIT = 150

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
async def translate_text_endpoint(
    req: TranslationRequest,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """Traduce un fragmento de texto. Los usuarios invitados tienen un límite de 150 caracteres."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="El texto a traducir no puede estar vacío.")

    # Restricción de Modo Invitado: máximo 150 caracteres si no ha iniciado sesión
    if not user and len(req.text) > GUEST_CHAR_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"Modo Invitado: Límite de {GUEST_CHAR_LIMIT} caracteres alcanzado ({len(req.text)} caracteres enviados). Inicia sesión o crea una cuenta para traducir textos sin límites."
        )

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
