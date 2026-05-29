# PROMPT:
# Generate pytest tests for anomaly detection including billing queue spike.
#
# CHANGES MADE:
# Focused on QUEUE_SPIKE because it is implemented in the MVP anomaly engine.

from fastapi.testclient import TestClient

from app.db import get_connection, init_db
from app.main import app

client = TestClient(app)


def clear_events():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM events")
    conn.commit()
    conn.close()


def test_queue_spike_anomaly():
    clear_events()

    payload = {
        "events": [
            {
                "event_id": "88888888-8888-4888-8888-888888888888",
                "store_id": "STORE_BLR_002",
                "camera_id": "CAM_BILLING_01",
                "visitor_id": "VIS_QUEUE_001",
                "event_type": "BILLING_QUEUE_JOIN",
                "timestamp": "2026-03-03T14:40:00Z",
                "zone_id": "BILLING",
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {
                    "queue_depth": 6,
                    "sku_zone": None,
                    "session_seq": 1,
                },
            }
        ]
    }

    client.post("/events/ingest", json=payload)

    response = client.get("/stores/STORE_BLR_002/anomalies")

    assert response.status_code == 200
    body = response.json()

    assert body["store_id"] == "STORE_BLR_002"
    assert body["active_anomalies"][0]["type"] == "QUEUE_SPIKE"
    assert body["active_anomalies"][0]["severity"] == "WARN"