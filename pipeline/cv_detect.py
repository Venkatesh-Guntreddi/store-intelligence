from pathlib import Path

import cv2

from ultralytics import YOLO # type: ignore


def inspect_video(video_path: str):
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    frame_count = 0
    detected_people = 0

    while frame_count < 30:
        success, frame = cap.read()
        if not success:
            break

        results = model(frame, verbose=False)

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # COCO class 0 = person
                if class_id == 0 and confidence >= 0.4:
                    detected_people += 1

        frame_count += 1

    cap.release()

    print(f"Video: {video_path}")
    print(f"Frames checked: {frame_count}")
    print(f"Person detections: {detected_people}")


if __name__ == "__main__":
    video = Path("D:/store-intelligence/data/Videos/CAM 1.mp4")
    inspect_video(str(video))