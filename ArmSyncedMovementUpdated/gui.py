import os
import sys
import time
import json
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import numpy as np

# Add workspace root to python path to import dynamixel_driver
from dynamixel_driver import DynamixelDriver

# Premium Cyber-Control Palette (C.H.I.M.A.N Warm Charcoal Theme)
BG_OSRS = "#09090B"            # Rich Charcoal/Zinc Black
CARD_OSRS = "#18181B"          # Zinc Dark Gray Card
BORDER_OSRS = "#27272A"        # High-Contrast Medium Border
TEXT_PRIMARY = "#F4F4F5"       # Warm Soft White
TEXT_MUTED = "#A1A1AA"         # Muted Zinc Gray
ACCENT_PINK = "#F43F5E"        # Neon Rose/Coral
ACCENT_VIOLET = "#F59E0B"      # Warm Amber/Gold Accent
ACCENT_EMERALD = "#10B981"     # Armed Green
ACCENT_CRIMSON = "#EF4444"     # Danger/Offline Red
ACCENT_BLUE = "#FF7A00"        # Electric Orange Telemetry
CARD_INNER = "#0F0F11"         # Inner dark zinc card


# Full Robot Profiles Mapping
ROBOT_PROFILES = {
    "Humanoid V1": {
        2: "Auxiliary XL430 (ID 2)",
        11: "R Shoulder Pitch (R1P)",
        12: "L Shoulder Roll (L2R)",
        13: "L Shoulder Yaw (L3Y)",
        14: "R Elbow Flex (R4F)",
        15: "R Forearm Yaw (R5Y)",
        16: "R Wrist Roll (R6R)",
        17: "R Wrist Pitch (R7P)",
        18: "R Hand Grip (R8G)",
        21: "L Shoulder Pitch (L1P)",
        22: "R Shoulder Roll (R2R)",
        23: "R Shoulder Yaw (R3Y)",
        24: "L Elbow Flex (L4F)",
        25: "L Forearm Yaw (L5Y)",
        26: "L Wrist Roll (L6R)",
        27: "L Wrist Pitch (L7P)",
        28: "L Hand Grip (L8G)",
        31: "Head Yaw",
        32: "Head Pitch"
    },
    "Leap Hand V1": {
        0: "Index Abduct",
        1: "Index MCP",
        2: "Index PIP",
        3: "Ring MCP",
        4: "Middle Abduct",
        5: "Middle MCP",
        6: "Middle PIP",
        7: "Middle DIP",
        8: "Ring Abduct",
        9: "Index DIP",
        10: "Ring PIP",
        11: "Ring DIP",
        12: "Thumb Abduct",
        13: "Thumb MCP",
        14: "Thumb PIP",
        15: "Thumb DIP"
    },
    "Leap Hand V2": {
        0: "Index Abduct",
        1: "Index Curl",
        2: "Middle Abduct",
        3: "Middle Curl",
        4: "Ring Abduct",
        5: "Ring Curl",
        6: "Thumb Abduct",
        7: "Thumb Curl"
    },
    "Open Manipulator X": {
        11: "Joint 1 - Yaw",
        12: "Joint 2 - Shoulder",
        13: "Joint 3 - Elbow",
        14: "Joint 4 - Wrist",
        15: "Joint 5 - Gripper"
    },
    "Rover Bot": {
        41: "L Front Drive",
        42: "L Mid Drive",
        43: "L Rear Drive",
        44: "R Front Drive",
        45: "R Mid Drive",
        46: "R Rear Drive"
    },
    "Custom Platform": {
        51: "Aux Joint 1",
        52: "Aux Joint 2",
        53: "Aux Joint 3",
        54: "Aux Joint 4"
    }
}

V1_LIMITS = {
    0:  {"min": 2048, "max": 2500},
    1:  {"min": 2048, "max": 3000},
    2:  {"min": 2048, "max": 3200},
    3:  {"min": 2048, "max": 3000},
    4:  {"min": 2048, "max": 2500},
    5:  {"min": 2048, "max": 3000},
    6:  {"min": 2048, "max": 3200},
    7:  {"min": 2048, "max": 3200},
    8:  {"min": 2048, "max": 2500},
    9:  {"min": 2048, "max": 3200},
    10: {"min": 2048, "max": 3200},
    11: {"min": 2048, "max": 3200},
    12: {"min": 2048, "max": 3200},
    13: {"min": 2048, "max": 3000},
    14: {"min": 2048, "max": 3200},
    15: {"min": 2048, "max": 3200},
}

V2_LIMITS = {
    0:  {"min": 2048, "max": 2500},
    1:  {"min": 2048, "max": 3200},
    2:  {"min": 2048, "max": 2500},
    3:  {"min": 2048, "max": 3200},
    4:  {"min": 2048, "max": 2500},
    5:  {"min": 2048, "max": 3200},
    6:  {"min": 2048, "max": 3200},
    7:  {"min": 2048, "max": 3200},
}

VALS_PRESETS = {
    "Open Hand":   (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0),
    "Closed Fist": (1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 0.5, 0.0, 0.8),
    "Scissors":    (0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.8),
    "Thumbs Up":   (1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0),
}

HUMANOID_DEFAULTS = {
    21: -3561, 12: -162, 13: 4344, 24: 812, 25: 943, 26: 21, 27: 60, 28: -2676,
    11: -1674, 22: 2138, 23: -1275, 14: 4038, 15: -995, 16: 4077, 17: 74, 18: 983,
    31: 0, 32: 0
}

MIRROR_PARTNERS = {
    21: 11, 11: 21,
    12: 22, 22: 12,
    13: 23, 23: 13,
    24: 14, 14: 24,
    25: 15, 15: 25,
    26: 16, 16: 26,
    27: 17, 17: 27,
    28: 18, 18: 28
}

class CollapsibleFrame(ctk.CTkFrame):
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.collapsed = False
        
        # Header Frame
        self.header = ctk.CTkFrame(self, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=6, height=36)
        self.header.pack(fill="x", pady=2)
        self.header.pack_propagate(False)
        
        # Title Label
        self.title_lbl = ctk.CTkLabel(self.header, text=title, font=ctk.CTkFont(family="Outfit", size=12, weight="bold"), text_color=TEXT_PRIMARY)
        self.title_lbl.pack(side="left", padx=15)
        
        # Toggle Button
        self.toggle_btn = ctk.CTkButton(
            self.header, 
            text="▼", 
            width=30, 
            height=26, 
            fg_color="transparent", 
            text_color=ACCENT_PINK,
            hover_color=BORDER_OSRS,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle
        )
        self.toggle_btn.pack(side="right", padx=10)
        
        # Content Frame
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="x", padx=5, pady=2)
        
    def toggle(self):
        if self.collapsed:
            self.content.pack(fill="x", padx=5, pady=2)
            self.toggle_btn.configure(text="▼")
            self.collapsed = False
        else:
            self.content.pack_forget()
            self.toggle_btn.configure(text="▲")
            self.collapsed = True

class ExtendedControlGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window settings
        self.title("C.H.I.M.A.N Operator Control Center")
        self.geometry("1420x900")
        self.minsize(1200, 800)
        self.configure(fg_color=BG_OSRS)
        
        # State variables
        self.driver = None
        self.connected = False
        self.active_ids = []
        self.online_ids = []
        self.consecutive_failures = {}
        self.torque_state = {}
        self.goal_positions = {}
        self.present_positions = {}
        self.last_written_positions = {}
        self.pending_actions = []
        
        # Diagnostics Telemetry variables
        self.latency_ms = 0.0
        self.loop_ticks = 0
        self.status_msg = "DISCONNECTED"
        self.status_is_err = True
        
        # Extended Live Telemetry caches
        self.present_currents = {}
        self.present_temperatures = {}
        self.present_voltages = {}
        
        # Advanced Features state
        self.console_logs = []
        self.keyframes = []
        self.mirror_sync_active = False
        self._in_mirror_sync = False
        self.virtual_mode = False
        self.active_tab = "connection"
        
        # Thread-safe locks against goal-sync race conditions
        self.pending_torque_actions = set()
        
        # Thread control
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        self.telemetry_loop_active = False
        
        # Layout components
        self.motor_widgets = {}
        self.motor_row_widgets = {}
        self.accordions = {}
        self.diag_rows = {}
        
        # GUI rendering state cache to prevent redundant updates
        self.last_rendered_states = {}
        self.last_status_state = {}
        
        # Set theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_layout()
        
    def setup_layout(self):
        # Grid settings: Sidebar (0) + Main Area (1)
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # =====================================================================
        # SIDEBAR (LEFT COL) - OS NAVIGATION DRAWER
        # =====================================================================
        self.sidebar = ctk.CTkFrame(self, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # C.H.I.M.A.N branding
        brand_lbl = ctk.CTkLabel(self.sidebar, text="C.H.I.M.A.N\nConsole", font=ctk.CTkFont(family="Outfit", size=18, weight="bold"), text_color=ACCENT_PINK)
        brand_lbl.pack(pady=(20, 25))
        
        # Segment Tab Buttons (Navigation Drawer look)
        tab_nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        tab_nav_frame.pack(fill="x", padx=15, pady=10)
        
        self.tab_btn_conn = ctk.CTkButton(
            tab_nav_frame,
            text="SYSTEM CONNECTION",
            font=ctk.CTkFont(family="Outfit", size=12, weight="bold"),
            fg_color=BORDER_OSRS,
            text_color=ACCENT_PINK,
            height=40,
            anchor="w",
            command=lambda: self.show_tab("connection")
        )
        self.tab_btn_conn.pack(fill="x", pady=4)
        
        self.tab_btn_ctrl = ctk.CTkButton(
            tab_nav_frame,
            text="CONTROL WORKSPACE",
            font=ctk.CTkFont(family="Outfit", size=12, weight="bold"),
            fg_color="transparent",
            text_color=TEXT_MUTED,
            height=40,
            anchor="w",
            command=lambda: self.show_tab("control")
        )
        self.tab_btn_ctrl.pack(fill="x", pady=4)
        
        self.tab_btn_diag = ctk.CTkButton(
            tab_nav_frame,
            text="ADVANCED DIAGNOSTICS",
            font=ctk.CTkFont(family="Outfit", size=12, weight="bold"),
            fg_color="transparent",
            text_color=TEXT_MUTED,
            height=40,
            anchor="w",
            command=lambda: self.show_tab("diagnostics")
        )
        self.tab_btn_diag.pack(fill="x", pady=4)
        
        # Emergency E-Stop Button at sidebar base
        self.estop_btn = ctk.CTkButton(
            self.sidebar, 
            text="EMERGENCY STOP", 
            fg_color=ACCENT_CRIMSON, 
            hover_color="#B91C1C", 
            height=50,
            font=ctk.CTkFont(family="Outfit", size=13, weight="bold"),
            command=self.trigger_estop
        )
        self.estop_btn.pack(side="bottom", padx=15, pady=20, fill="x")
        
        # =====================================================================
        # MAIN AREA (RIGHT COL) - TOP BAR & CONTENT AREA
        # =====================================================================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=0, minsize=65) # Top health bar
        self.main_container.grid_rowconfigure(1, weight=1)             # Multi-tab panels
        
        # --- Top Dashboard Health Bar ---
        top_bar = ctk.CTkFrame(self.main_container, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_bar.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Card 1: Connection & Latency Info
        self.dash_card1 = ctk.CTkFrame(top_bar, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=58)
        self.dash_card1.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        self.dash_card1.pack_propagate(False)
        self.card1_lbl = ctk.CTkLabel(self.dash_card1, text="COM PORT // BAUD\nDisconnections active", font=ctk.CTkFont(family="JetBrains Mono", size=10), text_color=TEXT_MUTED)
        self.card1_lbl.pack(pady=10)
        
        # Card 2: Active Node count
        self.dash_card2 = ctk.CTkFrame(top_bar, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=58)
        self.dash_card2.grid(row=0, column=1, padx=3, sticky="nsew")
        self.dash_card2.pack_propagate(False)
        self.card2_lbl = ctk.CTkLabel(self.dash_card2, text="NODES DETECTED\n0 active on bus", font=ctk.CTkFont(family="JetBrains Mono", size=10), text_color=TEXT_MUTED)
        self.card2_lbl.pack(pady=10)
        
        # Card 3: Performance Latency metrics
        self.dash_card3 = ctk.CTkFrame(top_bar, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=58)
        self.dash_card3.grid(row=0, column=2, padx=(6, 0), sticky="nsew")
        self.dash_card3.pack_propagate(False)
        self.card3_lbl = ctk.CTkLabel(self.dash_card3, text="BUS LATENCY // TIME\n-- ms average", font=ctk.CTkFont(family="JetBrains Mono", size=10), text_color=TEXT_MUTED)
        self.card3_lbl.pack(pady=10)
        
        # --- Content Area ---
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew")
        
        # =====================================================================
        # TAB 1: CONNECTION PANE
        # =====================================================================
        self.conn_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.conn_frame.grid_columnconfigure(0, weight=0, minsize=380)
        self.conn_frame.grid_columnconfigure(1, weight=1)
        self.conn_frame.grid_rowconfigure(0, weight=1)
        self.conn_frame.grid_rowconfigure(1, weight=0, minsize=200)
        
        # Left Config Frame
        conn_config_card = ctk.CTkFrame(self.conn_frame, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        conn_config_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(conn_config_card, text="Serial Connection Settings", font=ctk.CTkFont(family="Outfit", weight="bold", size=14), text_color=ACCENT_PINK).pack(pady=(15, 10), padx=15, anchor="w")
        
        ctk.CTkLabel(conn_config_card, text="COM Port:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=20)
        self.port_entry = ctk.CTkEntry(conn_config_card, placeholder_text="e.g. COM14", height=30, fg_color=BG_OSRS, border_color=BORDER_OSRS)
        self.port_entry.insert(0, "COM14")
        self.port_entry.pack(padx=20, pady=(2, 10), fill="x")
        
        ctk.CTkLabel(conn_config_card, text="Baud Rate:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=20)
        self.baud_menu = ctk.CTkOptionMenu(conn_config_card, values=["4000000", "2000000", "1000000", "115200", "57600"], height=30, fg_color=BG_OSRS, button_color=BORDER_OSRS, button_hover_color=ACCENT_VIOLET)
        self.baud_menu.set("4000000")
        self.baud_menu.pack(padx=20, pady=(2, 15), fill="x")
        
        # Simulation Mode
        self.sim_mode_switch = ctk.CTkSwitch(
            conn_config_card, 
            text="Virtual Simulation Mode", 
            font=ctk.CTkFont(family="Outfit", size=11, weight="bold"),
            text_color=TEXT_MUTED,
            progress_color=ACCENT_VIOLET,
            command=self.toggle_virtual_mode
        )
        self.sim_mode_switch.pack(padx=20, pady=(0, 15), anchor="w")
        
        self.conn_btn = ctk.CTkButton(
            conn_config_card, 
            text="CONNECT BUS", 
            fg_color=ACCENT_PINK, 
            hover_color="#D11871", 
            font=ctk.CTkFont(family="Outfit", weight="bold"), 
            command=self.toggle_connection,
            height=34
        )
        self.conn_btn.pack(padx=20, pady=(0, 10), fill="x")
        
        self.scan_btn = ctk.CTkButton(
            conn_config_card, 
            text="RE-SCAN DYNAMIXELS", 
            fg_color="#18181B", 
            text_color="#71717A",
            hover_color="#475569", 
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold"), 
            command=self.trigger_rescan,
            height=30
        )
        self.scan_btn.pack(padx=20, pady=(0, 10), fill="x")
        
        self.autobaud_btn = ctk.CTkButton(
            conn_config_card, 
            text="AUTO-BAUD SCANNER", 
            fg_color=ACCENT_VIOLET, 
            hover_color="#4F46E5", 
            font=ctk.CTkFont(family="Outfit", weight="bold"), 
            command=self.start_auto_baud_scan,
            height=30
        )
        self.autobaud_btn.pack(padx=20, pady=(0, 15), fill="x")
        
        # Torque Global frame in connection pane for quick setup
        global_torque_box = ctk.CTkFrame(conn_config_card, fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, corner_radius=6)
        global_torque_box.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(global_torque_box, text="Global Torque Controls", font=ctk.CTkFont(family="Outfit", weight="bold", size=12), text_color=TEXT_PRIMARY).pack(pady=(5, 5))
        self.torque_on_btn = ctk.CTkButton(global_torque_box, text="TORQUE ENABLED (ON)", fg_color="#18181B", text_color="#71717A", hover_color="#059669", state="disabled", font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.set_global_torque(True), height=26)
        self.torque_on_btn.pack(padx=10, pady=4, fill="x")
        self.torque_off_btn = ctk.CTkButton(global_torque_box, text="RELAX ALL (OFF)", fg_color="#18181B", text_color="#71717A", hover_color="#475569", state="disabled", font=ctk.CTkFont(size=11, weight="bold"), command=lambda: self.set_global_torque(False), height=26)
        self.torque_off_btn.pack(padx=10, pady=(4, 8), fill="x")
        
        # Right Topology Frame
        topology_card = ctk.CTkFrame(self.conn_frame, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        topology_card.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(topology_card, text="Bus Topology Map", font=ctk.CTkFont(family="Outfit", weight="bold", size=14), text_color=ACCENT_PINK).pack(pady=(15, 10), padx=15, anchor="w")
        
        self.topo_canvas = tk.Canvas(topology_card, bg="#0F0F11", highlightthickness=0)
        self.topo_canvas.pack(fill="both", expand=True, padx=15, pady=15)
        self.topo_canvas.bind("<Configure>", lambda event: self.draw_topology_map())
        
        # Bottom Console Frame
        console_card = ctk.CTkFrame(self.conn_frame, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        console_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        
        ctk.CTkLabel(console_card, text="System Logs", font=ctk.CTkFont(family="Outfit", weight="bold", size=12), text_color=ACCENT_PINK).pack(pady=(8, 4), padx=15, anchor="w")
        
        self.console_txt = ctk.CTkTextbox(console_card, font=ctk.CTkFont(family="JetBrains Mono", size=11), fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1)
        self.console_txt.pack(fill="both", expand=True, padx=15, pady=(2, 12))
        self.console_txt.configure(state="disabled")
        
        # Console tags color configuration
        self.console_txt.tag_config("info", foreground="#94A3B8")
        self.console_txt.tag_config("warning", foreground="#F59E0B")
        self.console_txt.tag_config("error", foreground="#EF4444")
        self.console_txt.tag_config("success", foreground="#10B981")
        self.console_txt.tag_config("cmd", foreground="#00F0FF")
        
        # =====================================================================
        # TAB 2: CONTROL WORKSPACE
        # =====================================================================
        self.ctrl_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.ctrl_frame.grid_columnconfigure(0, weight=0, minsize=380)
        self.ctrl_frame.grid_columnconfigure(1, weight=1)
        self.ctrl_frame.grid_rowconfigure(0, weight=1)
        
        # Left Panel: Poses Gallery & Timeline
        control_left_panel = ctk.CTkFrame(self.ctrl_frame, fg_color="transparent")
        control_left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Card 1: Poses & Symmetry Toggle
        pose_ctrl_card = ctk.CTkFrame(control_left_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        pose_ctrl_card.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(pose_ctrl_card, text="Calibrated Pose Presets", font=ctk.CTkFont(family="Outfit", weight="bold", size=13), text_color=ACCENT_PINK).pack(pady=(12, 6), padx=15, anchor="w")
        
        # Symmetry switch
        self.mirror_switch = ctk.CTkSwitch(
            pose_ctrl_card, 
            text="Dual-Arm Symmetry Mirroring", 
            font=ctk.CTkFont(family="Outfit", size=11, weight="bold"),
            text_color=TEXT_MUTED,
            progress_color=ACCENT_PINK,
            command=self.toggle_mirror_sync
        )
        self.mirror_switch.pack(padx=15, pady=(0, 10), anchor="w")
        
        # Quick Presets Buttons inside Gallery Card
        gallery_btn_frame = ctk.CTkFrame(pose_ctrl_card, fg_color="transparent")
        gallery_btn_frame.pack(fill="x", padx=15, pady=(2, 12))
        gallery_btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.both_arms_pose_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="BOTH ARMS POSE", 
            fg_color="#18181B", 
            text_color="#71717A", 
            hover_color="#D11871", 
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_both_arms_offsets,
            height=32
        )
        self.both_arms_pose_btn.grid(row=0, column=0, columnspan=2, padx=2, pady=4, sticky="ew")
        
        self.left_arm_pose_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="LEFT ARM POSE", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_offsets,
            height=30
        )
        self.left_arm_pose_btn.grid(row=1, column=0, padx=2, pady=3, sticky="ew")
        
        self.right_arm_pose_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="RIGHT ARM POSE", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_right_arm_offsets,
            height=30
        )
        self.right_arm_pose_btn.grid(row=1, column=1, padx=2, pady=3, sticky="ew")
        
        self.left_arm_up_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="LEFT ARM UP", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_up,
            height=30
        )
        self.left_arm_up_btn.grid(row=2, column=0, padx=2, pady=3, sticky="ew")
        
        self.left_arm_center_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="LEFT ARM CENTER", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_center,
            height=30
        )
        self.left_arm_center_btn.grid(row=2, column=1, padx=2, pady=3, sticky="ew")
        
        self.left_arm_down_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="LEFT ARM DOWN", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_down,
            height=30
        )
        self.left_arm_down_btn.grid(row=3, column=0, padx=2, pady=3, sticky="ew")
        
        self.left_hand_open_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="LEFT HAND OPEN", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_hand_open,
            height=30
        )
        self.left_hand_open_btn.grid(row=3, column=1, padx=2, pady=3, sticky="ew")
        
        self.left_hand_closed_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="LEFT HAND CLOSED", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_hand_closed,
            height=30
        )
        self.left_hand_closed_btn.grid(row=4, column=0, padx=2, pady=3, sticky="ew")
        
        self.preset_zero_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="ZERO ALL JOINTS", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_CRIMSON, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_zero_all,
            height=30
        )
        self.preset_zero_btn.grid(row=4, column=1, padx=2, pady=3, sticky="ew")
        
        self.sync_goals_btn = ctk.CTkButton(
            gallery_btn_frame, 
            text="SYNC GOALS TO PRESENT", 
            fg_color=CARD_INNER, 
            hover_color=ACCENT_BLUE, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_sync_goals,
            height=32
        )
        self.sync_goals_btn.grid(row=5, column=0, columnspan=2, padx=2, pady=4, sticky="ew")
        
        # Timeline Sequencer Card
        timeline_card = ctk.CTkFrame(control_left_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        timeline_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(timeline_card, text="Trajectory Sequencer", font=ctk.CTkFont(family="Outfit", weight="bold", size=13), text_color=ACCENT_PINK).pack(pady=(12, 6), padx=15, anchor="w")
        
        timeline_btn_frame = ctk.CTkFrame(timeline_card, fg_color="transparent")
        timeline_btn_frame.pack(fill="x", padx=15, pady=2)
        timeline_btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.record_frame_btn = ctk.CTkButton(
            timeline_btn_frame, 
            text="RECORD POSE", 
            fg_color=ACCENT_BLUE, 
            hover_color="#2563EB", 
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11), 
            command=self.record_keyframe,
            height=28
        )
        self.record_frame_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.clear_timeline_btn = ctk.CTkButton(
            timeline_btn_frame, 
            text="CLEAR ALL", 
            fg_color="#334155", 
            hover_color="#475569", 
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11), 
            command=self.clear_timeline,
            height=28
        )
        self.clear_timeline_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Timing Delay entry
        delay_frame = ctk.CTkFrame(timeline_card, fg_color="transparent")
        delay_frame.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(delay_frame, text="Transition delay (s):", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
        self.timeline_delay_entry = ctk.CTkEntry(delay_frame, width=50, height=24, fg_color=BG_OSRS, border_color=BORDER_OSRS)
        self.timeline_delay_entry.insert(0, "1.5")
        self.timeline_delay_entry.pack(side="right")
        
        self.play_timeline_btn = ctk.CTkButton(
            timeline_card, 
            text="▶ PLAY TIMELINE SEQUENCE", 
            fg_color=ACCENT_EMERALD, 
            hover_color="#059669", 
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11), 
            command=self.play_timeline,
            height=30
        )
        self.play_timeline_btn.pack(fill="x", padx=15, pady=(5, 10))
        
        # Scrollable Keyframes list frame
        self.timeline_list_frame = ctk.CTkScrollableFrame(timeline_card, fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, height=130)
        self.timeline_list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.update_timeline_list()
        
        # Right Panel: Sliders & Accordions
        control_right_panel = ctk.CTkFrame(self.ctrl_frame, fg_color="transparent")
        control_right_panel.grid(row=0, column=1, sticky="nsew")
        control_right_panel.grid_columnconfigure(0, weight=1)
        control_right_panel.grid_rowconfigure(0, weight=0, minsize=50) # Search bar
        control_right_panel.grid_rowconfigure(1, weight=1)             # Motors list
        
        # Search & Filter bar row
        filter_row = ctk.CTkFrame(control_right_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=46)
        filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        filter_row.grid_propagate(False)
        
        self.search_entry = ctk.CTkEntry(
            filter_row, 
            placeholder_text="🔍 Filter joints by ID or Name (e.g. 'Shoulder', '12')...", 
            fg_color=BG_OSRS, 
            border_color=BORDER_OSRS,
            height=32,
            font=ctk.CTkFont(family="Outfit", size=12)
        )
        self.search_entry.pack(fill="x", padx=15, pady=6)
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_motor_rows())
        
        # Scrollable container for motors list
        self.motors_scroll = ctk.CTkScrollableFrame(
            control_right_panel, 
            fg_color=CARD_OSRS, 
            border_color=BORDER_OSRS, 
            border_width=1, 
            label_text="C.H.I.M.A.N Joint Telemetry & Control"
        )
        self.motors_scroll.grid(row=1, column=0, sticky="nsew")
        
        self.placeholder = ctk.CTkLabel(
            self.motors_scroll, 
            text="Please establish serial line connection to scan for Dynamixels.",
            font=ctk.CTkFont(family="Outfit", size=13),
            text_color=TEXT_MUTED
        )
        self.placeholder.pack(pady=150)
        
        # =====================================================================
        # TAB 3: ADVANCED DIAGNOSTICS & TUNING
        # =====================================================================
        self.diag_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.diag_frame.grid_columnconfigure(0, weight=1)
        self.diag_frame.grid_columnconfigure(1, weight=0, minsize=420)
        self.diag_frame.grid_rowconfigure(0, weight=1)
        
        # Left side: Live Telemetry Table
        telemetry_panel = ctk.CTkFrame(self.diag_frame, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        telemetry_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(telemetry_panel, text="Diagnostic Telemetry Dashboard", font=ctk.CTkFont(family="Outfit", weight="bold", size=14), text_color=ACCENT_PINK).pack(pady=(15, 10), padx=15, anchor="w")
        
        # Table Header
        tbl_hdr = ctk.CTkFrame(telemetry_panel, fg_color=CARD_INNER, height=30)
        tbl_hdr.pack(fill="x", padx=15, pady=2)
        tbl_hdr.pack_propagate(False)
        
        ctk.CTkLabel(tbl_hdr, text="NODE ID", font=("Outfit", 11, "bold"), text_color=TEXT_MUTED, width=50, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(tbl_hdr, text="JOINT DESCRIPTION", font=("Outfit", 11, "bold"), text_color=TEXT_MUTED, width=180, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(tbl_hdr, text="POSITION (PRES/GOAL)", font=("Outfit", 11, "bold"), text_color=TEXT_MUTED, width=120, anchor="center").pack(side="left", padx=10)
        ctk.CTkLabel(tbl_hdr, text="CURRENT", font=("Outfit", 11, "bold"), text_color=TEXT_MUTED, width=80, anchor="center").pack(side="left", padx=10)
        ctk.CTkLabel(tbl_hdr, text="TEMP", font=("Outfit", 11, "bold"), text_color=TEXT_MUTED, width=80, anchor="center").pack(side="left", padx=10)
        ctk.CTkLabel(tbl_hdr, text="VOLTAGE", font=("Outfit", 11, "bold"), text_color=TEXT_MUTED, width=80, anchor="center").pack(side="left", padx=10)
        ctk.CTkLabel(tbl_hdr, text="STATUS", font=("Outfit", 11, "bold"), text_color=TEXT_MUTED, width=80, anchor="center").pack(side="left", padx=10)
        
        # Scrollable area for telemetry table rows
        self.diag_scroll = ctk.CTkScrollableFrame(telemetry_panel, fg_color="transparent")
        self.diag_scroll.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Right side: Panel containing Inspector, Ping and PID tuning
        diag_right_panel = ctk.CTkScrollableFrame(self.diag_frame, fg_color="transparent")
        diag_right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Card 1: Dynamixel Control Table Inspector
        inspect_card = ctk.CTkFrame(diag_right_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        inspect_card.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(inspect_card, text="Register Read/Write Inspector", font=ctk.CTkFont(family="Outfit", weight="bold", size=12), text_color=ACCENT_PINK).pack(pady=(10, 6), padx=15, anchor="w")
        
        inspect_grid = ctk.CTkFrame(inspect_card, fg_color="transparent")
        inspect_grid.pack(fill="x", padx=15, pady=2)
        inspect_grid.grid_columnconfigure((0, 1), weight=1)
        
        # Target ID dropdown
        ctk.CTkLabel(inspect_grid, text="Select ID:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=0, column=0, padx=2, pady=1, sticky="w")
        self.inspect_id_menu = ctk.CTkOptionMenu(inspect_grid, values=["--"], height=26, fg_color=BG_OSRS, button_color=BORDER_OSRS)
        self.inspect_id_menu.grid(row=0, column=1, padx=2, pady=3, sticky="ew")
        
        # Register address dropdown
        ctk.CTkLabel(inspect_grid, text="Address:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=1, column=0, padx=2, pady=1, sticky="w")
        self.inspect_addr_menu = ctk.CTkOptionMenu(
            inspect_grid, 
            values=["11: Operating Mode (1B)", "64: Torque Enable (1B)", "84: Position P Gain (2B)", "82: Position I Gain (2B)", "80: Position D Gain (2B)", "112: Profile Vel (4B)", "116: Goal Position (4B)", "132: Present Position (4B)", "126: Present Current (2B)", "146: Present Temp (1B)"], 
            height=26, 
            fg_color=BG_OSRS, 
            button_color=BORDER_OSRS,
            command=self.on_inspect_addr_changed
        )
        self.inspect_addr_menu.grid(row=1, column=1, padx=2, pady=3, sticky="ew")
        
        # Numeric values
        ctk.CTkLabel(inspect_grid, text="Address Value:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=2, column=0, padx=2, pady=1, sticky="w")
        self.inspect_addr_val = ctk.CTkEntry(inspect_grid, height=26, fg_color=BG_OSRS, border_color=BORDER_OSRS)
        self.inspect_addr_val.insert(0, "116")
        self.inspect_addr_val.grid(row=2, column=1, padx=2, pady=3, sticky="ew")
        
        ctk.CTkLabel(inspect_grid, text="Byte Length:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=3, column=0, padx=2, pady=1, sticky="w")
        self.inspect_len_menu = ctk.CTkOptionMenu(inspect_grid, values=["1", "2", "4"], height=26, fg_color=BG_OSRS, button_color=BORDER_OSRS)
        self.inspect_len_menu.set("4")
        self.inspect_len_menu.grid(row=3, column=1, padx=2, pady=3, sticky="ew")
        
        ctk.CTkLabel(inspect_grid, text="Write Value:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).grid(row=4, column=0, padx=2, pady=1, sticky="w")
        self.inspect_write_val = ctk.CTkEntry(inspect_grid, placeholder_text="e.g. 2048", height=26, fg_color=BG_OSRS, border_color=BORDER_OSRS)
        self.inspect_write_val.grid(row=4, column=1, padx=2, pady=3, sticky="ew")
        
        # Result output
        self.inspect_result_lbl = ctk.CTkLabel(inspect_card, text="Awaiting transaction...", font=("JetBrains Mono", 10), text_color=TEXT_MUTED)
        self.inspect_result_lbl.pack(pady=4)
        
        inspect_actions = ctk.CTkFrame(inspect_card, fg_color="transparent")
        inspect_actions.pack(fill="x", padx=15, pady=(2, 10))
        inspect_actions.grid_columnconfigure((0, 1), weight=1)
        
        self.inspect_read_btn = ctk.CTkButton(inspect_actions, text="READ REGISTER", fg_color=ACCENT_BLUE, hover_color="#2563EB", height=28, font=ctk.CTkFont(size=10, weight="bold"), command=self.perform_inspect_read)
        self.inspect_read_btn.grid(row=0, column=0, padx=2, sticky="ew")
        
        self.inspect_write_btn = ctk.CTkButton(inspect_actions, text="WRITE REGISTER", fg_color=ACCENT_PINK, hover_color="#D11871", height=28, font=ctk.CTkFont(size=10, weight="bold"), command=self.perform_inspect_write)
        self.inspect_write_btn.grid(row=0, column=1, padx=2, sticky="ew")
        
        # Card 2: Direct ID Ping Utility
        ping_card = ctk.CTkFrame(diag_right_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        ping_card.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(ping_card, text="Ping Latency Diagnostics", font=ctk.CTkFont(family="Outfit", weight="bold", size=12), text_color=ACCENT_PINK).pack(pady=(10, 4), padx=15, anchor="w")
        
        ping_actions_frame = ctk.CTkFrame(ping_card, fg_color="transparent")
        ping_actions_frame.pack(fill="x", padx=15, pady=2)
        
        self.ping_id_entry = ctk.CTkEntry(ping_actions_frame, placeholder_text="ID e.g. 14", width=120, height=28, fg_color=BG_OSRS, border_color=BORDER_OSRS)
        self.ping_id_entry.insert(0, "14")
        self.ping_id_entry.pack(side="left", padx=(0, 10))
        
        self.ping_btn = ctk.CTkButton(ping_actions_frame, text="PING NODE", fg_color=ACCENT_VIOLET, hover_color="#4F46E5", height=28, font=ctk.CTkFont(size=11, weight="bold"), command=self.perform_ping)
        self.ping_btn.pack(side="left", fill="x", expand=True)
        
        self.ping_result_lbl = ctk.CTkLabel(ping_card, text="Awaiting Ping command...", font=("JetBrains Mono", 10), text_color=TEXT_MUTED)
        self.ping_result_lbl.pack(pady=(2, 10))
        
        # Card 3: PID Loop Tuning Dashboard and Curve Canvas
        pid_card = ctk.CTkFrame(diag_right_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        pid_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(pid_card, text="PID Gain Configuration", font=ctk.CTkFont(family="Outfit", weight="bold", size=12), text_color=ACCENT_PINK).pack(pady=(10, 4), padx=15, anchor="w")
        
        pid_options = ctk.CTkFrame(pid_card, fg_color="transparent")
        pid_options.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(pid_options, text="Target Tuning ID:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
        self.pid_id_menu = ctk.CTkOptionMenu(pid_options, values=["--"], height=24, fg_color=BG_OSRS, button_color=BORDER_OSRS, command=self.on_pid_target_changed)
        self.pid_id_menu.pack(side="right")
        
        # Sliders for KP, KI, KD
        pid_sliders = ctk.CTkFrame(pid_card, fg_color="transparent")
        pid_sliders.pack(fill="x", padx=15, pady=4)
        
        # KP
        ctk.CTkLabel(pid_sliders, text="Proportional Gain (K_P):", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w")
        self.pid_kp_slider = ctk.CTkSlider(pid_sliders, from_=0, to=2000, number_of_steps=200, fg_color=BG_OSRS, progress_color=ACCENT_VIOLET, button_color=ACCENT_VIOLET, command=self.on_pid_slider_changed)
        self.pid_kp_slider.set(850)
        self.pid_kp_slider.pack(fill="x", pady=(1, 5))
        
        # KI
        ctk.CTkLabel(pid_sliders, text="Integral Gain (K_I):", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w")
        self.pid_ki_slider = ctk.CTkSlider(pid_sliders, from_=0, to=500, number_of_steps=100, fg_color=BG_OSRS, progress_color=ACCENT_VIOLET, button_color=ACCENT_VIOLET, command=self.on_pid_slider_changed)
        self.pid_ki_slider.set(0)
        self.pid_ki_slider.pack(fill="x", pady=(1, 5))
        
        # KD
        ctk.CTkLabel(pid_sliders, text="Derivative Gain (K_D):", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w")
        self.pid_kd_slider = ctk.CTkSlider(pid_sliders, from_=0, to=2000, number_of_steps=200, fg_color=BG_OSRS, progress_color=ACCENT_VIOLET, button_color=ACCENT_VIOLET, command=self.on_pid_slider_changed)
        self.pid_kd_slider.set(0)
        self.pid_kd_slider.pack(fill="x", pady=(1, 5))
        
        # Profile velocity
        ctk.CTkLabel(pid_sliders, text="Profile Velocity limit:", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w")
        self.pid_vel_slider = ctk.CTkSlider(pid_sliders, from_=0, to=1000, number_of_steps=100, fg_color=BG_OSRS, progress_color=ACCENT_VIOLET, button_color=ACCENT_VIOLET, command=self.on_pid_vel_changed)
        self.pid_vel_slider.set(100)
        self.pid_vel_slider.pack(fill="x", pady=(1, 10))
        
        # Oscilloscope Canvas Step Response
        ctk.CTkLabel(pid_card, text="PID Step Response Scope Simulation", font=ctk.CTkFont(family="Outfit", size=10, weight="bold"), text_color=TEXT_MUTED).pack(padx=15, anchor="w")
        self.pid_canvas = tk.Canvas(pid_card, height=130, bg="#0F0F11", highlightthickness=0)
        self.pid_canvas.pack(fill="x", padx=15, pady=(2, 10))
        self.pid_canvas.bind("<Configure>", lambda event: self.draw_pid_simulation())
        
        self.draw_pid_simulation()
        
        # Card 4: Macro Automation Console
        macro_card = ctk.CTkFrame(diag_right_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        macro_card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(macro_card, text="Script Execution Panel", font=ctk.CTkFont(family="Outfit", weight="bold", size=12), text_color=ACCENT_PINK).pack(pady=(10, 4), padx=15, anchor="w")
        self.macro_entry = ctk.CTkTextbox(macro_card, font=ctk.CTkFont(family="JetBrains Mono", size=11), fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, height=60)
        self.macro_entry.pack(fill="x", padx=15, pady=2)
        self.macro_entry.insert("1.0", "# Example Macro:\nmove(14, 6291)\nwait(1.0)\nmove(25, -150)\nwait(1.0)")
        
        self.macro_btn = ctk.CTkButton(macro_card, text="EXECUTE MACRO", fg_color=ACCENT_EMERALD, hover_color="#059669", font=ctk.CTkFont(size=11, weight="bold"), command=self.execute_macro, height=28)
        self.macro_btn.pack(fill="x", padx=15, pady=(5, 12))
        
        # Hook window close handlers
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Show first tab
        self.show_tab("connection")
        
    def show_tab(self, tab_name):
        self.active_tab = tab_name
        # Hide all
        self.conn_frame.pack_forget()
        self.ctrl_frame.pack_forget()
        self.diag_frame.pack_forget()
        
        # Reset sidebar navigation button styling
        self.tab_btn_conn.configure(fg_color="transparent", text_color=TEXT_MUTED)
        self.tab_btn_ctrl.configure(fg_color="transparent", text_color=TEXT_MUTED)
        self.tab_btn_diag.configure(fg_color="transparent", text_color=TEXT_MUTED)
        
        if tab_name == "connection":
            self.conn_frame.pack(fill="both", expand=True)
            self.tab_btn_conn.configure(fg_color=BORDER_OSRS, text_color=ACCENT_PINK)
            self.draw_topology_map()
        elif tab_name == "control":
            self.ctrl_frame.pack(fill="both", expand=True)
            self.tab_btn_ctrl.configure(fg_color=BORDER_OSRS, text_color=ACCENT_PINK)
        elif tab_name == "diagnostics":
            self.diag_frame.pack(fill="both", expand=True)
            self.tab_btn_diag.configure(fg_color=BORDER_OSRS, text_color=ACCENT_PINK)
            self.update_diag_table()
            
    def toggle_virtual_mode(self):
        self.virtual_mode = self.sim_mode_switch.get()
        state_str = "VIRTUAL MODE ENABLED" if self.virtual_mode else "VIRTUAL MODE DISABLED"
        self.log_message(state_str, level="WARNING")
        
    def toggle_connection(self):
        if self.connected:
            self.disconnect_bus()
        else:
            self.connect_bus()
            
    def connect_bus(self):
        port = self.port_entry.get().strip()
        try:
            baud = int(self.baud_menu.get())
        except ValueError:
            self.log_card_status("Invalid baudrate!", error=True)
            self.log_message("Invalid baudrate specified!", level="ERROR")
            return
            
        self.log_message(f"Connecting to port {port} at {baud} bps...", level="CMD")
        self.log_card_status(f"Opening {port}...")
        
        profile = "Humanoid V1"
        target_ids = sorted(list(ROBOT_PROFILES.get(profile, {}).keys()))
        
        if not target_ids:
            target_ids = list(range(60))
            
        self.log_message(f"Initializing Dynamixel bus scan for IDs {min(target_ids)}-{max(target_ids)}...", level="INFO")
        
        self.driver = DynamixelDriver(port=port, baudrate=baud, motor_ids=target_ids, mock_mode=self.virtual_mode)
        if not self.driver.connect():
            self.log_card_status("Port unavailable!", error=True)
            self.log_message(f"Failed to open port {port}. Line is locked or missing.", level="ERROR")
            self.driver = None
            return
            
        discovered = self.driver.scan()
        if not discovered:
            self.log_card_status("No nodes found!", error=True)
            self.log_message("Bus scan returned 0 active Dynamixels.", level="ERROR")
            self.driver.disconnect()
            self.driver = None
            return
            
        self.active_ids = sorted(discovered)
        self.online_ids = self.active_ids.copy()
        self.consecutive_failures = {mid: 0 for mid in self.active_ids}
        self.driver.motor_ids = self.active_ids
        
        self.log_message(f"SUCCESS: Scanned and found {len(self.active_ids)} Dynamixel nodes.", level="SUCCESS")
        
        # Extended position control (Mode 4)
        self.log_message("Enforcing Extended Position Control Mode (Mode 4)...", level="INFO")
        self.driver.set_operating_mode(self.active_ids, mode=4)
        
        # Build UI layout
        self.placeholder.pack_forget()
        self.build_motor_rows()
        self.filter_motor_rows()
        
        # Populate inspector and PID tuning dropdown menus
        id_strs = [str(mid) for mid in self.active_ids]
        self.inspect_id_menu.configure(values=id_strs)
        self.inspect_id_menu.set(id_strs[0])
        self.pid_id_menu.configure(values=id_strs)
        self.pid_id_menu.set(id_strs[0])
        
        # Enable UI options
        self.connected = True
        self.conn_btn.configure(text="DISCONNECT", fg_color=ACCENT_CRIMSON, hover_color="#C01662")
        self.scan_btn.configure(state="normal", fg_color="#334155", text_color="#FFFFFF")
        self.torque_on_btn.configure(state="normal", fg_color=ACCENT_EMERALD, text_color="#FFFFFF")
        self.torque_off_btn.configure(state="normal", fg_color="#334155", text_color="#FFFFFF")
        self.both_arms_pose_btn.configure(state="normal", fg_color=ACCENT_PINK, text_color="#FFFFFF")
        self.left_arm_pose_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.right_arm_pose_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.left_arm_up_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.left_arm_center_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.left_arm_down_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.left_hand_open_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.left_hand_closed_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.preset_zero_btn.configure(state="normal", fg_color=BG_OSRS, text_color=TEXT_PRIMARY)
        self.sync_goals_btn.configure(state="normal", fg_color=CARD_INNER, text_color=TEXT_PRIMARY)
        
        # Update cards
        self.dash_card1.configure(border_color=ACCENT_VIOLET)
        self.card1_lbl.configure(text=f"PORT: {port}\nBAUD: {baud}", text_color=TEXT_PRIMARY)
        
        self.dash_card2.configure(border_color=ACCENT_EMERALD)
        self.card2_lbl.configure(text=f"ACTIVE NODES\n{len(self.active_ids)} Online", text_color=ACCENT_EMERALD)
        
        self.status_msg = f"ONLINE // {len(self.active_ids)} nodes"
        self.status_is_err = False
        
        # Redraw topography
        self.draw_topology_map()
        
        # Launch workers
        self.running = True
        self.worker_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.worker_thread.start()
        
        self.start_telemetry_loop()
        
    def connect_with_params(self, port, baud):
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, port)
        self.baud_menu.set(str(baud))
        self.connect_bus()
        
    def disconnect_bus(self):
        self.running = False
        self.telemetry_loop_active = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
            self.worker_thread = None
            
        if self.driver:
            self.driver.disable_torque(self.active_ids)
            self.driver.disconnect()
            self.driver = None
            
        self.connected = False
        self.online_ids.clear()
        self.consecutive_failures.clear()
        self.last_written_positions.clear()
        self.present_currents.clear()
        self.present_temperatures.clear()
        self.present_voltages.clear()
        
        self.log_message("Bus disconnected. Relayed torque shutdown commands.", level="WARNING")
        
        self.conn_btn.configure(text="CONNECT BUS", fg_color=ACCENT_PINK, hover_color="#D11871")
        self.scan_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.torque_on_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.torque_off_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.both_arms_pose_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.left_arm_pose_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.right_arm_pose_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.left_arm_up_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.left_arm_center_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.left_arm_down_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.left_hand_open_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.left_hand_closed_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.preset_zero_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        self.sync_goals_btn.configure(state="disabled", fg_color="#18181B", text_color="#71717A")
        
        # Tear down motor rows inside collapsible accordions
        for mid, frame in list(self.motor_row_widgets.items()):
            try:
                frame.destroy()
            except Exception:
                pass
        self.motor_row_widgets.clear()
        self.motor_widgets.clear()
        
        # Clean accordions frame packing
        for accordion in self.accordions.values():
            accordion.destroy()
        self.accordions.clear()
        
        self.placeholder.pack(pady=150)
        
        # Clear Diagnostics rows
        for mid, w in list(self.diag_rows.items()):
            try:
                w["row_frame"].destroy()
            except Exception:
                pass
        self.diag_rows.clear()
        
        # Clear cards
        self.dash_card1.configure(border_color=BORDER_OSRS)
        self.card1_lbl.configure(text="COM PORT // BAUD\nDisconnections active", text_color=TEXT_MUTED)
        
        self.dash_card2.configure(border_color=BORDER_OSRS)
        self.card2_lbl.configure(text="NODES DETECTED\n0 active on bus", text_color=TEXT_MUTED)
        
        self.dash_card3.configure(border_color=BORDER_OSRS)
        self.card3_lbl.configure(text="BUS LATENCY // TIME\n-- ms average", text_color=TEXT_MUTED)
        
        self.active_ids = []
        self.status_msg = "DISCONNECTED"
        self.status_is_err = True
        self.last_rendered_states.clear()
        self.last_status_state.clear()
        self.draw_topology_map()
        
    def trigger_rescan(self):
        if not self.connected or not self.driver:
            return
        
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
            self.worker_thread = None
            
        self.log_message("Re-scanning bus for responsive nodes...", level="CMD")
        self.log_card_status("Re-scanning IDs...")
        discovered = self.driver.scan()
        if discovered:
            self.active_ids = sorted(discovered)
            self.online_ids = self.active_ids.copy()
            self.consecutive_failures = {mid: 0 for mid in self.active_ids}
            self.driver.motor_ids = self.active_ids
            self.driver.set_operating_mode(self.active_ids, mode=4)
            
            # Rebuild UI
            self.build_motor_rows()
            self.filter_motor_rows()
            
            # Populate dropdown lists
            id_strs = [str(mid) for mid in self.active_ids]
            self.inspect_id_menu.configure(values=id_strs)
            self.inspect_id_menu.set(id_strs[0])
            self.pid_id_menu.configure(values=id_strs)
            self.pid_id_menu.set(id_strs[0])
            
            self.card2_lbl.configure(text=f"ACTIVE NODES\n{len(self.active_ids)} Online", text_color=ACCENT_EMERALD)
            self.status_msg = f"ONLINE // {len(self.active_ids)} nodes"
            self.status_is_err = False
            self.log_message(f"Rescan complete. Found {len(self.active_ids)} active nodes.", level="SUCCESS")
            
            # Rebuild diag table
            for mid, w in list(self.diag_rows.items()):
                try:
                    w["row_frame"].destroy()
                except Exception:
                    pass
            self.diag_rows.clear()
            if self.active_tab == "diagnostics":
                self.update_diag_table()
        else:
            self.active_ids = []
            self.status_msg = "Scan returned zero nodes!"
            self.status_is_err = True
            self.log_message("Rescan returned no motors on the line.", level="ERROR")
            
        self.draw_topology_map()
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.worker_thread.start()
        
    def start_auto_baud_scan(self):
        self.autobaud_btn.configure(state="disabled", text="SCANNING...")
        threading.Thread(target=self._auto_baud_scan_thread, daemon=True).start()
        
    def _auto_baud_scan_thread(self):
        self.log_message("Initializing Auto-Baudrate scan sequence...", level="CMD")
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            self.log_message("Auto-Baud failed: No serial COM ports detected on this system.", level="ERROR")
            self.after(0, lambda: self.autobaud_btn.configure(state="normal", text="AUTO-BAUD SCANNER"))
            return
            
        bauds = [4000000, 2000000, 1000000, 115200, 57600]
        profile = "Humanoid V1"
        target_ids = sorted(list(ROBOT_PROFILES.get(profile, {}).keys()))
        
        for port in ports:
            for baud in bauds:
                self.log_message(f"Scanning port {port} at {baud} bps...", level="INFO")
                try:
                    test_driver = DynamixelDriver(port=port, baudrate=baud, motor_ids=target_ids, mock_mode=False)
                    if test_driver.connect():
                        # Just test if we can ping the first ID or scan
                        discovered = test_driver.scan()
                        test_driver.disconnect()
                        if discovered:
                            self.log_message(f"SUCCESS: Auto-Baud discovered active motors on {port} @ {baud} bps!", level="SUCCESS")
                            self.after(0, lambda p=port, b=baud: self.connect_with_params(p, b))
                            self.after(0, lambda: self.autobaud_btn.configure(state="normal", text="AUTO-BAUD SCANNER"))
                            return
                except Exception:
                    pass
                    
        self.log_message("Auto-Baud sequence complete. No responsive Dynamixel nodes found on any port.", level="WARNING")
        self.after(0, lambda: self.autobaud_btn.configure(state="normal", text="AUTO-BAUD SCANNER"))
        
    def draw_topology_map(self):
        self.topo_canvas.delete("all")
        w = self.topo_canvas.winfo_width()
        h = self.topo_canvas.winfo_height()
        if w <= 1: w = 700
        if h <= 1: h = 220
        
        # Grid layout background
        self.topo_canvas.create_rectangle(0, 0, w, h, fill="#0F0F11", outline="")
        for grid_x in range(0, w, 50):
            self.topo_canvas.create_line(grid_x, 0, grid_x, h, fill="#1F1F22", width=1)
        for grid_y in range(0, h, 50):
            self.topo_canvas.create_line(0, grid_y, w, grid_y, fill="#1F1F22", width=1)
            
        if not self.connected or not self.active_ids:
            self.topo_canvas.create_text(w/2, h/2, text="BUS OFFLINE - ESTABLISH CONNECTION", fill=TEXT_MUTED, font=("Outfit", 12, "bold"))
            return
            
        num_nodes = len(self.active_ids)
        # Determine grid / circle layout coordinates
        # Draw circles sequentially in an elegant winding row or multi-line path
        margin_x = 40
        spacing_x = (w - 2 * margin_x) / max(1, num_nodes - 1)
        if spacing_x < 50:
            spacing_x = 55 # Override to fit neatly
            
        points = []
        for i, mid in enumerate(self.active_ids):
            # If line runs out of bounds, fold it
            x = margin_x + i * spacing_x
            row_idx = int(x // (w - 20))
            x_pos = margin_x + (i * spacing_x) % (w - 80)
            y_pos = 50 + row_idx * 70
            points.append((x_pos, y_pos))
            
        # Draw connections
        if len(points) > 1:
            for i in range(len(points) - 1):
                self.topo_canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=BORDER_OSRS, width=3)
                
        # Draw node circles
        for i, mid in enumerate(self.active_ids):
            x, y = points[i]
            is_online = mid in self.online_ids
            color = ACCENT_EMERALD if is_online else ACCENT_CRIMSON
            outline_color = ACCENT_PINK if (mid in self.goal_positions and self.torque_state.get(mid, False)) else BORDER_OSRS
            
            # Hover highlight circle
            self.topo_canvas.create_oval(x-20, y-20, x+20, y+20, fill=color, outline=outline_color, width=2)
            self.topo_canvas.create_text(x, y, text=str(mid), fill="#FFFFFF", font=("JetBrains Mono", 10, "bold"))
            
            # Short label under node
            name = self.get_joint_name(mid, "Humanoid V1")
            short_name = name.split("(")[-1].replace(")", "") if "(" in name else name[:6]
            self.topo_canvas.create_text(x, y+26, text=short_name, fill=TEXT_MUTED, font=("Outfit", 8))
            
    def log_card_status(self, text, error=False):
        color = ACCENT_CRIMSON if error else ACCENT_PINK
        self.card1_lbl.configure(text=text, text_color=color)
        
    def log_message(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level.upper()}] {message}\n"
        if hasattr(self, 'console_txt') and self.console_txt:
            self.console_txt.configure(state="normal")
            tag = level.lower()
            if tag not in ["info", "warning", "error", "success", "cmd"]:
                tag = "info"
            self.console_txt.insert("end", formatted, tag)
            self.console_txt.see("end")
            self.console_txt.configure(state="disabled")
        print(formatted, end="")
        
    def start_telemetry_loop(self):
        self.telemetry_loop_active = True
        self.run_telemetry_loop()
        
    def run_telemetry_loop(self):
        if not self.telemetry_loop_active:
            return
        self.update_gui_telemetry()
        self.after(40, self.run_telemetry_loop)  # 25Hz Refresh
        
    def toggle_mirror_sync(self):
        self.mirror_sync_active = self.mirror_switch.get()
        state_str = "DUAL-ARM MIRROR SYNC ON" if self.mirror_sync_active else "DUAL-ARM MIRROR SYNC OFF"
        self.log_message(state_str, level="WARNING")
        
    def set_global_torque(self, enable):
        if not self.driver:
            return
        with self.lock:
            for mid in self.online_ids:
                if enable:
                    self.pending_torque_actions.add(mid)
            self.pending_actions.append({
                "type": "global_torque",
                "enable": enable
            })
            
    def reboot_motor(self, motor_id):
        if not self.driver:
            return
        with self.lock:
            if motor_id not in self.online_ids:
                self.online_ids.append(motor_id)
                self.online_ids.sort()
                self.consecutive_failures[motor_id] = 0
            self.pending_actions.append({
                "type": "reboot",
                "motor_id": motor_id
            })
            
    def trigger_estop(self):
        self.log_message("ESTOP TRIGGERED! Shutting down bus torque immediately.", level="ERROR")
        self.set_global_torque(False)
        self.disconnect_bus()
        
    def build_motor_rows(self):
        # Clean current widget lists
        for mid, frame in list(self.motor_row_widgets.items()):
            try:
                frame.destroy()
            except Exception:
                pass
        self.motor_row_widgets.clear()
        self.motor_widgets.clear()
        
        for accordion in list(self.accordions.values()):
            try:
                accordion.destroy()
            except Exception:
                pass
        self.accordions.clear()
        
        # Build new collapsible accordions
        self.accordions = {
            "left": CollapsibleFrame(self.motors_scroll, "🦾 LEFT ARM (IDs 21 - 28)"),
            "right": CollapsibleFrame(self.motors_scroll, "🦾 RIGHT ARM (IDs 11 - 18, 2)"),
            "head": CollapsibleFrame(self.motors_scroll, "👤 HEAD & NECK (IDs 31 - 32)"),
            "general": CollapsibleFrame(self.motors_scroll, "⚙ AUXILIARY / GENERAL ACTUATORS")
        }
        for accordion in self.accordions.values():
            accordion.pack(fill="x", padx=5, pady=4)
            
        current_profile = "Humanoid V1"
        
        for mid in self.active_ids:
            name = self.get_joint_name(mid, current_profile)
            # Find appropriate accordion
            if name.startswith("L ") or "L Shoulder" in name or "L Elbow" in name or "L Forearm" in name or "L Wrist" in name or "L Hand" in name or "L1" in name or "L2" in name or "L3" in name or "L4" in name or "L5" in name or "L6" in name or "L7" in name or "L8" in name:
                parent_frame = self.accordions["left"].content
            elif name.startswith("R ") or "R Shoulder" in name or "R Elbow" in name or "R Forearm" in name or "R Wrist" in name or "R Hand" in name or "R1" in name or "R2" in name or "R3" in name or "R4" in name or "R5" in name or "R6" in name or "R7" in name or "R8" in name or mid == 2:
                parent_frame = self.accordions["right"].content
            elif "Head" in name or name.startswith("Head") or mid in [31, 32]:
                parent_frame = self.accordions["head"].content
            else:
                parent_frame = self.accordions["general"].content
                
            # Row Card Container
            row_card = ctk.CTkFrame(parent_frame, fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, height=85)
            row_card.pack(fill="x", padx=10, pady=5)
            row_card.pack_propagate(False)
            self.motor_row_widgets[mid] = row_card
            
            # Grid Layout for Row Card
            row_card.grid_columnconfigure(0, weight=2, minsize=140) # Details / Badge
            row_card.grid_columnconfigure(1, weight=1, minsize=90)  # Telemetry feedback
            row_card.grid_columnconfigure(2, weight=4, minsize=120) # Slider
            row_card.grid_columnconfigure(3, weight=0, minsize=170) # Shift adjustments
            row_card.grid_columnconfigure(4, weight=0, minsize=76)  # Precise value Entry
            row_card.grid_columnconfigure(5, weight=0, minsize=80)  # Torque Switch
            row_card.grid_columnconfigure(6, weight=0, minsize=80)  # Reboot Button
            
            # Col 0: Name Details & Status Badge
            joint_name = name
            name_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            name_frame.grid(row=0, column=0, padx=12, pady=18, sticky="w")
            
            name_lbl = ctk.CTkLabel(
                name_frame, 
                text=f"ID {mid:02d}: {joint_name}", 
                font=ctk.CTkFont(family="Outfit", weight="bold", size=13), 
                anchor="w"
            )
            name_lbl.pack(anchor="w")
            
            badge_lbl = ctk.CTkLabel(
                name_frame, 
                text="ONLINE", 
                font=ctk.CTkFont(family="Outfit", size=9, weight="bold"),
                text_color=ACCENT_EMERALD,
                anchor="w"
            )
            badge_lbl.pack(anchor="w")
            
            # Col 1: Telemetry details
            telemetry_lbl = ctk.CTkLabel(
                row_card, 
                text="Present: --\nGoal: --", 
                font=ctk.CTkFont(family="JetBrains Mono", size=11), 
                text_color=TEXT_MUTED,
                justify="left",
                anchor="w"
            )
            telemetry_lbl.grid(row=0, column=1, padx=5, pady=15, sticky="w")
            
            # Init base goal / present maps
            self.goal_positions[mid] = 2048
            self.present_positions[mid] = 2048
            self.torque_state[mid] = False
            
            # Col 2: Slider control
            slider = ctk.CTkSlider(row_card, from_=-8192, to=8192, number_of_steps=400, fg_color=BG_OSRS, progress_color=ACCENT_VIOLET, button_color=ACCENT_VIOLET)
            slider.set(2048)
            slider.grid(row=0, column=2, padx=10, pady=22, sticky="ew")
            
            # Col 4: Precise numeric input
            entry = ctk.CTkEntry(row_card, width=70, height=28, font=ctk.CTkFont(family="JetBrains Mono", size=11), fg_color=BG_OSRS, border_color=BORDER_OSRS)
            entry.insert(0, "2048")
            entry.grid(row=0, column=4, padx=4, pady=22)
            
            # Bind callbacks
            def make_slider_cb(m_id, entry_w):
                return lambda val: self.update_goal_position(m_id, int(val), source_entry=False, entry_widget=entry_w)
                
            def make_entry_cb(m_id, slider_w, entry_w):
                return lambda event: self.on_entry_entered(m_id, slider_w, entry_w)
                
            slider.configure(command=make_slider_cb(mid, entry))
            entry.bind("<Return>", make_entry_cb(mid, slider, entry))
            
            # Col 3: Shift controller buttons
            shift_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            shift_frame.grid(row=0, column=3, padx=5, pady=20)
            
            shifts = [("-4k", -4096), ("-1k", -1024), ("0", 0), ("+1k", 1024), ("+4k", 4096)]
            for s_idx, (s_lbl, s_offset) in enumerate(shifts):
                btn = ctk.CTkButton(
                    shift_frame, 
                    text=s_lbl, 
                    width=32, 
                    height=24, 
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color=BG_OSRS,
                    hover_color=ACCENT_VIOLET,
                    command=lambda m=mid, o=s_offset, sl=slider, en=entry: self.shift_position(m, o, sl, en)
                )
                btn.grid(row=0, column=s_idx, padx=1)
                
            # Col 5: Individual Torque Switch
            t_switch = ctk.CTkSwitch(
                row_card, 
                text="Torque", 
                width=70,
                font=ctk.CTkFont(family="Outfit", size=10, weight="bold"),
                text_color=TEXT_MUTED,
                progress_color=ACCENT_EMERALD,
                command=lambda m=mid: self.on_row_torque_toggle(m)
            )
            t_switch.grid(row=0, column=5, padx=4, pady=22)
            
            # Col 6: Reboot button
            reboot_btn = ctk.CTkButton(
                row_card, 
                text="Reboot", 
                width=70, 
                height=26,
                font=ctk.CTkFont(family="Outfit", size=10, weight="bold"),
                fg_color="#1E293B",
                hover_color=ACCENT_CRIMSON,
                command=lambda m=mid: self.reboot_motor(m)
            )
            reboot_btn.grid(row=0, column=6, padx=8, pady=22)
            
            # Cache UI references
            self.motor_widgets[mid] = {
                "name_lbl": name_lbl,
                "badge_lbl": badge_lbl,
                "telemetry_lbl": telemetry_lbl,
                "slider": slider,
                "entry": entry,
                "t_switch": t_switch,
                "reboot_btn": reboot_btn,
                "row_card": row_card
            }

    def get_joint_name(self, mid, profile):
        if profile == "All (Merged)":
            matches = []
            for prof, mapping in ROBOT_PROFILES.items():
                if mid in mapping:
                    matches.append(mapping[mid])
            if matches:
                return " / ".join(list(dict.fromkeys(matches)))
            return f"Joint ID {mid}"
        else:
            mapping = ROBOT_PROFILES.get(profile, {})
            return mapping.get(mid, f"Joint ID {mid}")
            
    def update_joint_names_display(self):
        profile = "Humanoid V1"
        for mid in self.active_ids:
            if mid in self.motor_widgets:
                name_lbl = self.motor_widgets[mid]["name_lbl"]
                name_lbl.configure(text=f"ID {mid:02d}: {self.get_joint_name(mid, profile)}")
                
    def filter_motor_rows(self):
        query = self.search_entry.get().strip().lower()
        selected_profile = "Humanoid V1"
        
        for mid in self.active_ids:
            if mid in self.motor_widgets:
                row_card = self.motor_row_widgets[mid]
                name_text = self.get_joint_name(mid, selected_profile).lower()
                id_str = str(mid)
                
                if not query or (query in id_str) or (query in name_text):
                    row_card.pack(fill="x", padx=10, pady=5)
                else:
                    row_card.pack_forget()

    # Preset Actions
    def preset_zero_all(self):
        self.log_message("Preset: Zeroing all online motors.", level="CMD")
        for mid in self.active_ids:
            self.set_goal_value_direct(mid, 2048)
            
    def preset_sync_goals(self):
        self.log_message("Preset: Syncing goals to present encoder ticks.", level="CMD")
        with self.lock:
            for mid in self.active_ids:
                pres = self.present_positions.get(mid, 2048)
                self.goal_positions[mid] = pres
                
        for mid in self.active_ids:
            if mid in self.motor_widgets:
                self.sync_widgets_to_goal(mid, self.goal_positions[mid])
                
    def preset_humanoid_home(self):
        self.log_message("Preset: Loading Humanoid Home pose configuration.", level="CMD")
        for mid, home_val in HUMANOID_DEFAULTS.items():
            if mid in self.active_ids:
                self.set_goal_value_direct(mid, home_val)
                
    def preset_left_arm_offsets(self):
        left_arm_offsets = {24: 4026, 25: -82, 26: -1019, 27: 2065}
        
        joints_to_torque = [mid for mid in left_arm_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming Left Arm joints..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = left_arm_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, left_arm_offsets[mid])
                
    def preset_left_arm_up(self):
        left_arm_offsets = {24: 4026, 25: -150, 26: -1019, 27: 2065, 14: 6441}
        joints_to_torque = [mid for mid in left_arm_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming Left Arm Up..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = left_arm_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, left_arm_offsets[mid])
                
    def preset_left_arm_down(self):
        left_arm_offsets = {24: 4026, 25: 50, 26: -1019, 27: 2065, 14: 6141}
        joints_to_torque = [mid for mid in left_arm_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming Left Arm Down..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = left_arm_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, left_arm_offsets[mid])
                
    def preset_left_arm_center(self):
        left_arm_offsets = {24: 4026, 25: -50, 26: -1019, 27: 2065, 14: 6291}
        joints_to_torque = [mid for mid in left_arm_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming Left Arm Center..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = left_arm_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, left_arm_offsets[mid])
                
    def preset_left_hand_open(self):
        left_hand_offsets = {28: 860}
        joints_to_torque = [mid for mid in left_hand_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Opening Left Hand..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = left_hand_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, left_hand_offsets[mid])
                
    def preset_left_hand_closed(self):
        left_hand_offsets = {28: -685}
        joints_to_torque = [mid for mid in left_hand_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Closing Left Hand..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = left_hand_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, left_hand_offsets[mid])
                
    def preset_right_arm_offsets(self):
        right_arm_offsets = {14: 6291, 15: 4093, 16: 3093, 17: 4893}
        
        joints_to_torque = [mid for mid in right_arm_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming Right Arm joints..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = right_arm_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, right_arm_offsets[mid])
                
    def preset_both_arms_offsets(self):
        left_arm_offsets = {24: 4026, 25: -82, 26: -1019, 27: 2065}
        right_arm_offsets = {14: 6291, 15: 4093, 16: 3093, 17: 4893}
        both_offsets = {**left_arm_offsets, **right_arm_offsets}
        
        joints_to_torque = [mid for mid in both_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming both arms..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    self.pending_torque_actions.add(mid)
                    self.goal_positions[mid] = both_offsets[mid]
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, both_offsets[mid])
                
    def apply_leap_v1_preset(self, gesture):
        targets = get_v1_preset_ticks(gesture)
        for mid, val in targets.items():
            if mid in self.active_ids:
                self.set_goal_value_direct(mid, val)
                
    def apply_leap_v2_preset(self, gesture):
        targets = get_v2_preset_ticks(gesture)
        for mid, val in targets.items():
            if mid in self.active_ids:
                self.set_goal_value_direct(mid, val)
                
    def save_pose_dialog(self):
        file_path = filedialog.asksaveasfilename(
            initialdir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch"),
            title="Save Pose Preset",
            filetypes=[("JSON Files", "*.json")],
            defaultextension=".json"
        )
        if not file_path:
            return
        try:
            with self.lock:
                pose_data = {str(mid): self.present_positions.get(mid, 2048) for mid in self.active_ids}
            with open(file_path, "w") as f:
                json.dump(pose_data, f, indent=4)
            self.log_message("Preset saved successfully!", level="SUCCESS")
        except Exception as e:
            self.log_message(f"Save failed: {str(e)}", level="ERROR")
            
    def load_pose_dialog(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch"),
            title="Load Pose Preset",
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r") as f:
                pose_data = json.load(f)
            for smid, val in pose_data.items():
                mid = int(smid)
                if mid in self.active_ids:
                    self.set_goal_value_direct(mid, int(val))
            self.log_message("Preset loaded successfully!", level="SUCCESS")
        except Exception as e:
            self.log_message(f"Load failed: {str(e)}", level="ERROR")

    def get_mirrored_position(self, mid, val):
        defaults = HUMANOID_DEFAULTS
        calib_left = {24: 4026, 25: -82, 26: -1019, 27: 2065, 28: 860}
        calib_right = {14: 6291, 15: 4093, 16: 3093, 17: 4893, 18: -685}
        
        ref_centers = {**defaults, **calib_left, **calib_right}
        
        partner = MIRROR_PARTNERS.get(mid)
        if not partner or partner not in ref_centers or mid not in ref_centers:
            return val
            
        center_self = ref_centers[mid]
        center_partner = ref_centers[partner]
        
        delta = val - center_self
        
        # Determine mirror rotation rules (opposite or matching directional kinematics)
        opposite_joints = {24, 14, 25, 15, 26, 16, 28, 18, 13, 23}
        if mid in opposite_joints:
            mirrored_val = center_partner - delta
        else:
            mirrored_val = center_partner + delta
            
        return int(mirrored_val)

    def set_goal_value_direct(self, motor_id, value):
        with self.lock:
            self.goal_positions[motor_id] = value
        if motor_id in self.motor_widgets:
            self.sync_widgets_to_goal(motor_id, value)
            
        # Symmetrical Mirror Execution Path
        if self.mirror_sync_active and not self._in_mirror_sync:
            partner_id = MIRROR_PARTNERS.get(motor_id)
            if partner_id and partner_id in self.active_ids:
                mirrored_val = self.get_mirrored_position(motor_id, value)
                with self.lock:
                    prev_partner_goal = self.goal_positions.get(partner_id)
                if prev_partner_goal != mirrored_val:
                    self._in_mirror_sync = True
                    try:
                        self.set_goal_value_direct(partner_id, mirrored_val)
                    finally:
                        self._in_mirror_sync = False
            
    def sync_widgets_to_goal(self, motor_id, value):
        widgets = self.motor_widgets[motor_id]
        slider = widgets["slider"]
        entry = widgets["entry"]
        
        # Dynamically scale sliders
        s_min = slider.cget("from_")
        s_max = slider.cget("to")
        if value > s_max:
            slider.configure(to=value + 2048)
        elif value < s_min:
            slider.configure(from_=value - 2048)
            
        # Temporarily detach command to avoid loops
        slider.configure(command=None)
        slider.set(value)
        slider.configure(command=lambda val, m=motor_id, en=entry: self.update_goal_position(m, int(val), source_entry=False, entry_widget=en))
        
        entry.delete(0, tk.END)
        entry.insert(0, str(value))

    def update_goal_position(self, motor_id, value, source_entry=False, entry_widget=None):
        with self.lock:
            self.goal_positions[motor_id] = value
            
        if not source_entry and entry_widget:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, str(value))
            
        # Symmetrical Mirror Execution Path
        if self.mirror_sync_active and not self._in_mirror_sync:
            partner_id = MIRROR_PARTNERS.get(motor_id)
            if partner_id and partner_id in self.active_ids:
                mirrored_val = self.get_mirrored_position(motor_id, value)
                with self.lock:
                    prev_partner_goal = self.goal_positions.get(partner_id)
                if prev_partner_goal != mirrored_val:
                    self._in_mirror_sync = True
                    try:
                        self.set_goal_value_direct(partner_id, mirrored_val)
                    finally:
                        self._in_mirror_sync = False
            
    def on_entry_entered(self, motor_id, slider_widget, entry_widget):
        try:
            val = int(entry_widget.get().strip())
        except ValueError:
            return
        self.update_goal_position(motor_id, val, source_entry=True)
        
        # Expand slider limits dynamically if value exceeds bounds
        s_min = slider_widget.cget("from_")
        s_max = slider_widget.cget("to")
        if val > s_max:
            slider_widget.configure(to=val + 2048)
        elif val < s_min:
            slider_widget.configure(from_=val - 2048)
            
        slider_widget.set(val)

    def shift_position(self, motor_id, offset, slider_widget, entry_widget):
        with self.lock:
            current_goal = self.goal_positions.get(motor_id, 2048)
            
        target = 0 if offset == 0 else current_goal + offset
        
        # Auto-expand boundaries
        s_min = slider_widget.cget("from_")
        s_max = slider_widget.cget("to")
        if target > s_max:
            slider_widget.configure(to=target + 4096)
        elif target < s_min:
            slider_widget.configure(from_=target - 4096)
            
        slider_widget.set(target)
        self.update_goal_position(motor_id, target, source_entry=False, entry_widget=entry_widget)

    def on_row_torque_toggle(self, motor_id):
        if not self.driver:
            return
        enable = self.motor_widgets[motor_id]["t_switch"].get()
        
        with self.lock:
            if self.torque_state.get(motor_id) == enable:
                return
            if motor_id not in self.online_ids:
                self.online_ids.append(motor_id)
                self.online_ids.sort()
                self.consecutive_failures[motor_id] = 0
                
            self.status_msg = f"Queuing torque for ID {motor_id}..."
            self.status_is_err = False
            self.pending_torque_actions.add(motor_id)
            self.pending_actions.append({
                "type": "torque",
                "motor_id": motor_id,
                "enable": enable
            })

    # Timeline Sequencer helpers
    def record_keyframe(self):
        with self.lock:
            snapshot = self.goal_positions.copy()
        self.keyframes.append(snapshot)
        self.update_timeline_list()
        self.log_message(f"Keyframe {len(self.keyframes)} captured successfully.", level="SUCCESS")
        
    def clear_timeline(self):
        self.keyframes.clear()
        self.update_timeline_list()
        self.log_message("All sequencer keyframes cleared.", level="INFO")
        
    def delete_keyframe(self, idx):
        if 0 <= idx < len(self.keyframes):
            self.keyframes.pop(idx)
            self.update_timeline_list()
            self.log_message(f"Keyframe {idx+1} removed.", level="INFO")
            
    def play_timeline(self):
        if not self.keyframes:
            self.log_message("Play failed: Sequencer timeline is empty.", level="ERROR")
            return
        try:
            delay = float(self.timeline_delay_entry.get())
        except ValueError:
            delay = 1.5
        threading.Thread(target=self._play_timeline_thread, args=(delay,), daemon=True).start()
        
    def _play_timeline_thread(self, delay):
        self.log_message(f"Running keyframe timeline playback ({len(self.keyframes)} frames)...", level="CMD")
        for i, frame in enumerate(self.keyframes):
            self.log_message(f"Executing step {i+1} of {len(self.keyframes)}...", level="INFO")
            for mid, val in frame.items():
                if mid in self.active_ids:
                    self.set_goal_value_direct(mid, val)
            time.sleep(delay)
        self.log_message("Timeline playback sequence completed.", level="SUCCESS")
        
    def update_timeline_list(self):
        for w in self.timeline_list_frame.winfo_children():
            w.destroy()
            
        if not self.keyframes:
            lbl = ctk.CTkLabel(self.timeline_list_frame, text="No keyframes captured. Click 'Record Pose' to add steps.", font=("Outfit", 10, "italic"), text_color=TEXT_MUTED)
            lbl.pack(pady=20)
            return
            
        for i, frame in enumerate(self.keyframes):
            row = ctk.CTkFrame(self.timeline_list_frame, fg_color=CARD_INNER, height=28)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            
            lbl = ctk.CTkLabel(row, text=f"Frame {i+1}: {len(frame)} values active", font=("Outfit", 11, "bold"), text_color=TEXT_PRIMARY)
            lbl.pack(side="left", padx=10)
            
            del_btn = ctk.CTkButton(
                row, 
                text="✕", 
                width=16, 
                height=16, 
                fg_color="transparent", 
                hover_color=ACCENT_CRIMSON, 
                text_color=TEXT_MUTED,
                command=lambda idx=i: self.delete_keyframe(idx)
            )
            del_btn.pack(side="right", padx=10)

    # Diagnostic inspector callbacks
    def on_inspect_addr_changed(self, choice):
        addr_str = choice.split(":")[0].strip()
        len_str = choice.split("(")[-1].replace("B)", "").strip()
        self.inspect_addr_val.delete(0, tk.END)
        self.inspect_addr_val.insert(0, addr_str)
        self.inspect_len_menu.set(len_str)
        
    def perform_inspect_read(self):
        if not self.connected:
            return
        try:
            mid = int(self.inspect_id_menu.get())
            addr = int(self.inspect_addr_val.get().strip())
            length = int(self.inspect_len_menu.get())
        except ValueError:
            self.inspect_result_lbl.configure(text="Invalid numeric inputs!", text_color=ACCENT_CRIMSON)
            return
            
        with self.lock:
            self.pending_actions.append({
                "type": "inspect_read",
                "motor_id": mid,
                "address": addr,
                "length": length
            })
            
    def perform_inspect_write(self):
        if not self.connected:
            return
        try:
            mid = int(self.inspect_id_menu.get())
            addr = int(self.inspect_addr_val.get().strip())
            length = int(self.inspect_len_menu.get())
            val = int(self.inspect_write_val.get().strip())
        except ValueError:
            self.inspect_result_lbl.configure(text="Invalid numeric inputs!", text_color=ACCENT_CRIMSON)
            return
            
        with self.lock:
            self.pending_actions.append({
                "type": "inspect_write",
                "motor_id": mid,
                "address": addr,
                "length": length,
                "value": val
            })
            
    def perform_ping(self):
        if not self.connected:
            return
        try:
            mid = int(self.ping_id_entry.get().strip())
        except ValueError:
            return
            
        with self.lock:
            self.pending_actions.append({
                "type": "ping_node",
                "motor_id": mid
            })
            
    # PID Tuning events
    def on_pid_target_changed(self, choice):
        if not self.connected or not self.driver:
            return
        try:
            mid = int(choice)
        except ValueError:
            return
            
        self.log_message(f"Querying PID gain registers for ID {mid}...", level="INFO")
        if self.driver.mock_mode:
            self.pid_kp_slider.set(850)
            self.pid_ki_slider.set(0)
            self.pid_kd_slider.set(0)
            self.draw_pid_simulation()
        else:
            with self.lock:
                self.pending_actions.append({
                    "type": "read_pid",
                    "motor_id": mid
                })
                
    def update_pid_sliders(self, kp, ki, kd):
        self.pid_kp_slider.set(kp)
        self.pid_ki_slider.set(ki)
        self.pid_kd_slider.set(kd)
        self.draw_pid_simulation()
        
    def on_pid_slider_changed(self, val):
        self.draw_pid_simulation()
        if not self.connected or not self.driver:
            return
        try:
            mid = int(self.pid_id_menu.get())
            kp = int(self.pid_kp_slider.get())
            ki = int(self.pid_ki_slider.get())
            kd = int(self.pid_kd_slider.get())
        except ValueError:
            return
            
        with self.lock:
            # Replace existing write_pid targets to avoid packet flooding
            self.pending_actions = [a for a in self.pending_actions if a.get("type") != "write_pid"]
            self.pending_actions.append({
                "type": "write_pid",
                "motor_id": mid,
                "kp": kp,
                "ki": ki,
                "kd": kd
            })
            
    def on_pid_vel_changed(self, val):
        if not self.connected or not self.driver:
            return
        try:
            mid = int(self.pid_id_menu.get())
            vel = int(val)
        except ValueError:
            return
            
        with self.lock:
            self.pending_actions = [a for a in self.pending_actions if a.get("type") != "write_vel"]
            self.pending_actions.append({
                "type": "write_vel",
                "motor_id": mid,
                "velocity": vel
            })
            
    def draw_pid_simulation(self):
        kp = self.pid_kp_slider.get()
        ki = self.pid_ki_slider.get()
        kd = self.pid_kd_slider.get()
        
        self.pid_canvas.delete("all")
        w = self.pid_canvas.winfo_width()
        h = self.pid_canvas.winfo_height()
        if w <= 1: w = 390
        if h <= 1: h = 130
        
        # Draw background grid
        self.pid_canvas.create_rectangle(0, 0, w, h, fill="#0F0F11", outline="")
        for i in range(1, 8):
            x = i * (w / 8)
            self.pid_canvas.create_line(x, 0, x, h, fill="#1F1F22", dash=(2, 2))
        for i in range(1, 4):
            y = i * (h / 4)
            self.pid_canvas.create_line(0, y, w, y, fill="#1F1F22", dash=(2, 2))
            
        # Draw step target line (green)
        step_x = 50
        target_high = h * 0.3
        target_low = h * 0.7
        self.pid_canvas.create_line(0, target_low, step_x, target_low, fill=ACCENT_EMERALD, width=2)
        self.pid_canvas.create_line(step_x, target_low, step_x, target_high, fill=ACCENT_EMERALD, width=2)
        self.pid_canvas.create_line(step_x, target_high, w, target_high, fill=ACCENT_EMERALD, width=2)
        
        # Simulate step response dynamic loop
        y_val = target_low
        y_vel = 0.0
        y_int = 0.0
        points = [(0, target_low)]
        
        dt = 0.05
        Kp_s = kp / 15.0
        Ki_s = ki / 120.0
        Kd_s = kd / 10.0
        
        for px in range(1, int(w)):
            target = target_high if px >= step_x else target_low
            error = target - y_val
            y_int += error * dt
            y_int = max(-40, min(40, y_int)) # integral anti-windup
            
            deriv = (error - (target - points[-1][1])) / dt if len(points) > 1 else 0
            
            # Control force output
            u = Kp_s * error + Ki_s * y_int + Kd_s * deriv
            
            accel = u - 0.65 * y_vel # inertia & physical damping
            y_vel += accel * dt
            y_vel = max(-20, min(20, y_vel))
            y_val += y_vel * dt
            
            points.append((px, y_val))
            
        # Draw curve line
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            y1_c = max(2, min(h-2, y1))
            y2_c = max(2, min(h-2, y2))
            self.pid_canvas.create_line(x1, y1_c, x2, y2_c, fill=ACCENT_PINK, width=2)
            
    # Macro Automation Engine
    def execute_macro(self):
        macro_text = self.macro_entry.get("1.0", tk.END).strip()
        if not macro_text:
            return
        threading.Thread(target=self._run_macro_thread, args=(macro_text,), daemon=True).start()
        
    def _run_macro_thread(self, text):
        self.log_message("Starting macro parser execution...", level="CMD")
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                if line.startswith("move(") and line.endswith(")"):
                    parts = line[5:-1].split(",")
                    mid = int(parts[0].strip())
                    val = int(parts[1].strip())
                    self.after(0, lambda m=mid, v=val: self.set_goal_value_direct(m, v))
                    self.log_message(f"Macro: Set goal ID {mid} -> {val}", level="INFO")
                elif line.startswith("wait(") and line.endswith(")"):
                    sec = float(line[5:-1].strip())
                    self.log_message(f"Macro: Sleeping {sec}s...", level="INFO")
                    time.sleep(sec)
                elif line.startswith("relax(") and line.endswith(")"):
                    tgt = line[6:-1].strip()
                    if tgt == "all":
                        self.after(0, lambda: self.set_global_torque(False))
                        self.log_message("Macro: De-energize global bus torque.", level="INFO")
                    else:
                        mid = int(tgt)
                        with self.lock:
                            self.pending_actions.append({"type": "torque", "motor_id": mid, "enable": False})
                        self.log_message(f"Macro: Torque disabled for ID {mid}.", level="INFO")
                elif line.startswith("torque(") and line.endswith(")"):
                    tgt = line[7:-1].strip()
                    parts = tgt.split(",")
                    if len(parts) == 1 and parts[0].strip() == "all":
                        self.after(0, lambda: self.set_global_torque(True))
                        self.log_message("Macro: Global bus torque enabled.", level="INFO")
                    else:
                        mid = int(parts[0].strip())
                        state = parts[1].strip().lower() in ["true", "1", "on"]
                        with self.lock:
                            self.pending_actions.append({"type": "torque", "motor_id": mid, "enable": state})
                        self.log_message(f"Macro: Torque ID {mid} = {state}", level="INFO")
            except Exception as e:
                self.log_message(f"Macro Parse Error: '{line}' - {str(e)}", level="ERROR")
                break
        self.log_message("Macro execution finished.", level="SUCCESS")

    def _update_loop(self):
        """Hardware transaction thread running serial lines."""
        while self.running:
            if not self.driver or not self.driver.is_connected:
                time.sleep(0.1)
                continue
                
            # Read currents and temperatures every 25 iterations (~1Hz)
            self.loop_ticks += 1
            read_telemetry = (self.loop_ticks % 25 == 0)
            
            # 1. Pop pending actions under lock
            actions_to_process = []
            with self.lock:
                if self.pending_actions:
                    actions_to_process = list(self.pending_actions)
                    self.pending_actions.clear()
            
            # 2. Process actions outside lock
            for action in actions_to_process:
                if not self.driver or not self.driver.is_connected:
                    break
                atype = action["type"]
                
                if atype == "torque":
                    mid = action["motor_id"]
                    enable = action["enable"]
                    success = self.driver.enable_torque([mid], enable)
                    with self.lock:
                        self.torque_state[mid] = self.driver.torque_state.get(mid, False)
                        if success:
                            self.status_msg = f"Torque {'ON' if enable else 'OFF'} for ID {mid}."
                            self.status_is_err = False
                        else:
                            self.status_msg = f"Write error: torque failed for ID {mid}."
                            self.status_is_err = True
                        self.pending_torque_actions.discard(mid)
                        
                elif atype == "global_torque":
                    enable = action["enable"]
                    with self.lock:
                        target_ids = [mid for mid in self.active_ids if mid in self.online_ids]
                    if target_ids:
                        success = self.driver.enable_torque(target_ids, enable)
                        with self.lock:
                            for mid in target_ids:
                                self.torque_state[mid] = self.driver.torque_state.get(mid, False)
                    else:
                        success = True
                        
                    with self.lock:
                        if success:
                            self.status_msg = f"Global torque set {'ON' if enable else 'OFF'}."
                            self.status_is_err = False
                        else:
                            self.status_msg = "Global torque warning: some nodes failed."
                            self.status_is_err = True
                        for mid in self.active_ids:
                            self.pending_torque_actions.discard(mid)
                            
                elif atype == "reboot":
                    mid = action["motor_id"]
                    success = self.driver.reboot([mid])
                    with self.lock:
                        if success:
                            self.torque_state[mid] = False
                            self.status_msg = f"Reboot packet sent to ID {mid}."
                            self.status_is_err = False
                        else:
                            self.status_msg = f"Reboot write failed for ID {mid}!"
                            self.status_is_err = True
                            
                elif atype == "inspect_read":
                    mid = action["motor_id"]
                    addr = action["address"]
                    length = action["length"]
                    val = 0
                    if self.driver.mock_mode:
                        val = 2048
                        res = 0
                    else:
                        if length == 1:
                            val, res, err = self.driver.packet_handler.read1ByteTxRx(self.driver.port_handler, mid, addr)
                        elif length == 2:
                            val, res, err = self.driver.packet_handler.read2ByteTxRx(self.driver.port_handler, mid, addr)
                        else:
                            val, res, err = self.driver.packet_handler.read4ByteTxRx(self.driver.port_handler, mid, addr)
                            
                    if res == 0:
                        msg = f"Read SUCCESS: ID {mid} ADDR {addr} = {val}"
                        self.log_message(msg, level="SUCCESS")
                        self.after(0, lambda t=f"Value: {val}": self.inspect_result_lbl.configure(text=t, text_color=TEXT_PRIMARY))
                    else:
                        msg = f"Read FAILED: ID {mid} ADDR {addr}"
                        self.log_message(msg, level="ERROR")
                        self.after(0, lambda t=msg: self.inspect_result_lbl.configure(text=t, text_color=ACCENT_CRIMSON))
                        
                elif atype == "inspect_write":
                    mid = action["motor_id"]
                    addr = action["address"]
                    length = action["length"]
                    val = action["value"]
                    if self.driver.mock_mode:
                        res = 0
                    else:
                        if length == 1:
                            res, err = self.driver.packet_handler.write1ByteTxRx(self.driver.port_handler, mid, addr, val)
                        elif length == 2:
                            res, err = self.driver.packet_handler.write2ByteTxRx(self.driver.port_handler, mid, addr, val)
                        else:
                            res, err = self.driver.packet_handler.write4ByteTxRx(self.driver.port_handler, mid, addr, val)
                            
                    if res == 0:
                        msg = f"Write SUCCESS: ID {mid} ADDR {addr} -> {val}"
                        self.log_message(msg, level="SUCCESS")
                        self.after(0, lambda t="Write complete.": self.inspect_result_lbl.configure(text=t, text_color=ACCENT_EMERALD))
                    else:
                        msg = f"Write FAILED: ID {mid} ADDR {addr}"
                        self.log_message(msg, level="ERROR")
                        self.after(0, lambda t=msg: self.inspect_result_lbl.configure(text=t, text_color=ACCENT_CRIMSON))
                        
                elif atype == "ping_node":
                    mid = action["motor_id"]
                    start = time.perf_counter()
                    success = self.driver.ping(mid)
                    latency = (time.perf_counter() - start) * 1000.0
                    if success:
                        msg = f"Ping SUCCESS: ID {mid} latency = {latency:.1f} ms"
                        self.log_message(msg, level="SUCCESS")
                        self.after(0, lambda t=f"Online - {latency:.1f} ms": self.ping_result_lbl.configure(text=t, text_color=ACCENT_EMERALD))
                    else:
                        msg = f"Ping FAILED: ID {mid}"
                        self.log_message(msg, level="ERROR")
                        self.after(0, lambda t=msg: self.ping_result_lbl.configure(text=t, text_color=ACCENT_CRIMSON))
                        
                elif atype == "read_pid":
                    mid = action["motor_id"]
                    if self.driver.mock_mode:
                        kp, ki, kd = 850, 0, 0
                        res = 0
                    else:
                        kp, r1, e1 = self.driver.packet_handler.read2ByteTxRx(self.driver.port_handler, mid, 84)
                        ki, r2, e2 = self.driver.packet_handler.read2ByteTxRx(self.driver.port_handler, mid, 82)
                        kd, r3, e3 = self.driver.packet_handler.read2ByteTxRx(self.driver.port_handler, mid, 80)
                        res = r1 + r2 + r3
                    if res == 0:
                        self.after(0, lambda p=kp, i=ki, d=kd: self.update_pid_sliders(p, i, d))
                        
                elif atype == "write_pid":
                    mid = action["motor_id"]
                    kp, ki, kd = action["kp"], action["ki"], action["kd"]
                    self.driver.set_pid_gains([mid], kp, ki, kd)
                    
                elif atype == "write_vel":
                    mid = action["motor_id"]
                    vel = action["velocity"]
                    self.driver.set_profile_velocity([mid], vel)

            # 3. Read present positions
            with self.lock:
                online_ids_copy = list(self.online_ids)
            
            reads = {}
            currents = {}
            temps = {}
            voltages = {}
            latency = 0.0
            if online_ids_copy:
                try:
                    start_time = time.perf_counter()
                    reads = self.driver.read_positions(online_ids_copy)
                    if read_telemetry:
                        currents = self.driver.read_currents(online_ids_copy)
                        temps = self.driver.read_temperatures(online_ids_copy)
                        for mid in online_ids_copy:
                            if self.driver.mock_mode:
                                voltages[mid] = round(12.1 + 0.1 * np.sin(time.time() + mid), 1)
                            else:
                                # Input voltage address 144 (2 bytes, unit 0.1V)
                                val, res, err = self.driver.packet_handler.read2ByteTxRx(self.driver.port_handler, mid, 144)
                                voltages[mid] = round(val * 0.1, 1) if res == 0 else 12.0
                                
                    latency = (time.perf_counter() - start_time) * 1000.0
                except Exception:
                    pass
            
            # Update read results under lock
            with self.lock:
                self.latency_ms = latency
                for mid in online_ids_copy:
                    if mid in reads and isinstance(reads[mid], (int, float)):
                        self.present_positions[mid] = reads[mid]
                        self.consecutive_failures[mid] = 0
                        
                        # Sync goals if torque is disabled AND no torque enable action is pending!
                        if not self.torque_state.get(mid, False) and mid not in self.pending_torque_actions:
                            self.goal_positions[mid] = reads[mid]
                    else:
                        self.consecutive_failures[mid] += 1
                        if self.consecutive_failures[mid] >= 5:
                            if mid in self.online_ids:
                                self.online_ids.remove(mid)
                            self.torque_state[mid] = False
                            self.status_msg = f"ID {mid} failed (Timeout). Pruned."
                            self.status_is_err = True
                            
                    if mid in currents:
                        self.present_currents[mid] = currents[mid]
                    if mid in temps:
                        self.present_temperatures[mid] = temps[mid]
                    if mid in voltages:
                        self.present_voltages[mid] = voltages[mid]

            # 4. Write goal positions on change
            with self.lock:
                goals_to_write = self.goal_positions.copy()
                active_torqued_ids = [mid for mid, st in self.torque_state.items() if st]
                online_active_torqued = [mid for mid in active_torqued_ids if mid in self.online_ids]
            
            if online_active_torqued:
                write_packet = {}
                with self.lock:
                    for mid in online_active_torqued:
                        goal = goals_to_write.get(mid)
                        if goal is not None and goal != self.last_written_positions.get(mid):
                            write_packet[mid] = goal
                
                if write_packet:
                    try:
                        success = self.driver.write_positions(write_packet)
                        if success:
                            with self.lock:
                                for mid, val in write_packet.items():
                                    self.last_written_positions[mid] = val
                    except Exception:
                        pass
                        
            time.sleep(0.040)
            
    def update_gui_telemetry(self):
        if not self.connected:
            return
            
        with self.lock:
            goals = self.goal_positions.copy()
            presents = self.present_positions.copy()
            torques = self.torque_state.copy()
            online_list = self.online_ids.copy()
            status_text = self.status_msg
            is_err = self.status_is_err
            latency = self.latency_ms
            
        # Status card rendering cache
        status_state = {
            "is_err": is_err,
            "status_text": status_text,
            "online_len": len(online_list),
            "latency": round(latency, 1)
        }
        
        if self.last_status_state != status_state:
            self.last_status_state = status_state
            if is_err:
                self.dash_card1.configure(border_color=ACCENT_CRIMSON)
                self.card1_lbl.configure(text=f"STATUS ERROR\n{status_text}", text_color=ACCENT_CRIMSON)
            else:
                self.dash_card1.configure(border_color=ACCENT_VIOLET)
                port = self.port_entry.get().strip()
                baud = self.baud_menu.get()
                self.card1_lbl.configure(text=f"PORT: {port} // BAUD: {baud}\n{status_text}", text_color=TEXT_PRIMARY)
                
            self.card2_lbl.configure(text=f"ONLINE NODES\n{len(online_list)} / {len(self.active_ids)} Connected")
            self.card3_lbl.configure(text=f"BUS LATENCY // TIME\n{latency:.2f} ms cycle time")
            
        # If diagnostics tab is active, update the advanced telemetry table
        if self.active_tab == "diagnostics":
            self.update_diag_table()
            
        # Row card state styling changes (Offline/Online/Torque)
        for mid in self.active_ids:
            if mid in self.motor_widgets:
                w = self.motor_widgets[mid]
                g_pos = goals.get(mid, "--")
                p_pos = presents.get(mid, "--")
                
                is_online = mid in online_list
                is_torqued = torques.get(mid, False)
                
                prev = self.last_rendered_states.get(mid)
                
                # Driver state sync for torque toggles
                if self.driver and is_online:
                    t_driver_state = self.driver.torque_state.get(mid, False)
                    if t_driver_state != is_torqued:
                        is_torqued = t_driver_state
                        with self.lock:
                            self.torque_state[mid] = t_driver_state
                
                state_changed = (
                    prev is None or
                    prev.get("online") != is_online or
                    prev.get("torqued") != is_torqued or
                    prev.get("present_pos") != p_pos or
                    prev.get("goal_pos") != g_pos
                )
                
                if not state_changed:
                    continue
                    
                self.last_rendered_states[mid] = {
                    "online": is_online,
                    "torqued": is_torqued,
                    "present_pos": p_pos,
                    "goal_pos": g_pos
                }
                
                if prev is None or prev.get("online") != is_online or prev.get("torqued") != is_torqued:
                    if is_online:
                        w["badge_lbl"].configure(text="ONLINE", text_color=ACCENT_EMERALD)
                        w["row_card"].configure(border_color=BORDER_OSRS)
                        w["slider"].configure(state="normal")
                        w["entry"].configure(state="normal")
                        
                        t_switch = w["t_switch"]
                        t_switch.configure(command=None)
                        if is_torqued:
                            t_switch.select()
                        else:
                            t_switch.deselect()
                        t_switch.configure(command=lambda m=mid: self.on_row_torque_toggle(m))
                    else:
                        w["badge_lbl"].configure(text="OFFLINE", text_color=ACCENT_CRIMSON)
                        w["row_card"].configure(border_color=ACCENT_CRIMSON)
                        w["telemetry_lbl"].configure(text=f"Present: OFFLINE\nGoal: {g_pos}", text_color=ACCENT_CRIMSON)
                        w["slider"].configure(state="disabled")
                        w["entry"].configure(state="disabled")
                        
                        t_switch = w["t_switch"]
                        t_switch.configure(command=None)
                        t_switch.deselect()
                        t_switch.configure(command=lambda m=mid: self.on_row_torque_toggle(m))
                        
                if is_online:
                    if prev is None or prev.get("present_pos") != p_pos or prev.get("goal_pos") != g_pos:
                        w["telemetry_lbl"].configure(text=f"Present: {p_pos}\nGoal: {g_pos}", text_color=TEXT_MUTED)
                        
                    # Sync physically moved actuator goals when relaxed (not torqued)
                    if not is_torqued and isinstance(p_pos, int):
                        prev_p = prev.get("present_pos") if prev else None
                        if prev_p is None or not isinstance(prev_p, int) or abs(prev_p - p_pos) >= 8:
                            slider = w["slider"]
                            entry = w["entry"]
                            
                            s_min = slider.cget("from_")
                            s_max = slider.cget("to")
                            if p_pos > s_max:
                                slider.configure(to=p_pos + 2048)
                            elif p_pos < s_min:
                                slider.configure(from_=p_pos - 2048)
                                
                            slider.configure(command=None)
                            slider.set(p_pos)
                            slider.configure(command=lambda val, m=mid, en=entry: self.update_goal_position(m, int(val), source_entry=False, entry_widget=en))
                            
                            entry.delete(0, tk.END)
                            entry.insert(0, str(p_pos))

    def update_diag_table(self):
        if not hasattr(self, "diag_rows"):
            self.diag_rows = {}
            
        with self.lock:
            online_list = list(self.online_ids)
            presents = self.present_positions.copy()
            goals = self.goal_positions.copy()
            currents = self.present_currents.copy()
            temps = self.present_temperatures.copy()
            voltages = self.present_voltages.copy()
            
        for idx, mid in enumerate(self.active_ids):
            is_online = mid in online_list
            pres_val = presents.get(mid, "--")
            goal_val = goals.get(mid, "--")
            curr_val = currents.get(mid, 0)
            temp_val = temps.get(mid, 30)
            volt_val = voltages.get(mid, 12.0)
            
            if mid not in self.diag_rows:
                row_frame = ctk.CTkFrame(self.diag_scroll, fg_color=CARD_INNER if idx % 2 == 0 else "transparent", height=32)
                row_frame.pack(fill="x", pady=1)
                row_frame.pack_propagate(False)
                
                id_lbl = ctk.CTkLabel(row_frame, text=f"ID {mid:02d}", font=("JetBrains Mono", 11, "bold"), width=50, anchor="w")
                id_lbl.pack(side="left", padx=10)
                
                name_lbl = ctk.CTkLabel(row_frame, text=self.get_joint_name(mid, "Humanoid V1"), font=("Outfit", 11), width=180, anchor="w")
                name_lbl.pack(side="left", padx=10)
                
                pos_lbl = ctk.CTkLabel(row_frame, text=f"{pres_val} / {goal_val}", font=("JetBrains Mono", 11), width=120, anchor="center")
                pos_lbl.pack(side="left", padx=10)
                
                curr_lbl = ctk.CTkLabel(row_frame, text=f"{curr_val} mA", font=("JetBrains Mono", 11), width=80, anchor="center")
                curr_lbl.pack(side="left", padx=10)
                
                temp_lbl = ctk.CTkLabel(row_frame, text=f"{temp_val} °C", font=("JetBrains Mono", 11), width=80, anchor="center")
                temp_lbl.pack(side="left", padx=10)
                
                volt_lbl = ctk.CTkLabel(row_frame, text=f"{volt_val} V", font=("JetBrains Mono", 11), width=80, anchor="center")
                volt_lbl.pack(side="left", padx=10)
                
                status_lbl = ctk.CTkLabel(row_frame, text="ONLINE" if is_online else "OFFLINE", font=("Outfit", 10, "bold"), text_color=ACCENT_EMERALD if is_online else ACCENT_CRIMSON, width=80)
                status_lbl.pack(side="left", padx=10)
                
                self.diag_rows[mid] = {
                    "row_frame": row_frame,
                    "pos_lbl": pos_lbl,
                    "curr_lbl": curr_lbl,
                    "temp_lbl": temp_lbl,
                    "volt_lbl": volt_lbl,
                    "status_lbl": status_lbl
                }
            else:
                w = self.diag_rows[mid]
                w["pos_lbl"].configure(text=f"{pres_val} / {goal_val}")
                w["curr_lbl"].configure(text=f"{curr_val} mA")
                w["temp_lbl"].configure(text=f"{temp_val} °C")
                w["volt_lbl"].configure(text=f"{volt_val} V")
                w["status_lbl"].configure(
                    text="ONLINE" if is_online else "OFFLINE",
                    text_color=ACCENT_EMERALD if is_online else ACCENT_CRIMSON
                )

    def on_close(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
        if self.driver:
            self.driver.disable_torque(self.active_ids)
            self.driver.disconnect()
        self.destroy()

# Preset calculations helpers
def get_v1_preset_ticks(preset_name):
    if preset_name not in VALS_PRESETS: 
        return {}
    vals = VALS_PRESETS[preset_name]
    targets = {}
    def interp(v, mid):
        lim = V1_LIMITS[mid]
        return int(lim["min"] + v * (lim["max"] - lim["min"]))
    targets[0] = interp(vals[6], 0)
    targets[1] = interp(vals[0], 1)
    targets[2] = interp(vals[0], 2)
    targets[9] = interp(vals[0], 9)
    targets[4] = interp(vals[7], 4)
    targets[5] = interp(vals[1], 5)
    targets[6] = interp(vals[1], 6)
    targets[7] = interp(vals[1], 7)
    targets[8] = interp(vals[8], 8)
    targets[3] = interp(vals[2], 3)
    targets[10] = interp(vals[2], 10)
    targets[11] = interp(vals[2], 11)
    targets[12] = interp(1.0 - vals[9], 12)
    targets[13] = interp(vals[3], 13)
    targets[14] = interp(vals[4], 14)
    targets[15] = interp(vals[5], 15)
    return targets

def get_v2_preset_ticks(preset_name):
    if preset_name not in VALS_PRESETS: 
        return {}
    vals = VALS_PRESETS[preset_name]
    targets = {}
    def interp(v, mid):
        lim = V2_LIMITS[mid]
        return int(lim["min"] + v * (lim["max"] - lim["min"]))
    targets[0] = interp(vals[6], 0)
    targets[1] = interp(vals[0], 1)
    targets[2] = interp(vals[7], 2)
    targets[3] = interp(vals[1], 3)
    targets[4] = interp(vals[8], 4)
    targets[5] = interp(vals[2], 5)
    targets[6] = interp(1.0 - vals[9], 6)
    targets[7] = interp(vals[4], 7)
    return targets

if __name__ == "__main__":
    app = ExtendedControlGUI()
    app.mainloop()
