import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.translation_service import translation_service
from app.services.db_service import db_service

logger = logging.getLogger("linguaflow.websocket")
router = APIRouter(tags=["WebSockets"])

GUEST_CHAR_LIMIT = 150

@router.websocket("/ws/translate")
async def websocket_translation_endpoint(websocket: WebSocket):
    """
    WebSocket bidireccional para traducción instantánea mientras el usuario escribe.
    Permite enviar ráfagas de texto y recibir la traducción sin latencia de handshake HTTP.
    """
    await websocket.accept()
    logger.info("Cliente WebSocket conectado a LinguaFlow.")

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
                text = payload.get("text", "")
                source_lang = payload.get("source_lang", "auto")
                target_lang = payload.get("target_lang", "en")
                token = payload.get("token")

                if not text or not text.strip():
                    await websocket.send_json({
                        "original_text": "",
                        "translated_text": "",
                        "detected_lang": source_lang,
                        "status": "empty"
                    })
                    continue

                # Validar sesión de usuario o aplicar límite de 150 caracteres para invitados
                user = db_service.get_user_by_token(token) if token else None
                if not user and len(text) > GUEST_CHAR_LIMIT:
                    await websocket.send_json({
                        "original_text": text,
                        "translated_text": "",
                        "error": f"Modo Invitado: Límite de {GUEST_CHAR_LIMIT} caracteres alcanzado. Inicia sesión para traducir sin límite.",
                        "status": "limit_reached"
                    })
                    continue

                # Traducir texto de manera asíncrona
                result = await translation_service.translate_text(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang
                )

                await websocket.send_json({
                    "original_text": text,
                    "translated_text": result["translated_text"],
                    "source_lang": result["source_lang"],
                    "detected_lang": result["detected_lang"],
                    "target_lang": result["target_lang"],
                    "status": "success"
                })

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Formato de mensaje inválido. Debe ser JSON."})
            except Exception as e:
                logger.error(f"Error procesando WebSocket: {e}")
                await websocket.send_json({"error": str(e), "status": "error"})

    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado normalmente.")
    except Exception as e:
        logger.warning(f"Excepción en conexión WebSocket: {e}")
