import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import easyocr
import config as cfg


class VisionEngine:
    def __init__(self):
        self.model = YOLO(cfg.MODEL_PATH)
        self.memory_model = YOLO(cfg.MEMORY_MODEL_PATH)
        self.tracker = DeepSort(max_age=20, n_init=3)
        self.reader = easyocr.Reader(['en'], gpu=True)

    def process_frame(self, frame, use_memory_model=False):
        model = self.memory_model if use_memory_model else self.model
        confidence = cfg.MEMORY_CONF_THRESHOLD if use_memory_model else cfg.CONF_THRESHOLD
        results = model.predict(frame, conf=confidence, verbose=False)[0]

        detections = []

        for box, conf, cls in zip(
            results.boxes.xyxy,
            results.boxes.conf,
            results.boxes.cls
        ):
            x1, y1, x2, y2 = map(int, box)
            w, h = x2 - x1, y2 - y1
            cls_id = int(cls)

            detections.append(([x1, y1, w, h], float(conf), cls_id))

        return self.tracker.update_tracks(detections, frame=frame)

    def scan_for_letter(self, frame):
        h, w, _ = frame.shape
        roi = frame[int(h*0.3):int(h*0.7), int(w*0.3):int(w*0.7)]

        try:
            results = self.reader.readtext(
                roi,
                allowlist="AB",
                detail=0
            )
            for txt in results:
                t = txt.strip().upper()
                if t in ("A", "B"):
                    return t
        except Exception:
            pass

        return None
