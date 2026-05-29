def calculate_funnel(events: list[dict]) -> dict:
    sessions = {}

    for event in events:
        visitor_id = event["visitor_id"]
        event_type = event["event_type"]

        if event.get("is_staff") == 1:
            continue

        if visitor_id not in sessions:
            sessions[visitor_id] = {
                "entry": False,
                "zone_visit": False,
                "billing_queue": False,
                "purchase": False,
            }

        if event_type in ["ENTRY", "REENTRY"]:
            sessions[visitor_id]["entry"] = True

        if event_type in ["ZONE_ENTER", "ZONE_DWELL"]:
            sessions[visitor_id]["zone_visit"] = True

        if event_type == "BILLING_QUEUE_JOIN":
            sessions[visitor_id]["billing_queue"] = True

        # Temporary: later we will connect POS transactions here
        if event_type == "PURCHASE":
            sessions[visitor_id]["purchase"] = True

    total_entry = sum(1 for s in sessions.values() if s["entry"])
    total_zone_visit = sum(1 for s in sessions.values() if s["zone_visit"])
    total_billing = sum(1 for s in sessions.values() if s["billing_queue"])
    total_purchase = sum(1 for s in sessions.values() if s["purchase"])

    def dropoff(previous: int, current: int) -> float:
        if previous == 0:
            return 0
        return round(((previous - current) / previous) * 100, 2)

    return {
        "entry": total_entry,
        "zone_visit": total_zone_visit,
        "billing_queue": total_billing,
        "purchase": total_purchase,
        "dropoff_percent": {
            "entry_to_zone_visit": dropoff(total_entry, total_zone_visit),
            "zone_visit_to_billing": dropoff(total_zone_visit, total_billing),
            "billing_to_purchase": dropoff(total_billing, total_purchase),
        },
    }