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

# Add script directory to python path to import dynamixel_driver
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dynamixel_driver import DynamixelDriver

# Premium Cyber-Control Palette (C.H.I.M.A.N Theme)
BG_OSRS = "#070B19"            # High-Contrast Dark Navy
CARD_OSRS = "#121B2F"          # Deep Slate Gray-Blue Card
BORDER_OSRS = "#223554"        # Higher Contrast Muted Border
TEXT_PRIMARY = "#FFFFFF"       # Crisp Soft White
TEXT_MUTED = "#94A3B8"         # Muted Slate Gray (Sophisticated)
ACCENT_PINK = "#00F0FF"        # True Neon Electric Cyan (Sharp)
ACCENT_VIOLET = "#6366F1"      # Vibrant Royal Indigo/Violet Accent
ACCENT_EMERALD = "#10B981"     # Armed Green
ACCENT_CRIMSON = "#EF4444"     # Danger/Offline Red
ACCENT_BLUE = "#3B82F6"        # Telemetry Blue
CARD_INNER = "#0B1325"         # Inner dark card

# Full Robot Profiles Mapping from gui.py & humanoid.py
ROBOT_PROFILES = {
    "Humanoid V1": {
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

# Standard Preset Position Limits & Defaults for Leap Hand and Humanoid
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

class ExtendedControlGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window settings
        self.title("C.H.I.M.A.N")
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
        
        # Thread-safe locks against goal-sync race conditions
        self.pending_torque_actions = set()
        
        # Diagnostics Telemetry variables
        self.latency_ms = 0.0
        self.loop_ticks = 0
        self.status_msg = "DISCONNECTED"
        self.status_is_err = True
        
        # Thread control
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        self.telemetry_loop_active = False
        
        # Layout components
        self.motor_widgets = {}
        self.motor_row_widgets = {}
        
        # GUI rendering state cache to prevent redundant updates
        self.last_rendered_states = {}
        
        # Set theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_layout()
        
    def setup_layout(self):
        # Grid settings: Sidebar (0) + Main Area (1)
        self.grid_columnconfigure(0, weight=0, minsize=340)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # =====================================================================
        # SIDEBAR (LEFT COL)
        # =====================================================================
        self.sidebar = ctk.CTkFrame(self, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # C.H.I.M.A.N System Branding Label
        brand_lbl = ctk.CTkLabel(self.sidebar, text="C.H.I.M.A.N", font=ctk.CTkFont(family="Outfit", size=20, weight="bold"), text_color=ACCENT_PINK)
        brand_lbl.pack(pady=(20, 15))
        
        # Connection Panel
        conn_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        conn_frame.pack(padx=15, pady=8, fill="x")
        
        ctk.CTkLabel(conn_frame, text="Serial Controller Config", font=ctk.CTkFont(family="Outfit", weight="bold", size=13), text_color=TEXT_PRIMARY).pack(pady=(10, 5))
        
        # Port
        ctk.CTkLabel(conn_frame, text="COM Port:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
        self.port_entry = ctk.CTkEntry(conn_frame, placeholder_text="e.g. COM14", height=30, fg_color=BG_OSRS, border_color=BORDER_OSRS)
        self.port_entry.insert(0, "COM14")
        self.port_entry.pack(padx=15, pady=(2, 10), fill="x")
        
        # Baudrate
        ctk.CTkLabel(conn_frame, text="Baud Rate:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
        self.baud_menu = ctk.CTkOptionMenu(conn_frame, values=["4000000", "1000000", "57600", "115200"], height=30, fg_color=BG_OSRS, button_color=BORDER_OSRS, button_hover_color=ACCENT_VIOLET)
        self.baud_menu.set("4000000")
        self.baud_menu.pack(padx=15, pady=(2, 15), fill="x")
        
        # Connect & Scan buttons
        self.conn_btn = ctk.CTkButton(
            conn_frame, 
            text="CONNECT BUS", 
            fg_color=ACCENT_PINK, 
            hover_color="#D11871", 
            font=ctk.CTkFont(family="Outfit", weight="bold"), 
            command=self.toggle_connection,
            height=34
        )
        self.conn_btn.pack(padx=15, pady=(0, 10), fill="x")
        
        self.scan_btn = ctk.CTkButton(
            conn_frame, 
            text="RE-SCAN DYNAMIXELS", 
            fg_color="#334155", 
            hover_color="#475569", 
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold"), 
            command=self.trigger_rescan,
            height=30
        )
        self.scan_btn.pack(padx=15, pady=(0, 15), fill="x")
        
        # Torque Global Controls
        torque_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        torque_frame.pack(padx=15, pady=8, fill="x")
        
        ctk.CTkLabel(torque_frame, text="Global Arm / Relax", font=ctk.CTkFont(family="Outfit", weight="bold", size=13), text_color=TEXT_PRIMARY).pack(pady=(10, 10))
        
        self.torque_on_btn = ctk.CTkButton(
            torque_frame, 
            text="TORQUE ENABLED (ON)", 
            fg_color=ACCENT_EMERALD, 
            hover_color="#059669", 
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold"),
            command=lambda: self.set_global_torque(True)
        )
        self.torque_on_btn.pack(padx=15, pady=5, fill="x")
        
        self.torque_off_btn = ctk.CTkButton(
            torque_frame, 
            text="RELAX ALL (OFF)", 
            fg_color="#334155", 
            hover_color="#475569", 
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold"),
            command=lambda: self.set_global_torque(False)
        )
        self.torque_off_btn.pack(padx=15, pady=(5, 15), fill="x")
        
        # DEDICATED ARM POSE TARGET COMMANDS (ALWAYS PROMINENT IN SIDEBAR)
        self.pose_btn_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, corner_radius=8)
        self.pose_btn_frame.pack(padx=15, pady=8, fill="x")
        ctk.CTkLabel(self.pose_btn_frame, text="Quick Pose Target Command", font=ctk.CTkFont(family="Outfit", weight="bold", size=13), text_color=TEXT_PRIMARY).pack(pady=(10, 5))
        
        self.both_arms_pose_btn = ctk.CTkButton(
            self.pose_btn_frame, 
            text="GO TO BOTH ARMS POSE", 
            fg_color=ACCENT_PINK, 
            hover_color="#D11871", 
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold"),
            command=self.preset_both_arms_offsets,
            height=34
        )
        self.both_arms_pose_btn.pack(padx=15, pady=(8, 3), fill="x")
        
        # Row 2: Left and Right Arm Poses side-by-side
        arm_poses_frame = ctk.CTkFrame(self.pose_btn_frame, fg_color="transparent")
        arm_poses_frame.pack(padx=15, pady=3, fill="x")
        arm_poses_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.left_arm_pose_btn = ctk.CTkButton(
            arm_poses_frame, 
            text="LEFT POSE", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_offsets,
            height=30
        )
        self.left_arm_pose_btn.grid(row=0, column=0, padx=(0, 2), sticky="ew")
        
        self.right_arm_pose_btn = ctk.CTkButton(
            arm_poses_frame, 
            text="RIGHT POSE", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_right_arm_offsets,
            height=30
        )
        self.right_arm_pose_btn.grid(row=0, column=1, padx=(2, 0), sticky="ew")

        # Row 3: UP, centre, down side-by-side
        up_down_center_frame = ctk.CTkFrame(self.pose_btn_frame, fg_color="transparent")
        up_down_center_frame.pack(padx=15, pady=3, fill="x")
        up_down_center_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.left_arm_up_btn = ctk.CTkButton(
            up_down_center_frame, 
            text="UP", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_up,
            height=30
        )
        self.left_arm_up_btn.grid(row=0, column=0, padx=(0, 2), sticky="ew")
        
        self.left_arm_center_btn = ctk.CTkButton(
            up_down_center_frame, 
            text="centre", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_center,
            height=30
        )
        self.left_arm_center_btn.grid(row=0, column=1, padx=2, sticky="ew")
        
        self.left_arm_down_btn = ctk.CTkButton(
            up_down_center_frame, 
            text="down", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_arm_down,
            height=30
        )
        self.left_arm_down_btn.grid(row=0, column=2, padx=(2, 0), sticky="ew")
        
        # Row 4: Hand controls (open and closed side-by-side)
        hand_ctrl_frame = ctk.CTkFrame(self.pose_btn_frame, fg_color="transparent")
        hand_ctrl_frame.pack(padx=15, pady=(3, 10), fill="x")
        hand_ctrl_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.left_hand_open_btn = ctk.CTkButton(
            hand_ctrl_frame, 
            text="open", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_hand_open,
            height=30
        )
        self.left_hand_open_btn.grid(row=0, column=0, padx=(0, 2), sticky="ew")
        
        self.left_hand_closed_btn = ctk.CTkButton(
            hand_ctrl_frame, 
            text="closed", 
            fg_color=BG_OSRS, 
            hover_color=ACCENT_VIOLET, 
            border_color=BORDER_OSRS,
            border_width=1,
            state="disabled",
            font=ctk.CTkFont(family="Outfit", weight="bold", size=11),
            command=self.preset_left_hand_closed,
            height=30
        )
        self.left_hand_closed_btn.grid(row=0, column=1, padx=(2, 0), sticky="ew")
        
        # Emergency E-Stop Button at sidebar base
        self.estop_btn = ctk.CTkButton(
            self.sidebar, 
            text="🚨 EMERGENCY E-STOP", 
            fg_color=ACCENT_CRIMSON, 
            hover_color="#B91C1C", 
            height=50,
            font=ctk.CTkFont(family="Outfit", size=14, weight="bold"),
            command=self.trigger_estop
        )
        self.estop_btn.pack(side="bottom", padx=15, pady=20, fill="x")
        
        # =====================================================================
        # MAIN FRAME (RIGHT COL)
        # =====================================================================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=0, minsize=240) # Column 0: Quick Servo Navigation Tree
        self.main_container.grid_columnconfigure(1, weight=1)             # Column 1: Sliders Telemetry Feed
        self.main_container.grid_rowconfigure(1, weight=1)
        
        # Top Dashboard Panels - Row 0 (Spans across both columns)
        dash_panel = ctk.CTkFrame(self.main_container, fg_color="transparent", height=70)
        dash_panel.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        dash_panel.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Dashboard Card 1: Connection & Latency Info
        self.dash_card1 = ctk.CTkFrame(dash_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=65)
        self.dash_card1.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.dash_card1.pack_propagate(False)
        self.card1_lbl = ctk.CTkLabel(self.dash_card1, text="COM PORT // BAUD\nDisconnections active", font=ctk.CTkFont(family="JetBrains Mono", size=11), text_color=TEXT_MUTED)
        self.card1_lbl.pack(pady=12)
        
        # Dashboard Card 2: Active Node count
        self.dash_card2 = ctk.CTkFrame(dash_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=65)
        self.dash_card2.grid(row=0, column=1, padx=4, sticky="nsew")
        self.dash_card2.pack_propagate(False)
        self.card2_lbl = ctk.CTkLabel(self.dash_card2, text="NODES DETECTED\n0 active on bus", font=ctk.CTkFont(family="JetBrains Mono", size=11), text_color=TEXT_MUTED)
        self.card2_lbl.pack(pady=12)
        
        # Dashboard Card 3: Performance Latency metrics
        self.dash_card3 = ctk.CTkFrame(dash_panel, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=65)
        self.dash_card3.grid(row=0, column=2, padx=(8, 0), sticky="nsew")
        self.dash_card3.pack_propagate(False)
        self.card3_lbl = ctk.CTkLabel(self.dash_card3, text="BUS LATENCY // JITTER\n-- ms average", font=ctk.CTkFont(family="JetBrains Mono", size=11), text_color=TEXT_MUTED)
        self.card3_lbl.pack(pady=12)
        
        # --- LEFT PANEL: QUICK SERVO NAVIGATION TREE ---
        self.nav_card = ctk.CTkFrame(self.main_container, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1)
        self.nav_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.nav_card.grid_columnconfigure(0, weight=1)
        self.nav_card.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.nav_card, text="⚡ SERVO JUMP NAV", font=ctk.CTkFont(family="Outfit", size=13, weight="bold"), text_color=ACCENT_PINK).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.tree_scroll = ctk.CTkScrollableFrame(self.nav_card, fg_color="transparent")
        self.tree_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.tree_scroll.grid_columnconfigure(0, weight=1)
        
        # --- RIGHT PANEL: FEED CONTAINER ---
        self.feed_card = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.feed_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.feed_card.grid_columnconfigure(0, weight=1)
        self.feed_card.grid_rowconfigure(1, weight=1)
        
        # Search & Filter bar row - under dashboard
        filter_row = ctk.CTkFrame(self.feed_card, fg_color=CARD_OSRS, border_color=BORDER_OSRS, border_width=1, height=50)
        filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filter_row.grid_propagate(False)
        
        self.search_entry = ctk.CTkEntry(
            filter_row, 
            placeholder_text="🔍 Filter joints by ID or Name (e.g. 'Shoulder', '12')...", 
            fg_color=BG_OSRS, 
            border_color=BORDER_OSRS,
            height=34,
            font=ctk.CTkFont(family="Outfit", size=12)
        )
        self.search_entry.pack(fill="x", padx=15, pady=8)
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_motor_rows())
        
        # Scrollable container for motors list
        self.motors_scroll = ctk.CTkScrollableFrame(
            self.feed_card, 
            fg_color=CARD_OSRS, 
            border_color=BORDER_OSRS, 
            border_width=1, 
            label_text="C.H.I.M.A.N TELEMETRY HUB - DYNAMIXEL FEED"
        )
        self.motors_scroll.grid(row=1, column=0, sticky="nsew")
        
        self.placeholder = ctk.CTkLabel(
            self.motors_scroll, 
            text="Please establish serial line connection to scan for Dynamixels.",
            font=ctk.CTkFont(family="Outfit", size=13),
            text_color=TEXT_MUTED
        )
        self.placeholder.pack(pady=150)
        
        # Hook window close handlers
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize servo navigation tree
        self.update_servo_tree()
        
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
            return
            
        self.log_card_status(f"Opening {port}...")
        
        # Get target IDs based on selected profile for a faster scan
        profile = "Humanoid V1"
        target_ids = sorted(list(ROBOT_PROFILES.get(profile, {}).keys()))
            
        if not target_ids:
            target_ids = list(range(60))
            
        self.log_card_status(f"Scanning IDs {min(target_ids)}-{max(target_ids)}...")
        self.driver = DynamixelDriver(port=port, baudrate=baud, motor_ids=target_ids, mock_mode=False)
        if not self.driver.connect():
            self.log_card_status("Port unavailable!", error=True)
            self.driver = None
            return
            
        discovered = self.driver.scan()
        if not discovered:
            self.log_card_status("No nodes found!", error=True)
            self.driver.disconnect()
            self.driver = None
            return
            
        self.active_ids = sorted(discovered)
        self.online_ids = self.active_ids.copy()
        self.consecutive_failures = {mid: 0 for mid in self.active_ids}
        self.driver.motor_ids = self.active_ids
        
        # Extended position control (Mode 4)
        self.log_card_status("Setting Ext Pos Mode...")
        self.driver.set_operating_mode(self.active_ids, mode=4)
        
        # Build UI layout
        self.placeholder.pack_forget()
        self.build_motor_rows()
        self.filter_motor_rows()
        self.update_servo_tree()
        
        # Enable UI options
        self.connected = True
        self.conn_btn.configure(text="DISCONNECT", fg_color=ACCENT_CRIMSON, hover_color="#C01662")
        self.scan_btn.configure(state="normal")
        self.torque_on_btn.configure(state="normal")
        self.torque_off_btn.configure(state="normal")
        self.both_arms_pose_btn.configure(state="normal")
        self.left_arm_pose_btn.configure(state="normal")
        self.right_arm_pose_btn.configure(state="normal")
        self.left_arm_up_btn.configure(state="normal")
        self.left_arm_center_btn.configure(state="normal")
        self.left_arm_down_btn.configure(state="normal")
        self.left_hand_open_btn.configure(state="normal")
        self.left_hand_closed_btn.configure(state="normal")
        
        # Update cards
        self.dash_card1.configure(border_color=ACCENT_VIOLET)
        self.card1_lbl.configure(text=f"PORT: {port}\nBAUD: {baud}", text_color=TEXT_PRIMARY)
        
        self.dash_card2.configure(border_color=ACCENT_EMERALD)
        self.card2_lbl.configure(text=f"ACTIVE NODES\n{len(self.active_ids)} Online", text_color=ACCENT_EMERALD)
        
        self.status_msg = f"ONLINE // {len(self.active_ids)} nodes"
        self.status_is_err = False
        
        # Launch workers
        self.running = True
        self.worker_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.worker_thread.start()
        
        self.start_telemetry_loop()
        
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
        
        self.conn_btn.configure(text="CONNECT BUS", fg_color=ACCENT_PINK, hover_color="#D11871")
        self.scan_btn.configure(state="disabled")
        self.torque_on_btn.configure(state="disabled")
        self.torque_off_btn.configure(state="disabled")
        self.both_arms_pose_btn.configure(state="disabled")
        self.left_arm_pose_btn.configure(state="disabled")
        self.right_arm_pose_btn.configure(state="disabled")
        self.left_arm_up_btn.configure(state="disabled")
        self.left_arm_center_btn.configure(state="disabled")
        self.left_arm_down_btn.configure(state="disabled")
        self.left_hand_open_btn.configure(state="disabled")
        self.left_hand_closed_btn.configure(state="disabled")
        
        # Tear down motor rows
        for mid, frame in list(self.motor_row_widgets.items()):
            try:
                frame.destroy()
            except Exception:
                pass
        self.motor_row_widgets.clear()
        self.motor_widgets.clear()
        self.placeholder.pack(pady=150)
        
        # Clear cards
        self.dash_card1.configure(border_color=BORDER_OSRS)
        self.card1_lbl.configure(text="COM PORT // BAUD\nDisconnections active", text_color=TEXT_MUTED)
        
        self.dash_card2.configure(border_color=BORDER_OSRS)
        self.card2_lbl.configure(text="NODES DETECTED\n0 active on bus", text_color=TEXT_MUTED)
        
        self.dash_card3.configure(border_color=BORDER_OSRS)
        self.card3_lbl.configure(text="BUS LATENCY // JITTER\n-- ms average", text_color=TEXT_MUTED)
        
        self.active_ids = []
        self.status_msg = "DISCONNECTED"
        self.status_is_err = True
        self.update_servo_tree()
        self.last_rendered_states.clear()
        if hasattr(self, "last_status_state"):
            self.last_status_state.clear()
        
    def trigger_rescan(self):
        if not self.connected or not self.driver:
            return
        
        # Relax / Disconnect thread temporarily
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
            self.worker_thread = None
            
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
            self.update_servo_tree()
            
            self.card2_lbl.configure(text=f"ACTIVE NODES\n{len(self.active_ids)} Online", text_color=ACCENT_EMERALD)
            self.status_msg = f"ONLINE // {len(self.active_ids)} nodes"
            self.status_is_err = False
        else:
            self.active_ids = []
            self.update_servo_tree()
            self.status_msg = "Scan returned zero nodes!"
            self.status_is_err = True
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.worker_thread.start()
        
    def log_card_status(self, text, error=False):
        color = ACCENT_CRIMSON if error else ACCENT_PINK
        self.card1_lbl.configure(text=text, text_color=color)
        
    def start_telemetry_loop(self):
        self.telemetry_loop_active = True
        self.run_telemetry_loop()
        
    def run_telemetry_loop(self):
        if not self.telemetry_loop_active:
            return
        self.update_gui_telemetry()
        self.after(40, self.run_telemetry_loop)  # 25Hz Refresh
        
    def set_global_torque(self, enable):
        if not self.driver:
            return
        with self.lock:
            # Enforce lockouts for online joints only to avoid timeout lags
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
        
        current_profile = "Humanoid V1"
        
        for mid in self.active_ids:
            # Row Card Container
            row_card = ctk.CTkFrame(self.motors_scroll, fg_color=CARD_INNER, border_color=BORDER_OSRS, border_width=1, height=85)
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
            joint_name = self.get_joint_name(mid, current_profile)
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

    def on_profile_changed(self, choice):
        self.update_joint_names_display()
        self.build_preset_buttons()
        self.update_servo_tree()
        
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
                
    def update_servo_tree(self):
        """Builds a structured quick-navigation list/tree of all active servos."""
        for w in self.tree_scroll.winfo_children():
            w.destroy()
            
        if not self.active_ids:
            placeholder = ctk.CTkLabel(
                self.tree_scroll,
                text="Establish connection\nto view servos.",
                font=ctk.CTkFont(family="Outfit", size=11, slant="italic"),
                text_color=TEXT_MUTED
            )
            placeholder.pack(pady=20)
            return
            
        profile = "Humanoid V1"
        
        # Group the active motors
        groups = {}
        for mid in self.active_ids:
            name = self.get_joint_name(mid, profile)
            # Deduce group name based on prefix / content of the joint name
            if name.startswith("Index"):
                g_name = "☝ Index Finger"
            elif name.startswith("Middle"):
                g_name = "🖕 Middle Finger"
            elif name.startswith("Ring"):
                g_name = "💍 Ring Finger"
            elif name.startswith("Thumb"):
                g_name = "👍 Thumb"
            elif name.startswith("L ") or "L Shoulder" in name or "L Elbow" in name or "L Forearm" in name or "L Wrist" in name or "L Hand" in name or "L1" in name or "L2" in name or "L3" in name or "L4" in name or "L5" in name or "L6" in name or "L7" in name or "L8" in name:
                g_name = "🦾 Left Arm"
            elif name.startswith("R ") or "R Shoulder" in name or "R Elbow" in name or "R Forearm" in name or "R Wrist" in name or "R Hand" in name or "R1" in name or "R2" in name or "R3" in name or "R4" in name or "R5" in name or "R6" in name or "R7" in name or "R8" in name:
                g_name = "🦾 Right Arm"
            elif "Head" in name or name.startswith("Head"):
                g_name = "👤 Head"
            elif "Joint" in name:
                g_name = "🎛 Joints"
            else:
                g_name = "⚙ General Actuators"
                
            if g_name not in groups:
                groups[g_name] = []
            groups[g_name].append((mid, name))
            
        # Render the tree categories and items
        for g_name, motors in groups.items():
            # Group Header (simulated tree parent node)
            hdr = ctk.CTkLabel(self.tree_scroll, text=g_name, font=ctk.CTkFont(family="Outfit", size=12, weight="bold"), text_color=TEXT_MUTED, anchor="w")
            hdr.pack(fill="x", padx=5, pady=(10, 2))
            
            # Indented buttons for each motor
            for mid, m_name in motors:
                btn = ctk.CTkButton(
                    self.tree_scroll,
                    text=f"  ↳ [{mid}] {m_name}",
                    font=ctk.CTkFont(family="JetBrains Mono", size=10),
                    fg_color="transparent",
                    text_color=TEXT_PRIMARY,
                    hover_color=BORDER_OSRS,
                    anchor="w",
                    height=24,
                    command=lambda m=mid: self.jump_to_servo(m)
                )
                btn.pack(fill="x", padx=(15, 5), pady=1)
                
    def jump_to_servo(self, mid):
        """Scrolls to a specific servo row in the sliders container and highlights it."""
        canvas = getattr(self.motors_scroll, "_parent_canvas", None)
        if canvas is not None:
            if len(self.active_ids) > 1:
                try:
                    idx = self.active_ids.index(mid)
                    fraction = idx / len(self.active_ids)
                    # Adjust fraction to center it
                    fraction = max(0.0, min(1.0, fraction - 0.1))
                    canvas.yview_moveto(fraction)
                except ValueError:
                    pass
                    
        # Highlight the row card briefly
        row_card = self.motor_row_widgets.get(mid)
        if row_card is not None:
            row_card.configure(fg_color=ACCENT_VIOLET)
            # Revert color back to original CARD_INNER after 1000ms
            self.after(1000, lambda: row_card.configure(fg_color=CARD_INNER))
                
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

    def build_preset_buttons(self):
        pass

    # Preset Actions
    def preset_zero_all(self):
        for mid in self.active_ids:
            self.set_goal_value_direct(mid, 2048)
            
    def preset_sync_goals(self):
        with self.lock:
            for mid in self.active_ids:
                pres = self.present_positions.get(mid, 2048)
                self.goal_positions[mid] = pres
                
        # Sync widgets
        for mid in self.active_ids:
            if mid in self.motor_widgets:
                self.sync_widgets_to_goal(mid, self.goal_positions[mid])
                
    def preset_humanoid_home(self):
        for mid, home_val in HUMANOID_DEFAULTS.items():
            if mid in self.active_ids:
                self.set_goal_value_direct(mid, home_val)
                
    def preset_left_arm_offsets(self):
        left_arm_offsets = {24: 3065, 25: -56, 26: -1034, 27: 2100}
        
        # Safe auto-arming sequence: enable torque for left arm joints if disabled
        joints_to_torque = [mid for mid in left_arm_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming Left Arm joints..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    # Mark as pending torque action
                    self.pending_torque_actions.add(mid)
                    # Enforce goal position under lock
                    self.goal_positions[mid] = left_arm_offsets[mid]
                    # Queue torque enablement
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            
            # Sync GUI widgets immediately
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, left_arm_offsets[mid])
                
    def preset_left_arm_up(self):
        # Move L5 (25) to UP (-150) and sync R4 (14) by applying the mirrored difference + a slight offset (+150 total) from its center (2170)
        left_arm_offsets = {25: -150, 26: -983, 27: 2088, 14: 2320}
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
        # Move L5 (25) to Down (50) and sync R4 (14) by applying the mirrored difference (-100) from its center (2170)
        left_arm_offsets = {25: 50, 26: -983, 27: 2088, 14: 2070}
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
        # Move L5 (25) to Center (-50) and sync R4 (14) to its center (2170)
        left_arm_offsets = {25: -50, 26: -983, 27: 2088, 14: 2170}
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
        left_hand_offsets = {28: -286}
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
        right_arm_offsets = {14: 2170, 15: -24, 16: 3034, 17: 851}
        
        # Safe auto-arming sequence: enable torque for right arm joints if disabled
        joints_to_torque = [mid for mid in right_arm_offsets if mid in self.active_ids]
        if joints_to_torque:
            self.status_msg = "Arming Right Arm joints..."
            self.status_is_err = False
            with self.lock:
                for mid in joints_to_torque:
                    # Mark as pending torque action
                    self.pending_torque_actions.add(mid)
                    # Enforce goal position under lock
                    self.goal_positions[mid] = right_arm_offsets[mid]
                    # Queue torque enablement
                    self.pending_actions.append({
                        "type": "torque",
                        "motor_id": mid,
                        "enable": True
                    })
            
            # Sync GUI widgets immediately
            for mid in joints_to_torque:
                self.sync_widgets_to_goal(mid, right_arm_offsets[mid])
                
    def preset_both_arms_offsets(self):
        left_arm_offsets = {24: 3065, 25: -56, 26: -1034, 27: 2100}
        right_arm_offsets = {14: 2170, 15: -24, 16: 3034, 17: 851}
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
            self.log_card_status("Preset saved successfully!")
        except Exception as e:
            self.log_card_status(f"Save failed: {str(e)}", error=True)
            
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
            self.log_card_status("Preset loaded successfully!")
        except Exception as e:
            self.log_card_status(f"Load failed: {str(e)}", error=True)

    def set_goal_value_direct(self, motor_id, value):
        with self.lock:
            self.goal_positions[motor_id] = value
        if motor_id in self.motor_widgets:
            self.sync_widgets_to_goal(motor_id, value)
            
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

    def _update_loop(self):
        """Hardware transaction thread running serial lines."""
        while self.running:
            if not self.driver or not self.driver.is_connected:
                time.sleep(0.1)
                continue
                
            reads = {}
            # 1. Pop pending actions under lock
            actions_to_process = []
            with self.lock:
                if self.pending_actions:
                    actions_to_process = list(self.pending_actions)
                    self.pending_actions.clear()
            
            # 2. Process actions outside lock (one by one)
            for action in actions_to_process:
                if not self.driver or not self.driver.is_connected:
                    break
                if action["type"] == "torque":
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
                        
                elif action["type"] == "global_torque":
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
                            
                elif action["type"] == "reboot":
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

            # 3. Read present positions
            with self.lock:
                online_ids_copy = list(self.online_ids)
            
            reads = {}
            latency = 0.0
            if online_ids_copy:
                try:
                    start_time = time.perf_counter()
                    reads = self.driver.read_positions(online_ids_copy)
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
                        
            time.sleep(0.040)  # 25Hz loop frequency
            
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
        if not hasattr(self, "last_status_state"):
            self.last_status_state = {}
            
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
            
        # Row card state styling changes (Offline/Online/Torque)
        for mid in self.active_ids:
            if mid in self.motor_widgets:
                w = self.motor_widgets[mid]
                g_pos = goals.get(mid, "--")
                p_pos = presents.get(mid, "--")
                
                is_online = mid in online_list
                is_torqued = torques.get(mid, False)
                
                # Check cache to avoid redundant configurations
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
                    
                # Store in cache
                self.last_rendered_states[mid] = {
                    "online": is_online,
                    "torqued": is_torqued,
                    "present_pos": p_pos,
                    "goal_pos": g_pos
                }
                
                # 1. Update online/offline transition state styles
                if prev is None or prev.get("online") != is_online or prev.get("torqued") != is_torqued:
                    if is_online:
                        w["badge_lbl"].configure(text="ONLINE", text_color=ACCENT_EMERALD)
                        w["row_card"].configure(border_color=BORDER_OSRS)
                        w["slider"].configure(state="normal")
                        w["entry"].configure(state="normal")
                        
                        # Set switch state
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
                        
                        # Force switch off for offline motors
                        t_switch = w["t_switch"]
                        t_switch.configure(command=None)
                        t_switch.deselect()
                        t_switch.configure(command=lambda m=mid: self.on_row_torque_toggle(m))
                        
                # 2. Update telemetry labels and physically sync relaxed sliders (with encoder noise deadband)
                if is_online:
                    # Update label text if present or goal changed
                    if prev is None or prev.get("present_pos") != p_pos or prev.get("goal_pos") != g_pos:
                        w["telemetry_lbl"].configure(text=f"Present: {p_pos}\nGoal: {g_pos}", text_color=TEXT_MUTED)
                        
                    # Sync physically moved actuator goals when relaxed (not torqued)
                    if not is_torqued and isinstance(p_pos, int):
                        prev_p = prev.get("present_pos") if prev else None
                        # Sync only if this is the first render, or the movement is larger than the 8-tick jitter threshold
                        if prev_p is None or not isinstance(prev_p, int) or abs(prev_p - p_pos) >= 8:
                            slider = w["slider"]
                            entry = w["entry"]
                            
                            s_min = slider.cget("from_")
                            s_max = slider.cget("to")
                            if p_pos > s_max:
                                slider.configure(to=p_pos + 2048)
                            elif p_pos < s_min:
                                slider.configure(from_=p_pos - 2048)
                                
                            # Temporarily detach command callback to prevent feedback loops
                            slider.configure(command=None)
                            slider.set(p_pos)
                            slider.configure(command=lambda val, m=mid, en=entry: self.update_goal_position(m, int(val), source_entry=False, entry_widget=en))
                            
                            entry.delete(0, tk.END)
                            entry.insert(0, str(p_pos))

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
