# aegis_vision.py
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import config as cfg

class VisionEngine:
    def __init__(self):
        self.model = YOLO(cfg.MODEL_PATH)
        self.tracker = DeepSort(max_age=30, n_init=3)

    def process_frame(self, frame):
        """
        Runs inference and tracking on the frame.
        Returns the list of tracks.
        """
        # AI INFERENCE
        results = self.model.predict(frame, conf=cfg.CONF_THRESHOLD, verbose=False)[0]
        
        # Parse detections for DeepSort
        raw_dets = []
        for b, c, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
            x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
            w, h = x2 - x1, y2 - y1
            conf = float(c)
            det_class_name = cfg.CLASS_MAP.get(int(cls), ("unk", (0,0,0)))[0]
            
            raw_dets.append(([x1, y1, w, h], conf, det_class_name))

        # TRACKING
        tracks = self.tracker.update_tracks(raw_dets, frame=frame)
        return tracks