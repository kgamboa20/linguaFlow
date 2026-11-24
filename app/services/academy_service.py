import logging
import asyncio
from typing import Dict, Any, List, Optional
from app.config import SUPPORTED_LANGUAGES, EDGE_TTS_VOICES
from app.services.translation_service import translation_service

logger = logging.getLogger("linguaflow.academy")

# =====================================================================
# CURRÍCULUM MAESTRO DE CLASES Y CAPACITACIONES (PRE-CONFIGURADO ES / EN)
# =====================================================================
MASTER_MODULES = [
    {
        "id": "fundamentos",
        "title": "Fundamentos y Primeros Contactos",
        "level": "Principiante (A1)",
        "icon": "👋",
        "description": "Aprende a presentarte, saludar cordialmente y utilizar fórmulas de cortesía esenciales.",
        "lessons": [
            {
                "id": "saludos_1",
                "title": "Saludos cotidianos y presentaciones",
                "phrases": [
                    {
                        "es": "Hola, ¿cómo estás hoy?",
                        "en": "Hello, how are you today?",
                        "phonetic_en": "Jelóu, jáu ar iú tudéi?",
                        "context": "Saludo informal y cordial para iniciar cualquier conversación."
                    },
                    {
                        "es": "Buenos días, un placer conocerte.",
                        "en": "Good morning, nice to meet you.",
                        "phonetic_en": "Gud mórning, nais tu mit iú.",
                        "context": "Saludo formal apropiado para entornos profesionales o de primera cita."
                    },
                    {
                        "es": "¿Cómo te llamas? Mi nombre es...",
                        "en": "What is your name? My name is...",
                        "phonetic_en": "Guát is ior néim? Mái néim is...",
                        "context": "Fórmula fundamental para presentarse e intercambiar nombres."
                    },
                    {
                        "es": "Muchas gracias por tu ayuda, muy amable.",
                        "en": "Thank you very much for your help, you are very kind.",
                        "phonetic_en": "Tenk iú veri mach for ior jelp.",
                        "context": "Agradecimiento educado indispensable en cualquier interacción."
                    },
                    {
                        "es": "Disculpa, ¿puedes hablar un poco más despacio?",
                        "en": "Excuse me, could you speak a little slower?",
                        "phonetic_en": "Ekskiús mi, kud iú spik móur slóuli?",
                        "context": "Frase clave cuando estás aprendiendo y necesitas claridad auditiva."
                    },
                    {
                        "es": "Adiós, ¡que tengas un excelente día!",
                        "en": "Goodbye, have a wonderful day!",
                        "phonetic_en": "Gudbái, jav an ékselent déi!",
                        "context": "Despedida cálida y positiva para cerrar una conversación."
                    }
                ],
                "quiz": {
                    "question_es": "¿Cuál es la mejor frase formal para presentarte por primera vez?",
                    "correct_phrase_index": 1,
                    "tip": "Para entornos formales o de primera reunión se usa 'Good morning, nice to meet you'."
                }
            }
        ]
    },
    {
        "id": "viajes",
        "title": "Viajes, Aeropuerto y Transporte",
        "level": "Intermedio (A2)",
        "icon": "✈️",
        "description": "Domina las situaciones clave en aeropuertos, estaciones, taxis y reserva de hospedaje.",
        "lessons": [
            {
                "id": "viajes_1",
                "title": "En el aeropuerto y desplazamiento urbano",
                "phrases": [
                    {
                        "es": "¿Dónde está la puerta de embarque para mi vuelo?",
                        "en": "Where is the boarding gate for my flight?",
                        "phonetic_en": "Juer is de bórding géit for mái fláit?",
                        "context": "Pregunta imprescindible en terminales aéreas internacionales."
                    },
                    {
                        "es": "Tengo una reserva confirmada a mi nombre.",
                        "en": "I have a confirmed reservation under my name.",
                        "phonetic_en": "Ái jav a conférmd reservéishon ander mái néim.",
                        "context": "Úsala al llegar al hotel, alquiler de autos o mostrador de facturación."
                    },
                    {
                        "es": "¿Cuánto cuesta un boleto de metro hasta el centro de la ciudad?",
                        "en": "How much is a subway ticket to downtown?",
                        "phonetic_en": "Jáu mach is a sábuei tíket tu dáuntaun?",
                        "context": "Para consultar tarifas y transporte público en tu destino."
                    },
                    {
                        "es": "¿A qué hora sale el próximo tren o autobús?",
                        "en": "What time does the next train or bus leave?",
                        "phonetic_en": "Guát táim das de nekst tréin or bas liv?",
                        "context": "Para planificar horarios y evitar retrasos en conexiones."
                    },
                    {
                        "es": "Disculpe, me he perdido. ¿Podría indicarme el camino en el mapa?",
                        "en": "Excuse me, I am lost. Could you show me the way on the map?",
                        "phonetic_en": "Ekskiús mi, ái am lost. Kud iú shóu mi de uéi on de map?",
                        "context": "Solicitud de orientación amable para transeúntes o policías."
                    },
                    {
                        "es": "He extraviado mi equipaje, ¿dónde puedo hacer el reporte?",
                        "en": "I have lost my luggage, where can I file a report?",
                        "phonetic_en": "Ái jav lost mái láguedy, juer ken ái fáil a ripórt?",
                        "context": "Esencial para reclamar pérdidas o retrasos de maletas en el aeropuerto."
                    }
                ],
                "quiz": {
                    "question_es": "Si acabas de aterrizar y llegas al hotel, ¿qué debes decir al recepcionista?",
                    "correct_phrase_index": 1,
                    "tip": "Menciona que tienes una reserva confirmada: 'I have a confirmed reservation under my name'."
                }
            }
        ]
    },
    {
        "id": "restaurante",
        "title": "Gastronomía, Restaurantes y Pedidos",
        "level": "Práctico (A2-B1)",
        "icon": "🍽️",
        "description": "Pide comida como un local, consulta ingredientes, alergias y solicita la cuenta sin dudas.",
        "lessons": [
            {
                "id": "restaurante_1",
                "title": "Comer fuera y disfrutar de la gastronomía",
                "phrases": [
                    {
                        "es": "Una mesa para dos personas, por favor.",
                        "en": "A table for two people, please.",
                        "phonetic_en": "A téibl for tu pípol, plis.",
                        "context": "Para solicitar ubicación al anfitrión al ingresar a un restaurante."
                    },
                    {
                        "es": "¿Tiene el menú en inglés o español?",
                        "en": "Do you have the menu in English or Spanish?",
                        "phonetic_en": "Du iú jav de méniu in ínglish or spánish?",
                        "context": "Para pedir una versión del menú en un idioma más accesible."
                    },
                    {
                        "es": "¿Cuál es la especialidad de la casa o el plato más recomendado?",
                        "en": "What is the house specialty or most recommended dish?",
                        "phonetic_en": "Guát is de jáus speshíalti or moust recoménded dish?",
                        "context": "Ideal para probar la cocina autóctona y recibir sugerencias del chef."
                    },
                    {
                        "es": "Para beber deseo agua con gas y una copa de vino, por favor.",
                        "en": "To drink, I would like sparkling water and a glass of wine, please.",
                        "phonetic_en": "Tu drink, ái wud láik spárkling uóter and a glas of uáin, plis.",
                        "context": "Estructura estándar para ordenar bebidas durante el servicio."
                    },
                    {
                        "es": "Soy vegetariano y alérgico a los frutos secos.",
                        "en": "I am vegetarian and allergic to nuts.",
                        "phonetic_en": "Ái am veyetérian and aléryik tu nats.",
                        "context": "Información médica y alimentaria crucial para prevenir contratiempos."
                    },
                    {
                        "es": "¿Nos trae la cuenta, por favor? ¿Aceptan tarjeta de crédito?",
                        "en": "Could we have the bill, please? Do you accept credit cards?",
                        "phonetic_en": "Kud wi jav de bil, plis? Du iú aksépt krédit kards?",
                        "context": "Para finalizar la comida y confirmar el medio de pago."
                    }
                ],
                "quiz": {
                    "question_es": "¿Cómo pides la cuenta y preguntas si aceptan tarjeta?",
                    "correct_phrase_index": 5,
                    "tip": "La frase adecuada es: 'Could we have the bill, please? Do you accept credit cards?'."
                }
            }
        ]
    },
    {
        "id": "negocios",
        "title": "Negocios, Reuniones y Entorno Laboral",
        "level": "Avanzado (B1-B2)",
        "icon": "💼",
        "description": "Comunícate con diplomacia en juntas de trabajo, negociaciones, correos y presentaciones.",
        "lessons": [
            {
                "id": "negocios_1",
                "title": "Reuniones de trabajo y acuerdos estratégicos",
                "phrases": [
                    {
                        "es": "Es un placer colaborar con su equipo en este proyecto innovador.",
                        "en": "It is a pleasure to collaborate with your team on this innovative project.",
                        "phonetic_en": "Its a pléyer tu colaboréit guiz ior tim on dis inovétiv próyekt.",
                        "context": "Apertura profesional para forjar alianzas y establecer confianza."
                    },
                    {
                        "es": "¿Podríamos programar una videoconferencia para revisar los avances?",
                        "en": "Could we schedule a video conference to review the progress?",
                        "phonetic_en": "Kud wi skédiul a vídeo cónferens tu riviú de prógres?",
                        "context": "Para coordinar seguimiento y sincronización entre equipos."
                    },
                    {
                        "es": "Le enviaré la propuesta detallada y el presupuesto por correo electrónico.",
                        "en": "I will send you the detailed proposal and budget by email.",
                        "phonetic_en": "Ái wil send iú de ditéild propóusal and bádyet bái iméil.",
                        "context": "Compromiso de entrega de documentación formal tras una reunión."
                    },
                    {
                        "es": "Nuestro objetivo principal es maximizar la eficiencia y optimizar costos.",
                        "en": "Our main objective is to maximize efficiency and optimize costs.",
                        "phonetic_en": "Auar méin obyéktiv is tu máksimáiz efíshensi and óptimáiz kosts.",
                        "context": "Argumento de valor en discusiones financieras o de procesos."
                    },
                    {
                        "es": "Estamos totalmente de acuerdo con los términos estipulados en el contrato.",
                        "en": "We completely agree with the terms outlined in the contract.",
                        "phonetic_en": "Wi complítli egrí guiz de terms áutláind in de cóntrakt.",
                        "context": "Confirmación de conformidad para proceder a la firma o cierre."
                    },
                    {
                        "es": "Agradecemos enormemente su tiempo y valiosa retroalimentación.",
                        "en": "We truly appreciate your time and valuable feedback.",
                        "phonetic_en": "Wi trúli apríshieit ior táim and váliuabl fídback.",
                        "context": "Cierre elegante y profesional al finalizar una sesión de trabajo."
                    }
                ],
                "quiz": {
                    "question_es": "¿Qué frase usarías para enviar la propuesta formal después de una junta?",
                    "correct_phrase_index": 2,
                    "tip": "Usa la frase 'I will send you the detailed proposal and budget by email'."
                }
            }
        ]
    },
    {
        "id": "emergencias",
        "title": "Salud, Seguridad y Vida Diaria",
        "level": "Seguridad y Salud",
        "icon": "🏥",
        "description": "Vocabulario vital para farmacias, médicos, orientación de emergencia y vida diaria.",
        "lessons": [
            {
                "id": "emergencias_1",
                "title": "Asistencia médica y urgencias personales",
                "phrases": [
                    {
                        "es": "¡Necesito ayuda con urgencia, por favor llame a una ambulancia!",
                        "en": "I urgently need help, please call an ambulance!",
                        "phonetic_en": "Ái úryentli nid jelp, plis kol an ámbiulans!",
                        "context": "Para situaciones críticas que demandan socorro inmediato."
                    },
                    {
                        "es": "¿Dónde está la farmacia más cercana? Me duele mucho la cabeza.",
                        "en": "Where is the nearest pharmacy? I have a terrible headache.",
                        "phonetic_en": "Juer is de níarest fármasi? Ái jav a térribl jédeik.",
                        "context": "Para comprar analgésicos o consultar a un farmacéutico."
                    },
                    {
                        "es": "No me siento bien, tengo fiebre alta y mareos.",
                        "en": "I don't feel well, I have a high fever and dizziness.",
                        "phonetic_en": "Ái dount fil uel, ái jav a jái fíver and dízines.",
                        "context": "Para describir síntomas básicos al personal médico o en recepción."
                    },
                    {
                        "es": "He extraviado mi pasaporte, ¿dónde queda el consulado o embajada?",
                        "en": "I lost my passport, where is the consulate or embassy located?",
                        "phonetic_en": "Ái lost mái pásport, juer is de cónsiulat or émbasi loukéited?",
                        "context": "Indispensable ante el robo o pérdida de documentación oficial en el extranjero."
                    },
                    {
                        "es": "¿Podría prestarme su teléfono un momento para hacer una llamada de emergencia?",
                        "en": "Could you lend me your phone for a moment to make an emergency call?",
                        "phonetic_en": "Kud iú lend mi ior foun for a móument tu méik an iméryensi kol?",
                        "context": "Si te quedas sin batería o señal en una situación apremiante."
                    },
                    {
                        "es": "Todo está bajo control ahora, muchas gracias por su solidaridad.",
                        "en": "Everything is under control now, thank you so much for your support.",
                        "phonetic_en": "Évrizing is ánder contróul náu, tenk iú sou mach for ior sapórt.",
                        "context": "Para calmar la situación y agradecer a quienes te brindaron auxilio."
                    }
                ],
                "quiz": {
                    "question_es": "¿Cómo explicas en el hospital o farmacia que tienes fiebre alta y mareos?",
                    "correct_phrase_index": 2,
                    "tip": "La frase exacta es: 'I don't feel well, I have a high fever and dizziness'."
                }
            }
        ]
    }
]

class AcademyService:
    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    async def get_modules_for_language(self, target_lang: str) -> List[Dict[str, Any]]:
        """
        Obtiene el plan de estudios completo para el idioma seleccionado.
        Optimizado con respuestas inmediatas para inglés y español,
        y traducción por lotes (batch) en un solo viaje HTTP para otros idiomas.
        """
        clean_lang = target_lang.lower().strip()
        if clean_lang not in SUPPORTED_LANGUAGES or clean_lang == "auto":
            clean_lang = "en"

        if clean_lang in self._cache:
            return self._cache[clean_lang]

        # 1. Caso optimizado directo: Inglés o Español
        if clean_lang in ["en", "es"]:
            modules = []
            for master_mod in MASTER_MODULES:
                mod_copy = {
                    "id": master_mod["id"],
                    "title": master_mod["title"],
                    "level": master_mod["level"],
                    "icon": master_mod["icon"],
                    "description": master_mod["description"],
                    "lessons": []
                }
                for lesson in master_mod["lessons"]:
                    lesson_copy = {
                        "id": lesson["id"],
                        "title": lesson["title"],
                        "phrases": [],
                        "quiz": None
                    }
                    for phrase in lesson["phrases"]:
                        target_text = phrase["es"] if clean_lang == "es" else phrase["en"]
                        phonetic = phrase.get("phonetic_en", "") if clean_lang == "en" else ""
                        lesson_copy["phrases"].append({
                            "es": phrase["es"],
                            "target_text": target_text,
                            "phonetic": phonetic,
                            "context": phrase["context"]
                        })

                    # Quiz
                    q_meta = lesson["quiz"]
                    correct_idx = q_meta["correct_phrase_index"]
                    correct_phrase = lesson_copy["phrases"][correct_idx]["target_text"]
                    distractors = [
                        p["target_text"] for i, p in enumerate(lesson_copy["phrases"]) if i != correct_idx
                    ][:3]
                    options = [correct_phrase] + distractors
                    options_shuffled = [options[1], options[0], options[2], options[3]]
                    lesson_copy["quiz"] = {
                        "question": q_meta["question_es"],
                        "options": options_shuffled,
                        "correct_index": options_shuffled.index(correct_phrase),
                        "tip": q_meta["tip"]
                    }
                    mod_copy["lessons"].append(lesson_copy)
                modules.append(mod_copy)

            self._cache[clean_lang] = modules
            return modules

        # 2. Otros idiomas: Traducir en UN SOLO lote (Batch) por módulo para máxima velocidad
        modules = []
        for master_mod in MASTER_MODULES:
            mod_copy = {
                "id": master_mod["id"],
                "title": master_mod["title"],
                "level": master_mod["level"],
                "icon": master_mod["icon"],
                "description": master_mod["description"],
                "lessons": []
            }
            for lesson in master_mod["lessons"]:
                lesson_copy = {
                    "id": lesson["id"],
                    "title": lesson["title"],
                    "phrases": [],
                    "quiz": None
                }

                # Unir todas las frases del módulo con delimitador de salto de línea
                es_phrases = [p["es"] for p in lesson["phrases"]]
                batch_text = "\n".join(es_phrases)

                try:
                    tr_result = await translation_service.translate_text(
                        text=batch_text,
                        source_lang="es",
                        target_lang=clean_lang
                    )
                    translated_lines = [line.strip() for line in tr_result["translated_text"].split("\n") if line.strip()]
                except Exception as e:
                    logger.warning(f"Error en batch translation para {clean_lang}: {e}")
                    translated_lines = [p["en"] for p in lesson["phrases"]]

                for idx, phrase in enumerate(lesson["phrases"]):
                    target_text = translated_lines[idx] if idx < len(translated_lines) else phrase["en"]
                    lesson_copy["phrases"].append({
                        "es": phrase["es"],
                        "target_text": target_text,
                        "phonetic": "",
                        "context": phrase["context"]
                    })

                # Armar Quiz
                q_meta = lesson["quiz"]
                correct_idx = q_meta["correct_phrase_index"]
                correct_phrase = lesson_copy["phrases"][correct_idx]["target_text"]
                distractors = [
                    p["target_text"] for i, p in enumerate(lesson_copy["phrases"]) if i != correct_idx
                ][:3]
                options = [correct_phrase] + distractors
                options_shuffled = [options[1], options[0], options[2], options[3]]
                lesson_copy["quiz"] = {
                    "question": q_meta["question_es"],
                    "options": options_shuffled,
                    "correct_index": options_shuffled.index(correct_phrase),
                    "tip": q_meta["tip"]
                }
                mod_copy["lessons"].append(lesson_copy)
            modules.append(mod_copy)

        self._cache[clean_lang] = modules
        return modules

    async def generate_custom_lesson(self, topic: str, target_lang: str) -> Dict[str, Any]:
        """
        Genera una clase interactiva personalizada en tiempo real sobre cualquier tema.
        """
        clean_topic = topic.strip()
        if not clean_topic:
            raise ValueError("El tema de la clase no puede estar vacío.")

        base_phrases = [
            f"Me gustaría aprender más información sobre {clean_topic}.",
            f"¿Cuáles son los términos más importantes sobre {clean_topic}?",
            f"Estoy muy interesado en practicar este tema en situaciones cotidianas.",
            f"¿Podrías darme un ejemplo práctico de cómo usar esto?",
            f"¡Muchas gracias! Esta clase sobre {clean_topic} fue sumamente útil."
        ]

        batch_text = "\n".join(base_phrases)
        tr = await translation_service.translate_text(batch_text, source_lang="es", target_lang=target_lang)
        translated_lines = [l.strip() for l in tr["translated_text"].split("\n") if l.strip()]

        phrases_result = []
        for i, p in enumerate(base_phrases):
            t_text = translated_lines[i] if i < len(translated_lines) else p
            phrases_result.append({
                "es": p,
                "target_text": t_text,
                "phonetic": "",
                "context": f"Frase clave de capacitación sobre '{clean_topic}'."
            })

        quiz = {
            "question": f"¿Cómo indicarías en {SUPPORTED_LANGUAGES.get(target_lang, target_lang)} que te gustaría aprender más sobre este tema?",
            "options": [
                phrases_result[1]["target_text"],
                phrases_result[0]["target_text"],
                phrases_result[3]["target_text"],
                phrases_result[2]["target_text"]
            ],
            "correct_index": 1,
            "tip": "Usa la frase que expresa deseo de profundizar ('Me gustaría aprender más información...')."
        }

        return {
            "topic": clean_topic,
            "target_lang": target_lang,
            "lang_name": SUPPORTED_LANGUAGES.get(target_lang, target_lang),
            "phrases": phrases_result,
            "quiz": quiz
        }

academy_service = AcademyService()
