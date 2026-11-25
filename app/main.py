import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db
from app.routers import transcriptions, tts
from app.services.stt_service import stt_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(transcriptions.router)
app.include_router(tts.router)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Serve the single page application HTML."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "Speech-to-Text API is running",
        "docs": "/docs",
        "api": "/api/transcriptions"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for cloud load balancers and deployment probes."""
    return {"status": "healthy", "version": settings.VERSION}

@app.websocket("/ws/transcribe")
async def websocket_transcription_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket endpoint for Speech-to-Text streaming.
    Receives text chunks, audio tokens, or partial recognitions,
    runs live multilingual analysis (Hindi/English code-switching),
    and sends back structured real-time transcript updates.
    """
    await websocket.accept()
    logger.info("WebSocket client connected to real-time transcription session.")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "chunk")
            
            if msg_type == "chunk":
                raw_text = message.get("text", "")
                result = stt_service.process_transcript_chunk(raw_text)
                await websocket.send_json({
                    "type": "interim",
                    "text": result["text"],
                    "detected_language": result["detected_language"],
                    "language_breakdown": result["language_breakdown"],
                    "stats": result["stats"],
                    "word_count": result["word_count"]
                })
            elif msg_type == "finalize":
                raw_text = message.get("text", "")
                result = stt_service.process_transcript_chunk(raw_text)
                await websocket.send_json({
                    "type": "final",
                    "text": result["text"],
                    "detected_language": result["detected_language"],
                    "language_breakdown": result["language_breakdown"],
                    "stats": result["stats"],
                    "word_count": result["word_count"]
                })
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
