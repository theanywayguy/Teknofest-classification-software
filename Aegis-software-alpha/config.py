# config.py

# --- MODEL & SYSTEM ---
MODEL_PATH = "best.pt"
MEMORY_MODEL_PATH = "shapes-colors.pt"
MEMORY_CONF_THRESHOLD = 0.9
CONF_THRESHOLD=0.6
LOCK_FRAME_THRESHOLD = 5 
PRECISION_RADIUS = 20  
DEADZONE = 5            
PRECISION_COUNTDOWN = 3  # Countdown seconds for precision targeting

# --- COLORS ---
CLR_UI_CYAN = "#00ffff"
CLR_BG = "#080808"
CLR_PANEL = "#111"

# --- MEMORY MODE STATES ---
MEM_SCAN_OCR   = "SCANNING_ID"    # Phase 1: Read Letter
MEM_SCAN_CLASS = "SCANNING_TARGET" # Phase 2: Read Class
MEM_WAITING    = "MISSION_READY"   # Phase 3: Wait for command
MEM_SEEKING    = "SEEKING_PLATFORM"
MEM_ENGAGING   = "ENGAGING_TARGET"
MEM_RETURNING  = "RETURNING_HOME"

# --- DETECTION CLASSES ---
CLASS_MAP = {0: ("dost", (0, 255, 0)), 1: ("dusman", (0, 0, 255))}
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

# --- PLATFORM ANGLES (For Memory Mode) ---
# Angles are relative to center (0 is center, -90 is left, +90 is right)
PLATFORM_ANGLES = {
    "A": -45.0,     # Left
    "B": 45.0,      # Right
    "HOME": 0.0,  # Center
}

# --- SAFETY ANGLES (No-Fire Zones) ---
# Turret will not fire at these specific angles
NO_FIRE_ANGLES = {
    "LEFT_LIMIT": -90.0,
    "RIGHT_LIMIT": 90.0
}