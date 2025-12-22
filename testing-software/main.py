# main.py
import cv2
import tkinter as tk
from vision import VisionEngine
from ui import AegisUI
from turret import TurretController
import config as cfg

class AegisSystem:
    def __init__(self, root):
        self.root = root
        
        # --- Initialize Components ---
        self.ui = AegisUI(root, self) 
        self.vision = VisionEngine()
        self.turret = TurretController(log_callback=self.ui.log_message)

        # --- Camera Setup ---
        self.cap = cv2.VideoCapture(0)
        self.w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.center = (self.w // 2, self.h // 2)

        # --- State ---
        self.sticky_id = None  
        self.lock_count = 0
        self.current_status = "SCANNING"
        self.active_cx, self.active_cy = -1, -1

        self._bind_keys()
        self.update_loop()

    def _bind_keys(self):
        for key in ['w', 'W', '<Up>']: self.root.bind(key, lambda e: self.joy_cmd("UP"))
        for key in ['s', 'S', '<Down>']: self.root.bind(key, lambda e: self.joy_cmd("DOWN"))
        for key in ['a', 'A', '<Left>']: self.root.bind(key, lambda e: self.joy_cmd("LEFT"))
        for key in ['d', 'D', '<Right>']: self.root.bind(key, lambda e: self.joy_cmd("RIGHT"))
        self.root.bind('<space>', lambda e: self.manual_fire())

    def joy_cmd(self, direction):
        if self.ui.mode_var.get() == "MANUAL":
            self.ui.log_message(f"MANUAL_INPUT: {direction}")
        else:
            self.ui.log_message("BLOCK: INPUTS REJECTED IN AUTO")

    def reset_system(self):
        self.sticky_id = None
        self.lock_count = 0
        self.ui.log_message(f"SYSTEM RESET: MODE {self.ui.mode_var.get()}")

    def manual_fire(self):
        if self.ui.mode_var.get() != "MANUAL":
            self.ui.log_message("FIRE_BLOCKED: SWITCH TO MANUAL MODE")
            return
        
        # Gather current safety context
        s_l, s_r = self.ui.get_safety_limits()
        l_bound = (s_l / 100) * self.w
        r_bound = (s_r / 100) * self.w
        
        # Manual Mode: Aim point is implicitly the center
        aim_coords = self.center
        
        self.turret.discharge(aim_coords, self.center, (l_bound, r_bound), is_manual=True)

    def update_loop(self):
        ret, frame = self.cap.read()
        if not ret: return

        # --- 1. FORCE LARGE DISPLAY & SYNC COORDINATES ---
        frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_LINEAR)
        self.w, self.h = 1280, 720
        self.center = (640, 360) 

        mode = self.ui.mode_var.get()
        s_l, s_r = self.ui.get_safety_limits()
        l_bound = (s_l / 100) * self.w
        r_bound = (s_r / 100) * self.w

        # --- 2. AI INFERENCE & TRACKING ---
        tracks = self.vision.process_frame(frame)
        
        current_visible_ids = [f"{getattr(t, 'det_class', 'unk')}_{t.track_id}" for t in tracks if t.is_confirmed()]
        self.ui.update_target_options(["None"] + current_visible_ids)

        # --- 3. TARGET SELECTION LOGIC ---
        if mode == "CHERRY-PICK":
            selection = self.ui.target_var.get()
            if selection != "None": self.sticky_id = selection

        valid_candidates = []
        for t in tracks:
            if not t.is_confirmed(): continue
            full_id = f"{getattr(t, 'det_class', 'unk')}_{t.track_id}"
            is_match = (mode == "ALL") or \
                       (mode == "RED (Dusman)" and "dusman" in full_id) or \
                       (mode == "BLUE (Dost)" and "dost" in full_id) or \
                       (mode == "CHERRY-PICK" and full_id == self.sticky_id)
            if is_match: valid_candidates.append(t)

        if self.sticky_id not in current_visible_ids: self.sticky_id = None

        if self.sticky_id is None and valid_candidates and mode not in ("MANUAL", "CHERRY-PICK"):
            first_valid = sorted(valid_candidates, key=lambda x: x.track_id)[0]
            self.sticky_id = f"{getattr(first_valid, 'det_class', 'unk')}_{first_valid.track_id}"

        # --- 4. DRAWING & STATE UPDATE ---
        self.current_status = "SCANNING"
        self.active_cx, self.active_cy = -1, -1
        primary_track = None

        for t in tracks:
            if not t.is_confirmed(): continue
            full_id = f"{getattr(t, 'det_class', 'unk')}_{t.track_id}"
            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if mode != "MANUAL" and full_id == self.sticky_id:
                primary_track = t
                self.active_cx, self.active_cy = cx, cy
                self.current_status = "TRACKING"
                
                # Visuals
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"LOCK: {full_id}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.line(frame, self.center, (cx, cy), (0, 255, 255), 1)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
                
                # --- DELEGATE MOTOR LOGIC TO TURRET ---
                self.turret.calculate_motor_adjustments(cx, cy, self.center)
                
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (60, 60, 60), 1)
                cv2.circle(frame, (cx, cy), 2, (80, 80, 80), -1)
                cv2.putText(frame, full_id, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1, cv2.LINE_AA)

        # --- 5. LOCK & SAFETY LOGIC ---
        if mode != "MANUAL" and primary_track:
            # Check proximity for Visual Status only
            dist = ((self.active_cx - self.center[0])**2 + (self.active_cy - self.center[1])**2)**0.5
            
            # Logic check for Auto-Fire
            if dist <= cfg.PRECISION_RADIUS and l_bound < self.active_cx < r_bound:
                self.current_status = "LOCKED"
                self.lock_count += 1
                if self.lock_count >= cfg.LOCK_FRAME_THRESHOLD:
                    # --- DELEGATE AUTO FIRE TO TURRET ---
                    self.turret.discharge((self.active_cx, self.active_cy), self.center, (l_bound, r_bound), is_manual=False)
                    self.lock_count = 0 
            else: self.lock_count = 0
        elif mode == "MANUAL":
            self.current_status = "MANUAL_CONTROL"

        # --- 6. UI OVERLAY & DYNAMIC HUD ---
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (int(l_bound), self.h), (0,0,80), -1) 
        cv2.rectangle(overlay, (int(r_bound),0), (self.w, self.h), (0,0,80), -1) 
        frame = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0)
        
        cv2.circle(frame, self.center, cfg.PRECISION_RADIUS, (255,255,255), 1)
        if self.lock_count > 0:
            pct = min(self.lock_count/cfg.LOCK_FRAME_THRESHOLD, 1.0)
            cv2.ellipse(frame, self.center, (cfg.PRECISION_RADIUS+4, cfg.PRECISION_RADIUS+4), 0, -90, -90 + int(pct*360), (0,255,0), 2)

        # Dynamic Status Text
        status_colors = {
            "SCANNING": (0, 255, 255), "TRACKING": (255, 165, 0),
            "LOCKED": (0, 255, 0), "MANUAL_CONTROL": (250, 0, 250)
        }
        current_clr = status_colors.get(self.current_status, (255, 255, 255))
        
        cv2.putText(frame, f"AEGIS: {self.current_status}", (20, 45), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, current_clr, 1, cv2.LINE_AA)
        
        # --- 7. RENDER TO UI ---
        self.ui.update_video_panel(frame)
        self.root.after(10, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = AegisSystem(root)
    root.mainloop()