# LinguaFlow 🌐⚡
> **Plataforma de Traducción Multimodal en Tiempo Real & LinguaAcademy**  
> Desarrollado con FastAPI, WebSockets, DeepL API (Free / Pro), Edge Neural TTS, Autenticación Segura y Procesamiento de Documentos.

---

## 🚀 Características Principales

1. **Traducción con DeepL API (Free & Pro)**:
   - Integración oficial con **DeepL API (Free & Pro)** como motor principal de traducción neuronal de alta fidelidad.
   - Rotación y respaldo automático transparente a matriz multi-proveedor de alta disponibilidad.
   - Detección automática nativa del idioma de origen y soporte integral para más de 18 idiomas.

2. **Control de Acceso y Modo Invitado**:
   - **Invitados:** Traducción de texto libre limitada a 150 caracteres.
   - **Usuarios Registrados:** Traducción de texto ilimitada, voz en vivo, documentos y academia.
   - Indicador visual con **punto verde** de sesión activa al lado del nombre de usuario.

3. **Sistema de Cuentas y Correos Automatizados**:
   - Registro seguro con contraseñas cifradas con salt criptográfico (PBKDF2-HMAC-SHA256).
   - **Correo de bienvenida** enviado automáticamente al crear una cuenta.
   - Flujo de bienvenida que redirige al usuario a iniciar sesión con sus credenciales.
   - **Recuperación de cuenta:** Envío de correo con nombre de usuario y enlace seguro para restablecer contraseña en caso de olvido.

4. **Audio a Texto y Síntesis Neuronal (STT & TTS)**:
   - Captura continua de voz por micrófono en tiempo real.
   - Síntesis de voz neuronal de alta fidelidad con **Edge TTS** (Microsoft Neural Voices) y fallback a **gTTS**.

5. **Traducción Integral de Documentos**:
   - Subida por arrastrar y soltar (Drag & Drop) de archivos **PDF**, **Word (.docx)** y **Texto (.txt)**.
   - Generación automática del archivo traducido listo para descargar (`.docx` / `.txt`).

6. **Academia y Capacitaciones de Idiomas (LinguaAcademy)**:
   - Módulos interactivos estructurados para aprender idiomas.
   - Práctica de pronunciación por micrófono con evaluación de precisión.
   - Evaluaciones interactivas (Quizzes) y generador de clases personalizadas por tema.

7. **Base de Datos Dual (Producción & Local)**:
   - Soporte automático para **PostgreSQL en la nube** (Render, Supabase, Neon) mediante `DATABASE_URL`.
   - Fallback transparente a **SQLite local** (`linguaflow.db`) para desarrollo.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| **Backend Framework** | **FastAPI** + **Uvicorn** | Framework asíncrono ASGI de alto rendimiento, nativo para WebSockets y concurrencia. |
| **Tiempo Real** | **WebSockets** (`/ws/translate`) | Comunicación bidireccional continua con latencia mínima, ideal para traducción mientras se escribe. |
| **Motor de Traducción** | `deep-translator` + `langdetect` | Conector versátil y libre a Google Translate, Deepl y LibreTranslate sin tarifas obligatorias. |
| **Voz (TTS)** | `edge-tts` + `gTTS` | Voces neuronales ultrarrealistas y gratuitas con entonación natural humana. |
| **Voz (STT)** | Web Speech API + `SpeechRecognition` | Reconocimiento en tiempo real con latencia cero en cliente y procesamiento en backend. |
| **Documentos** | `pypdf` + `python-docx` | Extracción eficiente de páginas PDF y generación nativa de documentos Word (.docx). |
| **Frontend** | HTML5, CSS3 Moderno, Vanilla JS | Diseño de alta gama tipo DeepL / Linear, modo oscuro/claro y sin dependencias pesadas de npm. |

---

## 📁 Estructura del Proyecto

```text
LinguaFlow/
│
├── .gitignore                      # Exclusiones de Git para entornos Python y temporales
├── requirements.txt                # Dependencias del proyecto
├── README.md                       # Documentación técnica completa
│
├── app/
│   ├── __init__.py                 # Inicialización del paquete app
│   ├── main.py                     # Entrypoint de FastAPI, montaje de rutas y static
│   ├── config.py                   # Configuración global, catálogo de idiomas y voces
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_translate.py     # Endpoints REST de traducción y catálogo
│   │   ├── routes_audio.py         # Endpoints para TTS (audio MP3) y STT
│   │   ├── routes_documents.py     # Endpoints de subida, traducción y descarga de archivos
│   │   └── websockets.py           # Conexión WebSocket para traducción streaming
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── translation_service.py  # Lógica de traducción por chunks y autodetección
│   │   ├── audio_service.py        # Generación de audio TTS y transcripción STT
│   │   └── document_service.py     # Extracción y ensamblado de PDF, DOCX y TXT
│   │
│   └── static/
│       ├── index.html              # Interfaz de usuario responsiva
│       ├── css/
│       │   └── style.css           # Estilos modernos, temas Dark/Light y animaciones
│       └── js/
│           └── app.js              # Controlador del cliente (WebSockets, Mic, Drag&Drop)
│
└── uploads/                        # Directorio temporal de procesamiento de documentos
```

---

## ⚙️ Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd LinguaFlow
```

### 2. Crear y activar entorno virtual de Python
En Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

En Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Ejecutar el servidor de desarrollo
Puedes ejecutarlo directamente con Python:
```bash
python app/main.py
```
O directamente con `uvicorn`:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Abrir la aplicación
- **Aplicación Web:** Abre tu navegador en [http://localhost:8000](http://localhost:8000)
- **Documentación Interactiva (Swagger/OpenAPI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Especificación Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔐 Variables de Entorno (Producción / Render)

Configura las siguientes variables en el panel de **Render** o en un archivo `.env`:

| Variable | Descripción | Valor por Defecto / Ejemplo |
|---|---|---|
| `DEEPL_API_KEY` | Clave de autenticación de DeepL API (Free termina en `:fx`, o Pro) | `tu-deepl-key:fx` |
| `DEEPL_API_ENDPOINT` | Endpoint de DeepL (opcional, auto-detecta Free vs Pro) | `https://api-free.deepl.com/v2/translate` |
| `DATABASE_URL` | Conexión PostgreSQL en la nube | `postgresql://user:pass@host/dbname` |
| `SMTP_HOST` | Host SMTP para envío de correos (bienvenida y recuperación) | `smtp.gmail.com` |
| `SMTP_PORT` | Puerto SMTP | `587` |
| `SMTP_USER` | Usuario o correo emisor SMTP | `tu-correo@gmail.com` |
| `SMTP_PASSWORD` | Contraseña o App Password de la cuenta SMTP | `tu-contraseña-o-app-token` |
| `APP_URL` | URL pública de la aplicación para enlaces de recuperación | `https://linguaflow.onrender.com` |

---

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Página principal de la aplicación web. |
| `GET` | `/health` | Healthcheck del servicio. |
| `POST` | `/api/auth/register` | Registro de nuevos usuarios con contraseña segura cifrada. |
| `POST` | `/api/auth/login` | Inicio de sesión con usuario/correo y contraseña. |
| `GET` | `/api/auth/me` | Obtiene el perfil del usuario autenticado (requiere Bearer token). |
| `POST` | `/api/auth/logout` | Cierre de sesión e invalidación del token. |
| `GET` | `/api/languages` | Lista de idiomas soportados y códigos ISO. |
| `GET` | `/api/academy/languages` | Catálogo de idiomas disponibles para clases y capacitación. |
| `GET` | `/api/academy/modules/{lang}` | Currículum interactivo completo, tarjetas de frases y quizzes del idioma. |
| `POST` | `/api/academy/custom-lesson` | Genera una clase temática especializada a medida con IA. |
| `POST` | `/api/translate` | Traducción síncrona/REST con detección de idioma. |
| `WS` | `/ws/translate` | Canal bidireccional WebSocket para traducción en tiempo real. |
| `GET` | `/api/audio/tts` | Genera y transmite voz natural MP3 a partir de texto. |
| `POST` | `/api/audio/transcribe-translate` | Procesa un archivo o grabación de voz y traduce su contenido. |
| `POST` | `/api/documents/upload-translate` | Procesa un PDF, DOCX o TXT y genera el archivo traducido. |
| `GET` | `/api/documents/download/{filename}` | Descarga del archivo traducido generado. |
