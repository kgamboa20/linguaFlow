/**
 * LinguaFlow - Aplicación Frontend en Tiempo Real
 * Arquitectura modular con WebSockets, Web Speech API, TTS y Procesamiento de Documentos.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ==========================================
  // Estado Global de la Aplicación
  // ==========================================
  const state = {
    languages: {},
    activeTab: "text-tab",
    ws: null,
    wsConnected: false,
    typingTimer: null,
    typingDelay: 250, // ms debounce para traducción en vivo
    recognition: null,
    isRecording: false,
    selectedDocFile: null,
    theme: localStorage.getItem("linguaflow_theme") || "dark",
    user: null,
    token: localStorage.getItem("linguaflow_token") || null
  };

  // ==========================================
  // Elementos DOM
  // ==========================================
  // Tema y Conexión
  const body = document.body;
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const wsStatusBadge = document.getElementById("wsStatusBadge");
  const toastContainer = document.getElementById("toastContainer");
  const ttsPlayer = document.getElementById("ttsAudioPlayer");

  // Tabs & Lock Icons
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const lockIconVoice = document.getElementById("lockIconVoice");
  const lockIconDocs = document.getElementById("lockIconDocs");
  const lockIconAcademy = document.getElementById("lockIconAcademy");

  // Tab 1: Texto & Modo Invitado
  const textSourceLang = document.getElementById("textSourceLang");
  const textTargetLang = document.getElementById("textTargetLang");
  const detectedLangTag = document.getElementById("detectedLangTag");
  const swapLangsBtn = document.getElementById("swapLangsBtn");
  const quickLangPills = document.querySelectorAll("#quickLangPills .pill");
  const sourceText = document.getElementById("sourceText");
  const targetText = document.getElementById("targetText");
  const sourceCharCount = document.getElementById("sourceCharCount");
  const targetCharCount = document.getElementById("targetCharCount");
  const charLimitLabel = document.getElementById("charLimitLabel");
  const guestTierBanner = document.getElementById("guestTierBanner");
  const guestBannerAuthBtn = document.getElementById("guestBannerAuthBtn");
  const clearTextBtn = document.getElementById("clearTextBtn");
  const translatingIndicator = document.getElementById("translatingIndicator");
  const listenSourceBtn = document.getElementById("listenSourceBtn");
  const listenTargetBtn = document.getElementById("listenTargetBtn");
  const copyTargetBtn = document.getElementById("copyTargetBtn");

  // Tab 2: Voz & Lock Gate
  const voiceLockGate = document.getElementById("voiceLockGate");
  const voiceMainLayout = document.getElementById("voiceMainLayout");
  const micRecordBtn = document.getElementById("micRecordBtn");
  const voiceStatusText = document.getElementById("voiceStatusText");
  const audioWaveVisualizer = document.getElementById("audioWaveVisualizer");
  const voiceSourceLang = document.getElementById("voiceSourceLang");
  const voiceTargetLang = document.getElementById("voiceTargetLang");
  const autoSpeakToggle = document.getElementById("autoSpeakToggle");
  const voiceTranscriptBox = document.getElementById("voiceTranscriptBox");
  const voiceTranslationBox = document.getElementById("voiceTranslationBox");
  const clearVoiceBtn = document.getElementById("clearVoiceBtn");
  const speakVoiceResultBtn = document.getElementById("speakVoiceResultBtn");
  const copyVoiceResultBtn = document.getElementById("copyVoiceResultBtn");

  // Tab 3: Documentos & Lock Gate
  const docsLockGate = document.getElementById("docsLockGate");
  const docsMainLayout = document.getElementById("docsMainLayout");
  const documentDropZone = document.getElementById("documentDropZone");
  const docFileInput = document.getElementById("docFileInput");
  const selectedFileCard = document.getElementById("selectedFileCard");
  const fileNameDisplay = document.getElementById("fileNameDisplay");
  const fileSizeDisplay = document.getElementById("fileSizeDisplay");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const docTargetLang = document.getElementById("docTargetLang");
  const startDocTranslateBtn = document.getElementById("startDocTranslateBtn");
  const docProgressBarContainer = document.getElementById("docProgressBarContainer");
  const docProgressBar = document.getElementById("docProgressBar");
  const docProgressPercent = document.getElementById("docProgressPercent");
  const docProgressText = document.getElementById("docProgressText");
  const docResultCard = document.getElementById("docResultCard");
  const docDownloadBtn = document.getElementById("docDownloadBtn");
  const docOriginalPreview = document.getElementById("docOriginalPreview");
  const docTranslatedPreview = document.getElementById("docTranslatedPreview");

  // Tab 4: Capacitaciones / Clases (LinguaAcademy) & Lock Gate
  const academyLockGate = document.getElementById("academyLockGate");
  const academyMainLayout = document.getElementById("academyMainLayout");
  const academyTargetLang = document.getElementById("academyTargetLang");
  const academyModulesList = document.getElementById("academyModulesList");
  const customLessonForm = document.getElementById("customLessonForm");
  const customLessonTopic = document.getElementById("customLessonTopic");
  const customLessonBtn = document.getElementById("customLessonBtn");
  const lessonLevelBadge = document.getElementById("lessonLevelBadge");
  const lessonLangTargetName = document.getElementById("lessonLangTargetName");
  const lessonTitle = document.getElementById("lessonTitle");
  const lessonDescription = document.getElementById("lessonDescription");
  const tabStudyModeBtn = document.getElementById("tabStudyModeBtn");
  const tabQuizModeBtn = document.getElementById("tabQuizModeBtn");
  const lessonStudyPane = document.getElementById("lessonStudyPane");
  const lessonQuizPane = document.getElementById("lessonQuizPane");
  const phrasesCardsGrid = document.getElementById("phrasesCardsGrid");
  const gateAuthButtons = document.querySelectorAll(".btn-gate-auth");
  const quizQuestion = document.getElementById("quizQuestion");
  const quizOptionsGrid = document.getElementById("quizOptionsGrid");
  const quizFeedbackBox = document.getElementById("quizFeedbackBox");
  const quizFeedbackIcon = document.getElementById("quizFeedbackIcon");
  const quizFeedbackText = document.getElementById("quizFeedbackText");
  const quizTipText = document.getElementById("quizTipText");
  const pronunciationFeedbackCard = document.getElementById("pronunciationFeedbackCard");
  const pronunciationResultText = document.getElementById("pronunciationResultText");
  const pronunciationScoreBadge = document.getElementById("pronunciationScoreBadge");
  const closePronunciationBtn = document.getElementById("closePronunciationBtn");

  // Autenticación de Usuario (Navbar & Modal)
  const openAuthModalBtn = document.getElementById("openAuthModalBtn");
  const userProfileMenu = document.getElementById("userProfileMenu");
  const userProfileBtn = document.getElementById("userProfileBtn");
  const userOnlineDot = document.getElementById("userOnlineDot");
  const userDropdownCard = document.getElementById("userDropdownCard");
  const userAvatarInitial = document.getElementById("userAvatarInitial");
  const userDisplayName = document.getElementById("userDisplayName");
  const dropdownAvatarLg = document.getElementById("dropdownAvatarLg");
  const dropdownFullName = document.getElementById("dropdownFullName");
  const dropdownEmail = document.getElementById("dropdownEmail");
  const dropdownUsername = document.getElementById("dropdownUsername");
  const logoutBtn = document.getElementById("logoutBtn");

  // Modal Auth
  const authModalBackdrop = document.getElementById("authModalBackdrop");
  const closeAuthModalBtn = document.getElementById("closeAuthModalBtn");
  const authModalTitle = document.getElementById("authModalTitle");
  const authModalSubtitle = document.getElementById("authModalSubtitle");
  const tabLoginBtn = document.getElementById("tabLoginBtn");
  const tabRegisterBtn = document.getElementById("tabRegisterBtn");
  const authAlertBox = document.getElementById("authAlertBox");
  const authAlertMessage = document.getElementById("authAlertMessage");

  // Formulario Login
  const loginForm = document.getElementById("loginForm");
  const loginIdentifier = document.getElementById("loginIdentifier");
  const loginPassword = document.getElementById("loginPassword");
  const loginSubmitBtn = document.getElementById("loginSubmitBtn");
  const linkSwitchToRegister = document.getElementById("linkSwitchToRegister");
  const linkForgotPassword = document.getElementById("linkForgotPassword");

  // Formulario Registro
  const registerForm = document.getElementById("registerForm");
  const regFullName = document.getElementById("regFullName");
  const regUsername = document.getElementById("regUsername");
  const regEmail = document.getElementById("regEmail");
  const regPassword = document.getElementById("regPassword");
  const regPasswordConfirm = document.getElementById("regPasswordConfirm");
  const registerSubmitBtn = document.getElementById("registerSubmitBtn");
  const linkSwitchToLogin = document.getElementById("linkSwitchToLogin");
  const linkForgotFromRegister = document.getElementById("linkForgotFromRegister");

  // Formulario Recuperación de Cuenta / Contraseña
  const forgotPasswordForm = document.getElementById("forgotPasswordForm");
  const recoveryIdentifier = document.getElementById("recoveryIdentifier");
  const recoverySubmitBtn = document.getElementById("recoverySubmitBtn");
  const linkBackToLogin = document.getElementById("linkBackToLogin");

  // Formulario Reset Contraseña
  const resetPasswordForm = document.getElementById("resetPasswordForm");
  const resetTokenInput = document.getElementById("resetTokenInput");
  const newPasswordInput = document.getElementById("newPasswordInput");
  const confirmNewPasswordInput = document.getElementById("confirmNewPasswordInput");
  const resetPasswordSubmitBtn = document.getElementById("resetPasswordSubmitBtn");
  const linkCancelReset = document.getElementById("linkCancelReset");

  // ==========================================
  // Inicialización del Tema (Dark / Light)
  // ==========================================
  function applyTheme(theme) {
    if (theme === "light") {
      body.classList.remove("theme-dark");
      body.classList.add("theme-light");
    } else {
      body.classList.remove("theme-light");
      body.classList.add("theme-dark");
    }
    state.theme = theme;
    localStorage.setItem("linguaflow_theme", theme);
  }

  applyTheme(state.theme);

  themeToggleBtn.addEventListener("click", () => {
    applyTheme(state.theme === "dark" ? "light" : "dark");
  });

  // ==========================================
  // Sistema de Notificaciones Toast
  // ==========================================
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✓" : type === "error" ? "⚠" : "ℹ";
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(20px)";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  // ==========================================
  // Navegación por Pestañas (Tabs)
  // ==========================================
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      state.activeTab = tabId;

      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(tabId).classList.add("active");

      if (tabId === "academy-tab") {
        if (!state.academyLoaded) {
          loadAcademyModules(academyTargetLang.value || "en");
        }
      }
    });
  });

  // ==========================================
  // Carga de Catálogo de Idiomas desde la API
  // ==========================================
  async function loadSupportedLanguages() {
    try {
      const response = await fetch("/api/languages");
      if (!response.ok) throw new Error("No se pudo obtener el catálogo de idiomas.");
      const langs = await response.json();
      state.languages = langs;

      populateSelect(textSourceLang, langs, true, "auto");
      populateSelect(textTargetLang, langs, false, "en");
      populateSelect(voiceSourceLang, langs, true, "es");
      populateSelect(voiceTargetLang, langs, false, "en");
      populateSelect(docTargetLang, langs, false, "en");
      populateSelect(academyTargetLang, langs, false, "en");

      // Carga inicial de módulos de la academia en inglés
      loadAcademyModules("en");
    } catch (err) {
      console.error(err);
      showToast("Error al cargar lista de idiomas", "error");
    }
  }

  function populateSelect(selectElement, langs, allowAuto = false, defaultVal = "en") {
    const previousVal = selectElement.value || defaultVal;
    selectElement.innerHTML = "";
    Object.entries(langs).forEach(([code, name]) => {
      if (!allowAuto && code === "auto") return;
      const option = document.createElement("option");
      option.value = code;
      option.textContent = name;
      if (code === previousVal) {
        option.selected = true;
      }
      selectElement.appendChild(option);
    });
    if (!selectElement.value && selectElement.options.length > 0) {
      selectElement.value = defaultVal;
    }
  }

  // ==========================================
  // Motor WebSocket para Tiempo Real
  // ==========================================
  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/translate`;

    try {
      state.ws = new WebSocket(wsUrl);

      state.ws.onopen = () => {
        state.wsConnected = true;
        if (wsStatusBadge) {
          wsStatusBadge.classList.remove("disconnected");
          const st = wsStatusBadge.querySelector(".status-text");
          if (st) st.textContent = "Tiempo Real";
        }
      };

      state.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          translatingIndicator.classList.add("hidden");

          if (data.status === "success") {
            targetText.value = data.translated_text;
            targetCharCount.textContent = data.translated_text.length;

            if (data.detected_lang && textSourceLang.value === "auto") {
              const langName = state.languages[data.detected_lang] || data.detected_lang.toUpperCase();
              detectedLangTag.textContent = `Detectado: ${langName}`;
              detectedLangTag.classList.remove("hidden");
            }

            // Guardar en historial después de una pausa de escritura
            saveToHistory(data.original_text, data.translated_text, data.detected_lang || "auto", data.target_lang);
          } else if (data.status === "empty") {
            targetText.value = "";
            targetCharCount.textContent = "0";
            detectedLangTag.classList.add("hidden");
          } else if (data.status === "error" || data.error) {
            console.error("Error en WebSocket de traducción:", data.error);
            showToast(data.error || "Error al traducir texto", "error");
          }
        } catch (e) {
          console.error("Error analizando mensaje WebSocket:", e);
        }
      };

      state.ws.onclose = () => {
        state.wsConnected = false;
        if (wsStatusBadge) {
          wsStatusBadge.classList.add("disconnected");
          const st = wsStatusBadge.querySelector(".status-text");
          if (st) st.textContent = "Reconectando...";
        }
        setTimeout(initWebSocket, 3000); // Intento de reconexión
      };

      state.ws.onerror = (err) => {
        console.warn("WebSocket advertencia/error:", err);
        state.wsConnected = false;
      };
    } catch (err) {
      console.error("No se pudo inicializar WebSocket:", err);
      state.wsConnected = false;
    }
  }

  // Traducción síncrona/asíncrona con debounce
  function handleLiveTranslation() {
    let text = sourceText.value;

    // Control de límite para usuarios invitados (sin sesión)
    if (!state.user && text.length > 150) {
      text = text.slice(0, 150);
      sourceText.value = text;
      showToast("Modo Invitado limitado a 150 caracteres. Inicia sesión para traducciones ilimitadas.", "info");
    }

    sourceCharCount.textContent = text.length;

    clearTimeout(state.typingTimer);

    if (!text.trim()) {
      targetText.value = "";
      targetCharCount.textContent = "0";
      detectedLangTag.classList.add("hidden");
      translatingIndicator.classList.add("hidden");
      return;
    }

    translatingIndicator.classList.remove("hidden");

    state.typingTimer = setTimeout(() => {
      sendTranslationRequest(text, textSourceLang.value, textTargetLang.value);
    }, state.typingDelay);
  }

  async function sendTranslationRequest(text, sourceLang, targetLang) {
    // 1. Usar WebSocket si está disponible
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify({
        text: text,
        source_lang: sourceLang,
        target_lang: targetLang,
        token: state.token || null
      }));
      return;
    }

    // 2. Fallback a API REST
    try {
      const headers = { "Content-Type": "application/json" };
      if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
      }

      const resp = await fetch("/api/translate", {
        method: "POST",
        headers: headers,
        body: JSON.stringify({
          text: text,
          source_lang: sourceLang,
          target_lang: targetLang
        })
      });

      translatingIndicator.classList.add("hidden");

      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({ detail: "Error en el servidor." }));
        throw new Error(errorData.detail || "Error en la respuesta del servidor.");
      }
      const data = await resp.json();

      targetText.value = data.translated_text;
      targetCharCount.textContent = data.translated_text.length;

      if (data.detected_lang && textSourceLang.value === "auto") {
        const langName = state.languages[data.detected_lang] || data.detected_lang;
        detectedLangTag.textContent = `Detectado: ${langName}`;
        detectedLangTag.classList.remove("hidden");
      }

      saveToHistory(data.original_text, data.translated_text, data.detected_lang, data.target_lang);
    } catch (err) {
      translatingIndicator.classList.add("hidden");
      console.error(err);
      showToast("Error al traducir texto", "error");
    }
  }

  // Event Listeners para Tab 1
  sourceText.addEventListener("input", handleLiveTranslation);
  textSourceLang.addEventListener("change", handleLiveTranslation);
  textTargetLang.addEventListener("change", handleLiveTranslation);

  clearTextBtn.addEventListener("click", () => {
    sourceText.value = "";
    targetText.value = "";
    sourceCharCount.textContent = "0";
    targetCharCount.textContent = "0";
    detectedLangTag.classList.add("hidden");
    sourceText.focus();
  });

  swapLangsBtn.addEventListener("click", () => {
    if (textSourceLang.value === "auto") {
      showToast("Selecciona un idioma específico antes de intercambiar.", "info");
      return;
    }
    const temp = textSourceLang.value;
    textSourceLang.value = textTargetLang.value;
    textTargetLang.value = temp;

    const tempText = sourceText.value;
    sourceText.value = targetText.value;
    targetText.value = tempText;

    handleLiveTranslation();
  });

  quickLangPills.forEach(pill => {
    pill.addEventListener("click", () => {
      const lang = pill.getAttribute("data-lang");
      textTargetLang.value = lang;
      quickLangPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      handleLiveTranslation();
    });
  });

  copyTargetBtn.addEventListener("click", async () => {
    if (!targetText.value) return;
    try {
      await navigator.clipboard.writeText(targetText.value);
      showToast("¡Traducción copiada al portapapeles!", "success");
    } catch (e) {
      showToast("Error al copiar texto", "error");
    }
  });

  // ==========================================
  // Síntesis de Voz (Text-to-Speech)
  // ==========================================
  async function playTTS(text, lang) {
    if (!text || !text.trim()) {
      showToast("No hay texto para reproducir.", "info");
      return;
    }

    try {
      const cleanLang = lang === "auto" ? "es" : lang;
      const url = `/api/audio/tts?text=${encodeURIComponent(text.trim())}&lang=${cleanLang}`;
      ttsPlayer.src = url;
      await ttsPlayer.play();
    } catch (err) {
      console.warn("Fallo en audio remoto de backend. Usando Web Speech API local:", err);
      // Fallback a SpeechSynthesis del navegador
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang === "auto" ? "es-ES" : lang;
        window.speechSynthesis.speak(utterance);
      } else {
        showToast("Tu navegador no soporta síntesis de voz.", "error");
      }
    }
  }

  listenSourceBtn.addEventListener("click", () => {
    playTTS(sourceText.value, textSourceLang.value);
  });

  listenTargetBtn.addEventListener("click", () => {
    playTTS(targetText.value, textTargetLang.value);
  });

  // ==========================================
  // Tab 2: Speech-to-Text y Traducción Simultánea
  // ==========================================
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    state.recognition = new SpeechRecognition();
    state.recognition.continuous = true;
    state.recognition.interimResults = true;

    state.recognition.onstart = () => {
      state.isRecording = true;
      micRecordBtn.classList.add("recording");
      audioWaveVisualizer.classList.remove("hidden");
      voiceStatusText.textContent = "Escuchando... Habla ahora";
    };

    state.recognition.onresult = async (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const currentSpeech = (finalTranscript || interimTranscript).trim();
      if (currentSpeech) {
        voiceTranscriptBox.textContent = currentSpeech;

        // Traducir simultáneamente
        try {
          const headers = { "Content-Type": "application/json" };
          if (state.token) {
            headers["Authorization"] = `Bearer ${state.token}`;
          }
          const resp = await fetch("/api/translate", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
              text: currentSpeech,
              source_lang: voiceSourceLang.value,
              target_lang: voiceTargetLang.value
            })
          });

          if (resp.ok) {
            const data = await resp.json();
            voiceTranslationBox.textContent = data.translated_text;

            // Si es un enunciado final y el usuario activó auto-speak, reproducir
            if (finalTranscript && autoSpeakToggle.checked) {
              playTTS(data.translated_text, voiceTargetLang.value);
            }
          }
        } catch (e) {
          console.error("Error en traducción de voz:", e);
        }
      }
    };

    state.recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopRecording();
      if (event.error === "not-allowed") {
        showToast("Permiso de micrófono denegado. Permite el acceso en el navegador.", "error");
      }
    };

    state.recognition.onend = () => {
      if (state.isRecording) {
        // Reiniciar si se detuvo inesperadamente durante grabación activa
        try { state.recognition.start(); } catch(e) {}
      } else {
        stopRecording();
      }
    };
  }

  function startRecording() {
    if (!state.recognition) {
      showToast("Tu navegador no soporta reconocimiento de voz en vivo nativo.", "error");
      return;
    }
    const sourceCode = voiceSourceLang.value;
    state.recognition.lang = sourceCode === "auto" ? "es-ES" : sourceCode;
    state.isRecording = true;
    try {
      state.recognition.start();
    } catch (e) {
      console.warn("Reconocimiento ya activo o error:", e);
    }
  }

  function stopRecording() {
    state.isRecording = false;
    micRecordBtn.classList.remove("recording");
    audioWaveVisualizer.classList.add("hidden");
    voiceStatusText.textContent = "Presiona el micrófono para hablar";
    if (state.recognition) {
      try { state.recognition.stop(); } catch(e) {}
    }
  }

  micRecordBtn.addEventListener("click", () => {
    if (state.isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  clearVoiceBtn.addEventListener("click", () => {
    voiceTranscriptBox.innerHTML = '<span class="placeholder-italic">Las palabras que pronuncies aparecerán aquí en vivo...</span>';
    voiceTranslationBox.innerHTML = '<span class="placeholder-italic">La traducción inmediata de tu voz aparecerá aquí...</span>';
  });

  speakVoiceResultBtn.addEventListener("click", () => {
    const text = voiceTranslationBox.textContent;
    if (text && !text.includes("aparecerá aquí")) {
      playTTS(text, voiceTargetLang.value);
    }
  });

  copyVoiceResultBtn.addEventListener("click", async () => {
    const text = voiceTranslationBox.textContent;
    if (text && !text.includes("aparecerá aquí")) {
      await navigator.clipboard.writeText(text);
      showToast("Traducción de voz copiada", "success");
    }
  });

  // ==========================================
  // Tab 3: Traducción de Documentos (PDF, DOCX, TXT)
  // ==========================================
  documentDropZone.addEventListener("click", () => docFileInput.click());

  documentDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    documentDropZone.classList.add("dragover");
  });

  documentDropZone.addEventListener("dragleave", () => {
    documentDropZone.classList.remove("dragover");
  });

  documentDropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    documentDropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleSelectedDoc(e.dataTransfer.files[0]);
    }
  });

  docFileInput.addEventListener("change", () => {
    if (docFileInput.files.length > 0) {
      handleSelectedDoc(docFileInput.files[0]);
    }
  });

  function handleSelectedDoc(file) {
    const validExtensions = [".pdf", ".docx", ".doc", ".txt", ".md"];
    const ext = "." + file.name.split(".").pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
      showToast(`Formato "${ext}" no admitido. Usa PDF, DOCX o TXT.`, "error");
      return;
    }

    state.selectedDocFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = formatBytes(file.size);

    selectedFileCard.classList.remove("hidden");
    startDocTranslateBtn.disabled = false;
    docResultCard.classList.add("hidden");
  }

  removeFileBtn.addEventListener("click", () => {
    state.selectedDocFile = null;
    docFileInput.value = "";
    selectedFileCard.classList.add("hidden");
    startDocTranslateBtn.disabled = true;
    docResultCard.classList.add("hidden");
  });

  startDocTranslateBtn.addEventListener("click", async () => {
    if (!state.selectedDocFile) return;

    startDocTranslateBtn.disabled = true;
    docProgressBarContainer.classList.remove("hidden");
    docResultCard.classList.add("hidden");

    let progress = 10;
    docProgressBar.style.width = "10%";
    docProgressPercent.textContent = "10%";
    docProgressText.textContent = "Extrayendo y analizando texto del archivo...";

    const progressInterval = setInterval(() => {
      if (progress < 85) {
        progress += Math.floor(Math.random() * 15) + 5;
        docProgressBar.style.width = `${progress}%`;
        docProgressPercent.textContent = `${progress}%`;
        if (progress > 50) docProgressText.textContent = "Traduciendo párrafos manteniendo contexto...";
      }
    }, 400);

    const formData = new FormData();
    formData.append("file", state.selectedDocFile);
    formData.append("source_lang", "auto");
    formData.append("target_lang", docTargetLang.value);

    try {
      const docHeaders = {};
      if (state.token) {
        docHeaders["Authorization"] = `Bearer ${state.token}`;
      }

      const response = await fetch("/api/documents/upload-translate", {
        method: "POST",
        headers: docHeaders,
        body: formData
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Error procesando documento" }));
        throw new Error(errorData.detail || "Error en el servidor al traducir archivo.");
      }

      const result = await response.json();

      // Completar barra al 100%
      docProgressBar.style.width = "100%";
      docProgressPercent.textContent = "100%";
      docProgressText.textContent = "¡Traducción completada con éxito!";

      setTimeout(() => {
        docProgressBarContainer.classList.add("hidden");
        docResultCard.classList.remove("hidden");

        docOriginalPreview.textContent = result.extracted_preview || "Sin vista previa";
        docTranslatedPreview.textContent = result.translated_preview || "Sin vista previa";
        docDownloadBtn.href = result.download_url;
        docDownloadBtn.setAttribute("download", result.output_filename);

        showToast("¡Documento traducido y listo para descargar!", "success");
        startDocTranslateBtn.disabled = false;
      }, 500);

    } catch (err) {
      clearInterval(progressInterval);
      docProgressBarContainer.classList.add("hidden");
      startDocTranslateBtn.disabled = false;
      showToast(err.message, "error");
      console.error(err);
    }
  });

  function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  }

  // ==========================================
  // Tab 4: LinguaAcademy (Capacitaciones y Clases)
  // ==========================================
  function saveToHistory() {
    // Apartado de historial reemplazado por Capacitaciones
  }

  async function loadAcademyModules(langCode) {
    if (!state.user) {
      return; // Bloqueado para modo invitado (se muestra academyLockGate)
    }
    state.academyLoaded = true;
    const targetLang = langCode || academyTargetLang.value || "en";
    const langName = state.languages[targetLang] || targetLang;
    lessonLangTargetName.textContent = langName;

    academyModulesList.innerHTML = `
      <div style="padding: 1.5rem; text-align: center; color: var(--text-secondary);">
        <span class="spinner-sm"></span> Cargando módulos de ${escapeHTML(langName)}...
      </div>
    `;

    try {
      const headers = {};
      if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
      }
      const resp = await fetch(`/api/academy/modules/${targetLang}`, { headers });
      if (!resp.ok) throw new Error("No se pudieron cargar los módulos de capacitación.");
      const modules = await resp.json();
      state.academyModules = modules;

      renderAcademyModulesList(modules);
      if (modules.length > 0) {
        selectAcademyModule(modules[0]);
      }
    } catch (err) {
      console.error(err);
      academyModulesList.innerHTML = `
        <div style="padding: 1rem; color: var(--danger); font-size: 0.85rem;">
          Error al cargar clases de este idioma. Intenta de nuevo.
        </div>
      `;
    }
  }

  function renderAcademyModulesList(modules) {
    academyModulesList.innerHTML = "";

    modules.forEach((mod, idx) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = `academy-module-item ${idx === 0 ? "active" : ""}`;
      item.setAttribute("data-mod-id", mod.id);
      item.innerHTML = `
        <div class="mod-icon">${mod.icon || "📚"}</div>
        <div class="mod-info">
          <strong>${escapeHTML(mod.title)}</strong>
          <span class="mod-level">${escapeHTML(mod.level)}</span>
        </div>
      `;

      item.addEventListener("click", () => {
        document.querySelectorAll(".academy-module-item").forEach(b => b.classList.remove("active"));
        item.classList.add("active");
        selectAcademyModule(mod);
      });

      academyModulesList.appendChild(item);
    });
  }

  function selectAcademyModule(mod) {
    state.currentModule = mod;
    lessonLevelBadge.textContent = mod.level;
    lessonTitle.textContent = mod.title;
    lessonDescription.textContent = mod.description;

    const lesson = (mod.lessons && mod.lessons[0]) || null;
    const targetLang = academyTargetLang.value || "en";

    if (lesson) {
      renderPhraseCards(lesson.phrases || [], targetLang);
      renderQuiz(lesson.quiz);
    } else {
      phrasesCardsGrid.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">No hay frases cargadas para esta lección.</p>`;
    }

    // Por defecto modo estudio activo
    switchLessonTab("study");
  }

  function renderPhraseCards(phrases, targetLang) {
    phrasesCardsGrid.innerHTML = "";

    phrases.forEach((phrase) => {
      const card = document.createElement("div");
      card.className = "phrase-card";
      card.innerHTML = `
        <div class="phrase-texts">
          <div class="phrase-target">${escapeHTML(phrase.target_text)}</div>
          ${phrase.phonetic ? `<div class="phrase-phonetic">🗣️ ${escapeHTML(phrase.phonetic)}</div>` : ""}
          <div class="phrase-native">🇪🇸 ${escapeHTML(phrase.es)}</div>
          <div class="phrase-context">💡 ${escapeHTML(phrase.context || "Uso práctico")}</div>
        </div>
        <div class="phrase-actions">
          <button class="btn-phrase-audio" type="button" title="Escuchar pronunciación nativa">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            <span>Escuchar</span>
          </button>
          <button class="btn-phrase-mic" type="button" title="Practicar pronunciación con micrófono">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></svg>
            <span>Practicar</span>
          </button>
        </div>
      `;

      // Evento Escuchar TTS
      const audioBtn = card.querySelector(".btn-phrase-audio");
      audioBtn.addEventListener("click", () => {
        playTTS(phrase.target_text, targetLang);
      });

      // Evento Practicar con Micrófono
      const micBtn = card.querySelector(".btn-phrase-mic");
      micBtn.addEventListener("click", () => {
        handlePracticePronunciation(phrase.target_text, targetLang, micBtn);
      });

      phrasesCardsGrid.appendChild(card);
    });
  }

  function renderQuiz(quiz) {
    if (!quiz) {
      quizCard.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No hay evaluación para esta clase.</p>`;
      return;
    }

    quizQuestion.textContent = quiz.question;
    quizTipText.textContent = quiz.tip || "Revisa las frases anteriores para recordar la respuesta correcta.";
    quizFeedbackBox.classList.add("hidden");
    quizFeedbackBox.className = "quiz-feedback-box hidden";
    quizOptionsGrid.innerHTML = "";

    quiz.options.forEach((optText, optIdx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quiz-option-btn";
      btn.textContent = optText;

      btn.addEventListener("click", () => {
        const isCorrect = optIdx === quiz.correct_index;

        // Deshabilitar todas las opciones
        document.querySelectorAll(".quiz-option-btn").forEach((b, i) => {
          b.disabled = true;
          if (i === quiz.correct_index) {
            b.classList.add("correct");
          } else if (b === btn && !isCorrect) {
            b.classList.add("incorrect");
          }
        });

        // Mostrar feedback
        quizFeedbackBox.classList.remove("hidden");
        if (isCorrect) {
          quizFeedbackBox.className = "quiz-feedback-box correct";
          quizFeedbackIcon.textContent = "✓";
          quizFeedbackText.textContent = "¡Respuesta Correcta! Excelente retención del idioma.";
          showToast("¡Respuesta correcta! Felicitaciones 🎉", "success");
        } else {
          quizFeedbackBox.className = "quiz-feedback-box incorrect";
          quizFeedbackIcon.textContent = "✗";
          quizFeedbackText.textContent = "Casi... La respuesta correcta ha sido resaltada en verde.";
        }
      });

      quizOptionsGrid.appendChild(btn);
    });
  }

  // Práctica de pronunciación interactiva con reconocimiento de voz
  function handlePracticePronunciation(expectedText, langCode, micBtn) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      showToast("Tu navegador no soporta captura de voz nativa.", "error");
      return;
    }

    const rec = new SpeechRec();
    rec.lang = langCode === "auto" ? "en-US" : langCode;
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    micBtn.classList.add("recording");
    micBtn.querySelector("span").textContent = "Habla...";
    showToast(`Di en voz alta: "${expectedText}"`, "info");

    rec.onresult = (e) => {
      micBtn.classList.remove("recording");
      micBtn.querySelector("span").textContent = "Practicar";

      const spoken = e.results[0][0].transcript.trim();
      evaluateSpokenAccuracy(spoken, expectedText);
    };

    rec.onerror = () => {
      micBtn.classList.remove("recording");
      micBtn.querySelector("span").textContent = "Practicar";
      showToast("No se pudo capturar audio. Verifica el permiso de micrófono.", "error");
    };

    rec.onend = () => {
      micBtn.classList.remove("recording");
      micBtn.querySelector("span").textContent = "Practicar";
    };

    try {
      rec.start();
    } catch (err) {
      micBtn.classList.remove("recording");
      micBtn.querySelector("span").textContent = "Practicar";
    }
  }

  function evaluateSpokenAccuracy(spoken, target) {
    pronunciationFeedbackCard.classList.remove("hidden");
    pronunciationResultText.textContent = `Dijiste: "${spoken}"`;

    const normSpoken = spoken.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "").trim();
    const normTarget = target.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "").trim();

    if (normSpoken === normTarget || normTarget.includes(normSpoken) || normSpoken.includes(normTarget)) {
      pronunciationScoreBadge.textContent = "¡Excelente pronunciación! 🎉";
      pronunciationScoreBadge.style.color = "var(--success)";
      pronunciationScoreBadge.style.borderColor = "var(--success)";
      showToast("¡Pronunciación excelente!", "success");
    } else {
      pronunciationScoreBadge.textContent = "¡Buen intento! Escucha el audio y repítelo de nuevo.";
      pronunciationScoreBadge.style.color = "var(--warning)";
      pronunciationScoreBadge.style.borderColor = "var(--warning)";
    }
  }

  // Cambiar entre Pestaña Estudio y Pestaña Quiz
  function switchLessonTab(tab) {
    if (tab === "study") {
      tabStudyModeBtn.classList.add("active");
      tabQuizModeBtn.classList.remove("active");
      lessonStudyPane.classList.remove("hidden");
      lessonQuizPane.classList.add("hidden");
    } else {
      tabQuizModeBtn.classList.add("active");
      tabStudyModeBtn.classList.remove("active");
      lessonQuizPane.classList.remove("hidden");
      lessonStudyPane.classList.add("hidden");
    }
  }

  tabStudyModeBtn.addEventListener("click", () => switchLessonTab("study"));
  tabQuizModeBtn.addEventListener("click", () => switchLessonTab("quiz"));

  // Evento Cambio de Idioma en la Academia
  academyTargetLang.addEventListener("change", () => {
    loadAcademyModules(academyTargetLang.value);
  });

  // Generador de Clase Personalizada
  customLessonForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const topic = customLessonTopic.value.trim();
    if (!topic) return;

    const targetLang = academyTargetLang.value || "en";
    customLessonBtn.disabled = true;
    customLessonBtn.innerHTML = `<span class="spinner-sm"></span> Diseñando clase...`;

    try {
      const customHeaders = { "Content-Type": "application/json" };
      if (state.token) {
        customHeaders["Authorization"] = `Bearer ${state.token}`;
      }
      const resp = await fetch("/api/academy/custom-lesson", {
        method: "POST",
        headers: customHeaders,
        body: JSON.stringify({
          topic: topic,
          target_lang: targetLang
        })
      });

      if (!resp.ok) throw new Error("No se pudo generar la clase personalizada.");
      const customLesson = await resp.json();

      const newMod = {
        id: `custom_${Date.now()}`,
        title: `Clase: ${customLesson.topic}`,
        level: "Personalizada ✨",
        icon: "💡",
        description: `Capacitación interactiva enfocada en el tema solicitado: "${customLesson.topic}".`,
        lessons: [
          {
            id: `lesson_custom`,
            title: `Vocabulario de ${customLesson.topic}`,
            phrases: customLesson.phrases,
            quiz: customLesson.quiz
          }
        ]
      };

      state.academyModules.unshift(newMod);
      renderAcademyModulesList(state.academyModules);
      selectAcademyModule(newMod);
      customLessonForm.reset();
      showToast(`¡Clase de "${topic}" creada con éxito!`, "success");

    } catch (err) {
      console.error(err);
      showToast(err.message || "Error al generar clase.", "error");
    } finally {
      customLessonBtn.disabled = false;
      customLessonBtn.innerHTML = `<span>Crear Clase Personalizada</span>`;
    }
  });

  closePronunciationBtn.addEventListener("click", () => {
    pronunciationFeedbackCard.classList.add("hidden");
  });

  function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }

  function escapeAttr(str) {
    return str.replace(/"/g, '&quot;');
  }

  // ==========================================
  // Sistema de Autenticación de Usuarios
  // ==========================================

  // Verificar sesión activa al cargar
  async function checkAuthStatus() {
    if (!state.token) {
      renderUserUI();
      return;
    }

    try {
      const resp = await fetch("/api/auth/me", {
        headers: { "Authorization": `Bearer ${state.token}` }
      });

      if (resp.ok) {
        const data = await resp.json();
        state.user = data.user;
      } else {
        // Token inválido o expirado
        state.token = null;
        state.user = null;
        localStorage.removeItem("linguaflow_token");
      }
    } catch (err) {
      console.warn("No se pudo verificar el estado de autenticación:", err);
    } finally {
      renderUserUI();
    }
  }

  // Actualizar la interfaz de usuario según el estado de sesión
  function renderUserUI() {
    if (state.user) {
      openAuthModalBtn.classList.add("hidden");
      userProfileMenu.classList.remove("hidden");
      if (userOnlineDot) userOnlineDot.classList.remove("hidden");

      const displayName = state.user.full_name || state.user.username || "Usuario";
      const initial = displayName.trim().charAt(0).toUpperCase();

      userAvatarInitial.textContent = initial;
      dropdownAvatarLg.textContent = initial;
      userDisplayName.textContent = displayName;
      dropdownFullName.textContent = displayName;
      dropdownEmail.textContent = state.user.email || "";
      dropdownUsername.textContent = `@${state.user.username}`;

      // Ocultar candados en pestañas
      if (lockIconVoice) lockIconVoice.classList.add("hidden");
      if (lockIconDocs) lockIconDocs.classList.add("hidden");
      if (lockIconAcademy) lockIconAcademy.classList.add("hidden");

      // Desbloquear módulos y mostrar contenidos
      if (voiceLockGate) voiceLockGate.classList.add("hidden");
      if (voiceMainLayout) voiceMainLayout.classList.remove("hidden");

      if (docsLockGate) docsLockGate.classList.add("hidden");
      if (docsMainLayout) docsMainLayout.classList.remove("hidden");

      if (academyLockGate) academyLockGate.classList.add("hidden");
      if (academyMainLayout) academyMainLayout.classList.remove("hidden");

      // Banner y límite en traducción de texto
      if (guestTierBanner) guestTierBanner.classList.add("hidden");
      if (charLimitLabel) charLimitLabel.textContent = " caracteres (Ilimitado)";

      // Cargar módulos de la academia si no estaban cargados
      if (!state.academyLoaded && state.languages && Object.keys(state.languages).length > 0) {
        loadAcademyModules(academyTargetLang.value || "en");
      }
    } else {
      openAuthModalBtn.classList.remove("hidden");
      userProfileMenu.classList.add("hidden");
      userDropdownCard.classList.add("hidden");
      userProfileMenu.classList.remove("open");
      if (userOnlineDot) userOnlineDot.classList.add("hidden");

      // Mostrar candados en pestañas
      if (lockIconVoice) lockIconVoice.classList.remove("hidden");
      if (lockIconDocs) lockIconDocs.classList.remove("hidden");
      if (lockIconAcademy) lockIconAcademy.classList.remove("hidden");

      // Bloquear módulos con lock gate y ocultar layouts
      if (voiceLockGate) voiceLockGate.classList.remove("hidden");
      if (voiceMainLayout) voiceMainLayout.classList.add("hidden");

      if (docsLockGate) docsLockGate.classList.remove("hidden");
      if (docsMainLayout) docsMainLayout.classList.add("hidden");

      if (academyLockGate) academyLockGate.classList.remove("hidden");
      if (academyMainLayout) academyMainLayout.classList.add("hidden");

      // Banner y límite de 150 caracteres en texto
      if (guestTierBanner) guestTierBanner.classList.remove("hidden");
      if (charLimitLabel) charLimitLabel.textContent = " / 150 caracteres (Invitado)";

      // Truncar texto si excede 150 caracteres
      if (sourceText && sourceText.value.length > 150) {
        sourceText.value = sourceText.value.slice(0, 150);
        handleLiveTranslation();
      }
    }
  }

  // Abrir y cerrar el modal
  function openAuthModal(initialTab = "login") {
    authModalBackdrop.classList.remove("hidden");
    hideAuthAlert();
    switchAuthTab(initialTab);
  }

  function closeAuthModal() {
    authModalBackdrop.classList.add("hidden");
    hideAuthAlert();
    loginForm.reset();
    registerForm.reset();
    if (forgotPasswordForm) forgotPasswordForm.reset();
    if (resetPasswordForm) resetPasswordForm.reset();
  }

  function switchAuthTab(tabName) {
    hideAuthAlert();
    loginForm.classList.add("hidden");
    registerForm.classList.add("hidden");
    if (forgotPasswordForm) forgotPasswordForm.classList.add("hidden");
    if (resetPasswordForm) resetPasswordForm.classList.add("hidden");

    tabLoginBtn.classList.remove("active");
    tabRegisterBtn.classList.remove("active");

    const authTabs = document.querySelector(".auth-tabs");

    if (tabName === "login") {
      if (authTabs) authTabs.classList.remove("hidden");
      tabLoginBtn.classList.add("active");
      loginForm.classList.remove("hidden");
      authModalTitle.textContent = "Acceso a tu Cuenta";
      authModalSubtitle.textContent = "Inicia sesión para acceder a todas las funciones.";
      setTimeout(() => loginIdentifier.focus(), 50);
    } else if (tabName === "register") {
      if (authTabs) authTabs.classList.remove("hidden");
      tabRegisterBtn.classList.add("active");
      registerForm.classList.remove("hidden");
      authModalTitle.textContent = "Crear Cuenta Nueva";
      authModalSubtitle.textContent = "Únete a LinguaFlow gratis en pocos segundos.";
      setTimeout(() => regFullName.focus(), 50);
    } else if (tabName === "forgot") {
      if (authTabs) authTabs.classList.add("hidden");
      if (forgotPasswordForm) forgotPasswordForm.classList.remove("hidden");
      authModalTitle.textContent = "Recuperar Cuenta";
      authModalSubtitle.textContent = "¿Olvidaste tu contraseña o usuario? Te enviamos los datos a tu correo.";
      if (recoveryIdentifier) setTimeout(() => recoveryIdentifier.focus(), 50);
    } else if (tabName === "reset") {
      if (authTabs) authTabs.classList.add("hidden");
      if (resetPasswordForm) resetPasswordForm.classList.remove("hidden");
      authModalTitle.textContent = "Nueva Contraseña";
      authModalSubtitle.textContent = "Define una nueva contraseña para recuperar el acceso a tu cuenta.";
      if (newPasswordInput) setTimeout(() => newPasswordInput.focus(), 50);
    }
  }

  function showAuthAlert(message) {
    authAlertMessage.textContent = message;
    authAlertBox.classList.remove("hidden");
  }

  function hideAuthAlert() {
    authAlertBox.classList.add("hidden");
  }

  // Inicio de sesión
  async function handleLogin(e) {
    e.preventDefault();
    hideAuthAlert();

    const identifier = loginIdentifier.value.trim();
    const password = loginPassword.value;

    if (!identifier || !password) {
      showAuthAlert("Por favor completa todos los campos requeridos.");
      return;
    }

    const btnText = loginSubmitBtn.querySelector(".btn-text");
    const btnSpinner = loginSubmitBtn.querySelector(".btn-spinner");
    loginSubmitBtn.disabled = true;
    btnText.textContent = "Verificando...";
    btnSpinner.classList.remove("hidden");

    try {
      const resp = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username_or_email: identifier,
          password: password
        })
      });

      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || "Error al iniciar sesión.");
      }

      // Guardar sesión
      state.token = data.token;
      state.user = data.user;
      localStorage.setItem("linguaflow_token", data.token);

      renderUserUI();
      closeAuthModal();
      showToast(data.message || `¡Bienvenido de nuevo, ${data.user.full_name}!`, "success");

    } catch (err) {
      showAuthAlert(err.message || "Error al conectar con el servidor.");
    } finally {
      loginSubmitBtn.disabled = false;
      btnText.textContent = "Iniciar Sesión";
      btnSpinner.classList.add("hidden");
    }
  }

  // Registro de nuevo usuario
  async function handleRegister(e) {
    e.preventDefault();
    hideAuthAlert();

    const fullName = regFullName.value.trim();
    const username = regUsername.value.trim();
    const email = regEmail.value.trim();
    const password = regPassword.value;
    const confirmPassword = regPasswordConfirm.value;

    if (!fullName || !username || !email || !password || !confirmPassword) {
      showAuthAlert("Todos los campos son obligatorios.");
      return;
    }

    if (password.length < 6) {
      showAuthAlert("La contraseña debe tener al menos 6 caracteres.");
      return;
    }

    if (password !== confirmPassword) {
      showAuthAlert("Las contraseñas no coinciden. Por favor verifícalas.");
      return;
    }

    const btnText = registerSubmitBtn.querySelector(".btn-text");
    const btnSpinner = registerSubmitBtn.querySelector(".btn-spinner");
    registerSubmitBtn.disabled = true;
    btnText.textContent = "Creando cuenta...";
    btnSpinner.classList.remove("hidden");

    try {
      const resp = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          username: username,
          email: email,
          password: password
        })
      });

      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || "Error al registrar usuario.");
      }

      // Limpiar formulario de registro
      registerForm.reset();

      // Redirigir inmediatamente a inicio de sesión con el identificador listo
      switchAuthTab("login");
      loginIdentifier.value = username;
      loginPassword.value = "";

      showToast(data.message || "¡Cuenta creada exitosamente! Revisa tu correo de bienvenida e inicia sesión.", "success");
      showAuthAlert("¡Cuenta creada exitosamente! Te hemos enviado un correo de bienvenida a " + email + ". Por favor inicia sesión con tu contraseña.");
      setTimeout(() => loginPassword.focus(), 80);

    } catch (err) {
      showAuthAlert(err.message || "Error al registrar cuenta.");
    } finally {
      registerSubmitBtn.disabled = false;
      btnText.textContent = "Crear Cuenta Gratuita";
      btnSpinner.classList.add("hidden");
    }
  }

  // Solicitud de recuperación de contraseña / usuario
  async function handleForgotPassword(e) {
    e.preventDefault();
    hideAuthAlert();

    const identifier = recoveryIdentifier.value.trim();
    if (!identifier) {
      showAuthAlert("Por favor ingresa tu usuario o correo electrónico.");
      return;
    }

    const btnText = recoverySubmitBtn.querySelector(".btn-text");
    const btnSpinner = recoverySubmitBtn.querySelector(".btn-spinner");
    recoverySubmitBtn.disabled = true;
    btnText.textContent = "Enviando correo...";
    btnSpinner.classList.remove("hidden");

    try {
      const resp = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: identifier })
      });

      const data = await resp.json();
      showToast("Solicitud enviada. Revisa tu correo electrónico.", "info");
      showAuthAlert(data.message || "Si la cuenta existe, hemos enviado un correo con las instrucciones de acceso.");
      recoveryIdentifier.value = "";
    } catch (err) {
      showAuthAlert("Error al conectar con el servidor. Intenta de nuevo.");
    } finally {
      recoverySubmitBtn.disabled = false;
      btnText.textContent = "Enviar Correo de Recuperación";
      btnSpinner.classList.add("hidden");
    }
  }

  // Restablecer contraseña mediante token
  async function handleResetPassword(e) {
    e.preventDefault();
    hideAuthAlert();

    const token = resetTokenInput.value.trim();
    const newPassword = newPasswordInput.value;
    const confirmPassword = confirmNewPasswordInput.value;

    if (!token) {
      showAuthAlert("El código o enlace de recuperación no es válido.");
      return;
    }

    if (newPassword.length < 6) {
      showAuthAlert("La contraseña debe tener al menos 6 caracteres.");
      return;
    }

    if (newPassword !== confirmPassword) {
      showAuthAlert("Las contraseñas no coinciden. Por favor verifícalas.");
      return;
    }

    const btnText = resetPasswordSubmitBtn.querySelector(".btn-text");
    const btnSpinner = resetPasswordSubmitBtn.querySelector(".btn-spinner");
    resetPasswordSubmitBtn.disabled = true;
    btnText.textContent = "Guardando...";
    btnSpinner.classList.remove("hidden");

    try {
      const resp = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: token, new_password: newPassword })
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || "Error al restablecer contraseña.");
      }

      showToast("¡Contraseña restablecida con éxito!", "success");
      switchAuthTab("login");
      showAuthAlert("¡Contraseña actualizada con éxito! Ya puedes iniciar sesión con tu nueva contraseña.");
    } catch (err) {
      showAuthAlert(err.message || "Error al restablecer contraseña.");
    } finally {
      resetPasswordSubmitBtn.disabled = false;
      btnText.textContent = "Guardar Nueva Contraseña";
      btnSpinner.classList.add("hidden");
    }
  }

  // Cerrar sesión
  async function handleLogout() {
    if (state.token) {
      try {
        await fetch("/api/auth/logout", {
          method: "POST",
          headers: { "Authorization": `Bearer ${state.token}` }
        });
      } catch (e) {
        console.warn("Aviso al cerrar sesión remota:", e);
      }
    }

    state.token = null;
    state.user = null;
    localStorage.removeItem("linguaflow_token");
    renderUserUI();
    showToast("Has cerrado tu sesión en LinguaFlow.", "info");
  }

  // ==========================================
  // Event Listeners de Autenticación
  // ==========================================
  openAuthModalBtn.addEventListener("click", () => openAuthModal("login"));
  closeAuthModalBtn.addEventListener("click", closeAuthModal);

  tabLoginBtn.addEventListener("click", () => switchAuthTab("login"));
  tabRegisterBtn.addEventListener("click", () => switchAuthTab("register"));

  linkSwitchToRegister.addEventListener("click", (e) => {
    e.preventDefault();
    switchAuthTab("register");
  });

  linkSwitchToLogin.addEventListener("click", (e) => {
    e.preventDefault();
    switchAuthTab("login");
  });

  // Cerrar modal al hacer clic en el backdrop
  authModalBackdrop.addEventListener("click", (e) => {
    if (e.target === authModalBackdrop) {
      closeAuthModal();
    }
  });

  // Cerrar con tecla Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !authModalBackdrop.classList.contains("hidden")) {
      closeAuthModal();
    }
  });

  // Toggle de dropdown del usuario en navbar
  userProfileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = !userDropdownCard.classList.contains("hidden");
    if (isOpen) {
      userDropdownCard.classList.add("hidden");
      userProfileMenu.classList.remove("open");
    } else {
      userDropdownCard.classList.remove("hidden");
      userProfileMenu.classList.add("open");
    }
  });

  // Cerrar dropdown si se hace clic fuera
  document.addEventListener("click", (e) => {
    if (!userProfileMenu.contains(e.target)) {
      userDropdownCard.classList.add("hidden");
      userProfileMenu.classList.remove("open");
    }
  });

  // Envíos de formulario
  loginForm.addEventListener("submit", handleLogin);
  registerForm.addEventListener("submit", handleRegister);
  logoutBtn.addEventListener("click", handleLogout);

  // Eventos de Recuperación de Cuenta y Contraseña
  if (linkForgotPassword) {
    linkForgotPassword.addEventListener("click", () => switchAuthTab("forgot"));
  }
  if (linkForgotFromRegister) {
    linkForgotFromRegister.addEventListener("click", () => switchAuthTab("forgot"));
  }
  if (linkBackToLogin) {
    linkBackToLogin.addEventListener("click", (e) => {
      e.preventDefault();
      switchAuthTab("login");
    });
  }
  if (linkCancelReset) {
    linkCancelReset.addEventListener("click", (e) => {
      e.preventDefault();
      switchAuthTab("login");
    });
  }
  if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", handleForgotPassword);
  }
  if (resetPasswordForm) {
    resetPasswordForm.addEventListener("submit", handleResetPassword);
  }

  // Detección de token de reseteo en la URL (?reset_token=xyz)
  function checkUrlForResetToken() {
    try {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("reset_token");
      if (token) {
        openAuthModal("reset");
        if (resetTokenInput) resetTokenInput.value = token;
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    } catch (e) {
      console.warn("Aviso al leer parámetros de URL:", e);
    }
  }

  // Apertura de modal de acceso desde banners y gates bloqueados
  if (guestBannerAuthBtn) {
    guestBannerAuthBtn.addEventListener("click", () => openAuthModal("login"));
  }

  gateAuthButtons.forEach(btn => {
    btn.addEventListener("click", () => openAuthModal("login"));
  });

  // Botones para mostrar/ocultar contraseñas
  document.querySelectorAll(".btn-toggle-pwd").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (!input) return;

      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";

      const eyeOpen = btn.querySelector(".eye-open");
      const eyeClosed = btn.querySelector(".eye-closed");

      if (eyeOpen && eyeClosed) {
        if (isPassword) {
          eyeOpen.classList.add("hidden");
          eyeClosed.classList.remove("hidden");
        } else {
          eyeOpen.classList.remove("hidden");
          eyeClosed.classList.add("hidden");
        }
      }
    });
  });

  // ==========================================
  // Arranque Inicial
  // ==========================================
  checkAuthStatus();
  checkUrlForResetToken();
  loadSupportedLanguages();
  initWebSocket();
});
