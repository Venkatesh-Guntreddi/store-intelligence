# PROMPT:
# Generate pytest tests for store metrics endpoint including unique visitors,
# dwell time per zone, queue depth, and abandonment rate.
#
# CHANGES MADE:
# Added database cleanup so tests are deterministic with SQLite.

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


def test_metrics_endpoint():
    clear_events()

    payload = {
        "events": [
            {
                "event_id": "55555555-5555-4555-8555-555555555555",
                "store_id": "STORE_BLR_002",
                "camera_id": "CAM_ENTRY_01",
                "visitor_id": "VIS_METRIC_001",
                "event_type": "ENTRY",
                "timestamp": "2026-03-03T14:20:00Z",
                "zone_id": None,
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": 0.95,
                "metadata": {"session_seq": 1},
            },
            {
                "event_id": "66666666-6666-4666-8666-666666666666",
                "store_id": "STORE_BLR_002",
                "camera_id": "CAM_MAIN_01",
                "visitor_id": "VIS_METRIC_001",
                "event_type": "ZONE_DWELL",
                "timestamp": "2026-03-03T14:22:00Z",
                "zone_id": "SKINCARE",
                "dwell_ms": 9000,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {"sku_zone": "MOISTURISER", "session_seq": 2},
            },
            {
                "event_id": "77777777-7777-4777-8777-777777777777",
                "store_id": "STORE_BLR_002",
                "camera_id": "CAM_BILLING_01",
                "visitor_id": "VIS_METRIC_001",
                "event_type": "BILLING_QUEUE_JOIN",
                "timestamp": "2026-03-03T14:30:00Z",
                "zone_id": "BILLING",
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": 0.88,
                "metadata": {"queue_depth": 3, "session_seq": 3},
            },
        ]
    }

    client.post("/events/ingest", json=payload)

    response = client.get("/stores/STORE_BLR_002/metrics")

    assert response.status_code == 200
    body = response.json()

    assert body["unique_visitors"] == 1
    assert body["avg_dwell_per_zone"]["SKINCARE"] == 9000
    assert body["queue_depth"] == 3