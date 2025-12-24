# vision.py
import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import easyocr
import config as cfg

class VisionEngine:
    def __init__(self):
        self.model = YOLO(cfg.MODEL_PATH)
        self.tracker = DeepSort(max_age=30, n_init=3)
        # Initialize EasyOCR
        self.reader = easyocr.Reader(['en'], gpu=True) 

    def process_frame(self, frame):
        """ Standard YOLO + DeepSort Pipeline """
        results = self.model.predict(frame, conf=cfg.CONF_THRESHOLD, verbose=False)[0]
        raw_dets = []
        for b, c, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
            x1, y1, x2, y2 = map(int, b[:4])
            w, h = x2 - x1, y2 - y1
            conf = float(c)
            det_class_name = cfg.CLASS_MAP.get(int(cls), ("unk", (0,0,0)))[0]
            raw_dets.append(([x1, y1, w, h], conf, det_class_name))
        return self.tracker.update_tracks(raw_dets, frame=frame)

    def scan_for_letter(self, frame):
        """ 
        Runs OCR on the center of the frame.
        Returns 'A', 'B' (for Middle).
        """
        h, w, _ = frame.shape
        # Crop center 40%
        roi = frame[int(h*0.3):int(h*0.7), int(w*0.3):int(w*0.7)]
        
        try:
            # Allowlist letters
            results = self.reader.readtext(roi, allowlist='AB', detail=0)
            for text in results:
                clean = text.strip().upper()
                if clean in ["A", "B"]:
                    return clean
        except Exception:
            pass
        return None