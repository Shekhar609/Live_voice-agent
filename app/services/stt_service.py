import logging
import json
from typing import Optional, Dict, Any
import requests
from app.config import settings
from app.services.language_detector import analyze_multilingual_text

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-To-Text Orchestrator Service.
    Supports:
    1. Real-time streaming transcription via WebSocket chunks.
    2. Multilingual code-switching (Hindi & English / Hinglish) analysis.
    3. Server-side Gemini Live / Gemini API 3.1 / 2.0 Flash integration when GEMINI_API_KEY is configured.
    """

    def __init__(self):
        self.gemini_api_key = settings.GEMINI_API_KEY

    def process_transcript_chunk(self, raw_text: str) -> Dict[str, Any]:
        """
        Processes a real-time transcript chunk or completed transcript,
        runs multilingual analysis, and returns enriched structured metadata.
        """
        clean_text = raw_text.strip()
        detected_language, breakdown_str, breakdown_dict = analyze_multilingual_text(clean_text)
        
        return {
            "text": clean_text,
            "detected_language": detected_language,
            "language_breakdown": breakdown_str,
            "stats": breakdown_dict,
            "word_count": len(clean_text.split()) if clean_text else 0
        }

    def transcribe_with_gemini(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> Optional[str]:
        """
        If Gemini API key is provided, transcribe audio via Gemini 2.0 / 3.1 Flash API
        with prompt specifically instructed for Hindi-English multilingual transcription.
        """
        if not self.gemini_api_key:
            return None

        try:
            import base64
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    "You are an expert multilingual speech-to-text transcriber. "
                                    "Transcribe the following audio accurately. "
                                    "The audio may contain a mixture of Hindi and English (code-switching / Hinglish). "
                                    "Return ONLY the exact transcribed text without additional explanation or commentary."
                                )
                            },
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64_audio
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                transcription = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                return transcription
            else:
                logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error in Gemini STT: {e}")
            return None

stt_service = STTService()
