import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import STATIC_DIR
from app.api.routes_translate import router as translate_router
from app.api.routes_audio import router as audio_router
from app.api.routes_documents import router as document_router
from app.api.websockets import router as websocket_router

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="LinguaFlow API",
    description="Plataforma de Traducción Multimodal en Tiempo Real (Texto, Voz y Documentos)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS para permitir peticiones seguras
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar Routers
app.include_router(translate_router)
app.include_router(audio_router)
app.include_router(document_router)
app.include_router(websocket_router)

# Montar archivos estáticos para la interfaz web (CSS, JS, Assets)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", summary="Página principal de LinguaFlow")
async def serve_index():
    """Sirve la aplicación de interfaz de usuario de LinguaFlow."""
    index_file = STATIC_DIR / "index.html"
    return FileResponse(str(index_file))

@app.get("/health", summary="Verificación de estado")
async def health_check():
    """Endpoint de monitoreo y health check."""
    return {"status": "healthy", "service": "LinguaFlow", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    # Ejecución directa para desarrollo local
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
