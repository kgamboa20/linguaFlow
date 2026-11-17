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
    theme: localStorage.getItem("linguaflow_theme") || "dark"
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

  // Tabs
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  // Tab 1: Texto
  const textSourceLang = document.getElementById("textSourceLang");
  const textTargetLang = document.getElementById("textTargetLang");
  const detectedLangTag = document.getElementById("detectedLangTag");
  const swapLangsBtn = document.getElementById("swapLangsBtn");
  const quickLangPills = document.querySelectorAll("#quickLangPills .pill");
  const sourceText = document.getElementById("sourceText");
  const targetText = document.getElementById("targetText");
  const sourceCharCount = document.getElementById("sourceCharCount");
  const targetCharCount = document.getElementById("targetCharCount");
  const clearTextBtn = document.getElementById("clearTextBtn");
  const translatingIndicator = document.getElementById("translatingIndicator");
  const listenSourceBtn = document.getElementById("listenSourceBtn");
  const listenTargetBtn = document.getElementById("listenTargetBtn");
  const copyTargetBtn = document.getElementById("copyTargetBtn");

  // Tab 2: Voz
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

  // Tab 3: Documentos
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

  // Tab 4: Historial
  const historyListContainer = document.getElementById("historyListContainer");
  const clearAllHistoryBtn = document.getElementById("clearAllHistoryBtn");

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

      if (tabId === "history-tab") {
        renderHistory();
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
    } catch (err) {
      console.error(err);
      showToast("Error al cargar lista de idiomas", "error");
    }
  }

  function populateSelect(selectElement, langs, allowAuto = false, defaultVal = "en") {
    selectElement.innerHTML = "";
    Object.entries(langs).forEach(([code, name]) => {
      if (!allowAuto && code === "auto") return;
      const option = document.createElement("option");
      option.value = code;
      option.textContent = name;
      if (code === defaultVal) option.selected = true;
      selectElement.appendChild(option);
    });
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
        wsStatusBadge.classList.remove("disconnected");
        wsStatusBadge.querySelector(".status-text").textContent = "Tiempo Real";
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
          }
        } catch (e) {
          console.error("Error analizando mensaje WebSocket:", e);
        }
      };

      state.ws.onclose = () => {
        state.wsConnected = false;
        wsStatusBadge.classList.add("disconnected");
        wsStatusBadge.querySelector(".status-text").textContent = "Reconectando...";
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
    const text = sourceText.value;
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
        target_lang: targetLang
      }));
      return;
    }

    // 2. Fallback a API REST
    try {
      const resp = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          source_lang: sourceLang,
          target_lang: targetLang
        })
      });

      translatingIndicator.classList.add("hidden");

      if (!resp.ok) throw new Error("Error en la respuesta del servidor.");
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
          const resp = await fetch("/api/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
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
      const response = await fetch("/api/documents/upload-translate", {
        method: "POST",
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
  // Tab 4: Historial Local
  // ==========================================
  function saveToHistory(original, translated, sourceCode, targetCode) {
    if (!original || !translated || original.length < 3) return;

    let history = JSON.parse(localStorage.getItem("linguaflow_history") || "[]");
    // Evitar duplicados inmediatos
    if (history.length > 0 && history[0].original === original && history[0].translated === translated) {
      return;
    }

    const item = {
      id: Date.now(),
      original: original,
      translated: translated,
      source: sourceCode,
      target: targetCode,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    history.unshift(item);
    if (history.length > 20) history = history.slice(0, 20);
    localStorage.setItem("linguaflow_history", JSON.stringify(history));
  }

  function renderHistory() {
    const history = JSON.parse(localStorage.getItem("linguaflow_history") || "[]");
    historyListContainer.innerHTML = "";

    if (history.length === 0) {
      historyListContainer.innerHTML = `
        <div class="history-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <p>Aún no tienes traducciones recientes.</p>
        </div>
      `;
      return;
    }

    history.forEach(item => {
      const card = document.createElement("div");
      card.className = "history-item-card";
      card.innerHTML = `
        <div class="history-item-meta">
          <span class="history-lang-badge">${(state.languages[item.source] || item.source).toUpperCase()} → ${(state.languages[item.target] || item.target).toUpperCase()}</span>
          <span>${item.time}</span>
        </div>
        <div class="history-content-row">
          <div>${escapeHTML(item.original)}</div>
          <div style="color: var(--accent-primary); font-weight: 500;">${escapeHTML(item.translated)}</div>
        </div>
        <div class="history-actions">
          <button class="btn-tool-sm copy-hist-btn" data-text="${escapeAttr(item.translated)}">Copiar</button>
          <button class="btn-tool-sm restore-hist-btn" data-orig="${escapeAttr(item.original)}" data-trans="${escapeAttr(item.translated)}" data-src="${item.source}" data-tgt="${item.target}">Restaurar</button>
        </div>
      `;
      historyListContainer.appendChild(card);
    });

    document.querySelectorAll(".copy-hist-btn").forEach(b => {
      b.addEventListener("click", async () => {
        await navigator.clipboard.writeText(b.getAttribute("data-text"));
        showToast("Copiado al portapapeles", "success");
      });
    });

    document.querySelectorAll(".restore-hist-btn").forEach(b => {
      b.addEventListener("click", () => {
        sourceText.value = b.getAttribute("data-orig");
        targetText.value = b.getAttribute("data-trans");
        textSourceLang.value = b.getAttribute("data-src");
        textTargetLang.value = b.getAttribute("data-tgt");
        // Cambiar a pestaña texto
        document.querySelector('[data-tab="text-tab"]').click();
        showToast("Traducción restaurada en el editor", "info");
      });
    });
  }

  clearAllHistoryBtn.addEventListener("click", () => {
    localStorage.removeItem("linguaflow_history");
    renderHistory();
    showToast("Historial borrado", "info");
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
  // Arranque Inicial
  // ==========================================
  loadSupportedLanguages();
  initWebSocket();
});
