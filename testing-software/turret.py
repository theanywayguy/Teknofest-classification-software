# turret.py
import config as cfg

class TurretController:
    def __init__(self, log_callback):
        """
        :param log_callback: A function to send log strings to the UI console.
        """
        self.log = log_callback
        self.current_angle = 0.0  # Track current turret angle
        self.target_angle = 0.0   # Target angle for memory mode
        
    def get_current_angle(self):
        """Returns the current turret angle."""
        return self.current_angle
    
    def pan_to_angle(self, target_angle):
        """
        Pans turret to specified angle (for memory mode).
        Returns True when angle is reached.
        :param target_angle: Desired angle in degrees
        """
        self.target_angle = target_angle
        angle_diff = abs(self.current_angle - target_angle)
        
        if angle_diff < 1.0:  # Within 1 degree = arrived
            self.current_angle = target_angle
            return True
        
        # Simulate gradual movement
        step = 2.0 if angle_diff > 10 else 0.5
        if self.current_angle < target_angle:
            self.current_angle = min(self.current_angle + step, target_angle)
            self.log(f"PAN_RIGHT: {self.current_angle:.1f}°")
        else:
            self.current_angle = max(self.current_angle - step, target_angle)
            self.log(f"PAN_LEFT: {self.current_angle:.1f}°")
        
        return False

    def calculate_motor_adjustments(self, target_cx, target_cy, center_xy):
        """
        Calculates offsets and logs simulated motor movements.
        Also updates current_angle based on horizontal offset.
        """
        cx, cy = target_cx, target_cy
        center_x, center_y = center_xy
        
        dx, dy = cx - center_x, cy - center_y
        
        if abs(dx) > cfg.DEADZONE: 
            # Update angle based on pixel offset (rough simulation)
            angle_change = dx * 0.05  # Scale factor
            self.current_angle += angle_change
            self.current_angle = max(-90, min(90, self.current_angle))  # Clamp
            self.log(f"MOT_X: {'R' if dx > 0 else 'L'} {abs(dx)}px | Angle: {self.current_angle:.1f}°")
        if abs(dy) > cfg.DEADZONE: 
            self.log(f"MOT_Y: {'DN' if dy > 0 else 'UP'} {abs(dy)}px")

    def is_angle_safe(self, angle=None):
        """
        Checks if current angle is safe to fire.
        Returns False if at no-fire angles.
        """
        check_angle = angle if angle is not None else self.current_angle
        
        for name, forbidden_angle in cfg.NO_FIRE_ANGLES.items():
            if abs(check_angle - forbidden_angle) < 2.0:  # Within 2 degrees
                self.log(f"FIRE_BLOCKED: AT {name} ({forbidden_angle}°)")
                return False
        return True

    def validate_safety(self, aim_coords, center_xy, is_manual=False):
        """
        Checks if the shot is safe to fire.
        :param aim_coords: (x, y) of where the turret is aiming.
        """
        check_x = aim_coords[0]
        center_x, center_y = center_xy

        # 1. Check No-Fire Angles
        if not self.is_angle_safe():
            return False
        
        # 2. Check Precision Lock (if Auto)
        if not is_manual:
            dist = ((check_x - center_x)**2 + (aim_coords[1] - center_y)**2)**0.5
            if dist > cfg.PRECISION_RADIUS:
                self.log("FIRE_BLOCKED: NO_PRECISION_LOCK")
                return False
                
        return True

    def discharge(self, aim_coords, center_xy, is_manual=False):
        """
        Attempts to fire the weapon.
        """
        # Log the trigger pull
        if is_manual:
            self.log("TRIGGER: OPERATOR DISCHARGE")
        else:
            self.log(">>> AUTO_DISCHARGE: ENGAGED")

        # Validate
        if self.validate_safety(aim_coords, center_xy, is_manual):
            if is_manual:
                self.log(">>> SIGNAL: DISCHARGE_SUCCESS")
            else:
                self.log(">>> DISCHARGE: TARGET ELIMINATED")
            return True
        return False