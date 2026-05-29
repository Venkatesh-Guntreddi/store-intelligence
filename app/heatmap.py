def calculate_heatmap(events: list[dict]) -> dict:
    zone_stats = {}

    for event in events:
        if event["event_type"] not in ["ZONE_ENTER", "ZONE_DWELL"]:
            continue

        zone_id = event.get("zone_id")
        if not zone_id:
            continue

        if zone_id not in zone_stats:
            zone_stats[zone_id] = {
                "visits": 0,
                "total_dwell_ms": 0,
            }

        if event["event_type"] == "ZONE_ENTER":
            zone_stats[zone_id]["visits"] += 1

        if event["event_type"] == "ZONE_DWELL":
            zone_stats[zone_id]["total_dwell_ms"] += event["dwell_ms"]

    max_visits = max([z["visits"] for z in zone_stats.values()], default=0)

    result = {}

    for zone, stats in zone_stats.items():
        avg_dwell_ms = 0
        if stats["visits"] > 0:
            avg_dwell_ms = round(stats["total_dwell_ms"] / stats["visits"], 2)

        score = 0
        if max_visits > 0:
            score = round((stats["visits"] / max_visits) * 100, 2)

        result[zone] = {
            "visits": stats["visits"],
            "avg_dwell_ms": avg_dwell_ms,
            "heatmap_score": score,
        }

    return result