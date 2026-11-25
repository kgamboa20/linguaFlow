import re
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field, EmailStr, validator
from app.services.db_service import db_service
from app.services.email_service import email_service

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# -------------------------------------------------------------
# Esquemas Pydantic para Solicitudes y Respuestas
# -------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Nombre de usuario único")
    email: str = Field(..., min_length=5, max_length=100, description="Correo electrónico del usuario")
    password: str = Field(..., min_length=6, max_length=100, description="Contraseña segura (mínimo 6 caracteres)")
    full_name: Optional[str] = Field(None, max_length=80, description="Nombre completo o visible")

    @validator("username")
    def validate_username(cls, v):
        clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_.-]+$", clean):
            raise ValueError("El nombre de usuario solo puede contener letras, números, guiones y puntos.")
        return clean

    @validator("email")
    def validate_email(cls, v):
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("El formato del correo electrónico no es válido.")
        return clean

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        return v

class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1, description="Nombre de usuario o correo electrónico")
    password: str = Field(..., min_length=1, description="Contraseña de la cuenta")

class ForgotPasswordRequest(BaseModel):
    identifier: str = Field(..., min_length=2, max_length=100, description="Nombre de usuario o correo electrónico")

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Token de restablecimiento de contraseña")
    new_password: str = Field(..., min_length=6, max_length=100, description="Nueva contraseña")

class UserData(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: Optional[str] = None

class AuthResponse(BaseModel):
    status: str = "ok"
    message: str
    token: Optional[str] = None
    user: Optional[UserData] = None

# -------------------------------------------------------------
# Dependencia de Autenticación por Token Bearer
# -------------------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Extrae y valida el usuario activo a partir de la cabecera Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere iniciar sesión para acceder a este módulo.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split("Bearer ")[1].strip()
    user = db_service.get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o no válida. Inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Extrae el usuario activo si se envía un token válido, de lo contrario retorna None (modo invitado)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ")[1].strip()
    return db_service.get_user_by_token(token)

# -------------------------------------------------------------
# Endpoints de Autenticación
# -------------------------------------------------------------
@router.post("/register", response_model=AuthResponse, summary="Registro de nuevo usuario")
async def register(req: RegisterRequest):
    """
    Registra una nueva cuenta de usuario con contraseña cifrada.
    Envía un correo de bienvenida y requiere que el usuario inicie sesión.
    """
    try:
        user = db_service.create_user(
            username=req.username,
            email=req.email,
            password=req.password,
            full_name=req.full_name
        )
        
        # Enviar correo de bienvenida al nuevo usuario
        try:
            await email_service.send_welcome_email(
                to_email=user["email"],
                full_name=user.get("full_name") or user["username"],
                username=user["username"]
            )
        except Exception as mail_err:
            print(f"Aviso al enviar correo de bienvenida: {mail_err}")

        # No se retorna token para que el usuario sea redirigido a iniciar sesión
        return AuthResponse(
            status="ok",
            message="¡Cuenta creada con éxito! Te hemos enviado un correo de bienvenida. Por favor inicia sesión con tus credenciales.",
            token=None,
            user=UserData(**user)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error en el registro: {str(e)}")

@router.post("/login", response_model=AuthResponse, summary="Inicio de sesión")
async def login(req: LoginRequest):
    """
    Valida credenciales de un usuario existente por nombre de usuario o correo.
    Genera y retorna un token de sesión.
    """
    user = db_service.authenticate_user(req.username_or_email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifica tu usuario/correo y contraseña."
        )

    token = db_service.create_session(user["id"])
    return AuthResponse(
        status="ok",
        message=f"¡Hola de nuevo, {user['full_name']}!",
        token=token,
        user=UserData(**user)
    )

@router.post("/forgot-password", summary="Solicitud de recuperación de cuenta y contraseña")
async def forgot_password(req: ForgotPasswordRequest):
    """
    Localiza al usuario por nombre de usuario o correo.
    Envía un correo con el nombre de usuario y el enlace de restablecimiento.
    """
    clean_id = req.identifier.strip()
    user = db_service.get_user_by_username_or_email(clean_id)
    if user:
        token = db_service.create_password_reset(user["id"])
        try:
            await email_service.send_recovery_email(
                to_email=user["email"],
                username=user["username"],
                reset_token=token
            )
        except Exception as mail_err:
            print(f"Aviso al enviar correo de recuperación: {mail_err}")

    return {
        "status": "ok",
        "message": "Si los datos ingresados corresponden a una cuenta registrada, te hemos enviado un correo con tu nombre de usuario e instrucciones para restablecer tu contraseña."
    }

@router.post("/reset-password", summary="Restablecer contraseña mediante token")
async def reset_password(req: ResetPasswordRequest):
    """
    Valida el token de recuperación y actualiza la contraseña de la cuenta.
    """
    if len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 6 caracteres."
        )

    success = db_service.reset_password_with_token(req.token, req.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código o enlace de recuperación es inválido, ya fue utilizado o ha expirado. Por favor solicita uno nuevo."
        )

    return {
        "status": "ok",
        "message": "¡Tu contraseña ha sido restablecida exitosamente! Ahora puedes iniciar sesión con tu nueva contraseña."
    }

@router.get("/me", summary="Obtener usuario en sesión")
async def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna los datos del usuario actualmente autenticado."""
    return {"status": "ok", "user": user}

@router.post("/logout", summary="Cerrar sesión")
async def logout(authorization: Optional[str] = Header(None)):
    """Invalida el token de sesión activo."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        db_service.delete_session(token)
    return {"status": "ok", "message": "Sesión cerrada correctamente."}
