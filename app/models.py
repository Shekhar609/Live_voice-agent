import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from app.database import Base

class Transcription(Base):
    """
    SQLAlchemy Model for storing speech-to-text transcriptions and metadata.
    """
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="Speech Transcription")
    text = Column(Text, nullable=False)
    detected_language = Column(String(100), default="Multilingual (Hindi/English)")
    language_breakdown = Column(String(255), nullable=True) # e.g. "Hindi: 60%, English: 40%"
    duration_seconds = Column(Float, default=0.0)
    category = Column(String(100), default="General")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Transcription(id={self.id}, title='{self.title}', lang='{self.detected_language}')>"
