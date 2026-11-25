from fastapi import APIRouter, HTTPException, Response
from app.schemas import TTSRequest
from app.services.tts_service import tts_service

router = APIRouter(prefix="/api/tts", tags=["Text-to-Speech"])

@router.post("/speak")
def text_to_speech(payload: TTSRequest):
    """
    Generate speech audio for input text.
    Returns audio/mpeg stream for real-time browser playback.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        audio_bytes = tts_service.generate_speech(payload.text, lang=payload.language)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {str(e)}")
