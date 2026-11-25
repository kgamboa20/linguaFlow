from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.config import SUPPORTED_LANGUAGES
from app.services.academy_service import academy_service
from app.api.routes_auth import get_current_user

router = APIRouter(prefix="/api/academy", tags=["Capacitaciones y Clases"])

class CustomLessonRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=120, description="Tema de la clase a generar")
    target_lang: str = Field(..., min_length=2, max_length=10, description="Código del idioma a aprender")

@router.get("/languages", summary="Idiomas disponibles para capacitación")
async def get_learning_languages() -> Dict[str, str]:
    """Retorna los idiomas en los que el usuario puede tomar clases."""
    return {code: name for code, name in SUPPORTED_LANGUAGES.items() if code != "auto"}

@router.get("/modules/{lang_code}", summary="Obtener módulos y clases de un idioma")
async def get_modules(
    lang_code: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Retorna el currículum interactivo completo. Requiere autenticación de usuario."""
    clean_code = lang_code.lower().strip()
    if clean_code not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail=f"Idioma '{clean_code}' no encontrado en el catálogo.")

    return await academy_service.get_modules_for_language(clean_code)

@router.post("/custom-lesson", summary="Generar clase personalizada por tema")
async def create_custom_lesson(
    req: CustomLessonRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Crea una capacitación en vivo sobre cualquier tema personalizado. Requiere autenticación de usuario."""
    clean_code = req.target_lang.lower().strip()
    if clean_code not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Código de idioma no válido.")

    try:
        return await academy_service.generate_custom_lesson(req.topic, clean_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando clase personalizada: {str(e)}")
