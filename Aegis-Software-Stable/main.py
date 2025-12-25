import tkinter as tk
from ui import AegisUI
from mission_control import MissionControl

if __name__ == "__main__":
    # 1. Create the Root Window
    root = tk.Tk()
    
    # 2. Initialize the Brain 
    # (The Brain will initialize the UI and other components)
    app = MissionControl(root, AegisUI)
    
    # 3. Start the UI Loop
    root.mainloop()