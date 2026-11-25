import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.services.language_detector import analyze_multilingual_text

router = APIRouter(prefix="/api/transcriptions", tags=["Transcriptions"])

@router.get("", response_model=List[schemas.TranscriptionResponse])
def read_transcriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Search term for title, text, or category"),
    language: Optional[str] = Query(None, description="Filter by detected language"),
    db: Session = Depends(get_db)
):
    """List transcriptions with search, filter, and pagination."""
    return crud.get_transcriptions(db, skip=skip, limit=limit, search=search, language=language)

@router.get("/stats", response_model=schemas.TranscriptionStats)
def get_transcription_stats(db: Session = Depends(get_db)):
    """Retrieve aggregate analytics and dashboard counts."""
    return crud.get_stats(db)

@router.get("/export/{export_format}")
def export_transcriptions(export_format: str, db: Session = Depends(get_db)):
    """Export all transcription history to CSV, JSON, or TXT."""
    items = crud.get_transcriptions(db, skip=0, limit=10000)
    
    if export_format.lower() == "json":
        data = [
            {
                "id": t.id,
                "title": t.title,
                "text": t.text,
                "detected_language": t.detected_language,
                "language_breakdown": t.language_breakdown,
                "duration_seconds": t.duration_seconds,
                "category": t.category,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in items
        ]
        return Response(
            content=json.dumps(data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=transcriptions_export.json"}
        )
        
    elif export_format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Title", "Text", "Detected Language", "Breakdown", "Duration (s)", "Category", "Created At"])
        for t in items:
            writer.writerow([
                t.id, t.title, t.text, t.detected_language, t.language_breakdown,
                t.duration_seconds, t.category, t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
            ])
        return Response(
            content=output.getvalue().encode("utf-8-sig"),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transcriptions_export.csv"}
        )
        
    elif export_format.lower() == "txt":
        output = io.StringIO()
        for t in items:
            date_str = t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
            output.write(f"[{date_str}] {t.title} ({t.detected_language})\n")
            output.write(f"{t.text}\n")
            output.write("-" * 60 + "\n\n")
        return Response(
            content=output.getvalue().encode("utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=transcriptions_export.txt"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: json, csv, txt")

@router.get("/{transcription_id}", response_model=schemas.TranscriptionResponse)
def read_transcription(transcription_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single transcription."""
    db_item = crud.get_transcription(db, transcription_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return db_item

@router.post("", response_model=schemas.TranscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_transcription(transcription: schemas.TranscriptionCreate, db: Session = Depends(get_db)):
    """Create and persist a new speech-to-text transcription."""
    # If language is default or missing, analyze text automatically
    if not transcription.detected_language or transcription.detected_language == "Multilingual (Hindi/English)":
        lang, breakdown, _ = analyze_multilingual_text(transcription.text)
        transcription.detected_language = lang
        transcription.language_breakdown = breakdown
        
    return crud.create_transcription(db, transcription)

@router.put("/{transcription_id}", response_model=schemas.TranscriptionResponse)
def update_transcription(
    transcription_id: int,
    transcription_update: schemas.TranscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing transcription."""
    # If text is updated, recalculate language detection
    if transcription_update.text:
        lang, breakdown, _ = analyze_multilingual_text(transcription_update.text)
        if not transcription_update.detected_language:
            transcription_update.detected_language = lang
            
    db_item = crud.update_transcription(db, transcription_id, transcription_update)
    if not db_item:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return db_item

@router.delete("/{transcription_id}", status_code=status.HTTP_200_OK)
def delete_transcription(transcription_id: int, db: Session = Depends(get_db)):
    """Delete a transcription record."""
    success = crud.delete_transcription(db, transcription_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return {"message": "Transcription deleted successfully", "id": transcription_id}

@router.delete("", status_code=status.HTTP_200_OK)
def clear_all_transcriptions(db: Session = Depends(get_db)):
    """Delete all transcription history."""
    count = crud.delete_all_transcriptions(db)
    return {"message": f"Successfully deleted {count} records", "deleted_count": count}
