# config.py
from enum import Enum

# ==========================================
# 1. SYSTEM STATES (The Logic)
# ==========================================
class MissionState(Enum):
    """
    Using Enum prevents typo bugs. 
    In code, use: cfg.MissionState.SCAN_OCR
    """
    SCAN_OCR    = 1  # Phase 1: Read Letter
    SCAN_CLASS  = 2  # Phase 2: Read Class
    WAITING     = 3  # Phase 3: Wait for command
    SEEKING     = 4  # Moving to platform
    ENGAGING    = 5  # Locking and firing
    RETURNING   = 6  # Going back to home

# ==========================================
# 2. HARDWARE SETTINGS (The "Muscles")
# ==========================================
TURRET = {
    "DEADZONE": 5,             # Pixels
    "PRECISION_RADIUS": 40,    # Pixels (Size of the Crosshair/Lock Ring)
    
    # --- CRITICAL FIXES FOR CRASH ---
    "LOCK_FRAMES": 5,          # Code looks for this exact key
    "HOME_ANGLE": 0,           # Code looks for this exact key
    # --------------------------------
    
    "LOCK_FRAME_THRESH": 5,    # (Backup/Alternative)
    "PRECISION_COUNTDOWN": 3,  # Seconds
    
    # Angles (0 is center, -90 is left, +90 is right)
    "ANGLES": {
        "A": -45.0,
        "B": 45.0,
        "HOME": 0.0
    },
    
    # Safety Limits
    "NO_FIRE": {
        "LEFT_LIMIT": -90.0,
        "RIGHT_LIMIT": 90.0
    }
}

# --- ALIAS FOR CODE COMPATIBILITY ---
# The code expects "PLATFORM_ANGLES" to be available directly
PLATFORM_ANGLES = TURRET["ANGLES"]

# ==========================================
# 3. VISION SETTINGS (The "Eyes")
# ==========================================
VISION = {
    "MODEL_PATH": "balloons.pt",
    "MEMORY_MODEL_PATH": "shapes-colors.pt",
    "CONF_NORMAL": 0.6,
    "CONF_MEMORY": 0.9,
}

# ==========================================
# 4. UI & VISUALS (The "Skin")
# ==========================================
COLORS = {
    "UI_CYAN": "#00ffff",
    "BG": "#080808",
    "PANEL": "#111",
    "TEXT_GREEN": (0, 255, 0),
    "TEXT_RED": (0, 0, 255),
}

# Maps YOLO ID to (Label, Color_BGR)
# Standard Mode
CLASS_MAP = {
    0: ("dost",   (0, 255, 0)), 
    1: ("dusman", (0, 0, 255))
}

# Memory Mode
MEMORY_CLASS_MAP = {
    0: ("red_circle",     (0, 0, 255)),
    1: ("green_circle",   (0, 255, 0)),
    2: ("blue_circle",    (255, 0, 0)),
    3: ("red_triangle",   (0, 0, 200)),
    4: ("green_triangle", (0, 200, 0)),
    5: ("blue_triangle",  (200, 0, 0)),
    6: ("red_square",     (0, 0, 150)),
    7: ("green_square",   (0, 150, 0)),
    8: ("blue_square",    (150, 0, 0)),
}