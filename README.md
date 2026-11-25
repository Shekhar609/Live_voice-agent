# PolyScribe AI - Real-Time Multilingual Speech-to-Text Platform

> A full-stack, real-time multilingual Speech-to-Text (STT) web application with bidirectional WebSocket streaming, code-switching support (Hindi & English / Hinglish), relational database persistence, interactive CRUD dashboard, and open-source Text-to-Speech (TTS).

---

## 🌟 Key Features

1. **Real-time Multilingual Speech-to-Text**:
   - Transcribes spoken audio with zero latency as the user speaks.
   - Native support for **multilingual code-switching** (e.g. mixture of Hindi & English / Hinglish: *"Aap kaise ho, let's start the meeting"*).
   - Real-time classification engine: detects Devanagari Hindi, Romanized Hinglish, and English, calculating exact percentage breakdown dynamically.
   - Dual-engine architecture:
     - **Client-Server Hybrid Streamer**: Web Audio API frequency visualizer + live speech capture streamed over WebSockets to FastAPI.
     - **Gemini Live / Whisper Server-side integration**: Ready to connect with Gemini Live 3.1 / 2.0 Flash API for advanced server-side transcription when `GEMINI_API_KEY` is provided.

2. **Database Persistence & CRUD Operations**:
   - Stores transcripts in a relational database (SQLite for zero-config local development, PostgreSQL for cloud production).
   - **Create**: Save live speech sessions or manual transcripts with title, duration, category, and language tags.
   - **Read**: Live dashboard with search filter (by keyword), language filter (Hindi, English, Hinglish), and pagination.
   - **Update**: Edit title, transcription content, and categories via an in-app modal.
   - **Delete**: Individual record deletion and bulk purge ("Clear All").
   - **Analytics & Stats**: Live summary cards tracking total transcriptions, word counts, recorded duration, and language distribution.
   - **Export**: 1-click export of database history to **CSV**, **JSON**, or **TXT**.

3. **Open-Source Text-to-Speech (TTS)**:
   - Integrated open-source TTS engine powered by `gTTS` (Google Translate TTS wrapper) and browser SpeechSynthesis fallback.
   - Read aloud any saved or live transcribed sentence in authentic Hindi/English accents with the "🔊 Listen" button.

4. **Production-Ready & Cloud Deployable**:
   - Dockerized with a multi-stage `Dockerfile`.
   - `docker-compose.yml` for multi-container orchestration with PostgreSQL.
   - Ready-to-deploy blueprints for **Render** (`render.yaml`), **Railway** (`railway.json`), and **Fly.io** / **Heroku** (`Procfile`).

---

## 🏗️ Architecture & Tech Stack

```mermaid
flowchart TD
    User([User Voice / Microphone]) -->|Real-time Audio & Chunks| Client[Modern Web UI / AudioVisualizer]
    Client -->|Bidirectional WebSocket /ws/transcribe| WSServer[FastAPI WebSocket Streamer]
    Client -->|REST API Requests /api/transcriptions| APIServer[FastAPI REST API Server]
    
    WSServer --> LanguageEngine[Multilingual Code-Switching Analyzer]
    LanguageEngine -->|Interim & Final Transcripts| Client
    
    APIServer --> DB[(Relational Database: SQLite / PostgreSQL)]
    APIServer --> TTSEngine[Open-Source TTS Engine: gTTS]
    TTSEngine -->|Audio Stream MP3| Client
```

### Technology Stack:
- **Backend**: Python 3.9+, FastAPI, Uvicorn (ASGI), WebSockets
- **Database**: Relational ORM with SQLAlchemy (SQLite for local, PostgreSQL for cloud deployment)
- **Speech-to-Text**: Real-time Web Audio API streaming + Gemini Live 3.1 / 2.0 Flash API pipeline
- **Text-to-Speech**: Open-source `gTTS` and Web Speech API
- **Frontend**: HTML5, Modern Tailwind CSS (Dark theme), Web Audio API Visualizer, Vanilla JS ES6+ (No node/npm build step required)
- **Testing**: `pytest`, `httpx` (100% passing test suite for REST & WebSockets)
- **DevOps**: Docker, Docker Compose, Render Blueprint

---

## 📁 Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point, WebSocket streamer, static mounts
│   ├── config.py                # Environment configuration (DATABASE_URL, GEMINI_API_KEY)
│   ├── database.py              # SQLAlchemy engine, session maker, base setup
│   ├── models.py                # SQLAlchemy DB model (Transcription)
│   ├── schemas.py               # Pydantic v2 schemas for CRUD validation & stats
│   ├── crud.py                  # Database CRUD queries and analytics
│   ├── services/
│   │   ├── __init__.py
│   │   ├── language_detector.py # Multilingual Hindi-English code-switching analyzer
│   │   ├── stt_service.py       # Speech-to-Text orchestrator & Gemini Live API
│   │   └── tts_service.py       # Open-source Text-to-Speech engine (gTTS)
│   └── routers/
│       ├── __init__.py
│       ├── transcriptions.py    # CRUD endpoints, search, filtering, export
│       └── tts.py               # Text-to-Speech audio streaming endpoint
├── static/
│   ├── index.html               # Responsive single page application UI
│   ├── css/
│   │   └── style.css            # Custom animations, visualizer styling, glassmorphism
│   └── js/
│       ├── audio_recorder.js    # AudioContext, frequency visualizer, WebSocket stream
│       └── app.js               # Frontend controller, CRUD operations, TTS player
├── tests/
│   ├── __init__.py
│   └── test_api.py              # Unit & integration tests (REST API + WebSocket)
├── .env.example                 # Sample environment variables
├── .gitignore                   # Git ignore rules
├── Dockerfile                   # Production container definition
├── docker-compose.yml           # Local multi-service compose (Web + PostgreSQL)
├── render.yaml                  # 1-click Render cloud deployment blueprint
├── Procfile                     # Heroku / Railway deployment configuration
├── requirements.txt             # Python dependencies
├── run.sh                       # Quick-start bash script
└── README.md                    # Documentation
```

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.9 or higher
- Git

### 1. Clone & Navigate
```bash
git clone <YOUR_REPOSITORY_URL>
cd Assingment
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*Note: SQLite is configured by default for zero-friction setup. If you wish to use PostgreSQL, set `DATABASE_URL=postgresql://user:password@localhost:5432/dbname`.*

### 4. Start the Application
Run the helper script:
```bash
./run.sh
```
Or start directly with `uvicorn`:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at: **[http://localhost:8000](http://localhost:8000)**  
Interactive Swagger API documentation is available at: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🐳 Docker Deployment

### Run with Docker:
```bash
docker build -t polyscribe-stt .
docker run -p 8000:8000 polyscribe-stt
```

### Run with Docker Compose (with PostgreSQL):
```bash
docker-compose up --build
```
This starts both the FastAPI web application and a PostgreSQL 15 database instance with persistent volume storage.

---

## ☁️ Cloud Deployment (Deliverable 2)

### Deploying to Render (Recommended - Free Tier):
1. Push this repository to GitHub.
2. Sign in to [Render](https://render.com).
3. Click **New** > **Blueprint** and select your GitHub repository.
4. Render will automatically detect `render.yaml` and provision:
   - A Web Service running FastAPI with automatic HTTPS and WebSockets.
   - A managed PostgreSQL database instance.
5. Once deployed, Render provides a public URL: `https://<your-app-name>.onrender.com`.

### Deploying to Railway:
1. Connect your GitHub repository to [Railway](https://railway.app).
2. Add a PostgreSQL plugin service.
3. Railway automatically sets `DATABASE_URL` and detects the `Procfile` / `Dockerfile`.
4. Generate a public domain under service settings.

---

## 🧪 Running Automated Tests

Run the complete test suite verifying health, multilingual language detection, REST CRUD endpoints, export, and real-time WebSocket communication:

```bash
PYTHONPATH=. ./venv/bin/pytest tests/test_api.py -v
```

All tests execute in memory with SQLite `StaticPool` and verify:
- ✅ Health check endpoint
- ✅ Multilingual Hindi-English code-switching analyzer
- ✅ Pure Devanagari Hindi recognition
- ✅ Pure English recognition
- ✅ Create transcription with auto-language tagging
- ✅ Read transcription by ID & list with pagination
- ✅ Update transcription content & recalculate language breakdown
- ✅ Delete transcription
- ✅ Aggregate dashboard statistics
- ✅ Export as CSV, JSON, and TXT
- ✅ Bidirectional WebSocket streaming (`/ws/transcribe`)

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web UI dashboard |
| `GET` | `/health` | Cloud deployment health check probe |
| `WS` | `/ws/transcribe` | Real-time bidirectional WebSocket STT streaming |
| `GET` | `/api/transcriptions` | List saved transcriptions (supports `search`, `language`, `skip`, `limit`) |
| `GET` | `/api/transcriptions/stats` | Dashboard statistics (total count, words, duration, language breakdown) |
| `GET` | `/api/transcriptions/{id}` | Get single transcription details |
| `POST` | `/api/transcriptions` | Create and persist a new transcription |
| `PUT` | `/api/transcriptions/{id}` | Update transcription title, content, or category |
| `DELETE` | `/api/transcriptions/{id}` | Delete a transcription record |
| `DELETE` | `/api/transcriptions` | Clear all transcription history |
| `GET` | `/api/transcriptions/export/{format}` | Export records as `csv`, `json`, or `txt` |
| `POST` | `/api/tts/speak` | Synthesize speech MP3 audio via open-source TTS |
| `GET` | `/docs` | OpenAPI / Swagger interactive documentation |

---

## 🎙️ Testing Multilingual Code-Switching

Try speaking any of the following sample phrases to test real-time code-switching:
- **Hinglish (Code-Switching)**: *"Aap kaise ho, I want to discuss the project schedule today."*
- **Hinglish**: *"Meeting ko start karte hain, let's look at the quarterly report."*
- **Hindi (Devanagari)**: *"नमस्ते, आप सभी का आज की बैठक में स्वागत है।"*
- **English**: *"Welcome everyone, today we are testing real-time transcription."*

The system will instantly update the transcription stream in real-time, detect the code-switching ratio, and allow you to save, edit, read aloud with TTS, and export!
