import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
from ultralytics import YOLO # type: ignore

from pipeline.emit import make_event
from pipeline.tracker import VisitorTracker


CAMERA_CONFIG = {
    "CAM1": {"type": "ZONE", "zone_id": "COSMETICS", "sku_zone": "SHELF"},
    "CAM2": {"type": "ZONE", "zone_id": "MAKEUP", "sku_zone": "SHELF"},
    "CAM3": {"type": "ENTRY", "zone_id": None, "sku_zone": None},
    "CAM4": {"type": "ZONE", "zone_id": "BACK_AREA", "sku_zone": None},
    "CAM5": {"type": "BILLING", "zone_id": "BILLING", "sku_zone": None},
}


def camera_id_from_path(video_path: Path) -> str:
    return video_path.stem.replace(" ", "").upper()


def iso_time(base_time: datetime, seconds: int) -> str:
    return (base_time + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def generate_cv_events(video_path: Path, store_id: str, max_frames: int = 150) -> list[dict]:
    camera_id = camera_id_from_path(video_path)
    config = CAMERA_CONFIG.get(camera_id, {"type": "ZONE", "zone_id": "UNKNOWN", "sku_zone": None})

    model = YOLO("yolov8n.pt")
    tracker = VisitorTracker()

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    base_time = datetime.now(timezone.utc)

    seen_visitors = set()
    events = []
    frame_idx = 0

    while frame_idx < max_frames:
        ok, frame = cap.read()
        if not ok:
            break

        results = model.track(frame, persist=True, verbose=False)

        for result in results:
            if result.boxes.id is None:
                continue

            track_ids = result.boxes.id.int().cpu().tolist()
            confidences = result.boxes.conf.cpu().tolist()

            for track_id, confidence in zip(track_ids, confidences):
                visitor_id = tracker.get_visitor_id(track_id)

                if visitor_id in seen_visitors:
                    continue

                seen_visitors.add(visitor_id)

                seconds = int(frame_idx / fps)

                if config["type"] == "ENTRY":
                    event_type = "ENTRY"
                    zone_id = None
                    dwell_ms = 0
                    queue_depth = None
                elif config["type"] == "BILLING":
                    event_type = "BILLING_QUEUE_JOIN"
                    zone_id = "BILLING"
                    dwell_ms = 0
                    queue_depth = len(seen_visitors)
                else:
                    event_type = "ZONE_DWELL"
                    zone_id = config["zone_id"]
                    dwell_ms = 30000
                    queue_depth = None

                events.append(
                    make_event(
                        store_id=store_id,
                        camera_id=camera_id,
                        visitor_id=visitor_id,
                        event_type=event_type,
                        zone_id=zone_id,
                        dwell_ms=dwell_ms,
                        is_staff=False,
                        confidence=round(float(confidence), 4),
                        queue_depth=queue_depth,
                        sku_zone=config.get("sku_zone"),
                        session_seq=1,
                        timestamp=iso_time(base_time, seconds),
                    )
                )

        frame_idx += 1

    cap.release()
    return events


def main():
    video_dir = Path("data/videos")
    output_path = Path("data/cv_events.jsonl")
    store_id = "STORE_BLR_002"

    all_events = []

    for video_path in sorted(video_dir.glob("*.mp4")):
        print(f"Processing {video_path}")
        all_events.extend(generate_cv_events(video_path, store_id))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for event in all_events:
            f.write(json.dumps(event) + "\n")

    print(f"Generated {len(all_events)} CV events")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()