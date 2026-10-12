/**
 * PrintMoney Studio — Core Client Logic
 * Minimalist, formal video composition workflow interfacing with FastAPI
 */

const STATE = {
  presets: [],
  voices: [],
  subtitleStyles: [],
  selectedVoice: "pt-BR-AntonioNeural",
  selectedStyle: "viral_yellow",
  videoSource: "hybrid", // "hybrid" | "openverse" | "wikimedia" | "wikimedia_gif" | "nasa" | "local" | "pixabay" | "pexels"
  targetDuration: 60,
  targetWords: 150,
  videoClipDuration: 4,
  hasPexels: false,
  hasPixabay: false,
  mediaTags: {},
  activeIdeaCategory: "all",
  ideasSearchQuery: "",
  searchTerms: ["black hole space galaxy cosmic event horizon 4k", "universe stars astrophysics deep space"],
  currentTaskId: null,
  pollInterval: null,
  lastLoggedStep: null,
};

// ==========================================================================
// Live Diagnostic Terminal Drawer Controller
// ==========================================================================
const TerminalDrawer = {
  isOpen: false,
  autoScroll: true,
  logs: [],
  maxLogs: 500,
  unreadErrors: 0,

  init() {
    const btnToggle = document.getElementById("btn-toggle-terminal");
    const btnHeader = document.getElementById("btn-open-terminal");
    const btnMinimize = document.getElementById("btn-terminal-minimize");
    const btnClear = document.getElementById("btn-terminal-clear");
    const btnCopy = document.getElementById("btn-terminal-copy");
    const autoScrollCheck = document.getElementById("terminal-autoscroll-check");

    if (btnToggle) {
      btnToggle.addEventListener("click", () => this.toggle());
    }
    if (btnHeader) {
      btnHeader.addEventListener("click", () => this.toggle());
    }
    if (btnMinimize) {
      btnMinimize.addEventListener("click", () => this.close());
    }
    if (btnClear) {
      btnClear.addEventListener("click", () => this.clear());
    }
    if (btnCopy) {
      btnCopy.addEventListener("click", () => this.copy());
    }
    if (autoScrollCheck) {
      this.autoScroll = autoScrollCheck.checked;
      autoScrollCheck.addEventListener("change", (e) => {
        this.autoScroll = e.target.checked;
      });
    }

    // Initial boot diagnostics
    this.appendLog("info", "PrintMoney Studio v2.4 Engine inicializado. Terminal de diagnóstico online.");
    this.appendLog("info", "Monitorando pipeline de vídeo: Edge-TTS, legendas, acervo de mídias e FFmpeg.");
  },

  open() {
    this.isOpen = true;
    const drawer = document.getElementById("terminal-drawer");
    const btnToggle = document.getElementById("btn-toggle-terminal");
    const btnHeader = document.getElementById("btn-open-terminal");
    const toggleDot = document.getElementById("terminal-toggle-dot");

    if (drawer) drawer.classList.add("active");
    if (btnToggle) btnToggle.classList.add("active");
    if (btnHeader) btnHeader.classList.add("active");

    // Clear error pulse once inspected
    this.unreadErrors = 0;
    if (toggleDot) toggleDot.classList.remove("error-pulse");

    if (this.autoScroll) {
      const body = document.getElementById("terminal-console-body");
      if (body) body.scrollTop = body.scrollHeight;
    }
  },

  close() {
    this.isOpen = false;
    const drawer = document.getElementById("terminal-drawer");
    const btnToggle = document.getElementById("btn-toggle-terminal");
    const btnHeader = document.getElementById("btn-open-terminal");

    if (drawer) drawer.classList.remove("active");
    if (btnToggle) btnToggle.classList.remove("active");
    if (btnHeader) btnHeader.classList.remove("active");
  },

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  },

  log(level, message) {
    this.appendLog(level, message);
  },

  appendLog(level, message, timestamp) {
    const rawLevel = String(level || "info").toLowerCase();
    const validLevels = ["info", "success", "warn", "error"];
    const safeLevel = validLevels.includes(rawLevel) ? rawLevel : "info";

    const ts = timestamp || new Date().toTimeString().split(" ")[0];
    const tagMap = {
      info: "INFO",
      success: "SUCCESS",
      warn: "WARN",
      error: "ERROR",
    };
    const tag = tagMap[safeLevel] || "INFO";

    const entry = {
      level: safeLevel,
      message: String(message || ""),
      timestamp: ts,
      rawText: `[${ts}] [${tag}] ${message}`,
    };

    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    const consoleBody = document.getElementById("terminal-console-body");
    if (consoleBody) {
      const line = document.createElement("div");
      line.className = `terminal-line log-${safeLevel}`;

      const timeEl = document.createElement("span");
      timeEl.className = "terminal-time";
      timeEl.textContent = `[${ts}]`;

      const tagEl = document.createElement("span");
      tagEl.className = `terminal-tag tag-${safeLevel}`;
      tagEl.textContent = `[${tag}]`;

      const msgEl = document.createElement("span");
      msgEl.className = "terminal-msg";
      msgEl.textContent = entry.message;

      line.appendChild(timeEl);
      line.appendChild(tagEl);
      line.appendChild(msgEl);

      consoleBody.appendChild(line);

      // Keep DOM lean
      while (consoleBody.children.length > this.maxLogs) {
        consoleBody.removeChild(consoleBody.firstChild);
      }

      if (this.autoScroll) {
        consoleBody.scrollTop = consoleBody.scrollHeight;
      }
    }

    // Update log counter badge
    const counter = document.getElementById("terminal-log-counter");
    if (counter) {
      counter.textContent = `${this.logs.length} logs`;
    }

    // Update status indicators
    const statusDot = document.getElementById("terminal-status-dot");
    const statusLabel = document.getElementById("terminal-status-label");
    const toggleDot = document.getElementById("terminal-toggle-dot");

    if (safeLevel === "error") {
      this.unreadErrors++;
      if (statusDot) statusDot.className = "terminal-dot err";
      if (statusLabel) statusLabel.textContent = "Erro Detectado";
      if (toggleDot) toggleDot.classList.add("error-pulse");
    } else if (safeLevel === "warn") {
      if (statusDot && this.unreadErrors === 0) statusDot.className = "terminal-dot warn";
      if (statusLabel && this.unreadErrors === 0) statusLabel.textContent = "Aviso";
    } else if (safeLevel === "success") {
      if (statusDot && this.unreadErrors === 0) statusDot.className = "terminal-dot ok";
      if (statusLabel && this.unreadErrors === 0) statusLabel.textContent = "Concluído";
    } else if (safeLevel === "info" && this.unreadErrors === 0) {
      if (statusDot) statusDot.className = "terminal-dot ok";
      if (statusLabel) statusLabel.textContent = "Conectado";
    }
  },

  clear() {
    this.logs = [];
    this.unreadErrors = 0;
    const consoleBody = document.getElementById("terminal-console-body");
    if (consoleBody) consoleBody.innerHTML = "";

    const counter = document.getElementById("terminal-log-counter");
    if (counter) counter.textContent = "0 logs";

    const toggleDot = document.getElementById("terminal-toggle-dot");
    if (toggleDot) toggleDot.classList.remove("error-pulse");

    const statusDot = document.getElementById("terminal-status-dot");
    if (statusDot) statusDot.className = "terminal-dot ok";

    const statusLabel = document.getElementById("terminal-status-label");
    if (statusLabel) statusLabel.textContent = "Conectado";

    this.appendLog("info", "Console de diagnóstico limpo pelo usuário.");
  },

  copy() {
    if (this.logs.length === 0) {
      showToast("Nenhum log no terminal para copiar.", "info");
      return;
    }

    const text = this.logs.map((l) => l.rawText).join("\n");
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast("Logs copiados para a área de transferência.", "success");
      }).catch(() => {
        this.fallbackCopy(text);
      });
    } else {
      this.fallbackCopy(text);
    }
  },

  fallbackCopy(text) {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
      showToast("Logs copiados para a área de transferência.", "success");
    } catch {
      prompt("Copie os logs:", text);
    }
    document.body.removeChild(area);
  },
};

window.TerminalDrawer = TerminalDrawer;

function updateStatusBarTask(text, isError = false) {
  const el = document.getElementById("status-bar-task-text");
  if (el) {
    el.textContent = text;
    el.style.color = isError ? "var(--status-error)" : "#94a3b8";
  }
}

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  TerminalDrawer.init();
  setupNavigation();
  loadPresetsAndStatus();
  loadBgmTracks();
  setupDurationSelector();
  setupPaceSelector();
  setupAspectSelector();
  setupScriptCounter();
  setupTermsInput();
  setupSourceSelector();
  setupMaterialsModal();
  setupTaskCancel();
  setupSliders();
  setupForms();
  setupMagicPrompt();
  setupSafeZoneToggle();
  setupMetadataUI();
  setupViralAnalyticsUI();
  setupBatchStudio();
  setupAutopilotUI();
  setupKeyboardShortcuts();
  refreshLocalMaterialsCount();
});

// ==========================================================================
// Navigation & Views
// ==========================================================================
function setupNavigation() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      const targetId = tab.dataset.target;
      document.querySelectorAll(".view-section").forEach((sec) => {
        sec.classList.remove("active");
      });
      const targetSec = document.getElementById(targetId);
      if (targetSec) targetSec.classList.add("active");

      if (targetId === "view-gallery") {
        loadGallery();
      } else if (targetId === "view-tags") {
        renderMediaTags();
      } else if (targetId === "view-autopilot") {
        loadAutopilotData();
      }
    });
  });

  // Settings Modal Handlers
  const btnSettings = document.getElementById("btn-open-settings");
  const modal = document.getElementById("modal-settings");
  const btnClose = document.getElementById("btn-close-modal");

  if (btnSettings && modal) {
    btnSettings.addEventListener("click", () => modal.classList.add("active"));
  }
  if (btnClose && modal) {
    btnClose.addEventListener("click", () => modal.classList.remove("active"));
  }
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
  }
}

// ==========================================================================
// Data Fetching: Presets & System Status
// ==========================================================================
async function loadPresetsAndStatus() {
  try {
    const res = await fetch("/api/v1/saas/presets");
    if (res.ok) {
      const data = await res.json();
      const payload = data.data || {};
      STATE.presets = payload.science_presets || [];
      STATE.voices = payload.voices || [];
      STATE.subtitleStyles = payload.subtitle_styles || [];

      renderPresetChips();
      renderVoiceCards();
      renderStyleCards();
      renderIdeasLab();
      TerminalDrawer.log("info", `Catálogo científico carregado (${STATE.presets.length} temas, ${STATE.voices.length} vozes).`);
    }
  } catch (err) {
    console.warn("Presets endpoint loading fallback:", err);
  }

  // Load Media Tags
  try {
    const resTags = await fetch("/api/v1/saas/tags");
    if (resTags.ok) {
      const dataTags = await resTags.json();
      STATE.mediaTags = (dataTags.data || {}).tag_categories || {};
      renderMediaTags();
    }
  } catch (err) {
    console.warn("Tags endpoint loading fallback:", err);
  }

  // System Status & Pexels Key Verification
  try {
    const resStatus = await fetch("/api/v1/saas/status");
    if (resStatus.ok) {
      const statusData = (await resStatus.json()).data || {};
      const statusDot = document.getElementById("status-dot");
      const statusText = document.getElementById("status-text");
      const statTasks = document.getElementById("stat-total-tasks");

      if (statusText) statusText.textContent = statusData.ffmpeg_ready ? "FFmpeg Operacional" : "FFmpeg Indisponível";
      if (statusDot) statusDot.className = `dot-status ${statusData.ffmpeg_ready ? "" : "err"}`;
      if (statTasks) statTasks.textContent = statusData.total_tasks_created || "0";

      const sbEngineText = document.getElementById("status-bar-engine-text");
      const sbEngineDot = document.getElementById("status-bar-engine-dot");
      if (sbEngineText) sbEngineText.textContent = statusData.ffmpeg_ready ? "Motor FFmpeg: Pronto" : "Motor FFmpeg: Indisponível";
      if (sbEngineDot) sbEngineDot.className = `dot-status ${statusData.ffmpeg_ready ? "ok" : "err"}`;

      if (statusData.ffmpeg_ready) {
        TerminalDrawer.log("success", `Motor FFmpeg operacional (${statusData.ffmpeg_path || "sistema"}).`);
      } else {
        TerminalDrawer.log("warn", "Atenção: Motor FFmpeg não detectado no sistema.");
      }

      // Pexels Status
      STATE.hasPexels = Boolean(statusData.has_pexels);
      updatePexelsUI();

      // Pre-fill settings modal
      const providerSelect = document.getElementById("setting-llm-provider");
      if (providerSelect && statusData.llm_provider) {
        providerSelect.value = statusData.llm_provider;
      }

      // Pre-fill Social Publishing (Upload-Post)
      if (statusData.upload_post) {
        const up = statusData.upload_post;
        STATE.uploadPostConfigured = Boolean(up.configured);
        STATE.uploadPostAutoUpload = Boolean(up.auto_upload);

        const elEnabled = document.getElementById("setting-upload-post-enabled");
        if (elEnabled) elEnabled.checked = Boolean(up.enabled);

        const elAuto = document.getElementById("setting-upload-post-auto-upload");
        if (elAuto) elAuto.checked = Boolean(up.auto_upload);

        const elUser = document.getElementById("setting-upload-post-user");
        if (elUser && up.username) elUser.value = up.username;

        const platforms = up.platforms || ["tiktok", "youtube"];
        const elTiktok = document.getElementById("setting-platform-tiktok");
        if (elTiktok) elTiktok.checked = platforms.includes("tiktok");

        const elYt = document.getElementById("setting-platform-youtube");
        if (elYt) elYt.checked = platforms.includes("youtube");

        const elInsta = document.getElementById("setting-platform-instagram");
        if (elInsta) elInsta.checked = platforms.includes("instagram");

        const elPrivacy = document.getElementById("setting-upload-post-privacy");
        if (elPrivacy && up.youtube_privacy_status) elPrivacy.value = up.youtube_privacy_status;
      }
    }
  } catch (err) {
    console.warn("Status fetch warning:", err);
  }
}

function updatePexelsUI() {
  const metaLabel = document.getElementById("meta-pexels-label");
  const inlineDot = document.getElementById("inline-pexels-dot");
  const inlineStatusText = document.getElementById("inline-pexels-status-text");
  const inlineDesc = document.getElementById("inline-pexels-desc");
  const inlineForm = document.getElementById("inline-pexels-form");
  const panel = document.getElementById("pexels-config-panel");

  if (STATE.hasPexels) {
    if (metaLabel) metaLabel.textContent = "Conectado";
    if (inlineDot) inlineDot.className = "dot-status";
    if (inlineStatusText) inlineStatusText.textContent = "Chave Pexels Configurada e Ativa";
    if (panel) panel.classList.add("connected");
    if (inlineDesc) inlineDesc.textContent = "A integração com o acervo Pexels está pronta para downloads automáticos em alta resolução.";
    if (inlineForm) {
      inlineForm.innerHTML = `
        <span style="font-size:0.75rem; color:var(--status-success); font-family:var(--font-mono);">Chave configurada com sucesso.</span>
        <button type="button" class="btn-secondary" style="font-size:0.75rem; padding:0.25rem 0.5rem;" onclick="showPexelsReconfigureForm()">Alterar Chave</button>
      `;
    }
  } else {
    if (metaLabel) metaLabel.textContent = "Pendente";
    if (inlineDot) inlineDot.className = "dot-status warn";
    if (inlineStatusText) inlineStatusText.textContent = "Chave da API Pexels Necessária";
    if (panel) panel.classList.remove("connected");
    if (inlineDesc) inlineDesc.textContent = "Para buscar clipes 4K/HD online, insira sua chave gratuita do Pexels (ativação instantânea em pexels.com/api) ou escolha a opção Arquivos Locais.";
  }
}

function showPexelsReconfigureForm() {
  const inlineForm = document.getElementById("inline-pexels-form");
  if (inlineForm) {
    inlineForm.innerHTML = `
      <input type="password" id="input-quick-pexels-key" class="input-text" placeholder="Cole sua nova chave da API Pexels...">
      <button type="button" class="btn-secondary" id="btn-save-quick-pexels">Salvar</button>
    `;
    const btn = document.getElementById("btn-save-quick-pexels");
    if (btn) btn.addEventListener("click", handleSaveQuickPexels);
  }
}

// ==========================================================================
// Duration Selector & Target Length Management
// ==========================================================================
function setupDurationSelector() {
  const btns = document.querySelectorAll("#duration-selector-bar .source-btn");
  const hint = document.getElementById("target-duration-hint");
  btns.forEach((btn) => {
    btn.addEventListener("click", () => {
      btns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const d = parseInt(btn.dataset.duration) || 60;
      STATE.targetDuration = d;
      STATE.targetWords = d === 30 ? 75 : (d === 60 ? 150 : (d === 90 ? 220 : 300));
      if (hint) {
        hint.textContent = `Meta selecionada: ${d}s (~${STATE.targetWords} palavras)`;
      }
      updateScriptMeta();
    });
  });
}

// ==========================================================================
// Source Selector & Material Management
// ==========================================================================
function setupSourceSelector() {
  const btns = document.querySelectorAll(".source-selector-bar .source-btn[data-source]");
  const hybridPanel = document.getElementById("hybrid-config-panel");
  const openversePanel = document.getElementById("openverse-config-panel");
  const wikimediaPanel = document.getElementById("wikimedia-config-panel");
  const wikimediaGifPanel = document.getElementById("wikimedia-gif-config-panel");
  const pexelsPanel = document.getElementById("pexels-config-panel");
  const pixabayPanel = document.getElementById("pixabay-config-panel");
  const localPanel = document.getElementById("local-materials-panel");
  const nasaPanel = document.getElementById("nasa-config-panel");

  btns.forEach((btn) => {
    btn.addEventListener("click", () => {
      btns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      STATE.videoSource = btn.dataset.source;

      if (hybridPanel) hybridPanel.style.display = STATE.videoSource === "hybrid" ? "block" : "none";
      if (openversePanel) openversePanel.style.display = STATE.videoSource === "openverse" ? "block" : "none";
      if (wikimediaPanel) wikimediaPanel.style.display = STATE.videoSource === "wikimedia" ? "block" : "none";
      if (wikimediaGifPanel) wikimediaGifPanel.style.display = STATE.videoSource === "wikimedia_gif" ? "block" : "none";
      if (pexelsPanel) pexelsPanel.style.display = STATE.videoSource === "pexels" ? "block" : "none";
      if (pixabayPanel) pixabayPanel.style.display = STATE.videoSource === "pixabay" ? "block" : "none";
      if (localPanel) localPanel.style.display = STATE.videoSource === "local" ? "block" : "none";
      if (nasaPanel) nasaPanel.style.display = STATE.videoSource === "nasa" ? "block" : "none";

      showToast(`Fonte de mídia: ${btn.textContent.trim()}`, "info");
    });
  });

  const btnQuickSavePexels = document.getElementById("btn-save-quick-pexels");
  if (btnQuickSavePexels) {
    btnQuickSavePexels.addEventListener("click", handleSaveQuickPexels);
  }

  const btnQuickSavePixabay = document.getElementById("btn-save-quick-pixabay");
  if (btnQuickSavePixabay) {
    btnQuickSavePixabay.addEventListener("click", handleSaveQuickPixabay);
  }

  const uploadInput = document.getElementById("local-file-upload-input");
  if (uploadInput) {
    uploadInput.addEventListener("change", handleLocalFileUpload);
  }
}

async function handleSaveQuickPexels() {
  const input = document.getElementById("input-quick-pexels-key");
  if (!input) return;
  const key = input.value.trim();

  if (!key) {
    showToast("Por favor, insira a chave da API Pexels.", "error");
    return;
  }

  showToast("Salvando chave Pexels...", "info");
  try {
    const res = await fetch("/api/v1/saas/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pexels_api_keys: key }),
    });

    if (res.ok) {
      STATE.hasPexels = true;
      updatePexelsUI();
      showToast("Chave Pexels configurada com sucesso!", "success");
    } else {
      throw new Error("Falha ao salvar");
    }
  } catch (err) {
    showToast("Erro ao registrar chave Pexels.", "error");
  }
}

async function handleSaveQuickPixabay() {
  const input = document.getElementById("input-quick-pixabay-key");
  if (!input) return;
  const key = input.value.trim();

  if (!key) {
    showToast("Por favor, insira a chave da API Pixabay.", "error");
    return;
  }

  showToast("Salvando chave Pixabay...", "info");
  try {
    const res = await fetch("/api/v1/saas/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pixabay_api_keys: key }),
    });

    if (res.ok) {
      STATE.hasPixabay = true;
      updatePixabayUI();
      showToast("Chave Pixabay configurada com sucesso!", "success");
    } else {
      throw new Error("Falha ao salvar");
    }
  } catch (err) {
    showToast("Erro ao registrar chave Pixabay.", "error");
  }
}

function updatePixabayUI() {
  const dot = document.getElementById("inline-pixabay-dot");
  const txt = document.getElementById("inline-pixabay-status-text");
  const form = document.getElementById("inline-pixabay-form");
  if (STATE.hasPixabay) {
    if (dot) dot.className = "dot-status ok";
    if (txt) txt.textContent = "Chave Pixabay Ativa";
    if (form) {
      form.innerHTML = `
        <span style="font-size:0.75rem; color:var(--status-success); font-family:var(--font-mono);">Chave Pixabay configurada.</span>
        <button type="button" class="btn-secondary" style="font-size:0.75rem; padding:0.25rem 0.5rem;" onclick="showPixabayReconfigureForm()">Alterar</button>
      `;
    }
  }
}

function showPixabayReconfigureForm() {
  const form = document.getElementById("inline-pixabay-form");
  if (form) {
    form.innerHTML = `
      <input type="password" id="input-quick-pixabay-key" class="input-text" placeholder="Cole sua nova chave da API Pixabay...">
      <button type="button" class="btn-secondary" id="btn-save-quick-pixabay">Salvar</button>
    `;
    const btn = document.getElementById("btn-save-quick-pixabay");
    if (btn) btn.addEventListener("click", handleSaveQuickPixabay);
  }
}

async function handleLocalFileUpload(e) {
  const file = e.target.files?.[0];
  if (!file) return;

  showToast(`Enviando ${file.name} para o acervo local...`, "info");
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/v1/saas/upload_material", {
      method: "POST",
      body: formData,
    });

    if (res.ok) {
      showToast(`Vídeo '${file.name}' adicionado ao acervo com sucesso!`, "success");
      refreshLocalMaterialsCount();
    } else {
      showToast("Falha no envio do vídeo.", "error");
    }
  } catch (err) {
    showToast("Erro de comunicação ao enviar arquivo.", "error");
  }
}

async function refreshLocalMaterialsCount() {
  try {
    const res = await fetch("/api/v1/saas/materials");
    if (res.ok) {
      const data = await res.json();
      const count = data.data?.count || 0;
      const countEl = document.getElementById("local-materials-count-text");
      if (countEl) {
        countEl.textContent = `Acervo Local: ${count} clipes disponíveis (~10 min)`;
      }
    }
  } catch (e) {}
}

// ==========================================================================
// UI Renderers: Chips, Voices, Styles & Ideas
// ==========================================================================
function renderPresetChips() {
  const container = document.getElementById("preset-chips-container");
  if (!container) return;

  container.innerHTML = "";
  STATE.presets.forEach((preset, index) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `preset-chip ${index === 0 ? "active" : ""}`;
    chip.textContent = preset.title;
    chip.addEventListener("click", () => {
      document.querySelectorAll(".preset-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      applyPreset(preset);
    });
    container.appendChild(chip);
  });

  if (STATE.presets.length > 0) {
    applyPreset(STATE.presets[0]);
  }
}

function applyPreset(preset) {
  const subjectInput = document.getElementById("video-subject");
  const scriptInput = document.getElementById("video-script");

  if (subjectInput) subjectInput.value = preset.title;
  if (scriptInput) {
    scriptInput.value = preset.script;
    updateScriptMeta();
  }

  // Combine terms, image_tags, gif_tags, video_tags from preset
  const combinedTerms = [];
  if (preset.terms && Array.isArray(preset.terms)) combinedTerms.push(...preset.terms);
  if (preset.video_tags && Array.isArray(preset.video_tags)) combinedTerms.push(...preset.video_tags.slice(0, 2));
  if (preset.image_tags && Array.isArray(preset.image_tags)) combinedTerms.push(...preset.image_tags.slice(0, 2));
  if (preset.gif_tags && Array.isArray(preset.gif_tags)) combinedTerms.push(...preset.gif_tags.slice(0, 1));

  const uniqueTerms = Array.from(new Set(combinedTerms));
  if (uniqueTerms.length > 0) {
    STATE.searchTerms = uniqueTerms;
    renderTermTags();
  }

  if (preset.voice) selectVoice(preset.voice);
  if (preset.style) selectStyle(preset.style);

  // Set 60s target duration active by default
  const dur60Btn = document.querySelector('#duration-selector-bar .source-btn[data-duration="60"]');
  if (dur60Btn) {
    document.querySelectorAll('#duration-selector-bar .source-btn').forEach(b => b.classList.remove('active'));
    dur60Btn.classList.add('active');
    STATE.targetDuration = 60;
    STATE.targetWords = 150;
  }
}

let currentPreviewAudio = null;
let currentPreviewBtn = null;

function toggleAudioPreview(url, btn) {
  if (currentPreviewAudio && !currentPreviewAudio.paused && currentPreviewAudio.src.includes(url)) {
    currentPreviewAudio.pause();
    currentPreviewAudio.currentTime = 0;
    if (btn) {
      btn.classList.remove("playing");
      btn.querySelector("span").textContent = "Ouvir locução";
    }
    return;
  }

  if (currentPreviewAudio) {
    currentPreviewAudio.pause();
    if (currentPreviewBtn) {
      currentPreviewBtn.classList.remove("playing");
      currentPreviewBtn.querySelector("span").textContent = "Ouvir locução";
    }
  }

  currentPreviewAudio = new Audio(url);
  currentPreviewBtn = btn;
  if (btn) {
    btn.classList.add("playing");
    btn.querySelector("span").textContent = "Tocando...";
  }

  currentPreviewAudio.play().catch((err) => {
    console.warn("Audio play prevented:", err);
    if (btn) {
      btn.classList.remove("playing");
      btn.querySelector("span").textContent = "Ouvir locução";
    }
  });

  currentPreviewAudio.onended = () => {
    if (btn) {
      btn.classList.remove("playing");
      btn.querySelector("span").textContent = "Ouvir locução";
    }
  };
}

function renderVoiceCards() {
  const container = document.getElementById("voice-grid");
  if (!container) return;

  container.innerHTML = "";
  STATE.voices.forEach((v) => {
    const card = document.createElement("div");
    card.className = `voice-card ${v.id === STATE.selectedVoice ? "active" : ""}`;
    card.id = `voice-${v.id}`;
    const previewUrl = v.preview_url || `/audio/voices/${v.id}.mp3`;
    const isPt = v.id.startsWith("pt-BR");
    const langFlag = isPt ? "🇧🇷" : "🇺🇸";

    card.innerHTML = `
      <div class="voice-card-top">
        <div style="display:flex; align-items:center; gap:0.4rem;">
          <span style="font-size:0.95rem;">${langFlag}</span>
          <span class="voice-name">${v.name}</span>
        </div>
        <span class="voice-tag">${v.badge}</span>
      </div>
      <div class="voice-desc">${v.tone}</div>
      <button type="button" class="voice-preview-btn" title="Ouvir demonstração de áudio">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        <span>Amostra de Voz</span>
      </button>
    `;

    card.addEventListener("click", (e) => {
      if (e.target.closest(".voice-preview-btn")) return;
      selectVoice(v.id);
    });

    const previewBtn = card.querySelector(".voice-preview-btn");
    if (previewBtn) {
      previewBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleAudioPreview(previewUrl, previewBtn);
      });
    }

    container.appendChild(card);
  });
}

function selectVoice(voiceId) {
  STATE.selectedVoice = voiceId;
  document.querySelectorAll(".voice-card").forEach((c) => c.classList.remove("active"));
  const card = document.getElementById(`voice-${voiceId}`);
  if (card) card.classList.add("active");
}

const SUBTITLE_PREVIEWS = {
  hormozi_bold: { color: "#FFE600", stroke: "#000000", bg: "#0d0d10", label: "HORMOZI BOLD" },
  neon_cyberpunk: { color: "#00F0FF", stroke: "#FF007A", bg: "#06060c", label: "NEON CYBER" },
  minimalist_white: { color: "#FFFFFF", stroke: "rgba(0,0,0,0.85)", bg: "#101014", label: "MINIMAL WHITE" },
  karaoke_pop: { color: "#00FF66", stroke: "#000000", bg: "#070c08", label: "KARAOKÊ POP" },
  danger_red: { color: "#FF3344", stroke: "#000000", bg: "#0e0607", label: "ALERTA VIRAL" },
  gold_luxury: { color: "#FFD700", stroke: "#261a00", bg: "#0d0b06", label: "OURO LUXO" },
};

function renderStyleCards() {
  const container = document.getElementById("styles-grid");
  if (!container) return;

  container.innerHTML = "";
  STATE.subtitleStyles.forEach((s) => {
    const card = document.createElement("div");
    card.className = `style-card ${s.id === STATE.selectedStyle ? "active" : ""}`;
    card.id = `style-${s.id}`;

    const preview = SUBTITLE_PREVIEWS[s.id] || {
      color: "#FFE600",
      stroke: "#000000",
      bg: "#0d0d10",
      label: s.name.toUpperCase(),
    };

    card.innerHTML = `
      <div class="style-preview-swatch" style="background:${preview.bg}; color:${preview.color}; text-shadow: -1.5px -1.5px 0 ${preview.stroke}, 1.5px -1.5px 0 ${preview.stroke}, -1.5px 1.5px 0 ${preview.stroke}, 1.5px 1.5px 0 ${preview.stroke};">
        ${preview.label}
      </div>
      <div class="style-title">${s.name}</div>
      <div class="style-desc">${s.description}</div>
    `;

    card.addEventListener("click", () => selectStyle(s.id));
    container.appendChild(card);
  });
}

function selectStyle(styleId) {
  STATE.selectedStyle = styleId;
  document.querySelectorAll(".style-card").forEach((c) => c.classList.remove("active"));
  const card = document.getElementById(`style-${styleId}`);
  if (card) card.classList.add("active");
}

function renderIdeasLab() {
  const categoryFilters = document.querySelectorAll("#ideas-category-filters .preset-chip");
  categoryFilters.forEach((chip) => {
    chip.onclick = () => {
      categoryFilters.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      STATE.activeIdeaCategory = chip.dataset.category || "all";
      renderIdeasLabCards();
    };
  });

  const searchInput = document.getElementById("ideas-search-input");
  if (searchInput) {
    searchInput.oninput = (e) => {
      STATE.ideasSearchQuery = e.target.value.toLowerCase().trim();
      renderIdeasLabCards();
    };
  }

  renderIdeasLabCards();
}

function renderIdeasLabCards() {
  const container = document.getElementById("ideas-lab-grid");
  if (!container) return;

  container.innerHTML = "";
  const filtered = STATE.presets.filter((idea) => {
    const matchCategory = STATE.activeIdeaCategory === "all" || idea.category === STATE.activeIdeaCategory;
    const matchSearch = !STATE.ideasSearchQuery ||
      idea.title.toLowerCase().includes(STATE.ideasSearchQuery) ||
      idea.hook.toLowerCase().includes(STATE.ideasSearchQuery) ||
      idea.category.toLowerCase().includes(STATE.ideasSearchQuery);
    return matchCategory && matchSearch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 2.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
        Nenhuma pauta encontrada para os filtros selecionados.
      </div>
    `;
    return;
  }

  filtered.forEach((idea) => {
    const wordCount = idea.script ? idea.script.trim().split(/\s+/).length : 0;
    const estSeconds = Math.ceil(wordCount / 2.5);

    const card = document.createElement("div");
    card.className = "card";
    card.style.display = "flex";
    card.style.flexDirection = "column";
    card.style.justifyContent = "space-between";

    const vTags = (idea.video_tags || []).slice(0, 2).map(t => `<span style="font-size:0.68rem; padding:0.15rem 0.4rem; border-radius:4px; background:rgba(59,130,246,0.1); color:#60a5fa; border:1px solid rgba(59,130,246,0.2); font-family:var(--font-mono);">VÍDEO • ${t}</span>`).join(" ");
    const iTags = (idea.image_tags || []).slice(0, 2).map(t => `<span style="font-size:0.68rem; padding:0.15rem 0.4rem; border-radius:4px; background:rgba(16,185,129,0.1); color:#34d399; border:1px solid rgba(16,185,129,0.2); font-family:var(--font-mono);">IMG • ${t}</span>`).join(" ");
    const gTags = (idea.gif_tags || []).slice(0, 1).map(t => `<span style="font-size:0.68rem; padding:0.15rem 0.4rem; border-radius:4px; background:rgba(236,72,153,0.1); color:#f472b6; border:1px solid rgba(236,72,153,0.2); font-family:var(--font-mono);">GIF • ${t}</span>`).join(" ");

    card.innerHTML = `
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
          <span style="font-size:0.75rem; font-family:var(--font-mono); color:var(--text-muted);">${idea.category}</span>
          <span style="font-size:0.7rem; font-family:var(--font-mono); color:var(--status-success); background:rgba(16,185,129,0.1); padding:0.15rem 0.45rem; border-radius:4px; border:1px solid rgba(16,185,129,0.2);">
            ${wordCount} pal. • ~${estSeconds}s
          </span>
        </div>
        <h3 style="font-size:0.98rem; font-weight:600; color:var(--text-primary); margin-bottom:0.5rem; line-height:1.4;">
          ${idea.title}
        </h3>
        <p style="font-size:0.8rem; color:var(--text-secondary); line-height:1.5; margin-bottom:0.75rem; font-style:italic;">
          "${idea.hook}"
        </p>
        <p style="font-size:0.75rem; color:var(--text-muted); line-height:1.4; margin-bottom:0.85rem; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;">
          ${idea.script}
        </p>
        <div style="display:flex; flex-wrap:wrap; gap:0.35rem; margin-bottom:1rem;">
          ${vTags} ${iTags} ${gTags}
        </div>
      </div>
      <div style="display:grid; grid-template-columns: 1fr auto; gap:0.5rem; border-top:1px solid var(--border-subtle); padding-top:0.75rem;">
        <button type="button" class="btn-primary" style="font-size:0.78rem; padding:0.4rem 0.65rem; justify-content:center;" data-action="load">
          Carregar Roteiro & Tags
        </button>
        <button type="button" class="btn-secondary" style="font-size:0.78rem; padding:0.4rem 0.65rem;" data-action="copy" title="Copiar roteiro completo">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
      </div>
    `;

    card.querySelector('[data-action="load"]').onclick = () => {
      applyPreset(idea);
      document.querySelector('[data-target="view-studio"]').click();
      window.scrollTo({ top: 0, behavior: "smooth" });
      showToast(`Pauta carregada: ${idea.title}`, "success");
    };

    card.querySelector('[data-action="copy"]').onclick = () => {
      navigator.clipboard.writeText(idea.script);
      showToast("Roteiro copiado para a área de transferência!", "info");
    };

    container.appendChild(card);
  });
}

function renderMediaTags() {
  const container = document.getElementById("media-tags-grid");
  if (!container || !STATE.mediaTags) return;

  container.innerHTML = "";
  const categories = Object.keys(STATE.mediaTags);
  if (categories.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align:center; color:var(--text-muted); font-size:0.85rem; padding:2rem;">Carregando banco de tags...</div>`;
    return;
  }

  categories.forEach((catKey) => {
    const cat = STATE.mediaTags[catKey];
    const card = document.createElement("div");
    card.className = "card";

    const vTagsHtml = (cat.video_tags || []).map(t => `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:0.35rem 0.55rem; border-radius:4px; margin-bottom:0.35rem; font-size:0.75rem; border:1px solid var(--border-subtle);">
        <span style="font-family:var(--font-mono); color:var(--text-secondary);">${t}</span>
        <button type="button" class="btn-secondary" style="font-size:0.7rem; padding:0.15rem 0.4rem;" onclick="copyTag('${t}')">Copiar</button>
      </div>
    `).join("");

    const iTagsHtml = (cat.image_tags || []).map(t => `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:0.35rem 0.55rem; border-radius:4px; margin-bottom:0.35rem; font-size:0.75rem; border:1px solid var(--border-subtle);">
        <span style="font-family:var(--font-mono); color:var(--text-secondary);">${t}</span>
        <button type="button" class="btn-secondary" style="font-size:0.7rem; padding:0.15rem 0.4rem;" onclick="copyTag('${t}')">Copiar</button>
      </div>
    `).join("");

    const gTagsHtml = (cat.gif_tags || []).map(t => `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:0.35rem 0.55rem; border-radius:4px; margin-bottom:0.35rem; font-size:0.75rem; border:1px solid var(--border-subtle);">
        <span style="font-family:var(--font-mono); color:var(--text-secondary);">${t}</span>
        <button type="button" class="btn-secondary" style="font-size:0.7rem; padding:0.15rem 0.4rem;" onclick="copyTag('${t}')">Copiar</button>
      </div>
    `).join("");

    card.innerHTML = `
      <div style="margin-bottom:1rem; border-bottom:1px solid var(--border-subtle); padding-bottom:0.75rem;">
        <h3 style="font-size:1rem; font-weight:600; color:var(--text-primary); margin-bottom:0.25rem;">${cat.title}</h3>
        <span style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">${catKey}</span>
      </div>

      <div style="margin-bottom:1rem;">
        <div style="font-size:0.75rem; font-weight:600; color:#60a5fa; margin-bottom:0.4rem; text-transform:uppercase; letter-spacing:0.05em;">Acervo de Vídeos (4K/HD Stock)</div>
        ${vTagsHtml}
      </div>

      <div style="margin-bottom:1rem;">
        <div style="font-size:0.75rem; font-weight:600; color:#34d399; margin-bottom:0.4rem; text-transform:uppercase; letter-spacing:0.05em;">Acervo de Imagens (HD / CC0)</div>
        ${iTagsHtml}
      </div>

      <div>
        <div style="font-size:0.75rem; font-weight:600; color:#f472b6; margin-bottom:0.4rem; text-transform:uppercase; letter-spacing:0.05em;">Acervo de GIFs & Animações</div>
        ${gTagsHtml}
      </div>
    `;

    container.appendChild(card);
  });
}

function copyTag(tag) {
  navigator.clipboard.writeText(tag);
  if (!STATE.searchTerms.includes(tag)) {
    STATE.searchTerms.push(tag);
    renderTermTags();
    showToast(`Tag "${tag}" copiada e adicionada aos termos do projeto!`, "info");
  } else {
    showToast(`Tag "${tag}" copiada!`, "info");
  }
}

// ==========================================================================
// Form Controls: Terms, Script Counter, Sliders
// ==========================================================================
function setupScriptCounter() {
  const scriptInput = document.getElementById("video-script");
  if (scriptInput) {
    scriptInput.addEventListener("input", updateScriptMeta);
  }
}

function updateScriptMeta() {
  const scriptInput = document.getElementById("video-script");
  const wordsCounter = document.getElementById("word-count");
  const durationEstimate = document.getElementById("est-duration");
  if (!scriptInput || !wordsCounter || !durationEstimate) return;

  const text = scriptInput.value.trim();
  const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
  const voiceRateSlider = document.getElementById("voice-rate-slider");
  const rate = voiceRateSlider ? parseFloat(voiceRateSlider.value) || 1.15 : 1.15;
  const wps = 2.65 * (rate / 1.15);
  const seconds = words > 0 ? Math.ceil(words / wps) : 0;

  wordsCounter.textContent = `${words} palavras`;
  if (seconds >= 45 && seconds <= 65) {
    durationEstimate.textContent = `~${seconds}s (@ ${rate.toFixed(2)}x) • Ritmo ideal (45s–65s)`;
    durationEstimate.style.color = "var(--accent-emerald, #10b981)";
  } else if (seconds > 65) {
    durationEstimate.textContent = `~${seconds}s (@ ${rate.toFixed(2)}x) • Acima de 65s`;
    durationEstimate.style.color = "#fbbf24";
  } else if (seconds > 0) {
    durationEstimate.textContent = `~${seconds}s (@ ${rate.toFixed(2)}x) • Formato curto (<45s)`;
    durationEstimate.style.color = "#38bdf8";
  } else {
    durationEstimate.textContent = `~0s estimado`;
    durationEstimate.style.color = "var(--text-muted, #71717a)";
  }
}

function setupTermsInput() {
  renderTermTags();

  const termInput = document.getElementById("term-input-field");
  if (termInput) {
    termInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        const val = termInput.value.trim().replace(",", "");
        if (val && !STATE.searchTerms.includes(val)) {
          STATE.searchTerms.push(val);
          renderTermTags();
          termInput.value = "";
        }
      }
    });
  }

  const btnAutoTerms = document.getElementById("btn-auto-terms");
  if (btnAutoTerms) {
    btnAutoTerms.addEventListener("click", generateAutoTerms);
  }
}

function renderTermTags() {
  const container = document.getElementById("terms-tags-list");
  if (!container) return;

  container.innerHTML = "";
  STATE.searchTerms.forEach((term, index) => {
    const tag = document.createElement("span");
    tag.className = "term-tag";
    tag.innerHTML = `${term} <button type="button" title="Remover">✕</button>`;
    tag.querySelector("button").addEventListener("click", () => {
      STATE.searchTerms.splice(index, 1);
      renderTermTags();
    });
    container.appendChild(tag);
  });
}

async function generateAutoTerms() {
  const subject = document.getElementById("video-subject").value.trim();
  const script = document.getElementById("video-script").value.trim();

  if (!subject && !script) {
    showToast("Preencha o tema ou o roteiro antes de otimizar as tags.", "error");
    return;
  }

  showToast("Otimizando palavras-chave em inglês para busca de B-roll...", "info");
  try {
    const res = await fetch("/api/v1/terms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_subject: subject,
        video_script: script,
        amount: 4,
        match_materials_to_script: true,
      }),
    });

    if (res.ok) {
      const data = await res.json();
      const terms = data.data?.video_terms || [];
      if (terms.length > 0) {
        STATE.searchTerms = terms;
        renderTermTags();
        showToast("Palavras-chave geradas com sucesso.", "success");
        return;
      }
    }
  } catch (err) {
    // Fallback heuristic
  }

  const defaultTerms = [
    "space galaxy cosmic 4k cinematic",
    "deep universe astronomy scientific",
    "physics energy laboratory research",
  ];
  STATE.searchTerms = defaultTerms;
  renderTermTags();
  showToast("Tags padrão aplicadas.", "info");
}

function setupSliders() {
  const voiceRateSlider = document.getElementById("voice-rate-slider");
  const voiceRateVal = document.getElementById("voice-rate-val");
  if (voiceRateSlider && voiceRateVal) {
    voiceRateSlider.addEventListener("input", () => {
      voiceRateVal.textContent = `${parseFloat(voiceRateSlider.value).toFixed(2)}x`;
      updateScriptMeta();
    });
  }

  const bgmVolSlider = document.getElementById("bgm-vol-slider");
  const bgmVolVal = document.getElementById("bgm-vol-val");
  if (bgmVolSlider && bgmVolVal) {
    bgmVolSlider.addEventListener("input", () => {
      const pct = Math.round(parseFloat(bgmVolSlider.value) * 100);
      bgmVolVal.textContent = `${pct}%`;
    });
  }
}

// ==========================================================================
// Roteiro Automatizado & Submissão
// ==========================================================================
function setupForms() {
  const btnGenerateScript = document.getElementById("btn-ai-script");
  if (btnGenerateScript) {
    btnGenerateScript.addEventListener("click", generateAiScript);
  }

  const btnGenerateVideo = document.getElementById("btn-generate-video");
  if (btnGenerateVideo) {
    btnGenerateVideo.addEventListener("click", submitVideoGeneration);
  }

  const btnSaveSettings = document.getElementById("btn-save-settings");
  if (btnSaveSettings) {
    btnSaveSettings.addEventListener("click", saveSettings);
  }

  const btnPublishSocial = document.getElementById("btn-publish-social");
  if (btnPublishSocial) {
    btnPublishSocial.addEventListener("click", handleManualSocialPublish);
  }
}

async function generateAiScript() {
  const subject = document.getElementById("video-subject").value.trim();
  if (!subject) {
    showToast("Por favor, informe o tema ou título desejado.", "error");
    return;
  }

  const btn = document.getElementById("btn-ai-script");
  btn.disabled = true;
  btn.textContent = "Gerando Roteiro...";
  showToast(`Elaborando roteiro detalhado (~${STATE.targetDuration}s / ${STATE.targetWords} palavras)...`, "info");
  TerminalDrawer.log("info", `Solicitando geração de roteiro via LLM para "${subject}" (~${STATE.targetDuration}s)...`);

  try {
    const res = await fetch("/api/v1/scripts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_subject: subject,
        video_language: "pt-BR",
        paragraph_number: STATE.targetDuration >= 90 ? 4 : 3,
        video_script_prompt: `Escreva um roteiro altamente descritivo e substancial em português com cerca de ${STATE.targetWords} palavras (mínimo de ${STATE.targetDuration} segundos de fala). Estruture com gancho de abertura intrigante, desenvolvimento aprofundado com fatos ou analogias e conclusão marcante. Sem markdown, sem títulos e sem saudações.`,
      }),
    });

    if (!res.ok) throw new Error("Erro na solicitação de roteiro");

    const data = await res.json();
    const script = data.data?.video_script;
    if (script) {
      document.getElementById("video-script").value = script;
      updateScriptMeta();
      generateAutoTerms();
      showToast("Roteiro descritivo estruturado com sucesso.", "success");
      TerminalDrawer.log("success", `Roteiro estruturado com sucesso para "${subject}".`);
    }
  } catch (err) {
    const matched = STATE.presets.find((p) => p.title.toLowerCase().includes(subject.toLowerCase()));
    if (matched) {
      document.getElementById("video-script").value = matched.script;
      updateScriptMeta();
      generateAutoTerms();
      showToast("Roteiro completo carregado da biblioteca de pautas.", "info");
      TerminalDrawer.log("warn", `LLM indisponível; roteiro padrão aplicado da biblioteca para "${subject}".`);
    } else {
      showToast("Não foi possível gerar via LLM. Verifique as configurações de API.", "error");
      TerminalDrawer.log("error", `Falha ao gerar roteiro via LLM para "${subject}".`);
    }
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg> Gerar Roteiro`;
  }
}

// ==========================================================================
// 1-Click Magic Setup
// ==========================================================================
function setupMagicPrompt() {
  const btnMagic = document.getElementById("btn-magic-fill");
  if (!btnMagic) return;

  btnMagic.addEventListener("click", async () => {
    const subjectInput = document.getElementById("video-subject");
    if (!subjectInput) return;

    let subject = subjectInput.value.trim();
    if (!subject) {
      const sampleTopics = [
        "O que aconteceria se a Terra parasse de girar por 5 segundos?",
        "O monstro cósmico TON 618: O maior buraco negro conhecido",
        "A misteriosa cidade subterrânea de Derinkuyu na Turquia",
        "Por que você sente déjà vu? A fascinante explicação da neurociência",
        "O som assustador gravado no ponto mais profundo do oceano",
        "A verdade chocante sobre a Ilha da Queimada Grande no Brasil",
        "Como a teoria dos jogos explica as decisões humanas",
        "O mistério do sinal Wow captado do espaço profundo"
      ];
      subject = sampleTopics[Math.floor(Math.random() * sampleTopics.length)];
      subjectInput.value = subject;
    }

    // Set 60s
    STATE.targetDuration = 60;
    STATE.targetWords = 150;
    const durationBtn = document.querySelector('#duration-selector-bar [data-duration="60"]');
    if (durationBtn) {
      document.querySelectorAll("#duration-selector-bar .source-btn").forEach(b => b.classList.remove("active"));
      durationBtn.classList.add("active");
    }

    // Source Hybrid
    const hybridBtn = document.getElementById("src-btn-hybrid");
    if (hybridBtn) hybridBtn.click();

    // Style Hormozi
    const hormoziCard = document.querySelector('.style-card[data-style="hormozi_bold"]');
    if (hormoziCard) hormoziCard.click();

    // Voice Antonio
    const voiceCard = document.querySelector('.voice-card[data-voice="pt-BR-AntonioNeural"]');
    if (voiceCard) voiceCard.click();

    showToast(`Configuração recomendada aplicada para "${subject}".`, "success");
    await generateAiScript();
  });
}

// ==========================================================================
// Safe Zone & Posting Metadata
// ==========================================================================
function setupSafeZoneToggle() {
  const btnToggle = document.getElementById("btn-toggle-safezone");
  const overlay = document.getElementById("safe-zone-overlay");
  if (!btnToggle || !overlay) return;

  btnToggle.addEventListener("click", () => {
    overlay.classList.toggle("active");
    const isActive = overlay.classList.contains("active");
    if (isActive) {
      btnToggle.style.borderColor = "var(--accent-emerald, #10b981)";
      btnToggle.style.color = "var(--accent-emerald, #10b981)";
      showToast("Área Segura do TikTok / Reels ativada.", "info");
    } else {
      btnToggle.style.borderColor = "rgba(255,255,255,0.15)";
      btnToggle.style.color = "";
      showToast("Área Segura desativada.", "info");
    }
  });
}

function setupMetadataUI() {
  const btnTogglePanel = document.getElementById("btn-toggle-meta-panel");
  const panel = document.getElementById("metadata-panel");
  const btnCopyAll = document.getElementById("btn-copy-all-meta");
  const btnCopyPinned = document.getElementById("btn-copy-pinned-comment");
  const pinnedBox = document.getElementById("meta-pinned-comment-box");

  if (btnTogglePanel && panel) {
    btnTogglePanel.addEventListener("click", () => {
      const isVisible = panel.style.display !== "none";
      panel.style.display = isVisible ? "none" : "block";
    });
  }

  if (btnCopyPinned) {
    btnCopyPinned.addEventListener("click", () => {
      const textToCopy = STATE.currentPinnedComment || (pinnedBox ? pinnedBox.innerText : "");
      if (!textToCopy || textToCopy.includes("Aguardando geração")) {
        showToast("Nenhum comentário disponível para copiar.", "info");
        return;
      }
      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast("Comentário fixado copiado.", "success");
      }).catch(() => {
        prompt("Copie o comentário fixado:", textToCopy);
      });
    });
  }

  if (pinnedBox) {
    pinnedBox.addEventListener("click", () => {
      const textToCopy = STATE.currentPinnedComment || pinnedBox.innerText;
      if (textToCopy && !textToCopy.includes("Aguardando geração")) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          showToast("Comentário fixado copiado.", "success");
        }).catch(() => {
          prompt("Copie o comentário fixado:", textToCopy);
        });
      }
    });
  }

  if (btnCopyAll) {
    btnCopyAll.addEventListener("click", () => {
      if (!STATE.currentMetadata || !STATE.currentMetadata.clipboard_text) {
        showToast("Nenhum metadado gerado para copiar ainda.", "info");
        return;
      }
      navigator.clipboard.writeText(STATE.currentMetadata.clipboard_text).then(() => {
        showToast("Metadados copiados para a área de transferência.", "success");
      }).catch(() => {
        prompt("Copie os metadados:", STATE.currentMetadata.clipboard_text);
      });
    });
  }
}

function renderMetadata(meta) {
  if (!meta) return;
  STATE.currentMetadata = meta;

  const panel = document.getElementById("metadata-panel");
  const titlesContainer = document.getElementById("meta-titles-container");
  const descBox = document.getElementById("meta-desc-box");
  const tagsContainer = document.getElementById("meta-hashtags-container");
  const pinnedBox = document.getElementById("meta-pinned-comment-box");
  const monetizationExtra = document.getElementById("meta-monetization-extra");
  const rpmBadge = document.getElementById("meta-monetization-rpm-badge");
  const monetizationDetails = document.getElementById("meta-monetization-details");

  if (titlesContainer && Array.isArray(meta.titles)) {
    titlesContainer.innerHTML = "";
    meta.titles.forEach((t) => {
      const item = document.createElement("div");
      item.className = "metadata-title-item";
      item.innerHTML = `
        <span style="flex:1;">${t}</span>
        <span style="font-size:0.65rem; color:var(--text-muted); opacity:0.75;">Copiar</span>
      `;
      item.addEventListener("click", () => {
        navigator.clipboard.writeText(t);
        showToast(`Título copiado: "${t}"`, "info");
      });
      titlesContainer.appendChild(item);
    });
  }

  if (descBox && meta.description) {
    descBox.textContent = meta.description;
    descBox.onclick = () => {
      navigator.clipboard.writeText(meta.description);
      showToast("Gancho e descrição copiados!", "info");
    };
  }

  // Pinned comment & ManyChat DM trigger
  const pinnedText = meta.pinned_comment_dm_trigger ||
    (meta.monetization && meta.monetization.pinned_comment_dm_trigger) ||
    meta.pinned_comment || "";

  if (pinnedBox && pinnedText) {
    STATE.currentPinnedComment = pinnedText;
    pinnedBox.textContent = pinnedText;
    pinnedBox.style.color = "var(--text-primary)";
  }

  // Monetization RPM & funnel estimation card
  const monetization = meta.monetization || meta;
  const rev = monetization ? (monetization.revenue_estimator || monetization.estimated_earnings) : null;
  if (monetizationExtra && rev) {
    const t1 = rev.tier_1 ? rev.tier_1.views_100k : "$15.00 - $35.00";
    const br = rev.brazil_tier_3 ? rev.brazil_tier_3.views_100k : "R$ 15,00 - R$ 35,00";
    if (rpmBadge) {
      rpmBadge.textContent = `100k views: ${t1} (Tier 1) | ${br} (BR)`;
    }
    if (monetizationDetails && rev.longform_bridge_extra) {
      monetizationDetails.innerHTML = `
        <div><strong>Ponte para vídeo longo:</strong> ${rev.longform_bridge_extra.extra_100k_views}</div>
        <div><strong>Leads no Direct:</strong> ${rev.lead_capture_potential ? rev.lead_capture_potential.leads_100k_views : "1.500 - 3.000 leads automáticos"}</div>
      `;
    }
    monetizationExtra.style.display = "block";
  }

  if (tagsContainer && Array.isArray(meta.hashtags)) {
    tagsContainer.innerHTML = "";
    meta.hashtags.forEach((tag) => {
      const chip = document.createElement("span");
      chip.className = "metadata-tag-chip";
      chip.textContent = tag;
      chip.title = "Clique para copiar esta hashtag";
      chip.addEventListener("click", (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(tag);
        showToast(`Hashtag copiada: ${tag}`, "info");
      });
      tagsContainer.appendChild(chip);
    });
    tagsContainer.title = "Clique no container para copiar todas as hashtags";
    tagsContainer.onclick = () => {
      const allTags = meta.hashtags.join(" ");
      navigator.clipboard.writeText(allTags);
      showToast("Todas as hashtags copiadas!", "info");
    };
  }

  if (panel) {
    panel.style.display = "block";
  }
}

// ==========================================================================
// Diagnóstico de Retenção Viral & Ganchos A/B
// ==========================================================================
function setupViralAnalyticsUI() {
  const btnAnalyze = document.getElementById("btn-analyze-script");
  const btnClose = document.getElementById("btn-close-viral-panel");
  const panel = document.getElementById("viral-analysis-panel");

  if (btnAnalyze) {
    btnAnalyze.addEventListener("click", () => {
      triggerScriptAnalysis();
    });
  }

  if (btnClose && panel) {
    btnClose.addEventListener("click", () => {
      panel.style.display = "none";
    });
  }
}

async function triggerScriptAnalysis() {
  const scriptInput = document.getElementById("video-script");
  const subjectInput = document.getElementById("video-subject");
  const btnAnalyze = document.getElementById("btn-analyze-script");
  const panel = document.getElementById("viral-analysis-panel");

  const script = scriptInput ? scriptInput.value.trim() : "";
  const subject = subjectInput ? subjectInput.value.trim() : "";

  if (!script) {
    showToast("Por favor, digite ou gere um roteiro antes de analisar.", "warning");
    return;
  }

  const originalHtml = btnAnalyze ? btnAnalyze.innerHTML : "";
  if (btnAnalyze) {
    btnAnalyze.disabled = true;
    btnAnalyze.innerHTML = `<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" class="spin"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg> Analisando...`;
  }

  try {
    const res = await fetch("/api/v1/saas/script/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script, subject }),
    });

    const body = await res.json();
    if (res.ok && body.status === 200 && body.data) {
      renderViralAnalytics(body.data);
      if (panel) panel.style.display = "block";
      showToast("✓ Análise de retenção e ganchos concluída!", "success");
    } else {
      showToast(`Falha ao analisar roteiro: ${body.message || "Erro desconhecido"}`, "error");
    }
  } catch (err) {
    console.error("Erro na análise viral:", err);
    showToast("Erro ao conectar com o serviço de análise viral.", "error");
  } finally {
    if (btnAnalyze) {
      btnAnalyze.disabled = false;
      btnAnalyze.innerHTML = originalHtml;
    }
  }
}

function renderViralAnalytics(data) {
  if (!data) return;

  // 1. Overall badge
  const overallBadge = document.getElementById("viral-overall-badge");
  if (overallBadge) {
    overallBadge.textContent = `Score: ${data.overall_score || 0}/100`;
    if (data.overall_score >= 80) {
      overallBadge.style.color = "#10b981";
      overallBadge.style.background = "rgba(16,185,129,0.15)";
    } else if (data.overall_score >= 60) {
      overallBadge.style.color = "#f59e0b";
      overallBadge.style.background = "rgba(245,158,11,0.15)";
    } else {
      overallBadge.style.color = "#ef4444";
      overallBadge.style.background = "rgba(239,68,68,0.15)";
    }
  }

  // 2. Score Gauges
  const scoreHook = document.getElementById("score-hook");
  const scoreHookDesc = document.getElementById("score-hook-desc");
  if (scoreHook) scoreHook.textContent = `${data.hook_score || 0}/100`;
  if (scoreHookDesc && data.hook_analysis) scoreHookDesc.textContent = data.hook_analysis.rating || "-";

  const scorePacing = document.getElementById("score-pacing");
  const scorePacingDesc = document.getElementById("score-pacing-desc");
  if (scorePacing) scorePacing.textContent = `${data.pacing_score || 0}/100`;
  if (scorePacingDesc && data.pacing_analysis) scorePacingDesc.textContent = data.pacing_analysis.rating || "-";

  const scoreDuration = document.getElementById("score-duration");
  if (scoreDuration) scoreDuration.textContent = `~${data.estimated_duration_seconds || 0}s`;

  // 3. Retention Milestones
  const milestonesContainer = document.getElementById("retention-milestones-container");
  if (milestonesContainer && Array.isArray(data.retention_simulation)) {
    milestonesContainer.innerHTML = "";
    data.retention_simulation.forEach(m => {
      const pill = document.createElement("div");
      pill.style.cssText = "padding:0.4rem 0.3rem; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.06); border-radius:4px; text-align:center;";
      const color = m.dropoff_risk === "Baixo" || m.dropoff_risk === "Mínimo" ? "#10b981" : (m.dropoff_risk === "Médio" ? "#f59e0b" : "#ef4444");
      pill.innerHTML = `
        <div style="font-size:0.65rem; color:var(--text-muted); font-weight:600;">${m.second}s</div>
        <div style="font-size:0.85rem; font-weight:700; color:${color}; margin:0.15rem 0;">${m.retention_rate}%</div>
        <div style="font-size:0.6rem; color:${color};">${m.dropoff_risk}</div>
      `;
      milestonesContainer.appendChild(pill);
    });
  }

  // 4. Actionable Recommendations
  const recList = document.getElementById("viral-recommendations-list");
  if (recList && Array.isArray(data.recommendations)) {
    recList.innerHTML = "";
    data.recommendations.forEach(tip => {
      const li = document.createElement("li");
      li.style.marginBottom = "0.25rem";
      li.textContent = tip;
      recList.appendChild(li);
    });
  }

  // 5. 3 A/B Hook Variations
  const hooksContainer = document.getElementById("hook-variations-container");
  if (hooksContainer && Array.isArray(data.hook_variations)) {
    hooksContainer.innerHTML = "";
    data.hook_variations.forEach(v => {
      const card = document.createElement("div");
      card.style.cssText = "padding:0.55rem 0.75rem; background:rgba(0,0,0,0.25); border:1px solid rgba(255,255,255,0.06); border-radius:var(--radius-sm); display:flex; justify-content:space-between; align-items:center; gap:0.6rem;";
      card.innerHTML = `
        <div style="flex:1;">
          <div style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.2rem;">
            <span style="font-size:0.7rem; font-weight:700; color:#6366f1;">${v.type} (${v.type_pt})</span>
            <span style="font-size:0.65rem; padding:0.05rem 0.35rem; border-radius:3px; background:rgba(16,185,129,0.15); color:#10b981; font-weight:600;">${v.retention_lift}</span>
          </div>
          <div style="font-size:0.775rem; color:var(--text-primary); font-style:italic;">"${v.hook}"</div>
          <div style="font-size:0.65rem; color:var(--text-muted); margin-top:0.2rem;">Gatilho: ${v.psychological_trigger}</div>
        </div>
        <button type="button" class="btn-secondary" style="padding:0.25rem 0.5rem; font-size:0.7rem; flex-shrink:0;">
          Usar Gancho
        </button>
      `;
      const btnApply = card.querySelector("button");
      btnApply.addEventListener("click", () => {
        applyHookToScript(v.hook);
      });
      hooksContainer.appendChild(card);
    });
  }
}

function applyHookToScript(newHook) {
  const scriptInput = document.getElementById("video-script");
  if (!scriptInput || !newHook) return;

  const current = scriptInput.value.trim();
  if (!current) {
    scriptInput.value = newHook;
  } else {
    const firstEnd = current.search(/[.!?…\n]/);
    if (firstEnd !== -1) {
      const rest = current.substring(firstEnd + 1).trim();
      scriptInput.value = `${newHook.trim()} ${rest}`;
    } else {
      scriptInput.value = `${newHook.trim()}`;
    }
  }

  updateScriptMeta();
  showToast("Gancho aplicado ao início do roteiro.", "success");
}

// ==========================================================================
// Fábrica em Lote (Batch Production Studio)
// ==========================================================================
let isBatchRunning = false;
let batchCancelRequested = false;

function setupBatchStudio() {
  const topicsInput = document.getElementById("batch-topics-input");
  const countLabel = document.getElementById("batch-count-label");
  const btnPopulate = document.getElementById("btn-batch-populate-samples");
  const btnStart = document.getElementById("btn-start-batch");
  const btnStop = document.getElementById("btn-stop-batch");

  if (topicsInput && countLabel) {
    topicsInput.addEventListener("input", () => {
      const lines = topicsInput.value.split("\n").map(l => l.trim()).filter(Boolean);
      countLabel.textContent = `${lines.length} tópicos detectados`;
    });
  }

  if (btnPopulate && topicsInput) {
    btnPopulate.addEventListener("click", () => {
      const sampleList = [
        "O que aconteceria se a Terra parasse de girar por 5 segundos?",
        "A misteriosa cidade subterrânea de Derinkuyu na Turquia",
        "Por que você sente déjà vu? A fascinante explicação da neurociência",
        "TON 618: O buraco negro supermassivo que desafia a astrofísica",
        "O mistério assustador da Fossa das Marianas e o fundo do oceano"
      ];
      topicsInput.value = sampleList.join("\n");
      if (countLabel) countLabel.textContent = `5 tópicos detectados`;
      showToast("5 pautas virais carregadas na fila!", "success");
    });
  }

  if (btnStart) {
    btnStart.addEventListener("click", runBatchProduction);
  }

  if (btnStop) {
    btnStop.addEventListener("click", () => {
      batchCancelRequested = true;
      btnStop.textContent = "Cancelando...";
      showToast("Aguardando finalização do vídeo atual para pausar o lote...", "info");
    });
  }
}

async function runBatchProduction() {
  if (isBatchRunning) {
    showToast("A produção em lote já está em andamento.", "info");
    return;
  }

  const topicsInput = document.getElementById("batch-topics-input");
  const lines = (topicsInput?.value || "").split("\n").map(l => l.trim()).filter(Boolean);
  if (lines.length === 0) {
    showToast("Insira ao menos um tópico para iniciar a produção em lote.", "error");
    return;
  }

  const voiceSelect = document.getElementById("batch-voice-select");
  const styleSelect = document.getElementById("batch-style-select");
  const sourceSelect = document.getElementById("batch-source-select");
  const durationSelect = document.getElementById("batch-duration-select");

  const voiceName = voiceSelect?.value || "pt-BR-AntonioNeural";
  const styleId = styleSelect?.value || "hormozi_bold";
  const videoSource = sourceSelect?.value || "hybrid";
  const duration = parseInt(durationSelect?.value) || 60;

  const styleObj = STATE.subtitleStyles.find(s => s.id === styleId) || STATE.subtitleStyles[0] || {
    subtitle_position: "bottom",
    subtitle_display_mode: "word",
    subtitle_animation: "bounce",
    font_name: "BeVietnamPro-Bold",
    text_fore_color: "&H0000FFFF",
    font_size: 19,
    stroke_color: "&H00000000",
    stroke_width: 2.8,
  };

  isBatchRunning = true;
  batchCancelRequested = false;
  TerminalDrawer.log("info", `Produção em lote iniciada (${lines.length} itens na fila).`);
  updateStatusBarTask(`Lote: 0/${lines.length} em processamento`);

  const btnStart = document.getElementById("btn-start-batch");
  const btnStop = document.getElementById("btn-stop-batch");
  if (btnStart) {
    btnStart.disabled = true;
    btnStart.innerHTML = `<span class="spinner" style="display:inline-block; width:12px; height:12px; border:2px solid white; border-top-color:transparent; border-radius:50%; margin-right:6px; vertical-align:middle; animation:spin 1s linear infinite;"></span> Processando Lote...`;
  }
  if (btnStop) {
    btnStop.style.display = "inline-flex";
    btnStop.textContent = "Parar Fila";
  }

  const statTotal = document.getElementById("batch-stat-total");
  const statDone = document.getElementById("batch-stat-done");
  const statRunning = document.getElementById("batch-stat-running");
  const tableBody = document.getElementById("batch-table-body");

  if (statTotal) statTotal.textContent = lines.length;
  if (statDone) statDone.textContent = "0";
  if (statRunning) statRunning.textContent = "1";

  // Build table rows
  tableBody.innerHTML = "";
  lines.forEach((topic, idx) => {
    const tr = document.createElement("tr");
    tr.id = `batch-row-${idx}`;
    tr.innerHTML = `
      <td style="color:var(--text-muted); font-family:var(--font-mono);">${idx + 1}</td>
      <td style="font-weight:500; color:var(--text-primary); max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${topic}">${topic}</td>
      <td id="batch-status-${idx}">
        <span class="status-badge" style="font-size:0.7rem; padding:0.15rem 0.45rem;">Pendente</span>
      </td>
      <td id="batch-actions-${idx}" style="text-align:right;">
        <span style="font-size:0.75rem; color:var(--text-muted);">-</span>
      </td>
    `;
    tableBody.appendChild(tr);
  });

  let doneCount = 0;

  for (let i = 0; i < lines.length; i++) {
    if (batchCancelRequested) {
      showToast("Fila em lote interrompida pelo usuário.", "info");
      TerminalDrawer.log("warn", "Produção em lote interrompida pelo usuário.");
      updateStatusBarTask("Lote interrompido");
      break;
    }

    const topic = lines[i];
    const statusCell = document.getElementById(`batch-status-${i}`);
    const actionsCell = document.getElementById(`batch-actions-${i}`);

    if (statRunning) statRunning.textContent = `${i + 1}/${lines.length}`;
    TerminalDrawer.log("info", `[Lote ${i + 1}/${lines.length}] Processando: "${topic}"`);
    if (statusCell) {
      statusCell.innerHTML = `<span class="status-badge" style="background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); font-size:0.7rem; padding:0.15rem 0.45rem;">Renderizando...</span>`;
    }

    try {
      // 1. Get or generate script
      let script = "";
      const matched = STATE.presets.find(p => p.title.toLowerCase().includes(topic.toLowerCase()));
      if (matched) {
        script = matched.script;
      } else {
        const scriptRes = await fetch("/api/v1/scripts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_subject: topic,
            video_language: "pt-BR",
            paragraph_number: 3,
            video_script_prompt: `Escreva um roteiro altamente descritivo e substancial em português com cerca de 150 palavras (60 segundos de fala). Sem markdown, sem títulos e sem saudações.`,
          }),
        });
        if (scriptRes.ok) {
          const sData = await scriptRes.json();
          script = sData.data?.video_script || "";
        }
      }

      if (!script) {
        script = `Você sabia disso sobre ${topic}? Cientistas e pesquisadores recentemente descobriram evidências impressionantes que mudam tudo o que sabíamos. A cada nova medição, fica evidente que o universo guarda segredos muito maiores do que nossa imaginação pode conceber. Continue acompanhando para mais revelações científicas fascinantes.`;
      }

      // 2. Dispatch task
      const taskPayload = {
        video_subject: topic,
        video_script: script,
        video_terms: [topic],
        video_aspect: "9:16",
        voice_name: voiceName,
        voice_volume: 1.0,
        voice_rate: 1.15,
        bgm_type: "random",
        bgm_file: "",
        bgm_volume: 0.15,
        subtitle_enabled: true,
        subtitle_position: styleObj.subtitle_position,
        subtitle_display_mode: styleObj.subtitle_display_mode,
        subtitle_animation: styleObj.subtitle_animation,
        font_name: styleObj.font_name,
        text_fore_color: styleObj.text_fore_color,
        font_size: styleObj.font_size,
        stroke_color: styleObj.stroke_color,
        stroke_width: styleObj.stroke_width,
        video_source: videoSource,
        video_clip_duration: 4,
        video_count: 1,
      };

      const taskRes = await fetch("/api/v1/videos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskPayload),
      });

      if (!taskRes.ok) throw new Error("Falha ao enfileirar");
      const taskData = await taskRes.json();
      const taskId = taskData.data?.task_id;

      // 3. Poll until done
      let completedTask = null;
      for (let attempt = 0; attempt < 120; attempt++) {
        await new Promise(r => setTimeout(r, 3000));
        const checkRes = await fetch(`/api/v1/tasks/${taskId}`);
        if (checkRes.ok) {
          const cData = await checkRes.json();
          const tState = cData.data?.state;
          if (tState === 1) {
            completedTask = cData.data;
            break;
          } else if (tState === -1) {
            throw new Error(cData.data?.error || "Erro na renderização");
          }
        }
      }

      if (!completedTask || !completedTask.videos || completedTask.videos.length === 0) {
        throw new Error("Vídeo não finalizado dentro do tempo limite");
      }

      const videoUrl = completedTask.videos[0];
      const thumbUrl = `/tasks/${taskId}/thumbnail-1.jpg`;

      // Social publishing for batch
      const shouldPublishBatch = document.getElementById("batch-auto-publish-toggle")?.checked || STATE.uploadPostAutoUpload;
      let socialTag = "";
      if (shouldPublishBatch) {
        try {
          const pRes = await fetch("/api/v1/saas/publish", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task_id: taskId }),
          });
          const pJson = await pRes.json();
          if (pRes.ok && pJson.data?.success) {
            socialTag = `<span style="margin-left:0.35rem; color:var(--text-emerald); font-size:0.68rem; font-weight:500;" title="Publicado no TikTok e YouTube">📱 TikTok/YT</span>`;
          }
        } catch (e) {
          console.warn("Batch auto-publish trigger error:", e);
        }
      } else if (completedTask.cross_post_state === "complete") {
        socialTag = `<span style="margin-left:0.35rem; color:var(--text-emerald); font-size:0.68rem; font-weight:500;" title="Publicado no TikTok e YouTube">📱 TikTok/YT</span>`;
      }

      if (statusCell) {
        statusCell.innerHTML = `<span class="status-badge" style="background:rgba(16,185,129,0.15); color:var(--text-emerald); border:1px solid rgba(16,185,129,0.3); font-size:0.7rem; padding:0.15rem 0.45rem;">✓ Concluído</span>${socialTag}`;
      }
      if (actionsCell) {
        actionsCell.innerHTML = `
          <div style="display:flex; gap:0.35rem; justify-content:flex-end; align-items:center;">
            <a href="${videoUrl}" download="${topic.replace(/[^a-zA-Z0-9_-]/g, '_')}.mp4" class="btn-primary" style="font-size:0.68rem; padding:0.25rem 0.45rem; text-decoration:none;" title="Baixar Vídeo MP4">MP4</a>
            <a href="${thumbUrl}" download="${topic.replace(/[^a-zA-Z0-9_-]/g, '_')}-capa.jpg" class="btn-secondary" style="font-size:0.68rem; padding:0.25rem 0.45rem; text-decoration:none;" title="Baixar Capa HD">Capa</a>
            <button type="button" class="btn-secondary" style="font-size:0.68rem; padding:0.25rem 0.45rem;" onclick="publishBatchItem('${taskId}', this)" title="Publicar no TikTok e YouTube">Postar</button>
          </div>
        `;
      }

      doneCount++;
      if (statDone) statDone.textContent = doneCount;
      showToast(`Vídeo #${i + 1} concluído: "${topic}"`, "success");
      TerminalDrawer.log("success", `[Lote ${i + 1}/${lines.length}] Concluído com sucesso: "${topic}"`);
      updateStatusBarTask(`Lote: ${doneCount}/${lines.length} concluídos`);

    } catch (err) {
      if (statusCell) {
        statusCell.innerHTML = `<span class="status-badge" style="background:rgba(244,63,94,0.15); color:var(--status-error); border:1px solid rgba(244,63,94,0.3); font-size:0.7rem; padding:0.15rem 0.45rem;">✕ Falha</span>`;
      }
      showToast(`Erro no vídeo #${i + 1}: ${err.message}`, "error");
      TerminalDrawer.log("error", `[Lote ${i + 1}/${lines.length}] Erro ao produzir "${topic}": ${err.message}`);
      updateStatusBarTask(`Lote: Erro no item ${i + 1}`, true);
    }
  }

  isBatchRunning = false;
  if (statRunning) statRunning.textContent = "0";
  if (btnStart) {
    btnStart.disabled = false;
    btnStart.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Iniciar Produção em Lote`;
  }
  if (btnStop) btnStop.style.display = "none";
  showToast(`Lote finalizado! ${doneCount} de ${lines.length} vídeos produzidos.`, "success");
  TerminalDrawer.log("info", `Produção em lote finalizada: ${doneCount} de ${lines.length} vídeos produzidos.`);
  updateStatusBarTask(`Lote concluído: ${doneCount}/${lines.length}`);
}

// ==========================================================================
// Pipeline de Vídeo & Monitoramento
// ==========================================================================
// Pace, Aspect Ratio & Audio Features
// ==========================================================================
function setupPaceSelector() {
  const btns = document.querySelectorAll("#pace-selector-bar .source-btn");
  const hint = document.getElementById("pace-hint");
  btns.forEach((btn) => {
    btn.addEventListener("click", () => {
      btns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const p = parseInt(btn.dataset.pace) || 4;
      STATE.videoClipDuration = p;
      if (hint) {
        hint.textContent = p === 3 ? "3s por tomada (Dinâmico)" : (p === 6 ? "6s por tomada (Contemplativo)" : "4s por tomada (Equilibrado / Documental)");
      }
    });
  });
}

function setupAspectSelector() {
  const select = document.getElementById("video-aspect-select");
  const wrapper = document.querySelector(".player-wrapper");
  if (!select || !wrapper) return;

  select.addEventListener("change", () => {
    if (select.value === "16:9") {
      wrapper.classList.add("aspect-16-9");
    } else {
      wrapper.classList.remove("aspect-16-9");
    }
  });
}

let currentBgmAudio = null;

async function loadBgmTracks() {
  const select = document.getElementById("bgm-type-select");
  const previewBtn = document.getElementById("btn-preview-bgm");
  if (!select) return;

  try {
    const res = await fetch("/api/v1/saas/bgms");
    if (res.ok) {
      const data = await res.json();
      const songs = data.data?.songs || [];
      if (songs.length > 0) {
        select.innerHTML = `
          <option value="random">Trilha Neutra Suave (Aleatória)</option>
          <option value="none">Sem Trilha (Apenas Locução)</option>
        `;
        songs.forEach((s) => {
          const opt = document.createElement("option");
          opt.value = s.filename;
          opt.textContent = s.name;
          opt.dataset.preview = s.preview_url;
          select.appendChild(opt);
        });
      }
    }
  } catch (err) {
    console.warn("BGM endpoint loading fallback:", err);
  }

  if (previewBtn) {
    previewBtn.addEventListener("click", () => {
      const selOpt = select.options[select.selectedIndex];
      const previewUrl = selOpt?.dataset.preview || "/songs/output000.mp3";
      if (select.value === "none") {
        showToast("Nenhuma trilha sonora selecionada para prévia.", "info");
        return;
      }
      if (currentBgmAudio && !currentBgmAudio.paused) {
        currentBgmAudio.pause();
        currentBgmAudio.currentTime = 0;
        previewBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
      } else {
        if (currentBgmAudio) currentBgmAudio.pause();
        currentBgmAudio = new Audio(previewUrl);
        currentBgmAudio.volume = 0.25;
        currentBgmAudio.play().catch(() => {});
        previewBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>`;
        currentBgmAudio.onended = () => {
          previewBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
        };
      }
    });
  }
}

// ==========================================================================
// Materials Manager Modal
// ==========================================================================
function setupMaterialsModal() {
  const btnOpen = document.getElementById("btn-open-materials-modal");
  const modal = document.getElementById("modal-materials");
  const btnClose = document.getElementById("btn-close-materials-modal");
  const uploadInput = document.getElementById("materials-modal-upload-input");

  if (btnOpen && modal) {
    btnOpen.addEventListener("click", () => {
      modal.classList.add("active");
      loadMaterialsModalList();
    });
  }
  if (btnClose && modal) {
    btnClose.addEventListener("click", () => modal.classList.remove("active"));
  }
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
  }
  if (uploadInput) {
    uploadInput.addEventListener("change", handleLocalFileUpload);
  }
}

async function loadMaterialsModalList() {
  const container = document.getElementById("materials-modal-list");
  const summary = document.getElementById("materials-modal-summary");
  if (!container) return;

  container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted); font-size:0.8rem;">Carregando arquivos do acervo...</div>`;

  try {
    const res = await fetch("/api/v1/saas/materials");
    if (!res.ok) throw new Error("Erro ao carregar");
    const data = await res.json();
    const materials = data.data?.materials || [];

    if (summary) {
      const totalMb = materials.reduce((acc, m) => acc + (m.size_mb || 0), 0).toFixed(1);
      summary.textContent = `${materials.length} clipes disponíveis (${totalMb} MB total)`;
    }

    if (materials.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted); font-size:0.8rem;">Nenhum clipe no acervo local. Clique em Adicionar Vídeo MP4 para enviar.</div>`;
      return;
    }

    container.innerHTML = "";
    materials.forEach((m) => {
      const row = document.createElement("div");
      row.className = "material-item-row";
      const typeLabel = m.type === 'gif' ? 'GIF Animado' : (m.type === 'image' ? 'Imagem Estática' : 'Vídeo MP4');
      row.innerHTML = `
        <div class="material-item-info">
          <span class="material-item-name" title="${m.name}">${m.name}</span>
          <span class="material-item-meta">${m.size_mb} MB • ${typeLabel}</span>
        </div>
        <div class="material-item-actions">
          <button type="button" class="btn-secondary" style="font-size:0.7rem; padding:0.25rem 0.5rem; color:var(--status-error); border-color:rgba(244,63,94,0.3);" title="Excluir arquivo">
            Excluir
          </button>
        </div>
      `;

      row.querySelector("button").addEventListener("click", async () => {
        if (!confirm(`Deseja remover o vídeo "${m.name}" do acervo?`)) return;
        try {
          const delRes = await fetch(`/api/v1/saas/materials/${encodeURIComponent(m.name)}`, { method: "DELETE" });
          if (delRes.ok) {
            showToast(`Arquivo "${m.name}" removido com sucesso.`, "info");
            loadMaterialsModalList();
            refreshLocalMaterialsCount();
          } else {
            showToast("Falha ao excluir arquivo.", "error");
          }
        } catch (e) {
          showToast("Erro ao conectar com servidor.", "error");
        }
      });

      container.appendChild(row);
    });
  } catch (err) {
    container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--status-error); font-size:0.8rem;">Falha ao carregar lista de materiais.</div>`;
  }
}

function setupTaskCancel() {
  const btnCancel = document.getElementById("btn-cancel-task");
  if (!btnCancel) return;

  btnCancel.addEventListener("click", async () => {
    if (!STATE.currentTaskId) return;
    if (!confirm("Deseja interromper e cancelar a renderização em andamento?")) return;

    try {
      if (STATE.pollInterval) clearInterval(STATE.pollInterval);
      await fetch(`/api/v1/tasks/${STATE.currentTaskId}`, { method: "DELETE" });
      showToast("Renderização cancelada.", "info");

      const btnGen = document.getElementById("btn-generate-video");
      if (btnGen) {
        btnGen.disabled = false;
        btnGen.innerHTML = `Iniciar Renderização do Vídeo`;
      }
      btnCancel.style.display = "none";
      const progressSec = document.getElementById("progress-section");
      if (progressSec) progressSec.classList.remove("active");
      const badge = document.getElementById("task-status-badge");
      if (badge) badge.textContent = "Cancelado";
    } catch (err) {
      showToast("Erro ao cancelar tarefa.", "error");
    }
  });
}

// ==========================================================================
// Pipeline de Vídeo & Monitoramento
// ==========================================================================
async function submitVideoGeneration() {
  const subject = document.getElementById("video-subject").value.trim();
  const script = document.getElementById("video-script").value.trim();

  if (!subject) {
    showToast("Informe o título do projeto antes de iniciar.", "error");
    return;
  }
  if (!script) {
    showToast("O roteiro de locução não pode estar vazio.", "error");
    return;
  }

  if (STATE.videoSource === "pexels" && !STATE.hasPexels) {
    showToast("Sem chave Pexels configurada: o sistema utilizará o acervo da NASA e vídeos locais como alternativa automática.", "info");
  } else if (STATE.videoSource === "pixabay" && !STATE.hasPixabay) {
    showToast("Sem chave Pixabay configurada: o sistema utilizará o acervo da NASA e vídeos locais como alternativa automática.", "info");
  }

  const voiceRate = parseFloat(document.getElementById("voice-rate-slider").value) || 1.15;
  const bgmVolume = parseFloat(document.getElementById("bgm-vol-slider").value) || 0.15;
  const videoAspect = document.getElementById("video-aspect-select").value || "9:16";

  const bgmSelectVal = document.getElementById("bgm-type-select")?.value || "random";
  let bgmType = "random";
  let bgmFile = "";
  if (bgmSelectVal === "none") {
    bgmType = "none";
  } else if (bgmSelectVal === "random") {
    bgmType = "random";
  } else {
    bgmType = "custom";
    bgmFile = bgmSelectVal;
  }

  const selectedStyleObj = STATE.subtitleStyles.find((s) => s.id === STATE.selectedStyle) || STATE.subtitleStyles[0];

  const payload = {
    video_subject: subject,
    video_script: script,
    video_terms: STATE.searchTerms.length > 0 ? STATE.searchTerms : [subject],
    video_aspect: videoAspect,
    voice_name: STATE.selectedVoice,
    voice_volume: 1.0,
    voice_rate: voiceRate,
    bgm_type: bgmType,
    bgm_file: bgmFile,
    bgm_volume: bgmVolume,
    subtitle_enabled: true,
    subtitle_position: selectedStyleObj.subtitle_position,
    subtitle_display_mode: selectedStyleObj.subtitle_display_mode,
    subtitle_animation: selectedStyleObj.subtitle_animation,
    font_name: selectedStyleObj.font_name,
    text_fore_color: selectedStyleObj.text_fore_color,
    font_size: selectedStyleObj.font_size,
    stroke_color: selectedStyleObj.stroke_color,
    stroke_width: selectedStyleObj.stroke_width,
    video_source: STATE.videoSource,
    video_clip_duration: STATE.videoClipDuration || 4,
    video_count: 1,
  };

  const btnGen = document.getElementById("btn-generate-video");
  btnGen.disabled = true;
  btnGen.innerHTML = `Processando renderização...`;

  const btnCancel = document.getElementById("btn-cancel-task");
  if (btnCancel) btnCancel.style.display = "flex";

  const progressSection = document.getElementById("progress-section");
  if (progressSection) progressSection.classList.add("active");

  const playerPlaceholder = document.getElementById("player-placeholder");
  const videoElement = document.getElementById("main-video-player");
  const videoActions = document.getElementById("video-actions");

  if (playerPlaceholder) playerPlaceholder.style.display = "flex";
  if (videoElement) videoElement.style.display = "none";
  if (videoActions) videoActions.classList.remove("active");

  updateTaskStep(1, "Enviando parâmetros para a fila de renderização...");
  TerminalDrawer.log("info", `Iniciando produção: "${subject}" | Formato: ${videoAspect} | Voz: ${STATE.selectedVoice}`);
  updateStatusBarTask(`Renderizando: "${subject.substring(0, 24)}..."`);

  try {
    const res = await fetch("/api/v1/videos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.message || "Falha na criação da tarefa");
    }

    const resData = await res.json();
    const taskId = resData.data?.task_id;
    if (!taskId) throw new Error("Identificador da tarefa não retornado.");

    STATE.currentTaskId = taskId;
    showToast(`Tarefa iniciada: ${taskId.substring(0, 8)}...`, "info");
    TerminalDrawer.log("success", `Tarefa criada na fila [ID: ${taskId.substring(0, 8)}]`);
    startPollingTask(taskId);
  } catch (err) {
    console.error(err);
    TerminalDrawer.log("error", `Falha ao iniciar vídeo: ${err.message}`);
    updateStatusBarTask("Falha ao iniciar", true);
    showToast(`Erro ao iniciar vídeo: ${err.message}`, "error");
    btnGen.disabled = false;
    btnGen.innerHTML = `Iniciar Renderização do Vídeo`;
    if (btnCancel) btnCancel.style.display = "none";
    if (progressSection) progressSection.classList.remove("active");
  }
}

function startPollingTask(taskId) {
  if (STATE.pollInterval) clearInterval(STATE.pollInterval);

  let currentPercent = 10;
  STATE.pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}`);
      if (!res.ok) return;

      const data = await res.json();
      const task = data.data || {};
      const state = task.state;
      const progress = task.progress || currentPercent;

      updateProgressUI(progress, state);

      if (state === 1 || (task.videos && task.videos.length > 0)) {
        clearInterval(STATE.pollInterval);
        onTaskComplete(task);
      } else if (state === -1) {
        clearInterval(STATE.pollInterval);
        onTaskFailed(task);
      }
    } catch (err) {
      console.warn("Poll tick error:", err);
    }
  }, 2000);
}

function updateProgressUI(percent, state) {
  const bar = document.getElementById("progress-bar-fill");
  const pctText = document.getElementById("progress-percent");

  if (bar) bar.style.width = `${Math.min(percent, 100)}%`;
  if (pctText) pctText.textContent = `${Math.min(percent, 100)}%`;

  let currentStepLabel = "";
  if (percent < 30) {
    currentStepLabel = "Sintetizando locução em alta definição (Edge-TTS)...";
    updateTaskStep(2, currentStepLabel);
  } else if (percent < 55) {
    currentStepLabel = "Alinhando e gerando legendas temporizadas...";
    updateTaskStep(3, currentStepLabel);
  } else if (percent < 80) {
    currentStepLabel = "Coletando materiais e B-roll em alta resolução...";
    updateTaskStep(4, currentStepLabel);
  } else if (percent < 99) {
    currentStepLabel = "Composição de áudio, trilha e renderização FFmpeg...";
    updateTaskStep(5, currentStepLabel);
  }

  if (STATE.lastLoggedStep !== currentStepLabel && currentStepLabel) {
    STATE.lastLoggedStep = currentStepLabel;
    const taskPrefix = STATE.currentTaskId ? `[${STATE.currentTaskId.substring(0, 8)}] ` : "";
    TerminalDrawer.log("info", `${taskPrefix}${percent}% — ${currentStepLabel}`);
    updateStatusBarTask(`${percent}% — ${currentStepLabel}`);
  }
}

function updateTaskStep(stepNumber, label) {
  const labelEl = document.getElementById("task-current-action");
  if (labelEl) labelEl.textContent = label;

  for (let i = 1; i <= 5; i++) {
    const item = document.getElementById(`step-item-${i}`);
    if (!item) continue;
    if (i < stepNumber) {
      item.className = "step-item done";
    } else if (i === stepNumber) {
      item.className = "step-item active";
    } else {
      item.className = "step-item";
    }
  }
}

function onTaskComplete(task) {
  const btnGen = document.getElementById("btn-generate-video");
  if (btnGen) {
    btnGen.disabled = false;
    btnGen.innerHTML = `Iniciar Nova Renderização`;
  }

  const btnCancel = document.getElementById("btn-cancel-task");
  if (btnCancel) btnCancel.style.display = "none";

  updateProgressUI(100, 1);
  updateTaskStep(5, "Renderização concluída.");

  const badge = document.getElementById("task-status-badge");
  if (badge) badge.textContent = "Concluído";

  const videos = task.videos || [];
  if (videos.length > 0) {
    const videoUrl = videos[0];
    const playerPlaceholder = document.getElementById("player-placeholder");
    const videoElement = document.getElementById("main-video-player");
    const videoActions = document.getElementById("video-actions");
    const btnDownload = document.getElementById("btn-download-video");
    const btnCopyLink = document.getElementById("btn-copy-video-link");
    const btnDownloadThumb = document.getElementById("btn-download-thumb");

    if (playerPlaceholder) playerPlaceholder.style.display = "none";
    if (videoElement) {
      videoElement.src = videoUrl;
      videoElement.style.display = "block";
      videoElement.play().catch(() => {});
    }
    if (videoActions) videoActions.classList.add("active");
    if (btnDownload) {
      btnDownload.onclick = () => {
        const a = document.createElement("a");
        a.href = videoUrl;
        a.download = `${task.params?.video_subject || "video"}.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      };
    }
    if (btnCopyLink) {
      btnCopyLink.onclick = () => {
        const fullUrl = window.location.origin + (videoUrl.startsWith("/") ? videoUrl : `/${videoUrl}`);
        navigator.clipboard.writeText(fullUrl).then(() => {
          showToast("Link do vídeo copiado para a área de transferência!", "success");
        }).catch(() => {
          prompt("Copie o link do vídeo:", fullUrl);
        });
      };
    }

    // Thumbnail download
    if (btnDownloadThumb && task.task_id) {
      const thumbUrl = `/tasks/${task.task_id}/thumbnail-1.jpg`;
      btnDownloadThumb.onclick = () => {
        const a = document.createElement("a");
        a.href = thumbUrl;
        a.download = `${task.params?.video_subject || "thumbnail"}-capa.jpg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        showToast("Download da capa HD iniciado!", "info");
      };
    }

    // Fetch and render viral metadata
    if (task.task_id) {
      fetch(`/api/v1/saas/tasks/${task.task_id}/metadata`)
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data && data.data) {
            renderMetadata(data.data);
          }
        })
        .catch(err => console.warn("Metadata load warning:", err));
    }

    // Check cross post state
    const statusBox = document.getElementById("publish-status-box");
    if (statusBox) {
      if (task.cross_post_state === "complete") {
        statusBox.style.display = "block";
        statusBox.innerHTML = `<div style="color:var(--text-emerald); font-weight:600;">✓ Publicado automaticamente no TikTok e YouTube!</div>`;
      } else if (task.cross_post_state === "processing" || task.cross_post_state === "pending") {
        statusBox.style.display = "block";
        statusBox.innerHTML = `<div style="color:var(--status-running); font-size:0.75rem;">⏳ Publicação automática em andamento no TikTok e YouTube...</div>`;
        const pubPoll = setInterval(async () => {
          try {
            const pRes = await fetch(`/api/v1/saas/tasks/${task.task_id}/publish_status`);
            if (pRes.ok) {
              const pData = await pRes.json();
              const pState = pData.data?.cross_post_state;
              if (pState === "complete") {
                clearInterval(pubPoll);
                statusBox.innerHTML = `<div style="color:var(--text-emerald); font-weight:600;">✓ Publicado automaticamente no TikTok e YouTube!</div>`;
              } else if (pState === "failed") {
                clearInterval(pubPoll);
                statusBox.innerHTML = `<div style="color:var(--status-error); font-size:0.75rem;">✕ Auto-upload social falhou: ${pData.data?.cross_post_error || "verifique configurações"}</div>`;
              }
            }
          } catch (e) {
            clearInterval(pubPoll);
          }
        }, 3000);
      } else {
        statusBox.style.display = "none";
      }
    }

    showToast("Vídeo renderizado com sucesso.", "success");
    TerminalDrawer.log("success", `Renderização concluída com sucesso! Arquivo de vídeo final disponível.`);
    updateStatusBarTask("Produção concluída com sucesso");
  }
}

function onTaskFailed(task) {
  const btnGen = document.getElementById("btn-generate-video");
  if (btnGen) {
    btnGen.disabled = false;
    btnGen.innerHTML = `Tentar Novamente`;
  }

  const btnCancel = document.getElementById("btn-cancel-task");
  if (btnCancel) btnCancel.style.display = "none";

  const badge = document.getElementById("task-status-badge");
  if (badge) badge.textContent = "Falhou";

  const errorMsg = task.error || "Ocorreu um erro durante a renderização.";
  TerminalDrawer.log("error", `Falha na renderização da tarefa: ${errorMsg}`);
  updateStatusBarTask("Falha no pipeline de renderização", true);
  showToast(`Erro na geração: ${errorMsg}`, "error");
  updateTaskStep(1, "Falha na pipeline.");
}

// ==========================================================================
// Gallery View
// ==========================================================================
async function loadGallery() {
  const container = document.getElementById("gallery-grid");
  if (!container) return;

  container.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:0.85rem;">Carregando histórico de produções...</div>`;

  try {
    const res = await fetch("/api/v1/tasks?page=1&page_size=50");
    if (!res.ok) throw new Error("Falha ao carregar galeria");

    const data = await res.json();
    const tasks = data.data?.tasks || [];

    const completed = tasks.filter((t) => t.videos && t.videos.length > 0);
    if (completed.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:0.85rem;">
          Nenhum vídeo renderizado no histórico. Conclua uma produção para visualizá-la aqui.
        </div>
      `;
      return;
    }

    container.innerHTML = "";
    completed.forEach((t) => {
      const videoUrl = t.videos[0];
      const fullUrl = window.location.origin + (videoUrl.startsWith("/") ? videoUrl : `/${videoUrl}`);
      const title = t.params?.video_subject || "Projeto Audiovisual";
      const aspect = t.params?.video_aspect || "9:16";
      const voice = t.params?.voice_name || "pt-BR";
      const card = document.createElement("div");
      card.className = "gallery-card";
      card.id = `gallery-card-${t.task_id}`;

      card.innerHTML = `
        <video class="gallery-video-preview" src="${videoUrl}" controls preload="metadata"></video>
        <div class="gallery-card-title">${title}</div>
        <div class="gallery-meta-pills">
          <span class="gallery-pill success">Concluído</span>
          <span class="gallery-pill">${aspect}</span>
          <span class="gallery-pill">${voice.split("-").slice(-1)[0]}</span>
          <span class="gallery-pill">${t.task_id.substring(0, 8)}</span>
        </div>
        <div class="gallery-actions-row">
          <a href="${videoUrl}" download="${title.replace(/[^a-zA-Z0-9_-]/g, '_')}.mp4" class="btn-primary" style="text-decoration:none; font-size:0.75rem; padding:0.4rem; justify-content:center;">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            MP4
          </a>
          <a href="/tasks/${t.task_id}/thumbnail-1.jpg" download="${title.replace(/[^a-zA-Z0-9_-]/g, '_')}-capa.jpg" class="btn-secondary" style="text-decoration:none; font-size:0.75rem; padding:0.4rem; justify-content:center;" title="Baixar Capa HD">
            🖼️ Capa
          </a>
          <button type="button" class="btn-secondary btn-copy-link" title="Copiar link direto para área de transferência">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          </button>
        </div>
        <button type="button" class="btn-secondary btn-delete-task" style="margin-top:0.5rem; justify-content:center; font-size:0.7rem; padding:0.25rem 0.5rem; color:var(--status-error); border-color:rgba(244,63,94,0.25);" title="Excluir vídeo do servidor">
          Excluir Registro
        </button>
      `;

      card.querySelector(".btn-copy-link").addEventListener("click", () => {
        navigator.clipboard.writeText(fullUrl).then(() => {
          showToast("Link copiado para a área de transferência!", "success");
        }).catch(() => {
          prompt("Copie o link do vídeo:", fullUrl);
        });
      });

      card.querySelector(".btn-delete-task").addEventListener("click", async () => {
        if (!confirm(`Deseja excluir permanentemente o projeto "${title}"?`)) return;
        try {
          const delRes = await fetch(`/api/v1/tasks/${t.task_id}`, { method: "DELETE" });
          if (delRes.ok) {
            showToast("Projeto excluído com sucesso.", "info");
            card.remove();
          } else {
            showToast("Erro ao excluir projeto.", "error");
          }
        } catch (e) {
          showToast("Erro de comunicação ao excluir.", "error");
        }
      });

      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:3rem; color:var(--status-error); font-size:0.85rem;">Erro ao carregar o histórico de projetos.</div>`;
  }
}

// ==========================================================================
// Settings Modal Form Save
// ==========================================================================
async function saveSettings() {
  const provider = document.getElementById("setting-llm-provider").value;
  const geminiKey = document.getElementById("setting-gemini-key").value.trim();
  const openaiKey = document.getElementById("setting-openai-key").value.trim();
  const pexelsKey = document.getElementById("setting-pexels-key").value.trim();

  // Social Publishing Fields (Upload-Post)
  const upEnabled = document.getElementById("setting-upload-post-enabled")?.checked;
  const upAuto = document.getElementById("setting-upload-post-auto-upload")?.checked;
  const upKey = document.getElementById("setting-upload-post-key")?.value.trim();
  const upUser = document.getElementById("setting-upload-post-user")?.value.trim();
  const upPrivacy = document.getElementById("setting-upload-post-privacy")?.value;

  const platforms = [];
  if (document.getElementById("setting-platform-tiktok")?.checked) platforms.push("tiktok");
  if (document.getElementById("setting-platform-youtube")?.checked) platforms.push("youtube");
  if (document.getElementById("setting-platform-instagram")?.checked) platforms.push("instagram");

  const body = {
    llm_provider: provider,
  };
  if (geminiKey) body.gemini_api_key = geminiKey;
  if (openaiKey) body.openai_api_key = openaiKey;
  if (pexelsKey) body.pexels_api_keys = pexelsKey;

  body.upload_post_enabled = Boolean(upEnabled);
  body.upload_post_auto_upload = Boolean(upAuto);
  if (upKey) body.upload_post_api_key = upKey;
  if (upUser !== undefined) body.upload_post_username = upUser;
  body.upload_post_platforms = platforms;
  if (upPrivacy) body.upload_post_youtube_privacy_status = upPrivacy;

  try {
    const res = await fetch("/api/v1/saas/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (res.ok) {
      if (pexelsKey) {
        STATE.hasPexels = true;
        updatePexelsUI();
      }
      STATE.uploadPostAutoUpload = Boolean(upAuto);
      STATE.uploadPostConfigured = Boolean(upKey || upUser);
      showToast("Configurações atualizadas com sucesso.", "success");
      document.getElementById("modal-settings").classList.remove("active");
    } else {
      throw new Error("Erro ao salvar");
    }
  } catch (err) {
    showToast("Erro ao persistir configurações.", "error");
  }
}

async function handleManualSocialPublish() {
  if (!STATE.currentTaskId) {
    showToast("Nenhum vídeo concluído disponível para publicação.", "error");
    return;
  }

  const btn = document.getElementById("btn-publish-social");
  const statusBox = document.getElementById("publish-status-box");

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `Publicando...`;
  }
  if (statusBox) {
    statusBox.style.display = "block";
    statusBox.innerHTML = `<span style="color:var(--text-muted);">Enviando vídeo para TikTok e YouTube Shorts...</span>`;
  }

  try {
    const res = await fetch("/api/v1/saas/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: STATE.currentTaskId }),
    });

    const json = await res.json();
    if (res.ok && json.data && json.data.success) {
      showToast("Vídeo publicado com sucesso no TikTok e YouTube!", "success");
      if (statusBox) {
        statusBox.innerHTML = `
          <div style="color:var(--text-emerald); font-weight:600;">✓ Publicado com sucesso no TikTok e YouTube!</div>
          <div style="font-size:0.7rem; color:var(--text-muted); margin-top:0.25rem;">ID de Envio: ${json.data.request_id || "Concluído"}</div>
        `;
      }
    } else {
      const err = json.message || json.data?.error || "Erro desconhecido na publicação";
      showToast(`Falha no envio: ${err}`, "error");
      if (statusBox) {
        statusBox.innerHTML = `
          <div style="color:var(--status-error); font-weight:600;">✕ Falha no envio social</div>
          <div style="font-size:0.7rem; color:var(--text-muted); margin-top:0.25rem;">${err}</div>
        `;
      }
    }
  } catch (err) {
    showToast(`Erro na requisição: ${err.message}`, "error");
    if (statusBox) {
      statusBox.innerHTML = `<div style="color:var(--status-error); font-size:0.7rem;">Erro de conexão com o servidor.</div>`;
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg> Publicar no TikTok & YouTube Shorts`;
    }
  }
}

async function publishBatchItem(taskId, btnEl) {
  if (!taskId) return;
  const originalHtml = btnEl ? btnEl.innerHTML : "";
  if (btnEl) {
    btnEl.disabled = true;
    btnEl.innerHTML = "Enviando...";
  }

  try {
    const res = await fetch("/api/v1/saas/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId }),
    });
    const json = await res.json();
    if (res.ok && json.data && json.data.success) {
      showToast("Publicado com sucesso!", "success");
      if (btnEl) {
        btnEl.outerHTML = `<span style="font-size:0.68rem; color:var(--text-emerald); font-weight:500;">✓ Postado</span>`;
      }
    } else {
      const err = json.message || json.data?.error || "Falha";
      showToast(`Erro ao publicar: ${err}`, "error");
      if (btnEl) {
        btnEl.disabled = false;
        btnEl.innerHTML = originalHtml;
      }
    }
  } catch (err) {
    showToast(`Erro: ${err.message}`, "error");
    if (btnEl) {
      btnEl.disabled = false;
      btnEl.innerHTML = originalHtml;
    }
  }
}

// ==========================================================================
// Toast Notifications
// ==========================================================================
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(6px)";
    toast.style.transition = "all 0.2s ease";
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

// ==========================================================================
// Autopilot Automation UI
// ==========================================================================
let isAutopilotEngineActive = true;

function setupAutopilotUI() {
  const btnToggleMaster = document.getElementById("btn-toggle-autopilot-master");
  if (btnToggleMaster) {
    btnToggleMaster.addEventListener("click", toggleAutopilotMaster);
  }

  const btnRefresh = document.getElementById("btn-refresh-autopilot");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", loadAutopilotData);
  }

  const formCreate = document.getElementById("form-create-autopilot-profile");
  if (formCreate) {
    formCreate.addEventListener("submit", handleCreateAutopilotProfile);
  }
}

async function loadAutopilotData() {
  try {
    const statusRes = await fetch("/api/v1/saas/autopilot/status");
    if (statusRes.ok) {
      const sData = (await statusRes.json()).data || {};
      isAutopilotEngineActive = Boolean(sData.running && sData.global_enabled !== false);
      updateAutopilotBanner(sData);
    }

    const profRes = await fetch("/api/v1/saas/autopilot/profiles");
    if (profRes.ok) {
      const profiles = (await profRes.json()).data || [];
      renderAutopilotProfiles(profiles);
      const statProf = document.getElementById("autopilot-stat-profiles");
      if (statProf) statProf.textContent = profiles.length;
    }

    const histRes = await fetch("/api/v1/saas/autopilot/history");
    if (histRes.ok) {
      const history = (await histRes.json()).data || [];
      renderAutopilotHistory(history);
      const statHist = document.getElementById("autopilot-stat-history-count");
      if (statHist) statHist.textContent = history.length;
    }
  } catch (err) {
    console.warn("Autopilot load error:", err);
  }
}

function updateAutopilotBanner(status) {
  const dot = document.getElementById("autopilot-dot-indicator");
  const title = document.getElementById("autopilot-banner-status");
  const btn = document.getElementById("btn-toggle-autopilot-master");
  const nextRun = document.getElementById("autopilot-stat-next-run");

  const isRunning = Boolean(status.running);
  if (dot) dot.className = `dot-status ${isRunning ? "ok" : "err"}`;
  if (title) title.textContent = isRunning ? "Motor Autônomo Ativo" : "Motor Autônomo Pausado";
  if (btn) {
    btn.textContent = isRunning ? "Pausar Piloto Automático" : "Retomar Piloto Automático";
    btn.className = isRunning ? "btn-secondary" : "btn-primary";
  }

  if (nextRun) {
    if (status.next_run_iso) {
      const date = new Date(status.next_run_iso);
      nextRun.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      nextRun.textContent = isRunning ? "Calculando..." : "Pausado";
    }
  }
}

async function toggleAutopilotMaster() {
  const newState = !isAutopilotEngineActive;
  try {
    const res = await fetch("/api/v1/saas/autopilot/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: newState }),
    });
    if (res.ok) {
      showToast(newState ? "Piloto automático ativado!" : "Piloto automático pausado.", "info");
      loadAutopilotData();
    }
  } catch (err) {
    showToast(`Erro ao alterar motor: ${err.message}`, "error");
  }
}

function renderAutopilotProfiles(profiles) {
  const container = document.getElementById("autopilot-profiles-container");
  if (!container) return;

  if (!profiles || profiles.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; padding: 2rem; text-align:center; color:var(--text-muted); border:1px dashed var(--border-muted); border-radius:var(--radius-md);">
        Nenhum canal autônomo cadastrado. Preencha o formulário ao lado para começar.
      </div>
    `;
    return;
  }

  container.innerHTML = profiles.map(p => `
    <div class="profile-card">
      <div>
        <div class="profile-card-header">
          <div class="profile-title">${p.name || "Canal Sem Nome"}</div>
          <span class="status-badge" style="font-size:0.68rem; ${p.enabled ? "background:rgba(16,185,129,0.15); color:var(--text-emerald); border:1px solid rgba(16,185,129,0.3);" : "background:rgba(255,255,255,0.05); color:var(--text-muted);"}">
            ${p.enabled ? "✓ Ativo" : "Pausado"}
          </span>
        </div>
        
        <div class="profile-meta-row">
          <span>Categoria: ${p.category || "Geral"}</span>
          <span>Intervalo: ${p.interval_hours || 12}h</span>
          <span>Voz: ${p.voice ? (p.voice.split("-")[2] || p.voice) : "Antônio"}</span>
        </div>

        <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.75rem;">
          Destinos: <strong>${(p.platforms || ["tiktok", "youtube"]).join(", ")}</strong>
        </div>
      </div>

      <div class="profile-actions-row">
        <button type="button" class="btn-primary" style="flex:1; font-size:0.75rem; padding:0.35rem 0.6rem;" onclick="triggerAutopilotProfile('${p.id}', this)" title="Compilar e postar vídeo agora">
          Disparar Agora
        </button>
        <button type="button" class="btn-secondary" style="font-size:0.75rem; padding:0.35rem 0.6rem; color:var(--status-error); border-color:rgba(244,63,94,0.3);" onclick="deleteAutopilotProfile('${p.id}')" title="Excluir canal">
          Excluir
        </button>
      </div>
    </div>
  `).join("");
}

async function handleCreateAutopilotProfile(e) {
  e.preventDefault();
  const name = document.getElementById("ap-input-name")?.value.trim();
  const category = document.getElementById("ap-select-category")?.value;
  const intervalHours = parseFloat(document.getElementById("ap-select-interval")?.value) || 12;
  const source = document.getElementById("ap-select-source")?.value || "hybrid";
  const voice = document.getElementById("ap-select-voice")?.value || "pt-BR-AntonioNeural";
  const style = document.getElementById("ap-select-style")?.value || "hormozi_bold";
  const autoPublish = Boolean(document.getElementById("ap-check-autopublish")?.checked);

  if (!name) {
    showToast("Informe o nome do canal.", "error");
    return;
  }

  const payload = {
    name,
    category,
    interval_hours: intervalHours,
    source,
    voice,
    style,
    duration: 60,
    auto_publish: autoPublish,
    platforms: ["tiktok", "youtube"],
    enabled: true,
  };

  try {
    const res = await fetch("/api/v1/saas/autopilot/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      showToast(`Canal "${name}" criado com sucesso!`, "success");
      document.getElementById("form-create-autopilot-profile")?.reset();
      loadAutopilotData();
    } else {
      throw new Error("Erro ao salvar canal");
    }
  } catch (err) {
    showToast(`Erro ao criar canal: ${err.message}`, "error");
  }
}

async function triggerAutopilotProfile(profileId, btnEl) {
  if (!profileId) return;
  const origText = btnEl ? btnEl.innerHTML : "";
  if (btnEl) {
    btnEl.disabled = true;
    btnEl.innerHTML = "Iniciando...";
  }

  TerminalDrawer.log("info", `Piloto Automático: disparando canal manual [ID: ${profileId}]`);
  try {
    const res = await fetch(`/api/v1/saas/autopilot/trigger/${profileId}`, {
      method: "POST",
    });
    if (res.ok) {
      TerminalDrawer.log("success", `Piloto Automático: canal disparado com sucesso em segundo plano.`);
      showToast("Execução disparada em segundo plano! Acompanhe no log.", "success");
      setTimeout(loadAutopilotData, 2000);
    } else {
      TerminalDrawer.log("error", `Piloto Automático: falha ao disparar canal [ID: ${profileId}].`);
      showToast("Falha ao disparar canal.", "error");
    }
  } catch (err) {
    TerminalDrawer.log("error", `Piloto Automático: erro de conexão: ${err.message}`);
    showToast(`Erro: ${err.message}`, "error");
  } finally {
    if (btnEl) {
      btnEl.disabled = false;
      btnEl.innerHTML = origText;
    }
  }
}

async function deleteAutopilotProfile(profileId) {
  if (!confirm("Tem certeza que deseja remover este canal do piloto automático?")) return;

  try {
    const res = await fetch(`/api/v1/saas/autopilot/profiles/${profileId}`, {
      method: "DELETE",
    });
    if (res.ok) {
      showToast("Canal removido do piloto automático.", "info");
      loadAutopilotData();
    }
  } catch (err) {
    showToast(`Erro ao excluir: ${err.message}`, "error");
  }
}

function renderAutopilotHistory(history) {
  const tbody = document.getElementById("autopilot-history-body");
  if (!tbody) return;

  if (!history || history.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align:center; color:var(--text-muted); padding:2rem;">
          Nenhuma execução automática registrada ainda.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = history.slice(0, 20).map(item => {
    const isSuccess = item.status === "completed" || item.status === "success";
    const timeStr = item.timestamp ? new Date(item.timestamp * 1000).toLocaleString() : "--";
    return `
      <tr>
        <td><strong>${item.profile_name || "Canal"}</strong></td>
        <td>${item.topic || item.task_id || "Execução autônoma"}</td>
        <td style="font-size:0.75rem; color:var(--text-muted);">${timeStr}</td>
        <td>
          <span class="status-badge" style="font-size:0.68rem; ${isSuccess ? "background:rgba(16,185,129,0.15); color:var(--text-emerald); border:1px solid rgba(16,185,129,0.3);" : "background:rgba(244,63,94,0.15); color:var(--status-error); border:1px solid rgba(244,63,94,0.3);"}">
            ${isSuccess ? "✓ Concluído" : "✕ Falha"}
          </span>
        </td>
        <td style="text-align:right; font-size:0.72rem; color:var(--text-emerald);">
          ${item.published ? "TikTok / YouTube" : "--"}
        </td>
      </tr>
    `;
  }).join("");
}

// ==========================================================================
// Pro Studio Keyboard Shortcuts
// ==========================================================================
function setupKeyboardShortcuts() {
  const btnShortcuts = document.getElementById("btn-open-shortcuts");
  if (btnShortcuts) {
    btnShortcuts.addEventListener("click", () => {
      const modal = document.getElementById("modal-shortcuts");
      if (modal) modal.classList.toggle("active");
    });
  }

  document.addEventListener("keydown", (e) => {
    const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
    const isInputFocused = activeTag === "input" || activeTag === "textarea" || activeTag === "select" || (document.activeElement && document.activeElement.isContentEditable);
    const player = document.getElementById("main-video-player");

    // 1. Esc: Close any active modal
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay.active").forEach(m => m.classList.remove("active"));
      return;
    }

    // 2. ?: Open shortcuts modal if not typing
    if (e.key === "?" && !isInputFocused) {
      e.preventDefault();
      const modal = document.getElementById("modal-shortcuts");
      if (modal) modal.classList.toggle("active");
      return;
    }

    // 3. Ctrl + Enter: Trigger video render
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      const btnGen = document.getElementById("btn-generate-video");
      if (btnGen && !btnGen.disabled) {
        showToast("Atalho [Ctrl+Enter]: Iniciando renderização...", "info");
        btnGen.click();
      }
      return;
    }

    // 4. Ctrl + 1..6: Quick view switching
    if ((e.ctrlKey || e.metaKey) && ["1", "2", "3", "4", "5", "6"].includes(e.key)) {
      e.preventDefault();
      const tabMap = {
        "1": "nav-tab-studio",
        "2": "nav-tab-batch",
        "3": "nav-tab-autopilot",
        "4": "nav-tab-ideas",
        "5": "nav-tab-tags",
        "6": "nav-tab-gallery",
      };
      const tabId = tabMap[e.key];
      const targetTab = document.getElementById(tabId);
      if (targetTab) targetTab.click();
      return;
    }

    // 5. Ctrl + ` (tilde / backquote): Toggle Live Diagnostic Terminal Drawer
    if ((e.ctrlKey || e.metaKey) && (e.code === "Backquote" || e.key === "`" || e.key === "~")) {
      e.preventDefault();
      TerminalDrawer.toggle();
      return;
    }

    // 6. Video Player Pro Transport Controls (Suppressed when typing in text fields)
    if (isInputFocused || !player || !player.src || player.style.display === "none") return;

    switch (e.key.toLowerCase()) {
      case " ":
        e.preventDefault();
        if (player.paused) {
          player.play();
        } else {
          player.pause();
        }
        break;
      case "k":
        e.preventDefault();
        player.pause();
        showToast("⏸ Pausado", "info");
        break;
      case "j":
        e.preventDefault();
        player.currentTime = Math.max(0, player.currentTime - 3);
        showToast("⏪ -3s", "info");
        break;
      case "l":
        e.preventDefault();
        player.currentTime = Math.min(player.duration || 9999, player.currentTime + 3);
        showToast("⏩ +3s", "info");
        break;
      case "arrowleft":
        e.preventDefault();
        player.currentTime = Math.max(0, player.currentTime - (e.shiftKey ? 1.0 : 0.033));
        break;
      case "arrowright":
        e.preventDefault();
        player.currentTime = Math.min(player.duration || 9999, player.currentTime + (e.shiftKey ? 1.0 : 0.033));
        break;
      case "m":
        e.preventDefault();
        player.muted = !player.muted;
        showToast(player.muted ? "Áudio desativado" : "Áudio ativado", "info");
        break;
      case "f":
        e.preventDefault();
        if (document.fullscreenElement) {
          document.exitFullscreen().catch(() => {});
        } else {
          const wrapper = player.closest(".player-wrapper") || player;
          if (wrapper.requestFullscreen) wrapper.requestFullscreen().catch(() => {});
        }
        break;
    }
  });
}
