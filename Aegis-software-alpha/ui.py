# aegis_ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import cv2
import config as cfg

class AegisUI:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller 
        self.video_label = None
        self.console = None
        
        # State Variables
        self.mode_var = tk.StringVar(value="CHERRY-PICK")
        self.target_var = tk.StringVar(value="None")
        
        # Angle Display
        self.angle_label = None
        
        # No-Fire Zone Entries
        self.left_limit_entry = None
        self.right_limit_entry = None
        
        # Memory Mode
        self.mem_platform_label = None
        self.mem_class_label = None
        self.mem_state_label = None
        
        self._setup_window()
        self._build_layout()

    def _setup_window(self):
        self.root.title("AEGIS TACTICAL | v2.0 MEMORY MODE")
        self.root.geometry("1550x920")
        self.root.configure(bg=cfg.CLR_BG)

    def _build_layout(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabelframe", background=cfg.CLR_PANEL, foreground=cfg.CLR_UI_CYAN)
        style.configure("TLabelframe.Label", background=cfg.CLR_PANEL, foreground=cfg.CLR_UI_CYAN, font=("Consolas", 10, "bold"))

        main_container = tk.Frame(self.root, bg=cfg.CLR_BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.video_label = tk.Label(main_container, bg="black", bd=2, relief="sunken")
        self.video_label.pack(side=tk.LEFT, expand=True)

        sidebar = tk.Frame(main_container, bg=cfg.CLR_PANEL, width=400, padx=15)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(sidebar, text="AEGIS COMMAND", fg=cfg.CLR_UI_CYAN, bg=cfg.CLR_PANEL, font=("Consolas", 16, "bold")).pack(pady=10)

        # Current Angle Display
        angle_frame = tk.Frame(sidebar, bg=cfg.CLR_PANEL)
        angle_frame.pack(fill=tk.X, pady=5)
        tk.Label(angle_frame, text="TURRET POSITION:", fg=cfg.CLR_UI_CYAN, bg=cfg.CLR_PANEL, font=("Consolas", 9, "bold")).pack(side=tk.LEFT)
        self.angle_label = tk.Label(angle_frame, text="0.0°", fg="#00ff00", bg=cfg.CLR_PANEL, font=("Consolas", 12, "bold"))
        self.angle_label.pack(side=tk.LEFT, padx=10)

        # Targeting Frame
        target_fr = ttk.LabelFrame(sidebar, text=" TARGETING ")
        target_fr.pack(fill=tk.X, pady=5)
        self.mode_menu = ttk.Combobox(target_fr, textvariable=self.mode_var, 
                                      values=["MANUAL", "ALL", "RED (Dusman)", "BLUE (Dost)", "CHERRY-PICK", "MEMORY"], 
                                      state="readonly")
        self.mode_menu.pack(fill=tk.X, padx=5, pady=2)
        self.mode_menu.bind("<<ComboboxSelected>>", lambda e: self.controller.reset_system())

        self.target_menu = ttk.Combobox(target_fr, textvariable=self.target_var, state="readonly")
        self.target_menu.pack(fill=tk.X, padx=5, pady=2)

        # No-Fire Zones Frame
        safety_fr = ttk.LabelFrame(sidebar, text=" NO-FIRE ZONES ")
        safety_fr.pack(fill=tk.X, pady=5)
        
        left_frame = tk.Frame(safety_fr, bg=cfg.CLR_PANEL)
        left_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(left_frame, text="Left Limit (°):", fg="white", bg=cfg.CLR_PANEL, font=("Consolas", 9)).pack(side=tk.LEFT)
        self.left_limit_entry = tk.Entry(left_frame, width=8, font=("Consolas", 10), bg="#222", fg=cfg.CLR_UI_CYAN)
        self.left_limit_entry.insert(0, "-90")
        self.left_limit_entry.pack(side=tk.RIGHT)
        
        right_frame = tk.Frame(safety_fr, bg=cfg.CLR_PANEL)
        right_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(right_frame, text="Right Limit (°):", fg="white", bg=cfg.CLR_PANEL, font=("Consolas", 9)).pack(side=tk.LEFT)
        self.right_limit_entry = tk.Entry(right_frame, width=8, font=("Consolas", 10), bg="#222", fg=cfg.CLR_UI_CYAN)
        self.right_limit_entry.insert(0, "90")
        self.right_limit_entry.pack(side=tk.RIGHT)
        
        tk.Button(safety_fr, text="UPDATE LIMITS", bg="#444", fg=cfg.CLR_UI_CYAN, font=("Consolas", 9, "bold"),
                  command=self.update_no_fire_zones).pack(fill=tk.X, padx=5, pady=5)

        # Memory Mode Frame
        mem_fr = ttk.LabelFrame(sidebar, text=" MEMORY MODE ")
        mem_fr.pack(fill=tk.X, pady=5)
        
        self.mem_state_label = tk.Label(mem_fr, text="STATE: IDLE", fg="#888", bg=cfg.CLR_PANEL, font=("Consolas", 9, "bold"))
        self.mem_state_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.mem_platform_label = tk.Label(mem_fr, text="PLATFORM: ---", fg="#888", bg=cfg.CLR_PANEL, font=("Consolas", 9))
        self.mem_platform_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.mem_class_label = tk.Label(mem_fr, text="TARGET: ---", fg="#888", bg=cfg.CLR_PANEL, font=("Consolas", 9))
        self.mem_class_label.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Button(mem_fr, text="EXECUTE MISSION", bg="#006600", fg="white", font=("Consolas", 10, "bold"),
                  command=self.controller.execute_memory_mission, height=1).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(mem_fr, text="RETURN HOME", bg="#444444", fg="white", font=("Consolas", 10, "bold"),
                  command=self.controller.return_home, height=1).pack(fill=tk.X, padx=5, pady=5)

        # Joystick Frame
        joy_fr = ttk.LabelFrame(sidebar, text=" MANUAL JOYSTICK (WASD) ")
        joy_fr.pack(fill=tk.X, pady=5)
        btn_box = tk.Frame(joy_fr, bg=cfg.CLR_PANEL)
        btn_box.pack(pady=5)
        
        b_s = {"bg": "#222", "fg": cfg.CLR_UI_CYAN, "relief": "flat", "width": 6, "font": ("Consolas", 9, "bold")}
        tk.Button(btn_box, text="UP", **b_s, command=lambda: self.controller.joy_cmd("UP")).grid(row=0, column=1, pady=2)
        tk.Button(btn_box, text="LEFT", **b_s, command=lambda: self.controller.joy_cmd("LEFT")).grid(row=1, column=0, padx=2)
        tk.Button(btn_box, text="RIGHT", **b_s, command=lambda: self.controller.joy_cmd("RIGHT")).grid(row=1, column=2, padx=2)
        tk.Button(btn_box, text="DOWN", **b_s, command=lambda: self.controller.joy_cmd("DOWN")).grid(row=2, column=1, pady=2)
        
        tk.Button(sidebar, text="DISCHARGE (SPACE)", bg="#660000", fg="white", font=("Consolas", 12, "bold"), 
                  command=self.controller.manual_fire, height=2).pack(fill=tk.X, pady=10)

        self.console = scrolledtext.ScrolledText(sidebar, height=12, bg="#050505", fg=cfg.CLR_UI_CYAN, font=("Consolas", 9))
        self.console.pack(fill=tk.X)

    def log_message(self, msg):
        self.console.insert(tk.END, f"> {msg}\n")
        self.console.see(tk.END)

    def update_video_panel(self, cv2_frame):
        img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)))
        self.video_label.imgtk = img
        self.video_label.configure(image=img)
        
    def update_angle_display(self, angle):
        """Update the turret angle display."""
        self.angle_label.config(text=f"{angle:.1f}°")
        
        # Color code based on proximity to no-fire zones
        try:
            left_limit = float(self.left_limit_entry.get())
            right_limit = float(self.right_limit_entry.get())
            
            if abs(angle - left_limit) < 5 or abs(angle - right_limit) < 5:
                self.angle_label.config(fg="#ff0000")  # Red near limits
            elif abs(angle - left_limit) < 15 or abs(angle - right_limit) < 15:
                self.angle_label.config(fg="#ffaa00")  # Orange approaching limits
            else:
                self.angle_label.config(fg="#00ff00")  # Green safe
        except ValueError:
            pass
    
    def update_no_fire_zones(self):
        """Update the no-fire zone angles in config."""
        try:
            left_val = float(self.left_limit_entry.get())
            right_val = float(self.right_limit_entry.get())
            
            cfg.NO_FIRE_ANGLES["LEFT_LIMIT"] = left_val
            cfg.NO_FIRE_ANGLES["RIGHT_LIMIT"] = right_val
            
            self.log_message(f"NO-FIRE ZONES: L={left_val}° R={right_val}°")
        except ValueError:
            self.log_message("ERROR: Invalid angle values")
    
    def update_memory_display(self, state, platform, target_class):
        """Update memory mode information display."""
        # Update state with color coding
        state_colors = {
            cfg.MEM_SCAN_OCR: "#ffaa00",
            cfg.MEM_SCAN_CLASS: "#ffaa00",
            cfg.MEM_WAITING: "#00ff00",
            cfg.MEM_SEEKING: "#00aaff",
            cfg.MEM_ENGAGING: "#ff0000",
            cfg.MEM_RETURNING: "#00aaff"
        }
        
        self.mem_state_label.config(text=f"STATE: {state}", fg=state_colors.get(state, "#888"))
        self.mem_platform_label.config(text=f"PLATFORM: {platform if platform else '---'}", 
                                      fg="#00ff00" if platform else "#888")
        self.mem_class_label.config(text=f"TARGET: {target_class if target_class else '---'}",
                                   fg="#ff0000" if target_class == "dusman" else "#0000ff" if target_class == "dost" else "#888")

    def update_target_options(self, options):
        self.target_menu['values'] = options