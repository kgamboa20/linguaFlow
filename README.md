# LinguaFlow 🌐⚡
> **Traductor Inteligente Multimodal en Tiempo Real**  
> Desarrollado con FastAPI, WebSockets, Deep Translator, Edge Neural TTS, Speech-to-Text y Procesamiento de Documentos.

---

## 🚀 Características Principales

1. **Texto a Texto en Tiempo Real**:
   - Traducción instantánea mientras el usuario escribe mediante **WebSockets** y debounce inteligente.
   - Detección automática del idioma de origen.
   - Conmutación rápida entre múltiples idiomas y atajos con un solo clic.

2. **Audio a Texto (Speech-to-Text)**:
   - Captura continua de la voz del micrófono en tiempo real.
   - Transcripción instantánea en pantalla y traducción simultánea.
   - Soporte para Web Speech API en el navegador y endpoints en backend con Python SpeechRecognition.

3. **Texto a Audio (Text-to-Speech)**:
   - Síntesis de voz neuronal de alta fidelidad con **Edge TTS** (Microsoft Neural Voices) y fallback a **gTTS**.
   - Pronunciación fluida, con acento natural en español, inglés, francés, alemán, japonés, etc.
   - Modo "Auto-reproducir" para conversaciones fluidas en vivo.

4. **Traducción Integral de Documentos**:
   - Subida por arrastrar y soltar (Drag & Drop) de archivos **PDF**, **Word (.docx)** y **Texto (.txt)**.
   - Extracción de texto respetando párrafos y estructura de contexto.
   - Generación automática del archivo traducido listo para descargar (`.docx` / `.txt`).

5. **Academia y Capacitaciones de Idiomas (LinguaAcademy)**:
   - Módulos interactivos tipo clases para aprender cualquiera de los 18 idiomas soportados.
   - Tarjetas de vocabulario con pronunciación fonética y audio neuronal nativo.
   - Práctica de pronunciación por micrófono con evaluación de similitud en tiempo real.
   - Evaluaciones interactivas (Quizzes) con retroalimentación pedagógica instantánea.
   - Generador de clases personalizadas sobre cualquier tema a medida.

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
