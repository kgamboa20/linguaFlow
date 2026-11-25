import smtplib
import logging
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_TLS,
    APP_URL
)

logger = logging.getLogger("linguaflow.email")

class EmailService:
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME
        self.tls = SMTP_TLS
        self.app_url = APP_URL.rstrip("/")

    def is_configured(self) -> bool:
        """Indica si el servidor SMTP tiene configuración básica para envíos reales."""
        return bool(self.host and self.from_email)

    def _send_smtp(self, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """Envío síncrono mediante smtplib con soporte para TLS."""
        if not self.is_configured():
            logger.info(
                "\n======================================================\n"
                "[SIMULACIÓN EMAIL] Servidor SMTP no configurado.\n"
                "Para: %s\n"
                "Asunto: %s\n"
                "Contenido:\n%s\n"
                "======================================================",
                to_email, subject, text_content
            )
            return True

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        # Versión en texto plano y versión en HTML enriquecido
        part_text = MIMEText(text_content, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_text)
        msg.attach(part_html)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())
            logger.info("Correo enviado exitosamente a %s [Asunto: %s]", to_email, subject)
            return True
        except Exception as e:
            logger.error("Error al enviar correo SMTP a %s: %s", to_email, e)
            return False

    async def send_welcome_email(self, to_email: str, full_name: str, username: str) -> bool:
        """Envía el correo de bienvenida a un usuario recién registrado."""
        display_name = full_name.strip() if full_name else username
        subject = f"¡Bienvenido a LinguaFlow, {display_name}! 🚀"
        login_url = f"{self.app_url}/"

        text_content = f"""¡Hola {display_name}!

¡Te damos la bienvenida a LinguaFlow! Tu cuenta ha sido creada exitosamente.

Tu nombre de usuario es: {username}
Tu correo registrado: {to_email}

Con tu nueva cuenta registrada tienes acceso ilimitado a:
- Traducción de texto sin límite de 150 caracteres.
- Traducción de voz en vivo con voces neuronales.
- Traducción integral de documentos (PDF, Word, TXT).
- LinguaAcademy: Clases interactivas y práctica de pronunciación.

Para ingresar a tu cuenta, visita:
{login_url}

¡Gracias por unirte a LinguaFlow!
Equipo de LinguaFlow
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f9fafb; margin: 0; padding: 20px; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
    .header {{ text-align: center; border-bottom: 1px solid #1f2937; padding-bottom: 20px; margin-bottom: 24px; }}
    .logo {{ font-size: 26px; font-weight: 800; color: #6366f1; letter-spacing: -0.5px; }}
    .badge {{ background: rgba(99,102,241,0.15); color: #818cf8; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }}
    h1 {{ font-size: 22px; color: #ffffff; margin-top: 16px; margin-bottom: 8px; }}
    p {{ font-size: 15px; line-height: 1.6; color: #9ca3af; margin: 8px 0; }}
    .highlight-card {{ background: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 16px; margin: 20px 0; }}
    .highlight-card strong {{ color: #f3f4f6; }}
    .perks-list {{ list-style: none; padding: 0; margin: 16px 0; }}
    .perks-list li {{ padding: 6px 0; color: #e5e7eb; font-size: 14px; display: flex; align-items: center; }}
    .perks-list li span {{ color: #10b981; margin-right: 8px; font-weight: bold; }}
    .btn {{ display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 700; font-size: 15px; margin-top: 16px; }}
    .footer {{ text-align: center; margin-top: 28px; font-size: 12px; color: #6b7280; border-top: 1px solid #1f2937; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">LinguaFlow <span class="badge">AI Translation</span></div>
      <h1>¡Bienvenido a LinguaFlow!</h1>
    </div>
    <p>Hola <strong>{display_name}</strong>,</p>
    <p>Tu cuenta ha sido creada exitosamente. Estamos emocionados de tenerte con nosotros.</p>
    
    <div class="highlight-card">
      <p><strong>Tus datos de acceso:</strong></p>
      <p>Usuario: <strong>@{username}</strong></p>
      <p>Correo electrónico: <strong>{to_email}</strong></p>
    </div>

    <p>Ahora tienes acceso total e ilimitado a todas nuestras herramientas:</p>
    <ul class="perks-list">
      <li><span>✓</span> Traducción de texto en tiempo real sin límite de caracteres</li>
      <li><span>✓</span> Interpretación y traducción de voz simultánea en vivo</li>
      <li><span>✓</span> Traducción integral de documentos completos (PDF, DOCX, TXT)</li>
      <li><span>✓</span> LinguaAcademy: Clases interactivas y práctica de pronunciación con IA</li>
    </ul>

    <div style="text-align: center; margin-top: 24px;">
      <a href="{login_url}" class="btn" style="color: #ffffff;">Iniciar Sesión en LinguaFlow</a>
    </div>

    <div class="footer">
      <p>Este correo fue enviado a {to_email} porque creaste una cuenta en LinguaFlow.</p>
    </div>
  </div>
</body>
</html>
"""
        return await asyncio.to_thread(self._send_smtp, to_email, subject, text_content, html_content)

    async def send_recovery_email(self, to_email: str, username: str, reset_token: str) -> bool:
        """Envía el correo de recuperación de credenciales y contraseña."""
        subject = "Recuperación de cuenta - LinguaFlow 🔐"
        reset_url = f"{self.app_url}/?reset_token={reset_token}"

        text_content = f"""Hola @{username},

Has solicitado recuperar el acceso a tu cuenta en LinguaFlow.

Recordatorio de tus credenciales:
- Nombre de usuario: {username}
- Correo electrónico: {to_email}

Para restablecer tu contraseña y definir una nueva, haz clic en el siguiente enlace o cópialo en tu navegador:
{reset_url}

Código de restablecimiento:
{reset_token}

Este enlace y código son válidos durante 24 horas. Si no solicitaste este cambio, puedes ignorar este mensaje de forma segura; tu contraseña actual continuará protegida.

Atentamente,
El equipo de seguridad de LinguaFlow
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f9fafb; margin: 0; padding: 20px; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
    .header {{ text-align: center; border-bottom: 1px solid #1f2937; padding-bottom: 20px; margin-bottom: 24px; }}
    .logo {{ font-size: 26px; font-weight: 800; color: #6366f1; letter-spacing: -0.5px; }}
    h1 {{ font-size: 20px; color: #ffffff; margin-top: 16px; margin-bottom: 8px; }}
    p {{ font-size: 15px; line-height: 1.6; color: #9ca3af; margin: 8px 0; }}
    .credentials-box {{ background: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 16px; margin: 20px 0; }}
    .credentials-box strong {{ color: #f3f4f6; }}
    .btn-reset {{ display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 700; font-size: 15px; margin: 20px 0; }}
    .token-box {{ font-family: monospace; background: #0b0f19; border: 1px dashed #4b5563; padding: 10px; border-radius: 6px; font-size: 13px; color: #a5b4fc; word-break: break-all; margin: 12px 0; }}
    .warning-text {{ font-size: 13px; color: #6b7280; font-style: italic; margin-top: 20px; }}
    .footer {{ text-align: center; margin-top: 28px; font-size: 12px; color: #6b7280; border-top: 1px solid #1f2937; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">LinguaFlow</div>
      <h1>Recuperación de Acceso a tu Cuenta</h1>
    </div>
    <p>Hola <strong>@{username}</strong>,</p>
    <p>Hemos recibido una solicitud para recuperar tu cuenta y restablecer tu contraseña en LinguaFlow.</p>
    
    <div class="credentials-box">
      <p><strong>Tu nombre de usuario es:</strong> <span style="color:#818cf8; font-size: 16px;">@{username}</span></p>
      <p><strong>Correo vinculado:</strong> {to_email}</p>
    </div>

    <p>Haz clic en el siguiente botón para restablecer tu contraseña:</p>
    <div style="text-align: center;">
      <a href="{reset_url}" class="btn-reset" style="color: #ffffff;">Restablecer mi Contraseña</a>
    </div>

    <p>O ingresa directamente este código de recuperación en la aplicación:</p>
    <div class="token-box">{reset_token}</div>

    <p class="warning-text">Este enlace es válido durante 24 horas. Si no solicitaste este cambio, ignora este correo y tu cuenta permanecerá segura.</p>

    <div class="footer">
      <p>Equipo de Soporte de LinguaFlow</p>
    </div>
  </div>
</body>
</html>
"""
        return await asyncio.to_thread(self._send_smtp, to_email, subject, text_content, html_content)

# Instancia singleton del servicio de correos
email_service = EmailService()
