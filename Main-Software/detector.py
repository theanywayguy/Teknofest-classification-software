from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path, conf_threshold=0.5):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        results = self.model.predict(frame, imgsz=640, conf=self.conf_threshold, verbose=False)[0]
        detections = []
        for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
            x1, y1, x2, y2 = map(int, box)
            detections.append({
                "bbox": (x1, y1, x2, y2),
                "class": int(cls),
                "conf": float(conf)
            })
        return detections
