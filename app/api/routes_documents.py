import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from app.config import UPLOAD_DIR, MAX_FILE_SIZE_BYTES
from app.services.document_service import document_service

router = APIRouter(prefix="/api/documents", tags=["Documentos"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

@router.post("/upload-translate", summary="Subir y traducir documento")
async def upload_and_translate_document(
    file: UploadFile = File(..., description="Documento a traducir (PDF, DOCX, TXT)"),
    source_lang: str = Form("auto", description="Idioma de origen"),
    target_lang: str = Form("en", description="Idioma de destino")
):
    """
    Extrae el texto de un archivo PDF, DOCX o TXT, realiza la traducción
    manteniendo el contexto y estructura, y genera un archivo descargable.
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo '{file_ext}' no permitido. Formatos aceptados: PDF, DOCX, TXT."
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="El archivo subido está vacío.")

    try:
        result = await document_service.process_document(
            file_bytes=file_bytes,
            original_filename=file.filename,
            source_lang=source_lang,
            target_lang=target_lang
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al traducir el documento: {str(e)}")

@router.get("/download/{filename}", summary="Descargar documento traducido")
async def download_translated_document(filename: str):
    """Permite descargar el documento traducido generado."""
    # Validación de seguridad para evitar path traversal
    safe_filename = Path(filename).name
    file_path = Path(UPLOAD_DIR) / safe_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="El archivo solicitado no existe o ha expirado.")

    media_type = "application/octet-stream"
    if safe_filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif safe_filename.endswith(".txt"):
        media_type = "text/plain; charset=utf-8"

    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type=media_type
    )
