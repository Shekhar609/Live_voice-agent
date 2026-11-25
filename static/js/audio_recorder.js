/**
 * Real-Time Audio Recorder, Visualizer, and STT Streamer
 * Handles:
 * - Microphone input via Web Audio API
 * - Real-time visualizer canvas rendering
 * - Multilingual Speech Recognition (Hindi / English / Code-switching)
 * - WebSocket communication with FastAPI backend
 */

class AudioTranscriptionEngine {
  constructor(options = {}) {
    this.canvas = options.canvas || null;
    this.onTranscriptUpdate = options.onTranscriptUpdate || (() => {});
    this.onStatusChange = options.onStatusChange || (() => {});
    this.onError = options.onError || console.error;

    this.isRecording = false;
    this.audioContext = null;
    this.analyser = null;
    this.microphone = null;
    this.animFrameId = null;
    
    this.ws = null;
    this.wsConnected = false;
    this.recognition = null;
    this.languageMode = "auto"; // "auto" (multilingual hi/en), "hi-IN", "en-IN"
    
    this.startTime = null;
    this.fullTranscript = "";
    this.interimTranscript = "";

    this.initWebSocket();
  }

  initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/transcribe`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.wsConnected = true;
        this.onStatusChange({ ws: "connected" });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onTranscriptUpdate(data);
        } catch (e) {
          console.error("Error parsing WS message:", e);
        }
      };

      this.ws.onclose = () => {
        this.wsConnected = false;
        this.onStatusChange({ ws: "disconnected" });
        // Attempt reconnection after 3 seconds
        setTimeout(() => this.initWebSocket(), 3000);
      };

      this.ws.onerror = (err) => {
        console.warn("WebSocket error:", err);
      };
    } catch (e) {
      console.error("Failed to initialize WebSocket:", e);
    }
  }

  setLanguageMode(mode) {
    this.languageMode = mode;
    if (this.recognition && this.isRecording) {
      // Restart recognition with new language
      this.recognition.stop();
    }
  }

  async start() {
    if (this.isRecording) return;

    try {
      // 1. Initialize AudioContext and Microphone stream for visualizer
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioStream = stream;
      
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 128;
      
      this.microphone = this.audioContext.createMediaStreamSource(stream);
      this.microphone.connect(this.analyser);

      this.drawVisualizer();

      // 2. Setup Multilingual Speech Recognition
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        this.onError("SpeechRecognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
        return;
      }

      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;

      // Select language for Indian subcontinent multilingual code-switching
      if (this.languageMode === "hi-IN") {
        this.recognition.lang = "hi-IN";
      } else if (this.languageMode === "en-IN") {
        this.recognition.lang = "en-IN";
      } else {
        // Auto / Multilingual mode: hi-IN recognizes both Hindi and English loanwords/phrases
        this.recognition.lang = "hi-IN";
      }

      this.recognition.onstart = () => {
        this.isRecording = true;
        this.startTime = Date.now();
        this.onStatusChange({ recording: true });
      };

      this.recognition.onresult = (event) => {
        let interimText = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            this.fullTranscript += (this.fullTranscript ? " " : "") + event.results[i][0].transcript.trim();
          } else {
            interimText += event.results[i][0].transcript;
          }
        }

        const combinedText = (this.fullTranscript + (interimText ? " " + interimText : "")).trim();

        // Send to backend WebSocket for live multilingual language detection and structuring
        if (this.ws && this.ws.readyState === WebSocket.OPEN && combinedText) {
          this.ws.send(JSON.stringify({
            type: interimText ? "chunk" : "finalize",
            text: combinedText
          }));
        } else {
          // Local fallback update if WS disconnected
          this.onTranscriptUpdate({
            text: combinedText,
            detected_language: "Detecting...",
            language_breakdown: "Analyzing...",
            word_count: combinedText.split(/\s+/).length
          });
        }
      };

      this.recognition.onerror = (event) => {
        if (event.error !== "no-speech") {
          console.warn("Speech recognition error:", event.error);
        }
      };

      this.recognition.onend = () => {
        // Auto-restart if user hasn't explicitly stopped
        if (this.isRecording) {
          try {
            this.recognition.start();
          } catch (e) {
            // Already started or restarting
          }
        }
      };

      this.recognition.start();

    } catch (err) {
      this.onError("Error accessing microphone: " + (err.message || err));
      this.stop();
    }
  }

  stop() {
    this.isRecording = false;
    this.onStatusChange({ recording: false });

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }

    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
    }

    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext.close();
    }

    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
    }

    // Clear visualizer canvas
    if (this.canvas) {
      const ctx = this.canvas.getContext("2d");
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  drawVisualizer() {
    if (!this.canvas || !this.analyser) return;

    const ctx = this.canvas.getContext("2d");
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      this.animFrameId = requestAnimationFrame(render);
      this.analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      const barWidth = (this.canvas.width / bufferLength) * 2.2;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * this.canvas.height * 0.9;
        
        // Gradient color for visualizer bars
        const gradient = ctx.createLinearGradient(0, this.canvas.height, 0, 0);
        gradient.addColorStop(0, "#4f46e5");
        gradient.addColorStop(0.5, "#9333ea");
        gradient.addColorStop(1, "#ec4899");

        ctx.fillStyle = gradient;
        ctx.fillRect(x, this.canvas.height - barHeight, barWidth - 1, barHeight);

        x += barWidth;
      }
    };

    render();
  }

  resetTranscript() {
    this.fullTranscript = "";
    this.interimTranscript = "";
  }
}
