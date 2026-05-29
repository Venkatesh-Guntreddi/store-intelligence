from datetime import datetime, timedelta, timezone


def detect_anomalies(events: list[dict]) -> list[dict]:
    anomalies = []

    if not events:
        return anomalies

    # 1. Queue spike
    queue_events = [
        event for event in events
        if event["event_type"] == "BILLING_QUEUE_JOIN"
    ]

    if queue_events:
        latest_event = queue_events[-1]
        latest_queue_depth = latest_event.get("queue_depth")

        if latest_queue_depth is None:
            import json
            metadata = json.loads(latest_event["metadata"])
            latest_queue_depth = metadata.get("queue_depth", 0)

        if latest_queue_depth >= 5:
            anomalies.append({
                "type": "QUEUE_SPIKE",
                "severity": "WARN",
                "suggested_action": "Open an additional billing counter or assign staff to billing queue.",
                "metadata": {
                    "queue_depth": latest_queue_depth
                }
            })

    # 2. Dead zone: no zone visit in last 30 minutes
    latest_timestamp = max(
        datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        for event in events
    )

    threshold_time = latest_timestamp - timedelta(minutes=30)

    zone_last_seen = {}

    for event in events:
        if event["event_type"] not in ["ZONE_ENTER", "ZONE_DWELL"]:
            continue

        zone_id = event.get("zone_id")
        if not zone_id:
            continue

        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        zone_last_seen[zone_id] = max(zone_last_seen.get(zone_id, event_time), event_time)

    for zone_id, last_seen in zone_last_seen.items():
        if last_seen < threshold_time:
            anomalies.append({
                "type": "DEAD_ZONE",
                "severity": "INFO",
                "zone_id": zone_id,
                "suggested_action": "Check product placement, signage, or staff coverage in this zone.",
                "metadata": {
                    "last_seen": last_seen.isoformat()
                }
            })

    return anomalies