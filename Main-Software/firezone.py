class FireZone:
    def __init__(self, width, camera_fov_deg, fire_cone_deg):
        self.width = width
        self.center_x = width // 2
        self.camera_fov_deg = camera_fov_deg
        self.fire_cone_deg = fire_cone_deg

    def pixel_to_angle(self, px):
        return ((px - self.center_x) / self.width) * self.camera_fov_deg

    def in_fire_zone(self, px):
        return abs(self.pixel_to_angle(px)) <= self.fire_cone_deg
