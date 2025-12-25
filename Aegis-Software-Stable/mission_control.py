# mission_control.py
import cv2
import config as cfg
from vision import VisionEngine
from turret import TurretController
from modes import StandardMode, MemoryMode

class MissionControl:
    def __init__(self, root, ui_class):
        self.root = root
        
        # --- Subsystems ---
        self.ui = ui_class(root, self) 
        self.turret = TurretController(log_callback=self.ui.log_message)
        self.vision = VisionEngine()
        
        # --- Hardware ---
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.w, self.h = 1280, 720
        self.center = (640, 360)

        # --- Shared State ---
        self.lock_count = 0
        self.current_status = "SCANNING"
        self.active_target_xy = None # (x, y) coordinates of locked target
        
        # --- Mode State ---
        self.sticky_id = None # Used by StandardMode
        
        self.mem_state = cfg.MissionState.SCAN_OCR
        self.mem_platform = None
        self.mem_class = None
        self.mem_ocr_counter = 0

        # --- Modes ---
        self.modes = {
            "STANDARD": StandardMode(self),
            "MEMORY": MemoryMode(self)
        }

        self._bind_keys()
        self.ui.log_message("SYSTEM: ONLINE")
        self.update_loop()

    def _bind_keys(self):
        for key in ['w', 'W', '<Up>']: self.root.bind(key, lambda e: self.joy_cmd("UP"))
        for key in ['s', 'S', '<Down>']: self.root.bind(key, lambda e: self.joy_cmd("DOWN"))
        for key in ['a', 'A', '<Left>']: self.root.bind(key, lambda e: self.joy_cmd("LEFT"))
        for key in ['d', 'D', '<Right>']: self.root.bind(key, lambda e: self.joy_cmd("RIGHT"))
        self.root.bind('<space>', lambda e: self.manual_fire())

    # --- UI COMMANDS ---
    def joy_cmd(self, direction):
        if self.ui.mode_var.get() == "MANUAL":
            self.turret.manual_move(direction)
            self.ui.log_message(f"MANUAL: {direction}")

    def manual_fire(self):
        if self.ui.mode_var.get() == "MANUAL":
            self.turret.discharge(self.center, self.center, is_manual=True)

    def execute_memory_mission(self):
        if self.ui.mode_var.get() != "MEMORY": return
        if self.mem_state == cfg.MissionState.WAITING:
            self.mem_state = cfg.MissionState.SEEKING
            self.ui.log_message("MISSION START")

    def return_home(self):
        if self.turret.pan_to_angle(cfg.TURRET["HOME_ANGLE"]):
            self.ui.log_message("TURRET: AT HOME")
        else:
            self.mem_state = cfg.MissionState.RETURNING

    def reset_system(self):
        """Called when UI mode changes."""
        self.sticky_id = None
        self.reset_memory_state()
        self.ui.log_message(f"MODE CHANGED: {self.ui.mode_var.get()}")

    def reset_memory_state(self):
        self.mem_state = cfg.MissionState.SCAN_OCR
        self.mem_platform = None
        self.mem_class = None
        self.mem_ocr_counter = 0

    # --- MAIN LOOP ---
    def update_loop(self):
        ret, frame = self.cap.read()
        if not ret: return
        
        # 1. Resize/Pre-process
        if frame.shape[1] != self.w:
            frame = cv2.resize(frame, (self.w, self.h))

        # 2. Reset Per-Frame State
        self.current_status = "SCANNING"
        self.active_target_xy = None
        mode_str = self.ui.mode_var.get()

        # 3. Delegate Logic
        if mode_str == "MEMORY":
            self.modes["MEMORY"].tick(frame)
        else:
            self.modes["STANDARD"].tick(frame)

        # 4. Global Fire Control & HUD
        self._handle_global_fire()
        self._draw_hud(frame)

        # 5. Update UI
        self.ui.update_angle_display(self.turret.get_current_angle())
        self.ui.update_video_panel(frame)
        
        self.root.after(10, self.update_loop)

    def _handle_global_fire(self):
        """Checks if we are locked on a target (Standard or Memory) and fires."""
        if not self.active_target_xy:
            self.lock_count = 0
            return

        tx, ty = self.active_target_xy
        cx, cy = self.center
        dist = ((tx - cx)**2 + (ty - cy)**2)**0.5
        
        # Fire Condition: Inside Radius AND Turret is safe
        if dist < cfg.TURRET["PRECISION_RADIUS"] and self.turret.is_angle_safe():
            self.lock_count += 1
            self.current_status = "LOCKED"
            
            if self.lock_count >= cfg.TURRET["LOCK_FRAMES"]:
                self.turret.discharge(self.active_target_xy, self.center, is_manual=False)
                self.ui.log_message("AUTO: SPLASH")
                self.lock_count = 0
        else:
            self.lock_count = 0

    def _draw_hud(self, frame):
        # Crosshair
        cv2.circle(frame, self.center, cfg.TURRET["PRECISION_RADIUS"], (255,255,255), 1)
        
        # Lock Ring Animation
        if self.lock_count > 0:
            pct = min(self.lock_count / cfg.TURRET["LOCK_FRAMES"], 1.0)
            cv2.ellipse(frame, self.center, (cfg.TURRET["PRECISION_RADIUS"]+4, cfg.TURRET["PRECISION_RADIUS"]+4), 
                       0, -90, -90 + int(pct*360), (0,255,0), 2)

        # Status Text
        status_colors = {
            "SCANNING": (0, 255, 255), "TRACKING": (255, 165, 0),
            "LOCKED": (0, 255, 0), "MANUAL": (250, 0, 250)
        }
        color = status_colors.get(self.current_status, (255, 255, 255))
        cv2.putText(frame, f"AEGIS: {self.current_status}", (20, 45), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.9, color, 1)