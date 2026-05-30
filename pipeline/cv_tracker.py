from pathlib import Path
from pipeline.tracker import VisitorTracker

import cv2
from ultralytics import YOLO


model = YOLO("yolov8n.pt")
visitor_tracker = VisitorTracker()

video = Path(r"D:\store-intelligence\data\Videos\CAM 1.mp4")

cap = cv2.VideoCapture(str(video))

frames = 0

while frames < 30:
    ok, frame = cap.read()

    if not ok:
        break

    results = model.track(
        frame,
        persist=True,
        verbose=False,
    )

    for result in results:
        if result.boxes.id is None:
            continue

        track_ids = result.boxes.id.int().cpu().tolist()

        visitor_ids = [
            visitor_tracker.get_visitor_id(track_id)
            for track_id in track_ids
        ]
        
        print("Frame", frames, "Visitors:", visitor_ids)

    frames += 1

cap.release()