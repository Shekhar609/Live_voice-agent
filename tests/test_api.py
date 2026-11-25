import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.services.language_detector import analyze_multilingual_text

# Use an in-memory SQLite database with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_language_detector_hinglish():
    text = "Aap kaise ho, I am doing great today let's start"
    detected, breakdown, stats = analyze_multilingual_text(text)
    assert "Hinglish" in detected or "Multilingual" in detected
    assert stats["hindi"] > 0
    assert stats["english"] > 0

def test_language_detector_hindi():
    text = "नमस्ते आप कैसे हैं आज का मौसम बहुत अच्छा है"
    detected, breakdown, stats = analyze_multilingual_text(text)
    assert "Hindi" in detected

def test_language_detector_english():
    text = "Hello world this is a test of real time transcription engine"
    detected, breakdown, stats = analyze_multilingual_text(text)
    assert detected == "English"

def test_create_and_get_transcription():
    payload = {
        "title": "Hinglish Meeting",
        "text": "Aap kaise ho, we should start the product discussion now.",
        "category": "Meeting",
        "duration_seconds": 12.5
    }
    response = client.post("/api/transcriptions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Hinglish Meeting"
    assert "Hinglish" in data["detected_language"] or "Multilingual" in data["detected_language"]

    # Retrieve by ID
    get_res = client.get(f"/api/transcriptions/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Hinglish Meeting"

def test_update_transcription():
    # Create item
    res = client.post("/api/transcriptions", json={
        "title": "Initial Title",
        "text": "Initial speech text.",
        "category": "General"
    })
    item_id = res.json()["id"]

    # Update item
    update_res = client.put(f"/api/transcriptions/{item_id}", json={
        "title": "Updated Title",
        "text": "Updated speech text with Hindi words jaise kya haal hai."
    })
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title"

def test_delete_transcription():
    res = client.post("/api/transcriptions", json={
        "title": "To Delete",
        "text": "Temporary text.",
        "category": "Notes"
    })
    item_id = res.json()["id"]

    del_res = client.delete(f"/api/transcriptions/{item_id}")
    assert del_res.status_code == 200

    # Ensure it's deleted
    get_res = client.get(f"/api/transcriptions/{item_id}")
    assert get_res.status_code == 404

def test_stats_and_export():
    client.post("/api/transcriptions", json={
        "title": "Note 1",
        "text": "Hello world testing stats",
        "duration_seconds": 5.0
    })
    client.post("/api/transcriptions", json={
        "title": "Note 2",
        "text": "Aap kaise ho bhai",
        "duration_seconds": 10.0
    })

    # Stats
    stats_res = client.get("/api/transcriptions/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_count"] == 2
    assert stats["total_duration_seconds"] == 15.0

    # Export CSV
    csv_res = client.get("/api/transcriptions/export/csv")
    assert csv_res.status_code == 200
    assert "Note 1" in csv_res.text

    # Export JSON
    json_res = client.get("/api/transcriptions/export/json")
    assert json_res.status_code == 200
    assert len(json_res.json()) == 2

def test_websocket_transcription():
    with client.websocket_connect("/ws/transcribe") as websocket:
        # Send chunk
        websocket.send_json({
            "type": "chunk",
            "text": "Aap kaise ho friend"
        })
        data = websocket.receive_json()
        assert data["type"] == "interim"
        assert data["text"] == "Aap kaise ho friend"
        assert "Hinglish" in data["detected_language"] or "Multilingual" in data["detected_language"]
        assert data["word_count"] == 4

        # Send ping
        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"
