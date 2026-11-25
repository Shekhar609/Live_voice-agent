import os
import io
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

class TTSService:
    """
    Open-source and free Text-to-Speech service using gTTS (Google Translate TTS wrapper).
    Supports Hindi ('hi'), English ('en', 'en-in'), and fallback accents.
    """
    
    @staticmethod
    def generate_speech(text: str, lang: str = "hi") -> bytes:
        """
        Generate MP3 audio bytes from input text.
        Supports automatic Hindi / English multilingual handling.
        """
        # Determine language code
        target_lang = "hi" if lang in ("hi", "hindi", "hinglish") else "en"
        
        # If text is primarily Hindi or Hinglish, default to 'hi' for authentic pronunciation
        try:
            tts = gTTS(text=text, lang=target_lang, slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            logger.error(f"TTS Generation failed with lang '{target_lang}', falling back to 'en': {e}")
            # Fallback to English
            tts = gTTS(text=text, lang="en", slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()

tts_service = TTSService()
