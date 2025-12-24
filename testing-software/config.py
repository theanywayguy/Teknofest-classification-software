# config.py

# --- MODEL & SYSTEM ---
MODEL_PATH = "best.pt"
CONF_THRESHOLD = 0.5
LOCK_FRAME_THRESHOLD = 5 
PRECISION_RADIUS = 20  
DEADZONE = 5            
PRECISION_COUNTDOWN = 3  # Countdown seconds for precision targeting

# --- COLORS ---
CLR_UI_CYAN = "#00ffff"
CLR_UI_RED = "#fc0b0b"
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
# Format: ID: ("Name", (B, G, R))
CLASS_MAP = {0: ("dost", (0, 255, 0)), 1: ("dusman", (0, 0, 255))}

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