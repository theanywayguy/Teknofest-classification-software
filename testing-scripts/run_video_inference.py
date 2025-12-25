import cv2
import time
from ultralytics import YOLO

# --- SETTINGS ---
INPUT_FILE = "white-ball.mp4"
OUTPUT_FILE = "output_tracked.mp4"
MODEL_PATH = "balloons.pt" # Change to shapes-colors.pt if needed

CLASS_MAP = {
    0: ("dost", (0, 255, 0)),
    1: ("dusman", (255, 105, 180))
}

def main():
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(INPUT_FILE)
    
    if not cap.isOpened():
        print(f"Error: Cannot open {INPUT_FILE}")
        return

    # Video Properties
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay_ms = int(1000 / fps) if fps > 0 else 30

    # Writer
    out = cv2.VideoWriter(OUTPUT_FILE, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    print(f"Processing {INPUT_FILE} -> {OUTPUT_FILE}...")

    while True:
        start = time.time()
        ret, frame = cap.read()
        if not ret: break

        results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)[0]

        for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
            x1, y1, x2, y2 = map(int, box)
            label, color = CLASS_MAP.get(int(cls), ("unk", (255,255,255)))

            # Visuals
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Center Dot 
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)

            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        out.write(frame)
        cv2.imshow("Video Inference", frame)

        # Time Sync
        proc_time = (time.time() - start) * 1000
        wait = max(1, delay_ms - int(proc_time))
        
        if cv2.waitKey(wait) & 0xFF == 27:
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("Done.")

if __name__ == "__main__":
    main()