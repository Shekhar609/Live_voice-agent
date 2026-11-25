/**
 * Main Application Logic for Multilingual Speech-to-Text & Dashboard
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements - Studio
  const recordBtn = document.getElementById("recordBtn");
  const recordIcon = document.getElementById("recordIcon");
  const recordLabel = document.getElementById("recordLabel");
  const recordingTimer = document.getElementById("recordingTimer");
  const liveTranscriptText = document.getElementById("liveTranscriptText");
  const languageModeSelect = document.getElementById("languageModeSelect");
  const visualizerCanvas = document.getElementById("audioVisualizer");
  const liveLangBadge = document.getElementById("liveLangBadge");
  const liveBreakdownBadge = document.getElementById("liveBreakdownBadge");
  const liveWordCount = document.getElementById("liveWordCount");
  const wsStatusIndicator = document.getElementById("wsStatusIndicator");
  const wsStatusText = document.getElementById("wsStatusText");

  // Studio Action Buttons
  const saveBtn = document.getElementById("saveBtn");
  const ttsBtn = document.getElementById("ttsBtn");
  const copyBtn = document.getElementById("copyBtn");
  const clearBtn = document.getElementById("clearBtn");
  const customTitleInput = document.getElementById("customTitleInput");
  const categorySelect = document.getElementById("categorySelect");

  // Dashboard Elements
  const searchInput = document.getElementById("searchInput");
  const filterLang = document.getElementById("filterLang");
  const historyList = document.getElementById("historyList");
  const totalCountEl = document.getElementById("totalCount");
  const totalWordsEl = document.getElementById("totalWords");
  const totalDurationEl = document.getElementById("totalDuration");
  const hinglishCountEl = document.getElementById("hinglishCount");
  const exportBtn = document.getElementById("exportBtn");
  const clearAllBtn = document.getElementById("clearAllBtn");

  // Edit Modal Elements
  const editModal = document.getElementById("editModal");
  const editTitleInput = document.getElementById("editTitleInput");
  const editTextarea = document.getElementById("editTextarea");
  const editCategorySelect = document.getElementById("editCategorySelect");
  const saveEditBtn = document.getElementById("saveEditBtn");
  const cancelEditBtn = document.getElementById("cancelEditBtn");
  const closeEditModalBtn = document.getElementById("closeEditModalBtn");

  let currentEditingId = null;
  let timerInterval = null;
  let recordSeconds = 0;
  let currentRecordingResult = {
    text: "",
    detected_language: "Multilingual (Hindi/English)",
    language_breakdown: ""
  };

  // Toast Notification
  function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    const toastText = document.getElementById("toastText");
    const toastIcon = document.getElementById("toastIcon");

    toastText.textContent = message;
    toast.className = `fixed bottom-5 right-5 z-50 flex items-center space-x-2 px-4 py-3 rounded-lg shadow-xl text-white text-sm transform transition-all duration-300 ${
      type === "error" ? "bg-red-600" : type === "success" ? "bg-emerald-600" : "bg-indigo-600"
    }`;
    toast.classList.remove("opacity-0", "translate-y-4", "pointer-events-none");

    setTimeout(() => {
      toast.classList.add("opacity-0", "translate-y-4", "pointer-events-none");
    }, 3500);
  }

  // Initialize Transcription Engine
  const engine = new AudioTranscriptionEngine({
    canvas: visualizerCanvas,
    onStatusChange: (status) => {
      if (status.ws) {
        if (status.ws === "connected") {
          wsStatusIndicator.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse";
          wsStatusText.textContent = "Server Online";
        } else {
          wsStatusIndicator.className = "w-2.5 h-2.5 rounded-full bg-amber-500";
          wsStatusText.textContent = "Reconnecting...";
        }
      }

      if (status.recording !== undefined) {
        if (status.recording) {
          recordBtn.classList.add("record-btn-pulse", "bg-red-600");
          recordBtn.classList.remove("bg-indigo-600");
          recordLabel.textContent = "Stop Recording";
          recordingTimer.classList.remove("hidden");
          startTimer();
        } else {
          recordBtn.classList.remove("record-btn-pulse", "bg-red-600");
          recordBtn.classList.add("bg-indigo-600");
          recordLabel.textContent = "Start Speech";
          stopTimer();
        }
      }
    },
    onTranscriptUpdate: (data) => {
      if (!data.text) return;
      liveTranscriptText.textContent = data.text;
      currentRecordingResult.text = data.text;
      currentRecordingResult.detected_language = data.detected_language || "Multilingual (Hindi/English)";
      currentRecordingResult.language_breakdown = data.language_breakdown || "";

      liveLangBadge.textContent = data.detected_language || "Multilingual";
      liveBreakdownBadge.textContent = data.language_breakdown || "Analyzing";
      liveWordCount.textContent = `${data.word_count || data.text.split(/\s+/).length} words`;

      // Color code live badge
      updateBadgeColor(liveLangBadge, data.detected_language);
    },
    onError: (err) => {
      showToast(err, "error");
    }
  });

  function updateBadgeColor(badgeEl, lang) {
    badgeEl.className = "px-2.5 py-1 text-xs font-semibold rounded-full ";
    if (!lang) {
      badgeEl.classList.add("badge-hinglish");
      return;
    }
    const lower = lang.toLowerCase();
    if (lower.includes("hinglish") || lower.includes("multi")) {
      badgeEl.classList.add("badge-hinglish");
    } else if (lower.includes("hindi")) {
      badgeEl.classList.add("badge-hindi");
    } else {
      badgeEl.classList.add("badge-english");
    }
  }

  // Timer helpers
  function startTimer() {
    recordSeconds = 0;
    recordingTimer.textContent = "00:00";
    timerInterval = setInterval(() => {
      recordSeconds++;
      const mins = String(Math.floor(recordSeconds / 60)).padStart(2, "0");
      const secs = String(recordSeconds % 60).padStart(2, "0");
      recordingTimer.textContent = `${mins}:${secs}`;
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  // Record Button Toggle
  recordBtn.addEventListener("click", () => {
    if (engine.isRecording) {
      engine.stop();
    } else {
      engine.setLanguageMode(languageModeSelect.value);
      engine.start();
    }
  });

  languageModeSelect.addEventListener("change", () => {
    engine.setLanguageMode(languageModeSelect.value);
  });

  // Action: Save to DB
  saveBtn.addEventListener("click", async () => {
    const text = liveTranscriptText.textContent.trim();
    if (!text || text === "Start speaking or click the microphone to transcribe in real-time...") {
      showToast("No transcription text to save. Please speak first!", "error");
      return;
    }

    const title = customTitleInput.value.trim() || `Transcription (${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`;
    const category = categorySelect.value || "General";

    try {
      saveBtn.disabled = true;
      saveBtn.innerHTML = `<span class="animate-spin inline-block mr-1">⌛</span> Saving...`;

      const response = await fetch("/api/transcriptions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title,
          text: text,
          detected_language: currentRecordingResult.detected_language,
          language_breakdown: currentRecordingResult.language_breakdown,
          duration_seconds: recordSeconds > 0 ? recordSeconds : 0.0,
          category: category
        })
      });

      if (!response.ok) {
        throw new Error("Failed to save transcription");
      }

      const created = await response.json();
      showToast("Transcription saved to database successfully!", "success");
      customTitleInput.value = "";
      loadDashboardData();
    } catch (err) {
      showToast("Error saving to database: " + err.message, "error");
    } finally {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `<span>💾</span> <span>Save to Database</span>`;
    }
  });

  // Action: Listen (TTS)
  ttsBtn.addEventListener("click", () => {
    const text = liveTranscriptText.textContent.trim();
    if (!text || text === "Start speaking or click the microphone to transcribe in real-time...") {
      showToast("No text to speak", "error");
      return;
    }
    playTTS(text, currentRecordingResult.detected_language);
  });

  // Function to play text through TTS API
  async function playTTS(text, lang) {
    try {
      showToast("Synthesizing speech...", "info");
      const langCode = (lang && lang.toLowerCase().includes("hindi")) ? "hi" : "en";
      
      const response = await fetch("/api/tts/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: langCode })
      });

      if (!response.ok) {
        // Fallback to Web Speech API
        speakWithBrowser(text, langCode);
        return;
      }

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (e) {
      speakWithBrowser(text, "hi");
    }
  }

  function speakWithBrowser(text, langCode) {
    if (!window.speechSynthesis) {
      showToast("Text-to-speech not supported in this browser", "error");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  }

  // Action: Copy Text
  copyBtn.addEventListener("click", () => {
    const text = liveTranscriptText.textContent.trim();
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      showToast("Transcribed text copied to clipboard!", "success");
    });
  });

  // Action: Clear
  clearBtn.addEventListener("click", () => {
    liveTranscriptText.textContent = "Start speaking or click the microphone to transcribe in real-time...";
    engine.resetTranscript();
    currentRecordingResult.text = "";
    liveLangBadge.textContent = "Multilingual";
    liveBreakdownBadge.textContent = "Hindi / English";
    liveWordCount.textContent = "0 words";
    recordSeconds = 0;
    recordingTimer.textContent = "00:00";
    showToast("Cleared studio", "info");
  });

  // ==========================================
  // DASHBOARD & CRUD LOGIC
  // ==========================================

  async function loadDashboardData() {
    loadStats();
    loadTranscriptions();
  }

  async function loadStats() {
    try {
      const res = await fetch("/api/transcriptions/stats");
      if (!res.ok) return;
      const stats = await res.json();
      totalCountEl.textContent = stats.total_count;
      totalWordsEl.textContent = stats.total_words;
      totalDurationEl.textContent = `${stats.total_duration_seconds}s`;
      
      const hinglishCount = (stats.languages_breakdown["Hinglish (Hindi + English)"] || 0) + 
                            (stats.languages_breakdown["Multilingual (Hindi/English)"] || 0);
      hinglishCountEl.textContent = hinglishCount;
    } catch (e) {
      console.error("Error loading stats:", e);
    }
  }

  async function loadTranscriptions() {
    const search = searchInput.value.trim();
    const lang = filterLang.value;

    let url = `/api/transcriptions?limit=100`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (lang && lang !== "all") url += `&language=${encodeURIComponent(lang)}`;

    try {
      historyList.innerHTML = `<div class="p-8 text-center text-slate-400"><span class="animate-spin inline-block mr-2">⌛</span>Loading transcription records...</div>`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch records");
      const items = await res.json();
      renderHistoryList(items);
    } catch (e) {
      historyList.innerHTML = `<div class="p-8 text-center text-red-400">Error loading history: ${e.message}</div>`;
    }
  }

  function renderHistoryList(items) {
    if (!items || items.length === 0) {
      historyList.innerHTML = `
        <div class="p-12 text-center text-slate-500">
          <svg class="mx-auto h-12 w-12 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" />
          </svg>
          <p class="text-base font-medium">No transcription records found</p>
          <p class="text-sm text-slate-600 mt-1">Speak into the microphone above and click "Save to Database"</p>
        </div>
      `;
      return;
    }

    historyList.innerHTML = items.map(item => {
      const dateStr = item.created_at ? new Date(item.created_at).toLocaleString() : "";
      const langBadgeClass = getBadgeClass(item.detected_language);
      
      return `
        <div class="glass-panel p-5 rounded-xl border border-slate-700/60 hover:border-indigo-500/50 transition-all group flex flex-col justify-between">
          <div>
            <div class="flex items-start justify-between gap-3 mb-2">
              <h4 class="font-semibold text-white text-base truncate flex-1" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h4>
              <span class="px-2.5 py-0.5 text-xs font-medium rounded-full ${langBadgeClass}">
                ${escapeHtml(item.detected_language)}
              </span>
            </div>

            <p class="text-sm text-slate-300 leading-relaxed line-clamp-3 mb-4 whitespace-pre-wrap">${escapeHtml(item.text)}</p>
          </div>

          <div>
            <div class="flex items-center justify-between text-xs text-slate-400 border-t border-slate-700/60 pt-3 mb-3">
              <span class="flex items-center gap-1">
                <span>⏱️</span> ${item.duration_seconds || 0}s duration
              </span>
              <span class="flex items-center gap-1">
                <span>🏷️</span> ${escapeHtml(item.category || "General")}
              </span>
              <span class="text-slate-500">${dateStr}</span>
            </div>

            <div class="flex items-center justify-end gap-2">
              <button onclick="window.appPlayTTS('${encodeURIComponent(item.text)}', '${encodeURIComponent(item.detected_language)}')" 
                class="px-2.5 py-1 text-xs bg-slate-700 hover:bg-indigo-600 text-slate-200 hover:text-white rounded transition flex items-center gap-1" title="Read Aloud">
                🔊 Listen
              </button>
              <button onclick="window.appCopyText('${encodeURIComponent(item.text)}')" 
                class="px-2.5 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded transition flex items-center gap-1" title="Copy Text">
                📋 Copy
              </button>
              <button onclick="window.appOpenEditModal(${item.id}, '${encodeURIComponent(item.title)}', '${encodeURIComponent(item.text)}', '${encodeURIComponent(item.category || "General")}')" 
                class="px-2.5 py-1 text-xs bg-slate-700 hover:bg-amber-600 text-slate-200 hover:text-white rounded transition flex items-center gap-1" title="Edit Record">
                ✏️ Edit
              </button>
              <button onclick="window.appDeleteTranscription(${item.id})" 
                class="px-2.5 py-1 text-xs bg-slate-700 hover:bg-red-600 text-slate-200 hover:text-white rounded transition flex items-center gap-1" title="Delete">
                🗑️ Delete
              </button>
            </div>
          </div>
        </div>
      `;
    }).join("");
  }

  function getBadgeClass(lang) {
    if (!lang) return "badge-hinglish";
    const lower = lang.toLowerCase();
    if (lower.includes("hinglish") || lower.includes("multi")) return "badge-hinglish";
    if (lower.includes("hindi")) return "badge-hindi";
    return "badge-english";
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // Global UI hooks for generated buttons
  window.appPlayTTS = (encodedText, encodedLang) => {
    playTTS(decodeURIComponent(encodedText), decodeURIComponent(encodedLang));
  };

  window.appCopyText = (encodedText) => {
    navigator.clipboard.writeText(decodeURIComponent(encodedText)).then(() => {
      showToast("Copied to clipboard!", "success");
    });
  };

  window.appOpenEditModal = (id, encodedTitle, encodedText, encodedCategory) => {
    currentEditingId = id;
    editTitleInput.value = decodeURIComponent(encodedTitle);
    editTextarea.value = decodeURIComponent(encodedText);
    editCategorySelect.value = decodeURIComponent(encodedCategory);
    editModal.classList.remove("hidden");
  };

  window.appDeleteTranscription = async (id) => {
    if (!confirm("Are you sure you want to delete this transcription record?")) return;
    try {
      const res = await fetch(`/api/transcriptions/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      showToast("Record deleted", "info");
      loadDashboardData();
    } catch (e) {
      showToast(e.message, "error");
    }
  };

  // Edit Modal Event Handlers
  saveEditBtn.addEventListener("click", async () => {
    if (!currentEditingId) return;
    const newTitle = editTitleInput.value.trim();
    const newText = editTextarea.value.trim();
    const newCategory = editCategorySelect.value;

    if (!newText) {
      showToast("Transcription text cannot be empty", "error");
      return;
    }

    try {
      saveEditBtn.disabled = true;
      saveEditBtn.textContent = "Updating...";

      const res = await fetch(`/api/transcriptions/${currentEditingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTitle,
          text: newText,
          category: newCategory
        })
      });

      if (!res.ok) throw new Error("Failed to update record");
      showToast("Record updated successfully!", "success");
      editModal.classList.add("hidden");
      loadDashboardData();
    } catch (e) {
      showToast(e.message, "error");
    } finally {
      saveEditBtn.disabled = false;
      saveEditBtn.textContent = "Save Changes";
    }
  });

  cancelEditBtn.addEventListener("click", () => editModal.classList.add("hidden"));
  closeEditModalBtn.addEventListener("click", () => editModal.classList.add("hidden"));

  // Search & Filter event listeners
  let debounceTimeout = null;
  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => loadTranscriptions(), 300);
  });
  filterLang.addEventListener("change", () => loadTranscriptions());

  // Export
  exportBtn.addEventListener("click", () => {
    const format = prompt("Choose export format (csv, json, txt):", "csv");
    if (!format || !["csv", "json", "txt"].includes(format.toLowerCase().trim())) {
      if (format) showToast("Invalid format. Please enter csv, json, or txt", "error");
      return;
    }
    window.location.href = `/api/transcriptions/export/${format.toLowerCase().trim()}`;
  });

  // Clear All
  clearAllBtn.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to delete ALL transcription history? This action cannot be undone.")) return;
    try {
      const res = await fetch("/api/transcriptions", { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to clear database");
      showToast("All records cleared", "info");
      loadDashboardData();
    } catch (e) {
      showToast(e.message, "error");
    }
  });

  // Initial Data Load
  loadDashboardData();
});
