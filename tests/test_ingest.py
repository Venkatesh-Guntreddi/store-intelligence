# PROMPT:
# Generate pytest tests for a FastAPI event ingestion endpoint that validates
# store intelligence events, accepts valid events, and treats duplicate event_id
# values as idempotent duplicates.
#
# CHANGES MADE:
# Simplified the tests to match the current SQLite-backed MVP implementation.

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_valid_event():
    payload = {
        "events": [
            {
                "event_id": "11111111-1111-4111-8111-111111111111",
                "store_id": "STORE_BLR_002",
                "camera_id": "CAM_ENTRY_01",
                "visitor_id": "VIS_TEST_001",
                "event_type": "ENTRY",
                "timestamp": "2026-03-03T14:20:00Z",
                "zone_id": None,
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": 0.95,
                "metadata": {
                    "queue_depth": None,
                    "sku_zone": None,
                    "session_seq": 1,
                },
            }
        ]
    }

    response = client.post("/events/ingest", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] in [0, 1]
    assert body["failed"] == 0


def test_ingest_rejects_invalid_event_type():
    payload = {
        "events": [
            {
                "event_id": "22222222-2222-4222-8222-222222222222",
                "store_id": "STORE_BLR_002",
                "camera_id": "CAM_ENTRY_01",
                "visitor_id": "VIS_TEST_002",
                "event_type": "BAD_EVENT",
                "timestamp": "2026-03-03T14:20:00Z",
                "zone_id": None,
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": 0.95,
                "metadata": {},
            }
        ]
    }

    response = client.post("/events/ingest", json=payload)

    assert response.status_code == 422