import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import easyocr
import config as cfg

class VisionEngine:
    def __init__(self):
        # Initialize Models using new Config structure
        self.model = YOLO(cfg.VISION["MODEL_PATH"])
        self.memory_model = YOLO(cfg.VISION["MEMORY_MODEL_PATH"])
        
        # Initialize Tracker
        self.tracker = DeepSort(max_age=20, n_init=3)
        
        # Initialize OCR (Optimized for English)
        self.reader = easyocr.Reader(['en'], gpu=True)

    def process_frame(self, frame, use_memory_model=False):
        """
        Runs YOLO detection and DeepSort tracking.
        :param use_memory_model: Switch between standard (Enemy/Friend) and Memory (Shapes) models.
        """
        # Select the correct model and confidence threshold from config
        if use_memory_model:
            model = self.memory_model
            confidence = cfg.VISION["CONF_MEMORY"]
        else:
            model = self.model
            confidence = cfg.VISION["CONF_NORMAL"]

        # Run Inference
        results = model.predict(frame, conf=confidence, verbose=False)[0]

        detections = []
        
        # Parse results for DeepSort
        for box, conf, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
            x1, y1, x2, y2 = map(int, box)
            w, h = x2 - x1, y2 - y1
            cls_id = int(cls)
            
            # DeepSort expects: ([left, top, w, h], confidence, class_id)
            detections.append(([x1, y1, w, h], float(conf), cls_id))

        # Update Tracker
        return self.tracker.update_tracks(detections, frame=frame)

    def scan_for_letter(self, frame):
        """
        Scans the center of the screen for 'A' or 'B'.
        Used in Memory Mode to identify the platform.
        """
        h, w, _ = frame.shape
        
        # Crop center 40% of the screen to save processing power
        y_start, y_end = int(h * 0.3), int(h * 0.7)
        x_start, x_end = int(w * 0.3), int(w * 0.7)
        
        roi = frame[y_start:y_end, x_start:x_end]

        try:
            results = self.reader.readtext(
                roi,
                allowlist="AB", # Only look for these characters
                detail=0        # Return only text, not coordinates
            )
            
            for txt in results:
                t = txt.strip().upper()
                if t in ("A", "B"):
                    return t
                    
        except Exception as e:
            # OCR errors shouldn't crash the main loop
            print(f"OCR Error: {e}")
            pass

        return None