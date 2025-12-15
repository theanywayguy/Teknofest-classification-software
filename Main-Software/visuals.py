# visuals.py
import cv2
from classes import class_info

def draw_detections(frame, detections, fire_zone):
    fire_allowed = False
    height = frame.shape[0]

    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        cls_idx = det["class"]
        cls_name, base_color = class_info.get(cls_idx, ("unknown", (255, 255, 255)))
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # Determine firing only for foes
        if cls_name == "dusman":
            if fire_zone.in_fire_zone(cx):
                fire_allowed = True
                color = (0, 255, 0)
                status = "FIRE"
            else:
                color = (0, 0, 255)
                status = "NO FIRE"
        else:
            color = base_color
            status = cls_name.upper()

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)
        label = f"{status} | Conf:{det['conf']:.2f}"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # Draw no-fire zone overlays
    cone_px = int((fire_zone.fire_cone_deg / fire_zone.camera_fov_deg) * fire_zone.width)
    left_limit = fire_zone.center_x - cone_px
    right_limit = fire_zone.center_x + cone_px
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (left_limit, height), (0, 0, 255), -1)
    cv2.rectangle(overlay, (right_limit, 0), (fire_zone.width, height), (0, 0, 255), -1)
    frame = cv2.addWeighted(overlay, 0.25, frame, 0.75, 0)

    return frame, fire_allowed
