import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline.emit import make_event


CAMERA_CONFIG = {
    "CAM1": {"type": "ZONE", "zone_id": "COSMETICS", "sku_zone": "SHELF"},
    "CAM2": {"type": "ZONE", "zone_id": "MAKEUP", "sku_zone": "SHELF"},
    "CAM3": {"type": "ENTRY", "zone_id": None, "sku_zone": None},
    "CAM4": {"type": "ZONE", "zone_id": "BACK_AREA", "sku_zone": None},
    "CAM5": {"type": "BILLING", "zone_id": "BILLING", "sku_zone": None},
}


def iso_time(base_time: datetime, seconds: int) -> str:
    return (base_time + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def generate_events_for_camera(video_path: Path, store_id: str) -> list[dict]:
    camera_name = video_path.stem.replace(" ", "").upper()
    config = CAMERA_CONFIG.get(camera_name, {"type": "ZONE", "zone_id": "UNKNOWN", "sku_zone": None})

    base_time = datetime.now(timezone.utc)
    visitor_id = f"VIS_{camera_name}_001"

    events = []

    if config["type"] == "ENTRY":
        events.append(
            make_event(
                store_id=store_id,
                camera_id=camera_name,
                visitor_id=visitor_id,
                event_type="ENTRY",
                zone_id=None,
                confidence=0.85,
                session_seq=1,
                timestamp=iso_time(base_time, 0),
            )
        )

        events.append(
            make_event(
                store_id=store_id,
                camera_id=camera_name,
                visitor_id=visitor_id,
                event_type="EXIT",
                zone_id=None,
                confidence=0.82,
                session_seq=2,
                timestamp=iso_time(base_time, 300),
            )
        )

    elif config["type"] == "BILLING":
        events.append(
            make_event(
                store_id=store_id,
                camera_id=camera_name,
                visitor_id=visitor_id,
                event_type="BILLING_QUEUE_JOIN",
                zone_id="BILLING",
                confidence=0.8,
                queue_depth=3,
                session_seq=1,
                timestamp=iso_time(base_time, 120),
            )
        )

    else:
        events.append(
            make_event(
                store_id=store_id,
                camera_id=camera_name,
                visitor_id=visitor_id,
                event_type="ZONE_ENTER",
                zone_id=config["zone_id"],
                confidence=0.78,
                sku_zone=config["sku_zone"],
                session_seq=1,
                timestamp=iso_time(base_time, 30),
            )
        )

        events.append(
            make_event(
                store_id=store_id,
                camera_id=camera_name,
                visitor_id=visitor_id,
                event_type="ZONE_DWELL",
                zone_id=config["zone_id"],
                dwell_ms=30000,
                confidence=0.76,
                sku_zone=config["sku_zone"],
                session_seq=2,
                timestamp=iso_time(base_time, 60),
            )
        )

    return events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-dir", default="data/videos")
    parser.add_argument("--output", default="data/generated_events.jsonl")
    parser.add_argument("--store-id", default="STORE_BLR_002")
    args = parser.parse_args()

    video_dir = Path(args.video_dir)
    output_path = Path(args.output)

    all_events = []

    for video_path in sorted(video_dir.glob("*.mp4")):
        all_events.extend(generate_events_for_camera(video_path, args.store_id))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for event in all_events:
            f.write(json.dumps(event) + "\n")

    print(f"Generated {len(all_events)} events")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()