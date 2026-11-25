from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

class TranscriptionBase(BaseModel):
    title: str = Field(default="Speech Transcription", max_length=255)
    text: str = Field(..., min_length=1, description="Transcribed speech text")
    detected_language: Optional[str] = Field(default="Multilingual (Hindi/English)")
    language_breakdown: Optional[str] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=0.0)
    category: Optional[str] = Field(default="General", max_length=100)

class TranscriptionCreate(TranscriptionBase):
    pass

class TranscriptionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    text: Optional[str] = Field(None, min_length=1)
    detected_language: Optional[str] = None
    category: Optional[str] = None

class TranscriptionResponse(TranscriptionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TranscriptionStats(BaseModel):
    total_count: int
    total_words: int
    total_duration_seconds: float
    languages_breakdown: Dict[str, int]
    categories_breakdown: Dict[str, int]

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to convert into speech")
    language: Optional[str] = Field(default="hi", description="Language code: 'hi' for Hindi, 'en' for English")
