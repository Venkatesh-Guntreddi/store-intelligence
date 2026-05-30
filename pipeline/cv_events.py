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

    first_seen = {}
    last_seen = {}
    confidence_by_visitor = {}
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
                seconds = int(frame_idx / fps)

                first_seen.setdefault(visitor_id, seconds)
                last_seen[visitor_id] = seconds
                confidence_by_visitor[visitor_id] = max(
                    confidence_by_visitor.get(visitor_id, 0),
                    float(confidence),
                )

        frame_idx += 1

    cap.release()

    events = []
    queue_depth = 0

    for seq, visitor_id in enumerate(first_seen.keys(), start=1):
        start_sec = first_seen[visitor_id]
        end_sec = last_seen[visitor_id]
        dwell_ms = max(0, int((end_sec - start_sec) * 1000))
        confidence = round(confidence_by_visitor.get(visitor_id, 0.75), 4)

        if config["type"] == "ENTRY":
            events.append(
                make_event(
                    store_id=store_id,
                    camera_id=camera_id,
                    visitor_id=visitor_id,
                    event_type="ENTRY",
                    zone_id=None,
                    dwell_ms=0,
                    is_staff=False,
                    confidence=confidence,
                    session_seq=1,
                    timestamp=iso_time(base_time, start_sec),
                )
            )

        elif config["type"] == "BILLING":
            queue_depth += 1
            events.append(
                make_event(
                    store_id=store_id,
                    camera_id=camera_id,
                    visitor_id=visitor_id,
                    event_type="BILLING_QUEUE_JOIN",
                    zone_id="BILLING",
                    dwell_ms=0,
                    is_staff=False,
                    confidence=confidence,
                    queue_depth=queue_depth,
                    session_seq=1,
                    timestamp=iso_time(base_time, start_sec),
                )
            )

        else:
            events.append(
                make_event(
                    store_id=store_id,
                    camera_id=camera_id,
                    visitor_id=visitor_id,
                    event_type="ZONE_ENTER",
                    zone_id=config["zone_id"],
                    dwell_ms=0,
                    is_staff=False,
                    confidence=confidence,
                    sku_zone=config.get("sku_zone"),
                    session_seq=1,
                    timestamp=iso_time(base_time, start_sec),
                )
            )

            if dwell_ms >= 1000:
                events.append(
                    make_event(
                        store_id=store_id,
                        camera_id=camera_id,
                        visitor_id=visitor_id,
                        event_type="ZONE_DWELL",
                        zone_id=config["zone_id"],
                        dwell_ms=dwell_ms,
                        is_staff=False,
                        confidence=confidence,
                        sku_zone=config.get("sku_zone"),
                        session_seq=2,
                        timestamp=iso_time(base_time, end_sec),
                    )
                )

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