import cv2
import numpy as np
from turret import TurretController

def main():
    print("INITIALIZING TURRET LINK...")
    
    # Simple callback to print logs to console instead of UI
    def console_log(msg):
        print(f"[TURRET] {msg}")

    try:
        # Initialize Turret (Connects to Arduino)
        turret = TurretController(log_callback=console_log)
    except Exception as e:
        print(f"FAILED TO CONNECT: {e}")
        return

    # Create a dummy black window to capture keystrokes
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(img, "CLICK HERE TO CONTROL", (50, 200), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, "WASD / ARROWS = Move", (50, 250), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
    cv2.putText(img, "SPACE = Fire", (50, 280), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
    cv2.imshow("Turret Manual Control", img)

    print("\n--- MANUAL OVERRIDE ENGAGED ---")
    
    center = (320, 240) # Fake center for discharge function

    while True:
        key = cv2.waitKey(100) # Check every 100ms
        
        if key == 27: # ESC
            break
        
        # --- MAPPING ---
        elif key in [ord('w'), ord('W'), 2490368]: # Up / ArrowUp
            turret.manual_move("UP")
            print("CMD: UP")
            
        elif key in [ord('s'), ord('S'), 2621440]: # Down / ArrowDown
            turret.manual_move("DOWN")
            print("CMD: DOWN")
            
        elif key in [ord('a'), ord('A'), 2424832]: # Left / ArrowLeft
            turret.manual_move("LEFT")
            print("CMD: LEFT")
            
        elif key in [ord('d'), ord('D'), 2555904]: # Right / ArrowRight
            turret.manual_move("RIGHT")
            print("CMD: RIGHT")
            
        elif key == 32: # SPACE
            print("CMD: FIRE!")
            turret.discharge(center, center, is_manual=True)

    print("Closing Connection...")
    # turret.close() # If your Turret class has a close method
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()