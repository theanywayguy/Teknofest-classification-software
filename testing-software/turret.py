# aegis_turret.py
import config as cfg

class TurretController:
    def __init__(self, log_callback):
        """
        :param log_callback: A function to send log strings to the UI console.
        """
        self.log = log_callback

    def calculate_motor_adjustments(self, target_cx, target_cy, center_xy):
        """
        Calculates offsets and logs simulated motor movements.
        """
        cx, cy = target_cx, target_cy
        center_x, center_y = center_xy
        
        dx, dy = cx - center_x, cy - center_y
        
        if abs(dx) > cfg.DEADZONE: 
            self.log(f"MOT_X: {'R' if dx > 0 else 'L'} {abs(dx)}px")
        if abs(dy) > cfg.DEADZONE: 
            self.log(f"MOT_Y: {'DN' if dy > 0 else 'UP'} {abs(dy)}px")

    def validate_safety(self, aim_coords, center_xy, safety_limits, is_manual=False):
        """
        Checks if the shot is within safety bounds and precision lock.
        :param aim_coords: (x, y) of where the turret is aiming.
        :param safety_limits: (left_boundary_x, right_boundary_x)
        """
        check_x = aim_coords[0]
        center_x, center_y = center_xy
        l_bound, r_bound = safety_limits

        # 1. Check Safety Gates (Azimuth Limits)
        if not (l_bound < check_x < r_bound):
            self.log("FIRE_BLOCKED: SAFETY_LIMIT")
            return False
        
        # 2. Check Precision Lock (if Auto)
        if not is_manual:
            dist = ((check_x - center_x)**2 + (aim_coords[1] - center_y)**2)**0.5
            if dist > cfg.PRECISION_RADIUS:
                self.log("FIRE_BLOCKED: NO_PRECISION_LOCK")
                return False
                
        return True

    def discharge(self, aim_coords, center_xy, safety_limits, is_manual=False):
        """
        Attempts to fire the weapon.
        """
        # Log the trigger pull
        if is_manual:
            self.log("TRIGGER: OPERATOR DISCHARGE")
        else:
            self.log(">>> AUTO_DISCHARGE: ENGAGED")

        # Validate
        if self.validate_safety(aim_coords, center_xy, safety_limits, is_manual):
            # If manual, we log success. If auto, the "ENGAGED" log above covers it, 
            # but usually auto-fire implies success if it reached this point.
            if is_manual:
                self.log(">>> SIGNAL: DISCHARGE_SUCCESS")
            return True
        return False