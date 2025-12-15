import cv2
import time
from ultralytics import YOLO

# Load trained YOLOv8 model
model = YOLO("best.pt")  # trained model path

# Class names and colors
class_info = {
    0: ("dost", (0, 255, 0)),      # green
    1: ("dusman", (255, 105, 180)) # pink
}

# Open input video
cap = cv2.VideoCapture("white-ball.mp4")
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
frame_time = 1 / fps  # target time per frame

# Output video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("output_video_tracked.mp4", fourcc, fps, (width, height))

while True:
    start_time = time.time()
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO inference
    results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)[0]

    for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
        x1, y1, x2, y2 = map(int, box)
        cls_idx = int(cls)
        cls_name, color = class_info.get(cls_idx, ("unknown", (255, 255, 255)))

        # Draw bounding box and center point
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)

        # Draw label
        label = f"{cls_name} Conf:{conf:.2f}"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Print detection
        print(f"Detected: {cls_name} with confidence {conf:.2f}")

    out.write(frame)
    cv2.imshow("YOLO Detection", frame)

    # Wait to match video FPS
    elapsed = time.time() - start_time
    wait_ms = max(int((frame_time - elapsed) * 1000), 1)  # in milliseconds
    if cv2.waitKey(wait_ms) & 0xFF == 27:  # ESC to exit
        break

cap.release()
out.release()
cv2.destroyAllWindows()
