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
        
        # Binds
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
            # FIX 1: Actually move the turret logic
            self.turret.manual_move(direction)
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
            
            # Reset UI dropdown to clean state
            self.ui.update_target_options(["None"])
            self.ui.target_var.set("None")
        
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
        
        aim_coords = self.center
        self.turret.discharge(aim_coords, self.center, is_manual=True)

    # ---------------- MEMORY MODE LOGIC ----------------
    def _handle_memory_mode(self, frame):
        """Process memory mode: OCR -> Manual Shape Select -> Seek -> Engage."""
        
        # ---------------- PHASE 1: SCAN PLATFORM OCR ----------------
        if self.mem_state == cfg.MEM_SCAN_OCR:
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
                    
                    # Clear previous selection to force user to pick new
                    self.ui.target_var.set("None")
                    self.ui.log_message(f"MEM: PLATFORM {letter} LOCKED. SELECT TARGET SHAPE.")
            else:
                self.mem_ocr_counter = 0

        # ---------------- PHASE 2: SELECT TARGET CLASS (UPDATED) ----------------
        elif self.mem_state == cfg.MEM_SCAN_CLASS:
            cv2.putText(frame, "SELECT TARGET FROM DROPDOWN", (350, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2, cv2.LINE_AA)
            
            # 1. Run Detection
            tracks = self.vision.process_frame(frame, use_memory_model=True)
            
            # 2. Build List for Dropdown (e.g., "Triangle_1", "Square_2")
            dropdown_items = []
            valid_map = {} # Map "Triangle_1" back to class name "Triangle"

            for t in tracks:
                if not t.is_confirmed(): continue
                
                # Get ID from model (int) and map to Name (str)
                det_class_id = getattr(t, 'det_class', None)
                if det_class_id is None: continue
                
                det_name, color = cfg.MEMORY_CLASS_MAP.get(det_class_id, ("Unknown", (255,255,255)))
                
                # Create unique ID for the dropdown
                unique_id = f"{det_name}_{t.track_id}"
                dropdown_items.append(unique_id)
                valid_map[unique_id] = det_name

                # Visuals for what is seen
                x1, y1, x2, y2 = map(int, t.to_ltrb())
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, unique_id, (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

            # 3. Update Dropdown in UI
            self.ui.update_target_options(["None"] + dropdown_items)

            # 4. Check User Selection
            user_choice = self.ui.target_var.get()
            
            if user_choice != "None" and user_choice in valid_map:
                # USER PICKED SOMETHING
                selected_class_name = valid_map[user_choice]
                
                self.mem_class = selected_class_name
                self.mem_state = cfg.MEM_WAITING
                self.ui.log_message(f"MEM: TARGET CLASS '{selected_class_name.upper()}' SELECTED")
                
                # Optional: Clear dropdown so it doesn't look like we are still tracking that specific ID
                self.ui.target_var.set("None")

        # ---------------- PHASE 3: SEEK PLATFORM ----------------
        elif self.mem_state == cfg.MEM_SEEKING:
            cv2.putText(frame, f"SEEKING PLATFORM {self.mem_platform}...", (420, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2, cv2.LINE_AA)
            target_angle = cfg.PLATFORM_ANGLES.get(self.mem_platform, 0.0)
            if self.turret.pan_to_angle(target_angle):
                self.mem_state = cfg.MEM_ENGAGING
                self.ui.log_message("MEM: ARRIVED AT PLATFORM")

        # ---------------- PHASE 4: ENGAGE TARGET ----------------
        elif self.mem_state == cfg.MEM_ENGAGING:
            cv2.putText(frame, f"ENGAGING {self.mem_class.upper()}...", (420, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
            
            tracks = self.vision.process_frame(frame, use_memory_model=True)
            found_target = False
            
            for t in tracks:
                if not t.is_confirmed(): continue
                
                det_class_id = getattr(t, 'det_class', None)
                if det_class_id is None: continue
                
                det_name, color = cfg.MEMORY_CLASS_MAP.get(det_class_id, (None, None))
                
                # ONLY engage if name matches the one we selected in Phase 2
                if det_name != self.mem_class:
                    continue
                
                found_target = True
                x1, y1, x2, y2 = map(int, t.to_ltrb())
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                cv2.line(frame, self.center, (cx, cy), (0, 255, 255), 2)
                cv2.circle(frame, (cx, cy), 5, color, -1)
                
                self.turret.calculate_motor_adjustments(cx, cy, self.center)
                dist = ((cx - self.center[0])**2 + (cy - self.center[1])**2)**0.5
                
                # FIX 3: Charging logic for Memory Mode
                if dist < cfg.PRECISION_RADIUS and self.turret.is_angle_safe():
                    self.lock_count += 1
                    if self.lock_count >= cfg.LOCK_FRAME_THRESHOLD:
                        self.turret.discharge((cx, cy), self.center, is_manual=False)
                        self.ui.log_message("MEM: TARGET ELIMINATED")
                        self.lock_count = 0 
                else:
                    self.lock_count = 0
                break
            
            if not found_target:
                self.lock_count = 0

        # ---------------- PHASE 5: RETURN HOME ----------------
        elif self.mem_state == cfg.MEM_RETURNING:
            cv2.putText(frame, "RETURNING HOME...", (420, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            if self.turret.pan_to_angle(cfg.PLATFORM_ANGLES["HOME"]):
                self.mem_state = cfg.MEM_SCAN_OCR
                self.mem_platform = None
                self.mem_class = None
                self.ui.log_message("MEM: HOME - READY FOR NEW MISSION")

        # ---------------- PHASE 6: WAITING ----------------
        elif self.mem_state == cfg.MEM_WAITING:
            cv2.putText(frame, "MISSION READY", (420, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Platform: {self.mem_platform} | Target: {self.mem_class.upper()}",
                        (420, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, "Press EXECUTE MISSION to begin", (420, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


    def update_loop(self):
        ret, frame = self.cap.read()
        if not ret: return

        frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_LINEAR)
        self.w, self.h = 1280, 720
        self.center = (640, 360) 

        mode = self.ui.mode_var.get()

        if mode == "MEMORY":
            self._handle_memory_mode(frame)
            self.ui.update_memory_display(self.mem_state, self.mem_platform, self.mem_class)
        else:
            self._handle_standard_modes(frame, mode)

        # FIX 2: GLOBAL HUD (Crosshair & Lock Ring)
        # This now runs for BOTH Memory Mode and Standard Mode
        cv2.circle(frame, self.center, cfg.PRECISION_RADIUS, (255,255,255), 1)
        if self.lock_count > 0:
            pct = min(self.lock_count/cfg.LOCK_FRAME_THRESHOLD, 1.0)
            cv2.ellipse(frame, self.center, (cfg.PRECISION_RADIUS+4, cfg.PRECISION_RADIUS+4), 
                        0, -90, -90 + int(pct*360), (0,255,0), 2)

        self.ui.update_angle_display(self.turret.get_current_angle())
        self.ui.update_video_panel(frame)
        self.root.after(10, self.update_loop)

    def _handle_standard_modes(self, frame, mode):
        # --- AI INFERENCE & TRACKING ---
        tracks = self.vision.process_frame(frame)
        
        # Helper to get name from ID (e.g., 0 -> "dost")
        def get_id_name(t):
            c_id = int(getattr(t, 'det_class', -1))
            # Look up name in config, default to raw ID if not found
            c_name = cfg.CLASS_MAP.get(c_id, (str(c_id), None))[0]
            return f"{c_name}_{t.track_id}"

        # 1. Update Dropdown
        current_visible_ids = [get_id_name(t) for t in tracks if t.is_confirmed()]
        self.ui.update_target_options(["None"] + current_visible_ids)

        # 2. Handle Cherry-Picking
        if mode == "CHERRY-PICK":
            selection = self.ui.target_var.get()
            if selection != "None": self.sticky_id = selection

        # 3. Filter Candidates based on Mode
        valid_candidates = []
        for t in tracks:
            if not t.is_confirmed(): continue
            
            full_id = get_id_name(t) # Use the helper!
            
            is_match = (mode == "ALL") or \
                       (mode == "RED (Dusman)" and "dusman" in full_id) or \
                       (mode == "BLUE (Dost)" and "dost" in full_id) or \
                       (mode == "CHERRY-PICK" and full_id == self.sticky_id)
            
            if is_match: valid_candidates.append(t)

        # 4. Sticky Logic (Auto-lock if sticky is lost)
        if self.sticky_id not in current_visible_ids: self.sticky_id = None

        if self.sticky_id is None and valid_candidates and mode not in ("MANUAL", "CHERRY-PICK"):
            first_valid = sorted(valid_candidates, key=lambda x: x.track_id)[0]
            self.sticky_id = get_id_name(first_valid)

        # --- DRAWING ---
        self.current_status = "SCANNING"
        self.active_cx, self.active_cy = -1, -1
        primary_track = None

        for t in tracks:
            if not t.is_confirmed(): continue
            
            full_id = get_id_name(t) # Use the helper!
            
            # Get color from map or default to gray
            c_id = int(getattr(t, 'det_class', -1))
            _, color = cfg.CLASS_MAP.get(c_id, ("unk", (100, 100, 100)))

            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # IS THIS THE TARGET?
            if mode != "MANUAL" and full_id == self.sticky_id:
                primary_track = t
                self.active_cx, self.active_cy = cx, cy
                self.current_status = "TRACKING"
                
                # Draw Lock Box (Green)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"LOCK: {full_id}", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.line(frame, self.center, (cx, cy), (0, 255, 255), 1)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
                
                self.turret.calculate_motor_adjustments(cx, cy, self.center)
                
            else:
                # Draw Standard Box (using Class Color)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
                cv2.circle(frame, (cx, cy), 2, color, -1)
                cv2.putText(frame, full_id, (x1, y1-5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        # 5. Fire Control Logic
        if mode != "MANUAL" and primary_track:
            dist = ((self.active_cx - self.center[0])**2 + (self.active_cy - self.center[1])**2)**0.5
            
            if dist <= cfg.PRECISION_RADIUS and self.turret.is_angle_safe():
                self.current_status = "LOCKED"
                self.lock_count += 1
                if self.lock_count >= cfg.LOCK_FRAME_THRESHOLD:
                    self.turret.discharge((self.active_cx, self.active_cy), self.center, is_manual=False)
                    self.lock_count = 0 
            else: self.lock_count = 0
        elif mode == "MANUAL":
            self.current_status = "MANUAL_CONTROL"

        # 6. Status Text (HUD elements moved to update_loop)
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