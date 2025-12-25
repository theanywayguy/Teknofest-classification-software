import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import cv2
import config as cfg

class AegisUI:
    def __init__(self, root, controller):
        """
        Main UI Class.
        :param root: The Tkinter root window.
        :param controller: The MissionControl (or Main) object that handles logic.
        """
        self.root = root
        self.controller = controller 
        
        # -- UI Element Placeholders --
        self.video_label = None
        self.console = None
        self.angle_label = None
        
        # -- Inputs --
        self.left_limit_entry = None
        self.right_limit_entry = None
        
        # -- State Variables (Tkinter specific) --
        self.mode_var = tk.StringVar(value="CHERRY-PICK")
        self.target_var = tk.StringVar(value="None")
        
        # -- Memory Mode Labels --
        self.mem_platform_label = None
        self.mem_class_label = None
        self.mem_state_label = None
        
        # Initialize
        self._setup_window()
        self._build_layout()

    def _setup_window(self):
        """Configures the main window properties."""
        self.root.title("AEGIS TACTICAL | v2.1 MISSION COMMAND")
        self.root.geometry("1550x920")
        # Update: Access color via Dictionary
        self.root.configure(bg=cfg.COLORS["BG"])

    def _build_layout(self):
        """Constructs the widget hierarchy."""
        
        # 1. STYLE CONFIGURATION
        style = ttk.Style()
        style.theme_use('clam')
        # Update: Access colors via Dictionary
        style.configure("TLabelframe", 
                       background=cfg.COLORS["PANEL"], 
                       foreground=cfg.COLORS["UI_CYAN"])
        style.configure("TLabelframe.Label", 
                       background=cfg.COLORS["PANEL"], 
                       foreground=cfg.COLORS["UI_CYAN"], 
                       font=("Consolas", 10, "bold"))

        # 2. MAIN CONTAINER (Holds everything)
        main_container = tk.Frame(self.root, bg=cfg.COLORS["BG"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 3. VIDEO FEED (Left Side)
        self.video_label = tk.Label(main_container, bg="black", bd=2, relief="sunken")
        self.video_label.pack(side=tk.LEFT, expand=True)

        # 4. SIDEBAR (Right Side - Controls)
        sidebar = tk.Frame(main_container, bg=cfg.COLORS["PANEL"], width=400, padx=15)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        # -- Header --
        tk.Label(sidebar, text="AEGIS COMMAND", 
                 fg=cfg.COLORS["UI_CYAN"], bg=cfg.COLORS["PANEL"], 
                 font=("Consolas", 16, "bold")).pack(pady=10)

        # -- Angle Display --
        angle_frame = tk.Frame(sidebar, bg=cfg.COLORS["PANEL"])
        angle_frame.pack(fill=tk.X, pady=5)
        tk.Label(angle_frame, text="TURRET POSITION:", 
                 fg=cfg.COLORS["UI_CYAN"], bg=cfg.COLORS["PANEL"], 
                 font=("Consolas", 9, "bold")).pack(side=tk.LEFT)
        
        self.angle_label = tk.Label(angle_frame, text="0.0°", 
                                    fg="#00ff00", bg=cfg.COLORS["PANEL"], 
                                    font=("Consolas", 12, "bold"))
        self.angle_label.pack(side=tk.LEFT, padx=10)

        # -- Targeting Panel --
        target_fr = ttk.LabelFrame(sidebar, text=" TARGETING ")
        target_fr.pack(fill=tk.X, pady=5)
        
        self.mode_menu = ttk.Combobox(target_fr, textvariable=self.mode_var, 
                                      values=["MANUAL", "ALL", "RED (Dusman)", "BLUE (Dost)", "CHERRY-PICK", "MEMORY"], 
                                      state="readonly")
        self.mode_menu.pack(fill=tk.X, padx=5, pady=2)
        # Bind change event to reset system
        self.mode_menu.bind("<<ComboboxSelected>>", lambda e: self.controller.reset_system())

        self.target_menu = ttk.Combobox(target_fr, textvariable=self.target_var, state="readonly")
        self.target_menu.pack(fill=tk.X, padx=5, pady=2)

        # -- Safety Zones Panel --
        safety_fr = ttk.LabelFrame(sidebar, text=" NO-FIRE ZONES ")
        safety_fr.pack(fill=tk.X, pady=5)
        
        # Left Limit Input
        left_frame = tk.Frame(safety_fr, bg=cfg.COLORS["PANEL"])
        left_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(left_frame, text="Left Limit (°):", fg="white", bg=cfg.COLORS["PANEL"], font=("Consolas", 9)).pack(side=tk.LEFT)
        self.left_limit_entry = tk.Entry(left_frame, width=8, font=("Consolas", 10), bg="#222", fg=cfg.COLORS["UI_CYAN"])
        self.left_limit_entry.insert(0, "-90")
        self.left_limit_entry.pack(side=tk.RIGHT)
        
        # Right Limit Input
        right_frame = tk.Frame(safety_fr, bg=cfg.COLORS["PANEL"])
        right_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(right_frame, text="Right Limit (°):", fg="white", bg=cfg.COLORS["PANEL"], font=("Consolas", 9)).pack(side=tk.LEFT)
        self.right_limit_entry = tk.Entry(right_frame, width=8, font=("Consolas", 10), bg="#222", fg=cfg.COLORS["UI_CYAN"])
        self.right_limit_entry.insert(0, "90")
        self.right_limit_entry.pack(side=tk.RIGHT)
        
        tk.Button(safety_fr, text="UPDATE LIMITS", bg="#444", fg=cfg.COLORS["UI_CYAN"], font=("Consolas", 9, "bold"),
                  command=self.update_no_fire_zones).pack(fill=tk.X, padx=5, pady=5)

        # -- Memory Mode Status Panel --
        mem_fr = ttk.LabelFrame(sidebar, text=" MEMORY MODE ")
        mem_fr.pack(fill=tk.X, pady=5)
        
        self.mem_state_label = tk.Label(mem_fr, text="STATE: IDLE", fg="#888", bg=cfg.COLORS["PANEL"], font=("Consolas", 9, "bold"))
        self.mem_state_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.mem_platform_label = tk.Label(mem_fr, text="PLATFORM: ---", fg="#888", bg=cfg.COLORS["PANEL"], font=("Consolas", 9))
        self.mem_platform_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.mem_class_label = tk.Label(mem_fr, text="TARGET: ---", fg="#888", bg=cfg.COLORS["PANEL"], font=("Consolas", 9))
        self.mem_class_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Mission Buttons
        tk.Button(mem_fr, text="EXECUTE MISSION", bg="#006600", fg="white", font=("Consolas", 10, "bold"),
                  command=self.controller.execute_memory_mission, height=1).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(mem_fr, text="RETURN HOME", bg="#444444", fg="white", font=("Consolas", 10, "bold"),
                  command=self.controller.return_home, height=1).pack(fill=tk.X, padx=5, pady=5)

        # -- Manual Joystick Panel --
        joy_fr = ttk.LabelFrame(sidebar, text=" MANUAL JOYSTICK (WASD) ")
        joy_fr.pack(fill=tk.X, pady=5)
        btn_box = tk.Frame(joy_fr, bg=cfg.COLORS["PANEL"])
        btn_box.pack(pady=5)
        
        b_s = {"bg": "#222", "fg": cfg.COLORS["UI_CYAN"], "relief": "flat", "width": 6, "font": ("Consolas", 9, "bold")}
        tk.Button(btn_box, text="UP", **b_s, command=lambda: self.controller.joy_cmd("UP")).grid(row=0, column=1, pady=2)
        tk.Button(btn_box, text="LEFT", **b_s, command=lambda: self.controller.joy_cmd("LEFT")).grid(row=1, column=0, padx=2)
        tk.Button(btn_box, text="RIGHT", **b_s, command=lambda: self.controller.joy_cmd("RIGHT")).grid(row=1, column=2, padx=2)
        tk.Button(btn_box, text="DOWN", **b_s, command=lambda: self.controller.joy_cmd("DOWN")).grid(row=2, column=1, pady=2)
        
        # -- Fire Button --
        tk.Button(sidebar, text="DISCHARGE (SPACE)", bg="#660000", fg="white", font=("Consolas", 12, "bold"), 
                  command=self.controller.manual_fire, height=2).pack(fill=tk.X, pady=10)

        # -- Console Log --
        self.console = scrolledtext.ScrolledText(sidebar, height=12, bg="#050505", fg=cfg.COLORS["UI_CYAN"], font=("Consolas", 9))
        self.console.pack(fill=tk.X)

    def log_message(self, msg):
        """Appends a message to the scrolling console."""
        self.console.insert(tk.END, f"> {msg}\n")
        self.console.see(tk.END)

    def update_video_panel(self, cv2_frame):
        """Converts OpenCV frame to Tkinter image and updates label."""
        img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)))
        self.video_label.imgtk = img
        self.video_label.configure(image=img)
        
    def update_angle_display(self, angle):
        """Update the turret angle display and color-code safety warnings."""
        self.angle_label.config(text=f"{angle:.1f}°")
        
        # Color code based on proximity to no-fire zones
        try:
            left_limit = float(self.left_limit_entry.get())
            right_limit = float(self.right_limit_entry.get())
            
            if abs(angle - left_limit) < 5 or abs(angle - right_limit) < 5:
                self.angle_label.config(fg="#ff0000")  # Red = Danger
            elif abs(angle - left_limit) < 15 or abs(angle - right_limit) < 15:
                self.angle_label.config(fg="#ffaa00")  # Orange = Warning
            else:
                self.angle_label.config(fg="#00ff00")  # Green = Safe
        except ValueError:
            pass
    
    def update_no_fire_zones(self):
        """Update the no-fire zone angles in config based on user input."""
        try:
            left_val = float(self.left_limit_entry.get())
            right_val = float(self.right_limit_entry.get())
            
            # Update: Write to new nested config
            cfg.TURRET["NO_FIRE"]["LEFT_LIMIT"] = left_val
            cfg.TURRET["NO_FIRE"]["RIGHT_LIMIT"] = right_val
            
            self.log_message(f"NO-FIRE ZONES: L={left_val}° R={right_val}°")
        except ValueError:
            self.log_message("ERROR: Invalid angle values")
    
    def update_memory_display(self, state, platform, target_class):
        """
        Update memory mode information display.
        Handles the new Enum states correctly.
        """
        # Map Enum states to specific Colors
        state_colors = {
            cfg.MissionState.SCAN_OCR: "#ffaa00",   # Orange
            cfg.MissionState.SCAN_CLASS: "#ffaa00", # Orange
            cfg.MissionState.WAITING: "#00ff00",    # Green
            cfg.MissionState.SEEKING: "#00aaff",    # Cyan
            cfg.MissionState.ENGAGING: "#ff0000",   # Red
            cfg.MissionState.RETURNING: "#00aaff"   # Cyan
        }
        
        # Get color or default to gray
        color = state_colors.get(state, "#888")
        
        # Update labels
        # Note: state.name gives us the string name of the Enum (e.g. "SCAN_OCR")
        state_text = state.name if hasattr(state, 'name') else str(state)
        
        self.mem_state_label.config(text=f"STATE: {state_text}", fg=color)
        
        self.mem_platform_label.config(
            text=f"PLATFORM: {platform if platform else '---'}", 
            fg="#00ff00" if platform else "#888"
        )
        
        # Color code the target class (Red for Dusman/Enemy, Blue/Green for Dost/Friend)
        tgt_color = "#888"
        if target_class:
            if "dusman" in target_class or "red" in target_class:
                tgt_color = "#ff0000"
            elif "dost" in target_class or "green" in target_class:
                tgt_color = "#00ff00"
            elif "blue" in target_class:
                tgt_color = "#0000ff"

        self.mem_class_label.config(text=f"TARGET: {target_class if target_class else '---'}", fg=tgt_color)

    def update_target_options(self, options):
        self.target_menu['values'] = options