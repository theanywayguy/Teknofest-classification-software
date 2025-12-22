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
        
        self._setup_window()
        self._build_layout()

    def _setup_window(self):
        self.root.title("AEGIS TACTICAL | v1.0 STICKY LOCK")
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

        # Targeting Frame
        target_fr = ttk.LabelFrame(sidebar, text=" TARGETING ")
        target_fr.pack(fill=tk.X, pady=5)
        self.mode_menu = ttk.Combobox(target_fr, textvariable=self.mode_var, 
                                      values=["MANUAL", "ALL", "RED (Dusman)", "BLUE (Dost)", "CHERRY-PICK"], 
                                      state="readonly")
        self.mode_menu.pack(fill=tk.X, padx=5, pady=2)
        self.mode_menu.bind("<<ComboboxSelected>>", lambda e: self.controller.reset_system())

        self.target_menu = ttk.Combobox(target_fr, textvariable=self.target_var, state="readonly")
        self.target_menu.pack(fill=tk.X, padx=5, pady=2)

        # Safety Frame
        safety_fr = ttk.LabelFrame(sidebar, text=" SAFETY GATE ")
        safety_fr.pack(fill=tk.X, pady=5)
        self.s_l = tk.Scale(safety_fr, from_=0, to=100, orient=tk.HORIZONTAL, bg=cfg.CLR_PANEL, fg="white", label="L LIMIT %")
        self.s_l.set(20); self.s_l.pack(fill=tk.X)
        self.s_r = tk.Scale(safety_fr, from_=0, to=100, orient=tk.HORIZONTAL, bg=cfg.CLR_PANEL, fg="white", label="R LIMIT %")
        self.s_r.set(80); self.s_r.pack(fill=tk.X)

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
        
    def get_safety_limits(self):
        return self.s_l.get(), self.s_r.get()

    def update_target_options(self, options):
        self.target_menu['values'] = options