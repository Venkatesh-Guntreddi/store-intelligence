import json

from fastapi import FastAPI

from app.db import get_connection, init_db
from app.models import IngestRequest, IngestResponse
from app.funnel import calculate_funnel
from app.heatmap import calculate_heatmap
from app.anomalies import detect_anomalies

app = FastAPI(title="Store Intelligence API")

@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {"message": "Store Intelligence API Running"}


@app.post("/events/ingest", response_model=IngestResponse)
def ingest_events(payload: IngestRequest):
    accepted = 0
    duplicates = 0
    errors = []

    conn = get_connection()
    cursor = conn.cursor()

    for event in payload.events:
        data = event.model_dump(mode="json")

        try:
            cursor.execute(
                """
                INSERT INTO events (
                    event_id, store_id, camera_id, visitor_id,
                    event_type, timestamp, zone_id, dwell_ms,
                    is_staff, confidence, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["event_id"],
                    data["store_id"],
                    data["camera_id"],
                    data["visitor_id"],
                    data["event_type"],
                    data["timestamp"],
                    data["zone_id"],
                    data["dwell_ms"],
                    int(data["is_staff"]),
                    data["confidence"],
                    json.dumps(data["metadata"]),
                ),
            )
            accepted += 1

        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                duplicates += 1
            else:
                errors.append(
                    {
                        "event_id": data.get("event_id"),
                        "error": str(exc),
                    }
                )

    conn.commit()
    conn.close()

    return {
        "accepted": accepted,
        "duplicates": duplicates,
        "failed": len(errors),
        "errors": errors,
    }


@app.get("/stores/{store_id}/metrics")
def get_store_metrics(store_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM events
        WHERE store_id = ? AND is_staff = 0
        ORDER BY timestamp ASC
        """,
        (store_id,),
    )

    events = [dict(row) for row in cursor.fetchall()]
    conn.close()

    visitor_ids = {
        event["visitor_id"]
        for event in events
        if event["event_type"] in ["ENTRY", "REENTRY"]
    }

    zone_dwell = {}

    for event in events:
        zone_id = event.get("zone_id")

        if event["event_type"] == "ZONE_DWELL" and zone_id:
            zone_dwell.setdefault(zone_id, [])
            zone_dwell[zone_id].append(event["dwell_ms"])

    avg_dwell_per_zone = {
        zone: round(sum(values) / len(values), 2)
        for zone, values in zone_dwell.items()
    }

    queue_events = [
        event for event in events
        if event["event_type"] == "BILLING_QUEUE_JOIN"
    ]

    latest_queue_depth = 0
    if queue_events:
        metadata = json.loads(queue_events[-1]["metadata"])
        latest_queue_depth = metadata.get("queue_depth") or 0

    abandon_events = [
        event for event in events
        if event["event_type"] == "BILLING_QUEUE_ABANDON"
    ]

    abandonment_rate = 0
    if queue_events:
        abandonment_rate = round(len(abandon_events) / len(queue_events), 4)

    return {
        "store_id": store_id,
        "unique_visitors": len(visitor_ids),
        "conversion_rate": 0,
        "avg_dwell_per_zone": avg_dwell_per_zone,
        "queue_depth": latest_queue_depth,
        "abandonment_rate": abandonment_rate,
    }


@app.get("/health")
def health():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM events")
    total_events = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT store_id, MAX(timestamp) AS last_timestamp
        FROM events
        GROUP BY store_id
        """
    )

    last_event_per_store = {
        row["store_id"]: row["last_timestamp"]
        for row in cursor.fetchall()
    }

    conn.close()

    return {
        "status": "healthy",
        "total_events": total_events,
        "last_event_timestamp_per_store": last_event_per_store,
    }

@app.get("/stores/{store_id}/funnel")
def get_store_funnel(store_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM events
        WHERE store_id = ? AND is_staff = 0
        ORDER BY timestamp ASC
        """,
        (store_id,),
    )

    events = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "store_id": store_id,
        "funnel": calculate_funnel(events),
    }

@app.get("/stores/{store_id}/heatmap")
def get_store_heatmap(store_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM events
        WHERE store_id = ? AND is_staff = 0
        ORDER BY timestamp ASC
        """,
        (store_id,),
    )

    events = [dict(row) for row in cursor.fetchall()]
    conn.close()

    visitor_ids = {
        event["visitor_id"]
        for event in events
        if event["event_type"] in ["ENTRY", "REENTRY"]
    }

    return {
        "store_id": store_id,
        "data_confidence": "LOW" if len(visitor_ids) < 20 else "HIGH",
        "zones": calculate_heatmap(events),
    }

@app.get("/stores/{store_id}/anomalies")
def get_store_anomalies(store_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM events
        WHERE store_id = ? AND is_staff = 0
        ORDER BY timestamp ASC
        """,
        (store_id,),
    )

    events = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "store_id": store_id,
        "active_anomalies": detect_anomalies(events),
    }

