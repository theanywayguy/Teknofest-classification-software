import cv2
from ultralytics import YOLO

# Load trained YOLOv8 model
model = YOLO("best.pt")  # path to your trained YOLO model

# Class names and colors
class_info = {
    0: ("dost", (0, 255, 0)),      # green
    1: ("dusman", (255, 105, 180)) # pink
}

# Open webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO inference
    results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)[0]

    # Draw detections
    for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
        x1, y1, x2, y2 = map(int, box)
        cls_idx = int(cls)
        cls_name, color = class_info.get(cls_idx, ("unknown", (255, 255, 255)))

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        # Draw label
        label = f"{cls_name} Conf:{conf:.2f}"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Print detected class
        print(f"Detected: {cls_name} with confidence {conf:.2f}")

    cv2.imshow("YOLO Webcam Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # press Esc to exit
        break

cap.release()
cv2.destroyAllWindows()
