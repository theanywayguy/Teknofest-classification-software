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

        # --- Standard Tracking State ---
        self.sticky_id = None  
        self.lock_count = 0
        self.current_status = "SCANNING"
        self.active_cx, self.active_cy = -1, -1

        # --- Memory Mode State ---
        self.mem_state = cfg.MEM_SCAN_OCR
        self.mem_platform = None
        self.mem_class = None
        self.mem_ocr_counter = 0

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
        """Reset system when mode changes."""
        mode = self.ui.mode_var.get()
        
        # Reset standard tracking
        self.sticky_id = None
        self.lock_count = 0
        
        # Reset memory mode if switching away
        if mode != "MEMORY":
            self.mem_state = cfg.MEM_SCAN_OCR
            self.mem_platform = None
            self.mem_class = None
            self.mem_ocr_counter = 0
        
        self.ui.log_message(f"SYSTEM RESET: MODE {mode}")

    def execute_memory_mission(self):
        """Called when user presses EXECUTE MISSION button."""
        if self.ui.mode_var.get() != "MEMORY":
            self.ui.log_message("ERROR: Switch to MEMORY mode first")
            return
        
        if self.mem_state != cfg.MEM_WAITING:
            self.ui.log_message("ERROR: Mission not ready")
            return
        
        if not self.mem_platform or not self.mem_class:
            self.ui.log_message("ERROR: Incomplete mission data")
            return
        
        self.mem_state = cfg.MEM_SEEKING
        self.ui.log_message(f"MISSION START: Platform {self.mem_platform} | Target {self.mem_class}")

    def return_home(self):
        """Return turret to home position."""
        if self.turret.pan_to_angle(cfg.PLATFORM_ANGLES["HOME"]):
            self.ui.log_message("TURRET: HOME POSITION")
        else:
            self.mem_state = cfg.MEM_RETURNING
            self.ui.log_message("RETURNING TO HOME...")

    def manual_fire(self):
        if self.ui.mode_var.get() != "MANUAL":
            self.ui.log_message("FIRE_BLOCKED: SWITCH TO MANUAL MODE")
            return
        
        # Manual Mode: Aim point is implicitly the center
        aim_coords = self.center
        self.turret.discharge(aim_coords, self.center, is_manual=True)

    # ---------------- MEMORY MODE LOGIC ----------------
    def _handle_memory_mode(self, frame):
        """Process memory mode state machine."""
        if self.mem_state == cfg.MEM_SCAN_OCR:
            # Phase 1: Scan for platform letter
            cv2.rectangle(frame, (400, 200), (880, 520), (255, 0, 255), 2)
            cv2.putText(frame, "SCANNING PLATFORM ID...", (420, 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2, cv2.LINE_AA)
            
            letter = self.vision.scan_for_letter(frame)
            if letter:
                self.mem_ocr_counter += 1
                cv2.putText(frame, f"DETECTED: {letter}", (420, 550), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
                
                if self.mem_ocr_counter >= cfg.LOCK_FRAME_THRESHOLD:
                    self.mem_platform = letter
                    self.mem_state = cfg.MEM_SCAN_CLASS
                    self.mem_ocr_counter = 0
                    self.ui.log_message(f"MEM: PLATFORM {letter} LOCKED")
            else:
                self.mem_ocr_counter = 0
                
        elif self.mem_state == cfg.MEM_SCAN_CLASS:
            # Phase 2: Scan for target class
            cv2.putText(frame, "SCANNING TARGET CLASS...", (420, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2, cv2.LINE_AA)
            
            tracks = self.vision.process_frame(frame)
            for t in tracks:
                if t.is_confirmed() and getattr(t, 'det_class', '') in ["dost", "dusman"]:
                    det_class = getattr(t, 'det_class')
                    x1, y1, x2, y2 = map(int, t.to_ltrb())
                    
                    # Draw detected target
                    color = (0, 0, 255) if det_class == "dusman" else (255, 0, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                    cv2.putText(frame, f"LOCKED: {det_class.upper()}", (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
                    
                    self.mem_class = det_class
                    self.mem_state = cfg.MEM_WAITING
                    self.ui.log_message(f"MEM: TARGET {det_class.upper()} LOCKED")
                    break
                    
        elif self.mem_state == cfg.MEM_SEEKING:
            # Phase 3: Pan to platform
            cv2.putText(frame, f"SEEKING PLATFORM {self.mem_platform}...", (420, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2, cv2.LINE_AA)
            
            target_angle = cfg.PLATFORM_ANGLES.get(self.mem_platform, 0.0)
            if self.turret.pan_to_angle(target_angle):
                self.mem_state = cfg.MEM_ENGAGING
                self.ui.log_message("MEM: ARRIVED AT PLATFORM")
                
        elif self.mem_state == cfg.MEM_ENGAGING:
            # Phase 4: Engage target
            cv2.putText(frame, f"ENGAGING {self.mem_class.upper()}...", (420, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
            
            tracks = self.vision.process_frame(frame)
            for t in tracks:
                if not t.is_confirmed(): 
                    continue
                if getattr(t, 'det_class', '') == self.mem_class:
                    x1, y1, x2, y2 = map(int, t.to_ltrb())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Draw engagement visuals
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.line(frame, self.center, (cx, cy), (0, 255, 255), 2)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    
                    # Track and fire
                    self.turret.calculate_motor_adjustments(cx, cy, self.center)
                    dist = ((cx - self.center[0])**2 + (cy - self.center[1])**2)**0.5
                    
                    if dist < cfg.PRECISION_RADIUS and self.turret.is_angle_safe():
                        self.turret.discharge((cx, cy), self.center, is_manual=False)
                        self.ui.log_message("MEM: TARGET ELIMINATED")
                    break
                    
        elif self.mem_state == cfg.MEM_RETURNING:
            # Phase 5: Return to home
            cv2.putText(frame, "RETURNING HOME...", (420, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            
            if self.turret.pan_to_angle(cfg.PLATFORM_ANGLES["HOME"]):
                self.mem_state = cfg.MEM_SCAN_OCR
                self.mem_platform = None
                self.mem_class = None
                self.ui.log_message("MEM: HOME - READY FOR NEW MISSION")
                
        elif self.mem_state == cfg.MEM_WAITING:
            # Display mission details
            cv2.putText(frame, "MISSION READY", (420, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Platform: {self.mem_platform} | Target: {self.mem_class.upper()}", 
                       (420, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, "Press EXECUTE MISSION to begin", (420, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    def update_loop(self):
        ret, frame = self.cap.read()
        if not ret: return

        # --- 1. FORCE LARGE DISPLAY & SYNC COORDINATES ---
        frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_LINEAR)
        self.w, self.h = 1280, 720
        self.center = (640, 360) 

        mode = self.ui.mode_var.get()

        # --- 2. MODE ROUTING ---
        if mode == "MEMORY":
            self._handle_memory_mode(frame)
            self.ui.update_memory_display(self.mem_state, self.mem_platform, self.mem_class)
        else:
            # Standard tracking modes
            self._handle_standard_modes(frame, mode)

        # --- 3. UPDATE UI DISPLAYS ---
        self.ui.update_angle_display(self.turret.get_current_angle())
        
        # --- 4. RENDER TO UI ---
        self.ui.update_video_panel(frame)
        self.root.after(10, self.update_loop)

    def _handle_standard_modes(self, frame, mode):
        """Handle MANUAL, ALL, RED, BLUE, CHERRY-PICK modes."""
        # --- AI INFERENCE & TRACKING ---
        tracks = self.vision.process_frame(frame)
        
        current_visible_ids = [f"{getattr(t, 'det_class', 'unk')}_{t.track_id}" for t in tracks if t.is_confirmed()]
        self.ui.update_target_options(["None"] + current_visible_ids)

        # --- TARGET SELECTION LOGIC ---
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

        # --- DRAWING & STATE UPDATE ---
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

        # --- LOCK & AUTO-FIRE LOGIC ---
        if mode != "MANUAL" and primary_track:
            dist = ((self.active_cx - self.center[0])**2 + (self.active_cy - self.center[1])**2)**0.5
            
            if dist <= cfg.PRECISION_RADIUS and self.turret.is_angle_safe():
                self.current_status = "LOCKED"
                self.lock_count += 1
                if self.lock_count >= cfg.LOCK_FRAME_THRESHOLD:
                    # --- DELEGATE AUTO FIRE TO TURRET ---
                    self.turret.discharge((self.active_cx, self.active_cy), self.center, is_manual=False)
                    self.lock_count = 0 
            else: self.lock_count = 0
        elif mode == "MANUAL":
            self.current_status = "MANUAL_CONTROL"

        # --- UI OVERLAY & DYNAMIC HUD ---
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

if __name__ == "__main__":
    root = tk.Tk()
    app = AegisSystem(root)
    root.mainloop()