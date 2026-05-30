def calculate_funnel(events: list[dict]) -> dict:
    entry_visitors = set()
    zone_visitors = set()
    billing_visitors = set()
    purchase_visitors = set()

    for event in events:
        if event.get("is_staff") in [1, True]:
            continue

        visitor_id = event["visitor_id"]
        event_type = event["event_type"]

        if event_type in ["ENTRY", "REENTRY"]:
            entry_visitors.add(visitor_id)

        if event_type in ["ZONE_ENTER", "ZONE_DWELL"]:
            zone_visitors.add(visitor_id)

        if event_type == "BILLING_QUEUE_JOIN":
            billing_visitors.add(visitor_id)

        if event_type == "PURCHASE":
            purchase_visitors.add(visitor_id)

    def bounded_stage(stage: set, previous: set) -> set:
        if not previous:
            return stage
        return stage.intersection(previous)

    zone_visitors = bounded_stage(zone_visitors, entry_visitors)
    billing_visitors = bounded_stage(billing_visitors, zone_visitors)
    purchase_visitors = bounded_stage(purchase_visitors, billing_visitors)

    entry_count = len(entry_visitors)
    zone_count = len(zone_visitors)
    billing_count = len(billing_visitors)
    purchase_count = len(purchase_visitors)

    def dropoff(previous: int, current: int) -> float:
        if previous == 0:
            return 0
        return round(((previous - current) / previous) * 100, 2)

    return {
        "entry": entry_count,
        "zone_visit": zone_count,
        "billing_queue": billing_count,
        "purchase": purchase_count,
        "dropoff_percent": {
            "entry_to_zone_visit": dropoff(entry_count, zone_count),
            "zone_visit_to_billing": dropoff(zone_count, billing_count),
            "billing_to_purchase": dropoff(billing_count, purchase_count),
        },
    }