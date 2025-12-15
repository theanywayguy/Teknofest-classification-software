# main.py
import cv2
import csv
import time
from detector import YOLODetector
from firezone import FireZone
from visuals import draw_detections
from classes import class_info

MODEL_PATH = "best.pt"
CAMERA_FOV_DEG = 60.0
FIRE_CONE_DEG = 15.0
CONF_THRESHOLD = 0.5

def main():
    cap = cv2.VideoCapture(0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    detector = YOLODetector(MODEL_PATH, CONF_THRESHOLD)
    fire_zone = FireZone(width, CAMERA_FOV_DEG, FIRE_CONE_DEG)

    # CSV setup
    csv_file = open("fire_zone_dusman.csv", "w", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["timestamp", "frame", "cx", "cy", "x1", "y1", "x2", "y2", "confidence"])

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # absolute system time
        detections = detector.detect(frame)
        frame, fire_allowed = draw_detections(frame, detections, fire_zone)

        # Log "dusman" in fire zone with timestamp
        for det in detections:
            cls_idx = det["class"]
            cls_name, _ = class_info.get(cls_idx, ("unknown", (255, 255, 255)))
            if cls_name == "dusman":
                x1, y1, x2, y2 = det["bbox"]
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                if fire_zone.in_fire_zone(cx):
                    csv_writer.writerow([current_time, frame_count, cx, cy, x1, y1, x2, y2, det["conf"]])

        print("FIRE SIGNAL =", fire_allowed)
        cv2.imshow("YOLO No-Fire Zone", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    csv_file.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
