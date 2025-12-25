import cv2
import config as cfg

class BaseMission:
    def __init__(self, controller):
        self.ctrl = controller # Access to vision, turret, ui
    
    def tick(self, frame):
        pass

class StandardMode(BaseMission):
    """
    Handles:
    1. 'ALL' (Track everything)
    2. 'RED/BLUE' (Team filtering)
    3. 'CHERRY-PICK' (Specific target locking)
    4. 'MANUAL' (Passive tracking)
    """
    def tick(self, frame):
        mode = self.ctrl.ui.mode_var.get()
        vision = self.ctrl.vision
        
        # --- 1. AI INFERENCE ---
        tracks = vision.process_frame(frame, use_memory_model=False)

        # Helper: ID Formatting
        def fmt_id(t):
            c_id = int(getattr(t, 'det_class', -1))
            data = cfg.CLASS_MAP.get(c_id, (str(c_id), (200, 200, 200)))
            return f"{data[0]}_{t.track_id}"

        # Helper: Get Distance to Crosshair
        def get_dist(t):
            l, t_y, r, b = map(int, t.to_ltrb())
            cx, cy = (l + r) // 2, (t_y + b) // 2
            # Euclidean distance to center screen
            return ((cx - self.ctrl.center[0])**2 + (cy - self.ctrl.center[1])**2)**0.5

        # --- 2. UPDATE DROPDOWN ---
        visible_ids = [fmt_id(t) for t in tracks if t.is_confirmed()]
        self.ctrl.ui.update_target_options(["None"] + visible_ids)

        # --- 3. FILTER CANDIDATES ---
        candidates = []
        current_target_track = None # To store our current lock object if found

        for t in tracks:
            if not t.is_confirmed(): continue
            fid = fmt_id(t)
            
            # Check if this track is our currently locked target
            if fid == self.ctrl.sticky_id:
                current_target_track = t

            is_match = False
            if mode == "ALL": is_match = True
            elif mode == "RED (Dusman)" and "dusman" in fid: is_match = True
            elif mode == "BLUE (Dost)" and "dost" in fid: is_match = True
            
            if is_match: candidates.append(t)

        # --- 4. TARGET SELECTION LOGIC (With Hysteresis) ---
        if mode == "CHERRY-PICK":
            # (Same as before: manual force)
            selection = self.ctrl.ui.target_var.get()
            if selection != "None" and selection in visible_ids:
                self.ctrl.sticky_id = selection
            elif self.ctrl.sticky_id not in visible_ids:
                self.ctrl.sticky_id = None

        elif mode != "MANUAL":
            if not candidates:
                self.ctrl.sticky_id = None
            else:
                # Sort all candidates by distance to center
                candidates.sort(key=get_dist)
                best_candidate = candidates[0]
                best_dist = get_dist(best_candidate)

                # LOGIC:
                # 1. If we have no current lock, take the closest one.
                # 2. If we HAVE a lock, only switch if the new guy is MUCH closer (hysteresis).
                
                if current_target_track is None:
                    # Current target lost or never existed -> Pick the new best
                    self.ctrl.sticky_id = fmt_id(best_candidate)
                else:
                    # We have a current target. How far is it?
                    current_dist = get_dist(current_target_track)
                    
                    # HYSTERESIS THRESHOLD:
                    # Only switch if the new target is 50 pixels closer than the current one
                    # This prevents jitter when two targets are side-by-side.
                    if best_dist < (current_dist - 50): 
                        self.ctrl.sticky_id = fmt_id(best_candidate)
                        # self.ctrl.ui.log_message(f"Switched to closer target: {self.ctrl.sticky_id}")

        # --- 5. VISUALIZATION ---
        for t in tracks:
            if not t.is_confirmed(): continue
            
            fid = fmt_id(t)
            c_id = int(getattr(t, 'det_class', -1))
            _, color = cfg.CLASS_MAP.get(c_id, ("unk", (100, 100, 100)))
            
            l, t_y, r, b = map(int, t.to_ltrb())
            cx, cy = (l + r) // 2, (t_y + b) // 2
            
            # Visual 1: Dot
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1) 

            is_active_target = (mode != "MANUAL" and fid == self.ctrl.sticky_id)
            
            if is_active_target:
                self.ctrl.current_status = "TRACKING"
                self.ctrl.active_target_xy = (cx, cy)
                self.ctrl.turret.calculate_motor_adjustments(cx, cy, self.ctrl.center)
                
                # Visual 2: Line
                cv2.line(frame, self.ctrl.center, (cx, cy), (0, 255, 255), 2)
                # Visual 3: Box
                cv2.rectangle(frame, (l, t_y), (r, b), (0, 255, 0), 2)
                cv2.putText(frame, f"LOCK: {fid}", (l, t_y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                dist = get_dist(t)
                cv2.putText(frame, f"ERR: {int(dist)}px", (l, b + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            else:
                cv2.rectangle(frame, (l, t_y), (r, b), color, 1)
                cv2.putText(frame, fid, (l, t_y - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        if mode == "MANUAL":
            self.ctrl.current_status = "MANUAL"
            self.ctrl.sticky_id = None

class MemoryMode(BaseMission):
    """
    Handles the Mission Lifecycle:
    Scan OCR -> Select Shape -> Seek Platform -> Engage -> Return Home
    """
    def tick(self, frame):
        state = self.ctrl.mem_state
        
        # --- PHASE 1: OCR SCANNING ---
        if state == cfg.MissionState.SCAN_OCR:
            # Draw ROI (Where to look)
            cv2.rectangle(frame, (400, 200), (880, 520), (255, 0, 255), 2)
            cv2.putText(frame, "SCANNING PLATFORM ID...", (420, 180),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            
            letter = self.ctrl.vision.scan_for_letter(frame)
            if letter:
                self.ctrl.mem_ocr_counter += 1
                # Visual Feedback: Show what we see
                cv2.putText(frame, f"DETECTED: {letter}", (420, 550),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Progress Bar for Lock
                bar_width = int((self.ctrl.mem_ocr_counter / cfg.TURRET["LOCK_FRAMES"]) * 480)
                cv2.rectangle(frame, (400, 560), (400 + bar_width, 570), (0, 255, 0), -1)

                if self.ctrl.mem_ocr_counter >= cfg.TURRET["LOCK_FRAMES"]:
                    self.ctrl.mem_platform = letter
                    self.ctrl.mem_state = cfg.MissionState.SCAN_CLASS
                    self.ctrl.mem_ocr_counter = 0
                    self.ctrl.ui.target_var.set("None") # Reset UI dropdown
                    self.ctrl.ui.log_message(f"MEM: PLATFORM {letter} LOCKED")
            else:
                self.ctrl.mem_ocr_counter = 0

        # --- PHASE 2: CLASS SELECTION ---
        elif state == cfg.MissionState.SCAN_CLASS:
            cv2.putText(frame, "SELECT TARGET SHAPE IN DROPDOWN", (350, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
            
            tracks = self.ctrl.vision.process_frame(frame, use_memory_model=True)
            dropdown_map = {} 
            dropdown_list = []
            
            for t in tracks:
                if not t.is_confirmed(): continue
                c_id = getattr(t, 'det_class', -1)
                name, color = cfg.MEMORY_CLASS_MAP.get(c_id, ("Unknown", (255,255,255)))
                
                unique_id = f"{name}_{t.track_id}"
                dropdown_list.append(unique_id)
                dropdown_map[unique_id] = name
                
                # --- VISUALS ---
                l, t_y, r, b = map(int, t.to_ltrb())
                cx, cy = (l + r) // 2, (t_y + b) // 2

                # 1. Center Dot
                cv2.circle(frame, (cx, cy), 4, color, -1)
                # 2. Bounding Box
                cv2.rectangle(frame, (l, t_y), (r, b), color, 2)
                # 3. Label
                cv2.putText(frame, unique_id, (l, t_y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Update UI
            self.ctrl.ui.update_target_options(["None"] + dropdown_list)
            
            # Check User Selection
            user_pick = self.ctrl.ui.target_var.get()
            if user_pick != "None" and user_pick in dropdown_map:
                self.ctrl.mem_class = dropdown_map[user_pick]
                self.ctrl.mem_state = cfg.MissionState.WAITING
                self.ctrl.ui.log_message(f"MEM: TARGET '{self.ctrl.mem_class}' LOCKED")
                self.ctrl.ui.target_var.set("None") # clear dropdown

        # --- PHASE 3: SEEKING PLATFORM ---
        elif state == cfg.MissionState.SEEKING:
            cv2.putText(frame, f"MOVING TO PLATFORM {self.ctrl.mem_platform}...", (380, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            
            # Big Arrow Direction Indicator
            # (Simple visual to show the user the turret is busy moving)
            cv2.arrowedLine(frame, (640, 360), (640, 300), (0, 255, 255), 3)

            target_ang = cfg.PLATFORM_ANGLES.get(self.ctrl.mem_platform, 0.0)
            if self.ctrl.turret.pan_to_angle(target_ang):
                self.ctrl.mem_state = cfg.MissionState.ENGAGING
                self.ctrl.ui.log_message("MEM: ARRIVED. ENGAGING.")

        # --- PHASE 4: ENGAGING TARGET ---
        elif state == cfg.MissionState.ENGAGING:
            cv2.putText(frame, f"HUNTING: {self.ctrl.mem_class}", (20, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            tracks = self.ctrl.vision.process_frame(frame, use_memory_model=True)
            found = False
            
            for t in tracks:
                if not t.is_confirmed(): continue
                c_id = getattr(t, 'det_class', -1)
                name, color = cfg.MEMORY_CLASS_MAP.get(c_id, (None, None))
                
                l, t_y, r, b = map(int, t.to_ltrb())
                cx, cy = (l + r) // 2, (t_y + b) // 2
                
                # --- VISUALS (Always draw what we see) ---
                cv2.circle(frame, (cx, cy), 4, color, -1)
                
                # Is this THE target?
                if name == self.ctrl.mem_class:
                    found = True
                    # Set Global Target for Firing Logic (handled in MissionControl)
                    self.ctrl.active_target_xy = (cx, cy)
                    self.ctrl.current_status = "LOCKED"
                    
                    # Move Turret
                    self.ctrl.turret.calculate_motor_adjustments(cx, cy, self.ctrl.center)
                    
                    # --- ACTIVE VISUALS ---
                    # 1. Bold Box
                    cv2.rectangle(frame, (l, t_y), (r, b), color, 3)
                    # 2. Target Line
                    cv2.line(frame, self.ctrl.center, (cx, cy), (0, 255, 255), 2)
                    # 3. Text
                    cv2.putText(frame, "ENGAGING", (l, t_y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    break 
                else:
                    # Passive visual for wrong targets
                    cv2.rectangle(frame, (l, t_y), (r, b), (100, 100, 100), 1)
            
            if not found:
                self.ctrl.lock_count = 0

        # --- PHASE 5: RETURNING HOME ---
        elif state == cfg.MissionState.RETURNING:
            cv2.putText(frame, "MISSION COMPLETE - RETURNING HOME", (350, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            if self.ctrl.turret.pan_to_angle(cfg.TURRET["HOME_ANGLE"]):
                self.ctrl.reset_memory_state()
                self.ctrl.ui.log_message("MEM: RESET FOR NEXT MISSION")

        # --- PHASE 6: WAITING ---
        elif state == cfg.MissionState.WAITING:
             cv2.putText(frame, "MISSION READY - PRESS EXECUTE", (380, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
             
             # Summary Box
             cv2.rectangle(frame, (400, 300), (880, 420), (50, 50, 50), -1)
             cv2.putText(frame, f"PLATFORM: {self.ctrl.mem_platform}", (420, 340), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
             cv2.putText(frame, f"TARGET:   {self.ctrl.mem_class}", (420, 380), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        # Update UI Panel Labels
        self.ctrl.ui.update_memory_display(state, self.ctrl.mem_platform, self.ctrl.mem_class)