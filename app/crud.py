from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models import Transcription
from app.schemas import TranscriptionCreate, TranscriptionUpdate

def get_transcription(db: Session, transcription_id: int) -> Optional[Transcription]:
    """Retrieve a single transcription record by ID."""
    return db.query(Transcription).filter(Transcription.id == transcription_id).first()

def get_transcriptions(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    language: Optional[str] = None
) -> List[Transcription]:
    """Retrieve all transcription records with optional search filter and pagination."""
    query = db.query(Transcription)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Transcription.title.ilike(search_term),
                Transcription.text.ilike(search_term),
                Transcription.category.ilike(search_term)
            )
        )
        
    if language and language != "all":
        query = query.filter(Transcription.detected_language.ilike(f"%{language}%"))
        
    return query.order_by(desc(Transcription.created_at)).offset(skip).limit(limit).all()

def count_transcriptions(
    db: Session,
    search: Optional[str] = None,
    language: Optional[str] = None
) -> int:
    """Get total count of transcription records."""
    query = db.query(Transcription)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Transcription.title.ilike(search_term),
                Transcription.text.ilike(search_term),
                Transcription.category.ilike(search_term)
            )
        )
    if language and language != "all":
        query = query.filter(Transcription.detected_language.ilike(f"%{language}%"))
    return query.count()

def create_transcription(db: Session, transcription: TranscriptionCreate) -> Transcription:
    """Create a new transcription entry in the database."""
    db_item = Transcription(
        title=transcription.title,
        text=transcription.text,
        detected_language=transcription.detected_language,
        language_breakdown=transcription.language_breakdown,
        duration_seconds=transcription.duration_seconds,
        category=transcription.category
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_transcription(
    db: Session,
    transcription_id: int,
    transcription_update: TranscriptionUpdate
) -> Optional[Transcription]:
    """Update an existing transcription."""
    db_item = get_transcription(db, transcription_id)
    if not db_item:
        return None
    
    # Support both pydantic v1 dict() and v2 model_dump()
    if hasattr(transcription_update, "model_dump"):
        update_data = transcription_update.model_dump(exclude_unset=True)
    else:
        update_data = transcription_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_transcription(db: Session, transcription_id: int) -> bool:
    """Delete a single transcription by ID."""
    db_item = get_transcription(db, transcription_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True

def delete_all_transcriptions(db: Session) -> int:
    """Clear all records from database."""
    deleted_count = db.query(Transcription).delete()
    db.commit()
    return deleted_count

def get_stats(db: Session):
    """Compute aggregate analytics for dashboard."""
    transcriptions = db.query(Transcription).all()
    total_count = len(transcriptions)
    total_words = sum(len(t.text.split()) for t in transcriptions)
    total_duration = sum(t.duration_seconds or 0.0 for t in transcriptions)
    
    languages_breakdown = {}
    categories_breakdown = {}
    
    for t in transcriptions:
        lang = t.detected_language or "Unknown"
        languages_breakdown[lang] = languages_breakdown.get(lang, 0) + 1
        
        cat = t.category or "General"
        categories_breakdown[cat] = categories_breakdown.get(cat, 0) + 1
        
    return {
        "total_count": total_count,
        "total_words": total_words,
        "total_duration_seconds": round(total_duration, 1),
        "languages_breakdown": languages_breakdown,
        "categories_breakdown": categories_breakdown
    }
