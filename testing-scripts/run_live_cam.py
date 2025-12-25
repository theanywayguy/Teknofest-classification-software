import cv2
from ultralytics import YOLO

# --- CONFIGURATION ---
MODEL_BALLOONS = "balloons.pt"   # Renamed from best.pt for clarity
MODEL_SHAPES   = "shapes-colors.pt"

# Class Maps
MAP_BALLOONS = {
    0: ("dost",   (0, 255, 0)),    # Green
    1: ("dusman", (255, 105, 180)) # Pink
}

MAP_SHAPES = {
    0: ("red_circle",     (0, 0, 255)),
    1: ("green_circle",   (0, 255, 0)),
    2: ("blue_circle",    (255, 0, 0)),
    3: ("red_triangle",   (0, 0, 200)),
    4: ("green_triangle", (0, 200, 0)),
    5: ("blue_triangle",  (200, 0, 0)),
    6: ("red_square",     (0, 0, 150)),
    7: ("green_square",   (0, 150, 0)),
    8: ("blue_square",    (150, 0, 0)),
}

def main():
    print("LOADING MODELS...")
    # Pre-load both models to avoid lag when switching
    model_b = YOLO(MODEL_BALLOONS)
    model_s = YOLO(MODEL_SHAPES)
    
    # State
    use_balloons = False # Default to Shapes
    current_model = model_s
    current_map = MAP_SHAPES
    mode_name = "SHAPES"

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(3, 1280)
    cap.set(4, 720)

    print("SYSTEM READY.")
    print("Press 'A' to toggle models (Balloons <-> Shapes)")
    print("Press 'ESC' to quit")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Inference
        results = current_model.predict(frame, imgsz=640, conf=0.5, verbose=False)[0]

        # Draw
        for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
            x1, y1, x2, y2 = map(int, box)
            c_id = int(cls)
            label, color = current_map.get(c_id, ("Unknown", (255,255,255)))

            # Box & Label
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # UI Overlay
        cv2.putText(frame, f"MODE: {mode_name}", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Live Inference", frame)

        # Controls
        key = cv2.waitKey(1) & 0xFF
        if key == 27: # ESC
            break
        elif key == ord('a') or key == ord('A'):
            use_balloons = not use_balloons
            if use_balloons:
                current_model = model_b
                current_map = MAP_BALLOONS
                mode_name = "BALLOONS"
            else:
                current_model = model_s
                current_map = MAP_SHAPES
                mode_name = "SHAPES"
            print(f"SWITCHED TO: {mode_name}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()