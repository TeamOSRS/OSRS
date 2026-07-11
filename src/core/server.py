import sys
import os
import time
import threading
import asyncio
import base64
import cv2
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

# Core Managers
from src.core.event_bus import EventBus
from src.core.logging import logger
from src.core.websocket_manager import WebsocketManager
from src.core.robot_manager import RobotManager
from src.core.telemetry_manager import TelemetryManager
from src.core.plugin_manager import PluginManager

# Create App
app = FastAPI(title="OSRS Modular Robotics Operating Platform Server")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate Core Architecture
event_bus = EventBus()
websocket_manager = WebsocketManager()
robot_manager = RobotManager(event_bus)
telemetry_manager = TelemetryManager(event_bus)
plugin_manager = PluginManager(event_bus)
robot_manager.plugin_manager = plugin_manager

# Load plugins
plugin_manager.load_builtins()

# Set initial default robot profile (Humanoid V1)
default_robot = plugin_manager.robots.get("Humanoid V1")
if default_robot:
    robot_manager.set_robot(default_robot)

# Websocket callback handler to receive manual target values
def manual_ws_command_handler(data: Dict[str, Any]):
    action = data.get("action")
    if action == "manual":
        positions = data.get("positions", {})
        if robot_manager.active_robot:
            limits = robot_manager.active_robot.get_joint_layout()
            for mid_str, pos in positions.items():
                try:
                    mid = int(mid_str)
                    if mid in robot_manager.manual_positions:
                        default_val = limits.get(mid, {}).get("default", 2048)
                        robot_manager.set_manual_position(mid, int(pos) + default_val)
                except Exception:
                    pass


websocket_manager.register_handler(manual_ws_command_handler)

# Web endpoints request definitions
class ConnectRequest(BaseModel):
    port: str
    baudrate: int
    mock_mode: bool
    current_limit: int = 250
    speed_limit: int = 150

class ProfileRequest(BaseModel):
    version: str

class TorqueRequest(BaseModel):
    motor_id: str
    enable: bool

class RebootRequest(BaseModel):
    motor_id: int

class ManualRequest(BaseModel):
    positions: Dict[int, int]

class TrackingRequest(BaseModel):
    enable: bool

class VisionRequest(BaseModel):
    camera_index: int
    enable: bool

class EmoteRequest(BaseModel):
    name: str
    loop: int = 1
    speed: float = 1.0

class CalibControlRequest(BaseModel):
    action: str

class ConfigSaveRequest(BaseModel):
    motor_id: int
    new_id: int
    name: str
    min_val: int
    max_val: int

class ConfigDeleteRequest(BaseModel):
    motor_id: int

# REST API Endpoints
@app.get("/api/status")
def get_status():
    limits = robot_manager.active_robot.get_joint_layout() if robot_manager.active_robot else {}
    mapped_limits = {}
    for mid, val in limits.items():
        mapped_limits[mid] = {
            "name": val["name"],
            "min": val["min"],
            "max": val["max"],
            "default": val["default"]
        }
        
    return {
        "connected": robot_manager.connected,
        "port": robot_manager.active_port,
        "baudrate": robot_manager.baudrate,
        "mock_mode": robot_manager.mock_mode,
        "hand_version": robot_manager.active_robot.version if robot_manager.active_robot else "Unknown",
        "estop_active": robot_manager.estop_active,
        "tracking_enabled": robot_manager.tracking_enabled,
        "camera_active": robot_manager.camera_active,
        "camera_index": getattr(robot_manager, "camera_index", 0),
        "active_motor_ids": robot_manager.driver.motor_ids if robot_manager.driver else list(limits.keys()),
        "limits": mapped_limits,
        "system_health": robot_manager.system_health,
        "cpu_usage": robot_manager.cpu_usage,
        "ram_usage": robot_manager.ram_usage,
        "latency": robot_manager.latency,
        "fps": robot_manager.fps,
        "logs": logger.get_logs(25)
    }

@app.get("/api/robot/description")
def get_robot_description():
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    return robot_manager.active_robot.get_robot_description().to_dict()

from fastapi.responses import FileResponse

@app.get("/api/robot/asset")
def get_robot_asset(path: str):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_path = os.path.abspath(os.path.join(root_dir, path))
    if not abs_path.startswith(root_dir):
        raise HTTPException(status_code=403, detail="Access denied.")
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Asset not found.")
    return FileResponse(abs_path)

@app.post("/api/connect")
def connect_system(req: ConnectRequest):
    res = robot_manager.connect(
        port=req.port,
        baudrate=req.baudrate,
        mock_mode=req.mock_mode,
        current_limit=req.current_limit,
        speed_limit=req.speed_limit
    )
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@app.post("/api/disconnect")
def disconnect_system():
    return robot_manager.disconnect()

@app.post("/api/estop")
def trigger_estop(action: Dict[str, bool] = Body(...)):
    active = action.get("active", False)
    robot_manager.trigger_estop(active)
    return {"estop_active": robot_manager.estop_active}

@app.post("/api/profile")
def change_profile(req: ProfileRequest):
    robot = plugin_manager.robots.get(req.version)
    if not robot:
        raise HTTPException(status_code=400, detail=f"Profile {req.version} not found.")
    robot_manager.set_robot(robot)
    return {"status": "success", "hand_version": robot_manager.active_robot.version}

@app.post("/api/torque")
def set_torque(req: TorqueRequest):
    success = robot_manager.toggle_torque(req.motor_id, req.enable)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to write torque packet.")
    return {"status": "success"}

@app.post("/api/reboot")
def reboot_motor(req: RebootRequest):
    robot_manager.trigger_reboot(req.motor_id)
    return {"status": "scheduled", "motor_id": req.motor_id}

class MirrorSyncRequest(BaseModel):
    active: bool

@app.get("/api/robot/mirror-sync")
def get_mirror_sync():
    return {"mirror_sync_active": robot_manager.mirror_sync_active}

@app.post("/api/robot/mirror-sync")
def set_mirror_sync(req: MirrorSyncRequest):
    robot_manager.mirror_sync_active = req.active
    logger.log(f"Dual-Arm Symmetry Mirroring state: {'ENABLED' if req.active else 'DISABLED'}")
    return {"mirror_sync_active": robot_manager.mirror_sync_active}

@app.post("/api/manual")
def set_manual_positions(req: ManualRequest):
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    limits = robot_manager.active_robot.get_joint_layout()
    for mid, pos in req.positions.items():
        if mid in robot_manager.manual_positions:
            default_val = limits.get(mid, {}).get("default", 2048)
            robot_manager.set_manual_position(mid, pos + default_val)
    return {"status": "success"}


@app.post("/api/tracking")
def set_tracking(req: TrackingRequest):
    robot_manager.tracking_enabled = req.enable
    logger.log(f"Visual hand-tracking autopilot state: {req.enable}")
    return {"tracking_enabled": robot_manager.tracking_enabled}

@app.post("/api/vision/toggle")
def toggle_vision(req: VisionRequest):
    robot_manager.camera_index = req.camera_index
    vision = plugin_manager.perception_modules.get("vision")
    
    if req.enable:
        logger.log(f"Initializing perception pipeline on Camera Index {req.camera_index}...")
        success = vision.start(camera_index=req.camera_index)
        if success:
            robot_manager.camera_active = True
            logger.log("Perception vision camera thread live.")
            return {"camera_active": True}
        else:
            robot_manager.camera_active = False
            logger.log("Failed to open camera index. Verify webcam connections.", "ERROR")
            raise HTTPException(status_code=400, detail="Webcam initialize failed.")
    else:
        vision.stop()
        robot_manager.camera_active = False
        logger.log("Perception vision camera thread offline.")
        return {"camera_active": False}

# Presets / Emotes endpoints
@app.post("/api/emote")
def run_emote(req: EmoteRequest):
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System disconnected.")
        
    emotes = robot_manager.active_robot.get_emotes()
    if req.name not in emotes:
        raise HTTPException(status_code=400, detail=f"Preset {req.name} not found.")
        
    # Compile animation frames
    single_loop_frames = emotes[req.name]
    frames = []
    for _ in range(req.loop):
        frames.extend(single_loop_frames)
        
    robot_manager.active_emote_frames = frames
    robot_manager.is_emote_running = True
    robot_manager.emote_delay_ms = int(50 / max(0.1, req.speed))
    
    # Run emote play sequence in helper thread
    def play_sequence():
        # Setup torque if off
        with robot_manager.dxl_lock:
            motor_ids = list(robot_manager.active_robot.get_joint_layout().keys())
            robot_manager.driver.enable_torque(motor_ids, True)
            for m in motor_ids:
                robot_manager.driver.torque_state[m] = True
        
        # Step frames
        for frame in robot_manager.active_emote_frames:
            if not robot_manager.is_emote_running:
                break
            with robot_manager.dxl_lock:
                for mid_name, val in frame.get("modifications", {}).items():
                    # Find motor by name
                    for mid, info in robot_manager.active_robot.get_joint_layout().items():
                        if info["name"] == mid_name:
                            robot_manager.manual_positions[mid] = val + info["default"]
            time.sleep(robot_manager.emote_delay_ms / 1000.0)
            
        robot_manager.is_emote_running = False
        
    threading.Thread(target=play_sequence, daemon=True).start()
    return {"status": "success", "frames_compiled": len(frames)}

SAVED_EMOTES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "custom_emotes.json")

def load_saved_emotes() -> dict:
    if not os.path.exists(SAVED_EMOTES_FILE):
        return {}
    try:
        with open(SAVED_EMOTES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_emotes_to_file(emotes: dict):
    try:
        with open(SAVED_EMOTES_FILE, "w") as f:
            json.dump(emotes, f, indent=4)
    except Exception as e:
        logger.log(f"Error saving custom emotes: {e}", "ERROR")

class SaveEmoteRequest(BaseModel):
    name: str
    frames: List[dict]

class DeleteEmoteRequest(BaseModel):
    name: str

class CustomEmoteRequest(BaseModel):
    loop: int = 1
    frames: List[dict]
    speed: float = 1.0

@app.get("/api/emote/custom/list")
def list_custom_emotes():
    return load_saved_emotes()

@app.post("/api/emote/custom/save")
def save_custom_emote(req: SaveEmoteRequest):
    emotes = load_saved_emotes()
    emotes[req.name] = req.frames
    save_emotes_to_file(emotes)
    return {"status": "success"}

@app.post("/api/emote/custom/delete")
def delete_custom_emote(req: DeleteEmoteRequest):
    emotes = load_saved_emotes()
    if req.name in emotes:
        emotes.pop(req.name)
        save_emotes_to_file(emotes)
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Emote not found.")

@app.post("/api/emote/custom")
def run_custom_emote(req: CustomEmoteRequest):
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System disconnected.")
        
    frames = []
    limits = robot_manager.active_robot.get_joint_layout() if robot_manager.active_robot else {}
    
    for _ in range(req.loop):
        for f in req.frames:
            delay = f.get("delay", 10)
            mods = f.get("modifications", {})
            frames.append({"delay": delay, "modifications": mods})
            
    robot_manager.active_emote_frames = frames
    robot_manager.is_emote_running = True
    robot_manager.emote_delay_ms = int(50 / max(0.1, req.speed))
    
    def play_custom():
        for frame in robot_manager.active_emote_frames:
            if not robot_manager.is_emote_running:
                break
            with robot_manager.dxl_lock:
                for name, val in frame.get("modifications", {}).items():
                    for mid, info in limits.items():
                        if info["name"] == name:
                            robot_manager.manual_positions[mid] = val + info["default"]
            time.sleep(robot_manager.emote_delay_ms / 1000.0)
        robot_manager.is_emote_running = False
        
    threading.Thread(target=play_custom, daemon=True).start()
    return {"status": "success", "frames_compiled": len(frames)}

# Calibration control
@app.post("/api/calibration/control")
def control_calibration(req: CalibControlRequest):
    action = req.action
    if action == "start":
        if not robot_manager.connected:
            raise HTTPException(status_code=400, detail="System offline.")
        active_ids = robot_manager.driver.motor_ids
        
        # Read start pose
        with robot_manager.dxl_lock:
            start_pose = robot_manager.driver.read_positions(active_ids)
            
        limits = robot_manager.active_robot.get_joint_layout()
        end_pose = {mid: info["default"] for mid, info in limits.items()}
        
        robot_manager.calib_running = True
        robot_manager.calib_progress = 0.0
        robot_manager.calib_status_msg = "Moving joints slowly using quintic profile"
        
        # Compile path
        trajectory = robot_manager.active_robot.get_calibration_trajectory(active_ids, start_pose, end_pose)
        
        def run_calib():
            idx = 0
            while robot_manager.calib_running and idx < len(trajectory):
                if robot_manager.calib_paused:
                    time.sleep(0.1)
                    continue
                target = trajectory[idx]
                with robot_manager.dxl_lock:
                    robot_manager.driver.write_positions(target)
                    for mid, val in target.items():
                        robot_manager.manual_positions[mid] = val
                        robot_manager.target_positions[mid] = val
                time.sleep(0.02) # 50Hz
                idx += 1
                robot_manager.calib_progress = round(idx / len(trajectory), 3)
            robot_manager.calib_running = False
            robot_manager.calib_status_msg = "Completed successfully"
            
        threading.Thread(target=run_calib, daemon=True).start()
        return {"status": "started"}
        
    elif action == "pause":
        robot_manager.calib_paused = True
        return {"status": "paused"}
    elif action == "resume":
        robot_manager.calib_paused = False
        return {"status": "resumed"}
    elif action == "abort":
        robot_manager.calib_running = False
        return {"status": "aborted"}
        
    raise HTTPException(status_code=400, detail="Invalid calibration action.")

@app.post("/api/calibration/set-zero")
def set_zero_calibration():
    if not robot_manager.connected or not robot_manager.driver:
        raise HTTPException(status_code=400, detail="Bus offline.")
        
    limits = robot_manager.active_robot.get_joint_layout()
    motor_ids = list(limits.keys())
    with robot_manager.dxl_lock:
        pres_pos = robot_manager.driver.read_positions(motor_ids)
        
    if not pres_pos:
         raise HTTPException(status_code=400, detail="Failed to read physical joint telemetry.")
         
    for mid in motor_ids:
        pos = pres_pos.get(mid)
        if isinstance(pos, (int, float)) and mid in limits:
            pos_int = int(pos)
            limits[mid]["default"] = pos_int
            limits[mid]["min"] = pos_int - 4096
            limits[mid]["max"] = pos_int + 4096
            
    robot_manager.update_motor_defaults()
    # Save active config back
    if robot_manager.active_robot:
        robot_manager.active_robot.save_config()
    return {"status": "success"}

@app.post("/api/calibration/save-base-frame")
def save_base_frame(req: Dict[str, int] = Body(...)):
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
        
    limits = robot_manager.active_robot.get_joint_layout()
    for mid_str, default_val in req.items():
        try:
            mid = int(mid_str)
        except ValueError:
            continue
        if mid in limits:
            old_default = limits[mid].get("default", 2048)
            diff = default_val - old_default
            limits[mid]["default"] = default_val
            limits[mid]["min"] += diff
            limits[mid]["max"] += diff
            
    robot_manager.update_motor_defaults()
    if robot_manager.active_robot:
        robot_manager.active_robot.save_config()
    return {"status": "success"}

@app.post("/api/calibration/go-to-base")
def go_to_base_pose():
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System disconnected: Please connect robot or simulation first.")
        
    limits = robot_manager.active_robot.get_joint_layout()
    with robot_manager.dxl_lock:
        motor_ids = list(limits.keys())
        if robot_manager.driver:
            robot_manager.driver.enable_torque(motor_ids, True)
            for mid in motor_ids:
                robot_manager.driver.torque_state[mid] = True
            
        for mid, info in limits.items():
            default_val = info["default"]
            robot_manager.manual_positions[mid] = default_val
            robot_manager.target_positions[mid] = default_val
            
    logger.log("Commanded robot arms to move to calibrated base frame pose.")
    return {"status": "success"}

# Config edit endpoints
@app.post("/api/config/save")
def save_config(req: ConfigSaveRequest):
    limits = robot_manager.active_robot.get_joint_layout() if robot_manager.active_robot else {}
    if req.motor_id not in limits:
        raise HTTPException(status_code=400, detail="Motor ID not found.")
        
    info = limits[req.motor_id]
    info["name"] = req.name
    info["min"] = req.min_val
    info["max"] = req.max_val
    
    if req.new_id != req.motor_id:
        limits.pop(req.motor_id)
        limits[req.new_id] = info
        
    if robot_manager.driver:
        with robot_manager.dxl_lock:
            robot_manager.driver.motor_ids = list(limits.keys())
            
    robot_manager.update_motor_defaults()
    if robot_manager.active_robot:
        robot_manager.active_robot.save_config()
    return {"status": "success"}

@app.post("/api/config/delete")
def delete_config(req: ConfigDeleteRequest):
    limits = robot_manager.active_robot.get_joint_layout() if robot_manager.active_robot else {}
    if req.motor_id in limits:
        limits.pop(req.motor_id)
        if robot_manager.driver:
            with robot_manager.dxl_lock:
                robot_manager.driver.motor_ids = list(limits.keys())
        robot_manager.update_motor_defaults()
        if robot_manager.active_robot:
            robot_manager.active_robot.save_config()
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Motor ID not found.")

@app.post("/api/mock/trigger-error")
def mock_trigger_error(data: Dict[str, Any] = Body(...)):
    motor_id = data.get("motor_id")
    error_byte = data.get("error_byte", 32)
    if motor_id is not None:
        robot_manager.mock_errors[int(motor_id)] = int(error_byte)
        logger.log(f"[MOCK] Injecting error {hex(error_byte)} on Motor ID {motor_id}", "WARNING")
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Missing motor_id.")

# Ball Balancer Research endpoints
class BallBalancerConfigRequest(BaseModel):
    kp: float
    kd: float
    ki: float
    provider: str  # "vision", "force", "fusion"
    speed: Optional[float] = None  # 0.1 – 2.0 multiplier
    max_tilt_positive: Optional[float] = None  # servo units above center
    max_tilt_negative: Optional[float] = None  # servo units below center
    auto_tune: Optional[bool] = None
    exploration_mode: Optional[bool] = None
    loadcell_mode: Optional[int] = None
    loadcell_arm: Optional[str] = None
    ball_weight_ref: Optional[float] = None
    invert_output: Optional[bool] = None
    ball_type: Optional[str] = None

class CalibrateScaleRequest(BaseModel):
    side: str  # "left" or "right"
    known_weight: float  # grams

class PortConfigRequest(BaseModel):
    port: str  # e.g., "COM11" or "/dev/ttyUSB0"

class CameraSettingsRequest(BaseModel):
    laser_power: Optional[float] = None
    emitter_state: Optional[int] = None
    visual_preset: Optional[int] = None
    auto_exposure: Optional[bool] = None
    exposure_us: Optional[float] = None
    auto_white_balance: Optional[bool] = None
    white_balance_temp: Optional[float] = None
    hsv_bounds: Optional[Dict[str, int]] = None
    filter_mode: Optional[str] = None
    filter_window: Optional[int] = None
    filter_process_noise: Optional[float] = None
    filter_measurement_noise: Optional[float] = None

@app.post("/api/research/ball-balancer/config")
def configure_ball_balancer(req: BallBalancerConfigRequest):
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer:
        raise HTTPException(status_code=400, detail="Ball Balancer research module offline.")
    balancer.update_gains(req.kp, req.kd, req.ki)
    balancer.set_provider(req.provider)
    if req.speed is not None:
        balancer.set_speed(req.speed)
    if req.max_tilt_positive is not None and req.max_tilt_negative is not None:
        balancer.set_tilt_limits(req.max_tilt_positive, req.max_tilt_negative)
    if req.auto_tune is not None:
        balancer.auto_tune_enabled = req.auto_tune
    if req.exploration_mode is not None:
        balancer.exploration_mode = req.exploration_mode
    if req.loadcell_mode is not None:
        balancer.loadcell_mode = req.loadcell_mode
        if getattr(balancer, "force_sensor", None):
            balancer.force_sensor.loadcell_mode = req.loadcell_mode
    if req.loadcell_arm is not None:
        balancer.loadcell_arm = req.loadcell_arm
        if getattr(balancer, "force_sensor", None):
            balancer.force_sensor.loadcell_arm = req.loadcell_arm
    if req.ball_weight_ref is not None:
        balancer.ball_weight_ref = req.ball_weight_ref
    if req.invert_output is not None:
        balancer.invert_output = req.invert_output
    if req.ball_type is not None:
        balancer.ball_type = req.ball_type
        # Update vision tracker HSV bounds and default ball weight parameters automatically
        vision = plugin_manager.perception_modules.get("vision")
        if vision and getattr(vision, "tracker", None):
            if req.ball_type == "metal_chrome":
                 # Tuned for metal ball painted in bright lemon yellow (medium-high hue, high saturation & brightness)
                # Restricting search space via the plate bounding box mask prevents background false-positives.
                vision.tracker.hsv_bounds = {
                    "h_low": 22, "s_low": 80, "v_low": 90,
                    "h_high": 38, "s_high": 255, "v_high": 255
                }
                balancer.ball_weight_ref = 225.0
            else:  # green_ping_pong
                vision.tracker.hsv_bounds = {
                    "h_low": 35, "s_low": 40, "v_low": 40,
                    "h_high": 85, "s_high": 255, "v_high": 255
                }
                balancer.ball_weight_ref = 100.0
    balancer._save_learning_data()
    return {"status": "success"}

@app.post("/api/research/balancer/loadcell/tare")
def loadcell_tare():
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer or not balancer.force_sensor:
        raise HTTPException(status_code=400, detail="Ball balancer force sensing offline.")
    balancer.force_sensor.tare_scales()
    return {"status": "success"}

@app.post("/api/research/balancer/loadcell/calibrate")
def loadcell_calibrate(req: CalibrateScaleRequest):
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer or not balancer.force_sensor:
        raise HTTPException(status_code=400, detail="Ball balancer force sensing offline.")
    success = balancer.force_sensor.calibrate_scale(req.side, req.known_weight)
    if not success:
        raise HTTPException(status_code=400, detail="Calibration failed. Check weight and side.")
    return {"status": "success"}

@app.post("/api/research/balancer/loadcell/port")
def loadcell_port(req: PortConfigRequest):
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer or not balancer.force_sensor:
        raise HTTPException(status_code=400, detail="Ball balancer force sensing offline.")
    balancer.force_sensor.update_port(req.port)
    return {"status": "success"}

@app.get("/api/research/balancer/loadcell/ports")
def list_loadcell_ports():
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    return {"ports": [p.device for p in ports]}

@app.post("/api/research/balancer/loadcell/connect")
def loadcell_connect():
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer or not balancer.force_sensor:
        raise HTTPException(status_code=400, detail="Ball balancer force sensing offline.")
    balancer.force_sensor.start_reading()
    return {"status": "success", "connected": balancer.force_sensor.connected}

@app.post("/api/research/balancer/loadcell/disconnect")
def loadcell_disconnect():
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer or not balancer.force_sensor:
        raise HTTPException(status_code=400, detail="Ball balancer force sensing offline.")
    balancer.force_sensor.stop_reading()
    return {"status": "success", "connected": balancer.force_sensor.connected}

@app.post("/api/research/balancer/loadcell/reset-model")
def loadcell_reset_model():
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer:
        raise HTTPException(status_code=400, detail="Ball balancer offline.")
    balancer.reset_loadcell_model()
    return {"status": "success"}

@app.get("/api/perception/realsense/settings")
def get_realsense_settings():
    vision = plugin_manager.perception_modules.get("vision")
    if not vision or not getattr(vision, "tracker", None):
        raise HTTPException(status_code=400, detail="RealSense vision system is offline.")
    try:
        settings = vision.tracker.get_camera_settings()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/perception/realsense/settings")
def set_realsense_settings(settings: CameraSettingsRequest):
    vision = plugin_manager.perception_modules.get("vision")
    if not vision or not getattr(vision, "tracker", None):
        raise HTTPException(status_code=400, detail="RealSense vision system is offline.")
    try:
        update_data = {k: v for k, v in settings.dict().items() if v is not None}
        vision.tracker.set_camera_settings(update_data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research/ball-balancer/toggle")
def toggle_ball_balancer(action: Dict[str, bool] = Body(...)):
    active = action.get("active", False)
    balancer = plugin_manager.research_modules.get("ball_balancer")
    if not balancer:
         raise HTTPException(status_code=400, detail="Ball Balancer research module offline.")
    
    balancer.is_active = active
    logger.log(f"Ball balancer task: {'ENABLED' if active else 'DISABLED'}")
    
    if active and robot_manager.connected and robot_manager.active_robot:
        limits = robot_manager.active_robot.get_joint_layout()
        motor_ids = list(limits.keys())
        
        # 1. Trigger reboot on joint 25 to clear any overload status
        logger.log("Auto balancer activated: Rebooting joint 25 to clear potential overload errors...")
        robot_manager.trigger_reboot(25)
        
        # 2. Wait 650ms for the motor to boot back up
        time.sleep(0.65)
        
        # 3. Ensure torque is enabled for all motors
        logger.log("Auto balancer activated: Enabling torque on all joints...")
        with robot_manager.dxl_lock:
            if robot_manager.driver:
                robot_manager.driver.enable_torque(motor_ids, True)
                for mid in motor_ids:
                    robot_manager.driver.torque_state[mid] = True
                    
    return {"active": balancer.is_active}

@app.post("/api/research/ball-balancer/go-to-start")
def go_to_start_pose():
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System disconnected: Please connect robot or simulation first.")
        
    limits = robot_manager.active_robot.get_joint_layout()
    with robot_manager.dxl_lock:
        # Enable torque for all joints
        motor_ids = list(limits.keys())
        robot_manager.driver.enable_torque(motor_ids, True)
        for mid in motor_ids:
            robot_manager.driver.torque_state[mid] = True
            
        # Move all joints smoothly to their profile defaults
        for mid, info in limits.items():
            default_val = info["default"]
            robot_manager.manual_positions[mid] = default_val
            robot_manager.target_positions[mid] = default_val
            
    logger.log("Commanded robot arms to move to ball balancing start pose.")
    return {"status": "success"}

@app.post("/api/research/ball-balancer/initialize-arms")
def initialize_arms_pose():
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System disconnected: Please connect robot or simulation first.")
        
    calib_l = getattr(robot_manager.active_robot, "calib_left", {})
    calib_r = getattr(robot_manager.active_robot, "calib_right", {})
    def cl(mid, default): return calib_l.get(mid, default)
    def cr(mid, default): return calib_r.get(mid, default)

    targets = {
        21: cl(21, -3561),
        12: cl(12, -162),
        13: cl(13, 4344),
        24: cl(24, 4026),
        25: cl(25, -82),
        26: cl(26, -1019),
        27: cl(27, 2065),
        28: cl(28, -2676),
        11: cr(11, -1674),
        22: cr(22, 2138),
        23: cr(23, -1275),
        14: cr(14, 2195),
        15: cr(15, -3),
        16: cr(16, 5117),
        17: cr(17, 2079),
        18: cr(18, 983)
    }
    
    limits = robot_manager.active_robot.get_joint_layout()
    with robot_manager.dxl_lock:
        motor_ids = list(targets.keys())
        if robot_manager.driver:
            drv_mids = [m for m in motor_ids if m in robot_manager.driver.motor_ids]
            if drv_mids:
                robot_manager.driver.enable_torque(drv_mids, True)
                for mid in drv_mids:
                    robot_manager.driver.torque_state[mid] = True
                
        for mid, val in targets.items():
            if mid in limits:
                info = limits[mid]
                val = max(info["min"], min(info["max"], val))
            robot_manager.manual_positions[mid] = val
            robot_manager.target_positions[mid] = val
            
    logger.log("Commanded robot arms to move to initial balancer pose coordinates.")
    return {"status": "success"}

class BalancerCommandRequest(BaseModel):
    command: str

@app.post("/api/research/ball-balancer/command")
def run_balancer_command(req: BalancerCommandRequest):
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System disconnected: Please connect robot or simulation first.")
        
    cmd = req.command
    targets = {}
    
    calib_l = getattr(robot_manager.active_robot, "calib_left", {})
    calib_r = getattr(robot_manager.active_robot, "calib_right", {})
    def cl(mid, default): return calib_l.get(mid, default)
    def cr(mid, default): return calib_r.get(mid, default)
    
    if cmd == "left_pose":
        targets = {
            21: cl(21, -3561), 12: cl(12, -162), 13: cl(13, 4344),
            24: cl(24, 4026), 25: cl(25, -82), 26: cl(26, -1019),
            27: cl(27, 2065), 28: cl(28, -2676)
        }
    elif cmd == "right_pose":
        targets = {
            11: cr(11, -1674), 22: cr(22, 2138), 23: cr(23, -1275),
            14: cr(14, 2195), 15: cr(15, -3), 16: cr(16, 5117),
            17: cr(17, 2079), 18: cr(18, 983)
        }
    elif cmd == "both_arms":
        targets = {
            21: cl(21, -3561), 12: cl(12, -162), 13: cl(13, 4344),
            24: cl(24, 4026), 25: cl(25, -82), 26: cl(26, -1019),
            27: cl(27, 2065), 28: cl(28, -2676),
            11: cr(11, -1674), 22: cr(22, 2138), 23: cr(23, -1275),
            14: cr(14, 2195), 15: cr(15, -3), 16: cr(16, 5117),
            17: cr(17, 2079), 18: cr(18, 983)
        }
    elif cmd == "tilt_up":
        targets = {
            24: cl(24, 4026), 25: cl(25, -82) - 150, 26: cl(26, -1019), 27: cl(27, 2065),
            14: cr(14, 2195) + 150
        }
    elif cmd == "tilt_center":
        targets = {
            24: cl(24, 4026), 25: cl(25, -82), 26: cl(26, -1019), 27: cl(27, 2065),
            14: cr(14, 2195)
        }
    elif cmd == "tilt_down":
        targets = {
            24: cl(24, 4026), 25: cl(25, -82) + 150, 26: cl(26, -1019), 27: cl(27, 2065),
            14: cr(14, 2195) - 150
        }
    elif cmd == "gripper_open":
        targets = {
            28: cl(28, -2676),
            18: cr(18, 983)
        }
    elif cmd == "gripper_closed":
        targets = {
            28: cl(28, -2676) - 1545,
            18: cr(18, 983) + 1545
        }
    elif cmd == "left_hand_open":
        targets = {
            28: cl(28, -2676)
        }
    elif cmd == "left_hand_closed":
        targets = {
            28: cl(28, -2676) - 1545
        }
    elif cmd == "zero_all":
        targets = {mid: 2048 for mid in limits.keys()}
    elif cmd == "sync_goals":
        presents = {}
        for mid in limits.keys():
            val = robot_manager.latest_telemetry.get(mid, {}).get("present")
            if val is not None and val != "--":
                presents[mid] = int(val)
            else:
                presents[mid] = robot_manager.manual_positions.get(mid, limits[mid].get("default", 2048))
        targets = presents
    else:
        raise HTTPException(status_code=400, detail=f"Invalid balancer command: {cmd}")
        
    limits = robot_manager.active_robot.get_joint_layout()
    with robot_manager.dxl_lock:
        motor_ids = list(targets.keys())
        if robot_manager.driver:
            drv_mids = [m for m in motor_ids if m in robot_manager.driver.motor_ids]
            if drv_mids:
                robot_manager.driver.enable_torque(drv_mids, True)
                for mid in drv_mids:
                    robot_manager.driver.torque_state[mid] = True
                
        for mid, val in targets.items():
            if mid in limits:
                info = limits[mid]
                val = max(info["min"], min(info["max"], val))
            robot_manager.manual_positions[mid] = val
            robot_manager.target_positions[mid] = val
            
    logger.log(f"Commanded robot to execute balancer command: {cmd}")
    return {"status": "success", "command": cmd}

# Arm Calibration Endpoints
class CalibrationSaveRequest(BaseModel):
    calib_left: Dict[str, int]
    calib_right: Dict[str, int]

@app.get("/api/research/balancer/calibration")
def get_calibration():
    if not robot_manager.active_robot:
        return {
            "calib_left": {
                "21": -3561, "12": -162, "13": 4344,
                "24": 4026, "25": -82, "26": -1019, "27": 2065, "28": -2676
            },
            "calib_right": {
                "11": -1674, "22": 2138, "23": -1275,
                "14": 2195, "15": -3, "16": 5117, "17": 2079, "18": 983
            }
        }
    calib_l = getattr(robot_manager.active_robot, "calib_left", {})
    calib_r = getattr(robot_manager.active_robot, "calib_right", {})
    return {
        "calib_left": {str(k): int(v) for k, v in calib_l.items()},
        "calib_right": {str(k): int(v) for k, v in calib_r.items()}
    }

@app.post("/api/research/balancer/calibration/save")
def save_calibration(req: CalibrationSaveRequest):
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
        
    robot_manager.active_robot.calib_left = {int(k): int(v) for k, v in req.calib_left.items()}
    robot_manager.active_robot.calib_right = {int(k): int(v) for k, v in req.calib_right.items()}
    
    success = robot_manager.active_robot.save_chiman_calibration()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save calibration to file.")
        
    if robot_manager.connected:
        with robot_manager.dxl_lock:
            for mid, val in robot_manager.active_robot.calib_left.items():
                robot_manager.manual_positions[mid] = val
                robot_manager.target_positions[mid] = val
            for mid, val in robot_manager.active_robot.calib_right.items():
                robot_manager.manual_positions[mid] = val
                robot_manager.target_positions[mid] = val
                
    return {"status": "success"}

@app.post("/api/research/balancer/calibration/capture")
def capture_calibration(req: Dict[str, str] = Body(...)):
    arm = req.get("arm")
    if arm not in ["left", "right"]:
        raise HTTPException(status_code=400, detail="Invalid arm specified.")
    if not robot_manager.active_robot:
        raise HTTPException(status_code=400, detail="No active robot profile.")
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System disconnected.")
        
    presents = {}
    with robot_manager.dxl_lock:
        for mid in robot_manager.latest_telemetry.keys():
            val = robot_manager.latest_telemetry[mid].get("present")
            if val is not None and val != "--":
                presents[int(mid)] = int(val)
                
    if arm == "left":
        mids = [21, 12, 13, 24, 25, 26, 27, 28]
        calib = robot_manager.active_robot.calib_left
    else:
        mids = [11, 22, 23, 14, 15, 16, 17, 18]
        calib = robot_manager.active_robot.calib_right
        
    captured = {}
    for mid in mids:
        if mid in presents:
            captured[mid] = presents[mid]
            
    if not captured:
        raise HTTPException(status_code=400, detail=f"No active positions telemetry captured for {arm} arm.")
        
    calib.update(captured)
    
    with robot_manager.dxl_lock:
        for mid, val in captured.items():
            robot_manager.manual_positions[mid] = val
            robot_manager.target_positions[mid] = val
            
    robot_manager.active_robot.save_chiman_calibration()
    return {"status": "success", "captured": {str(k): v for k, v in captured.items()}}


# Ball Balancer Research Pose Sequences API
BALANCER_SEQUENCES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "balancer_sequences.json")

class BalancerStep(BaseModel):
    delay: int
    modifications: Dict[str, int]

class BalancerSequence(BaseModel):
    name: str
    steps: List[BalancerStep]

class BalancerSequencesSaveRequest(BaseModel):
    sequences: List[BalancerSequence]

class PlayBalancerSequenceRequest(BaseModel):
    name: str
    loop: int = 1
    speed: float = 1.0

class PreviewStepRequest(BaseModel):
    modifications: Dict[str, int]

@app.get("/api/research/balancer/sequences")
def get_balancer_sequences():
    if not os.path.exists(BALANCER_SEQUENCES_FILE):
        default_seqs = [
            {
                "name": "Plate Holding Pose",
                "steps": [
                    {
                        "delay": 20,
                        "modifications": {
                            "L1P": -2000,
                            "R1P": -2000,
                            "L2R": -1500,
                            "R2R": 1500,
                            "L4F": 2000,
                            "R4F": -2000,
                            "L8G": -4000,
                            "R8G": -4000
                        }
                    }
                ]
            }
        ]
        try:
            with open(BALANCER_SEQUENCES_FILE, "w") as f:
                json.dump(default_seqs, f, indent=4)
        except Exception as e:
            logger.log(f"Error saving default sequences: {e}", "ERROR")
        return default_seqs
        
    try:
        with open(BALANCER_SEQUENCES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.log(f"Error loading sequences: {e}", "ERROR")
        return []

@app.post("/api/research/balancer/sequences/save")
def save_balancer_sequences(req: BalancerSequencesSaveRequest):
    try:
        data = [seq.dict() for seq in req.sequences]
        with open(BALANCER_SEQUENCES_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return {"status": "success"}
    except Exception as e:
        logger.log(f"Error saving sequences: {e}", "ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/research/balancer/sequences/preview")
def preview_balancer_step(req: PreviewStepRequest):
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System offline.")
    limits = robot_manager.active_robot.get_joint_layout() if robot_manager.active_robot else {}
    
    with robot_manager.dxl_lock:
        if robot_manager.driver and robot_manager.driver.is_connected:
            motor_ids = list(limits.keys())
            to_torque = [mid for mid in motor_ids if not robot_manager.driver.torque_state.get(mid, False)]
            if to_torque:
                robot_manager.driver.enable_torque(to_torque, True)
                for mid in to_torque:
                    robot_manager.driver.torque_state[mid] = True
                    
        for name, val in req.modifications.items():
            for mid, info in limits.items():
                if info["name"] == name:
                    robot_manager.manual_positions[mid] = val + info["default"]
    return {"status": "success"}

@app.post("/api/research/balancer/sequences/play")
def play_balancer_sequence(req: PlayBalancerSequenceRequest):
    if not robot_manager.connected:
        raise HTTPException(status_code=400, detail="System offline.")
        
    sequences = []
    if os.path.exists(BALANCER_SEQUENCES_FILE):
        try:
            with open(BALANCER_SEQUENCES_FILE, "r") as f:
                sequences = json.load(f)
        except Exception:
            pass
            
    seq = None
    for s in sequences:
        if s.get("name") == req.name:
            seq = s
            break
            
    if not seq:
        raise HTTPException(status_code=400, detail="Sequence not found.")
        
    steps = seq.get("steps", [])
    if not steps:
        raise HTTPException(status_code=400, detail="Sequence is empty.")
        
    robot_manager.is_balancer_seq_playing = False
    
    def run_play():
        robot_manager.is_balancer_seq_playing = True
        robot_manager.balancer_seq_name = req.name
        robot_manager.balancer_seq_total = len(steps)
        
        limits = robot_manager.active_robot.get_joint_layout() if robot_manager.active_robot else {}
        
        try:
            for l in range(req.loop):
                for idx, step in enumerate(steps):
                    if not robot_manager.is_balancer_seq_playing:
                        break
                    robot_manager.balancer_seq_step = idx + 1
                    
                    mods = step.get("modifications", {})
                    with robot_manager.dxl_lock:
                        if robot_manager.driver and robot_manager.driver.is_connected:
                            motor_ids = list(limits.keys())
                            to_torque = [mid for mid in motor_ids if not robot_manager.driver.torque_state.get(mid, False)]
                            if to_torque:
                                robot_manager.driver.enable_torque(to_torque, True)
                                for mid in to_torque:
                                    robot_manager.driver.torque_state[mid] = True
                                    
                        for name_joint, val in mods.items():
                            for mid, info in limits.items():
                                if info["name"] == name_joint:
                                    robot_manager.manual_positions[mid] = val + info["default"]
                    
                    delay_ticks = step.get("delay", 20)
                    step_duration = (delay_ticks * 0.05) / max(0.1, req.speed)
                    time.sleep(step_duration)
        except Exception as e:
            logger.log(f"Error playing balancer sequence: {e}", "ERROR")
        finally:
            robot_manager.is_balancer_seq_playing = False
            robot_manager.balancer_seq_name = ""
            robot_manager.balancer_seq_step = 0
            robot_manager.balancer_seq_total = 0
            
    threading.Thread(target=run_play, daemon=True).start()
    return {"status": "started"}

@app.post("/api/research/balancer/sequences/stop")
def stop_balancer_sequence():
    robot_manager.is_balancer_seq_playing = False
    return {"status": "stopped"}

# Telemetry Recording Endpoints
class LoadReplayRequest(BaseModel):
    filepath: str

@app.post("/api/recording/toggle")
def toggle_telemetry_recording(action: Dict[str, Any] = Body(...)):
    active = action.get("active", False)
    experiment = action.get("experiment", "telemetry")
    if active:
        telemetry_manager.start_recording(experiment)
        return {"recording": True}
    else:
        res = telemetry_manager.stop_recording()
        return {"recording": False, "frames": res["frames"]}

@app.post("/api/recording/export")
def export_recording(data: Dict[str, str] = Body(...)):
    fmt = data.get("format", "json")
    filename = data.get("filename", f"telemetry_log_{int(time.time())}")
    
    # Save in workspace root
    out_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if fmt == "csv":
        filepath = os.path.join(out_dir, f"{filename}.csv")
        success = telemetry_manager.export_csv(filepath)
    else:
        filepath = os.path.join(out_dir, f"{filename}.json")
        success = telemetry_manager.export_json(filepath)
        
    if not success:
        raise HTTPException(status_code=400, detail="Failed to write log file.")
    return {"status": "success", "filepath": filepath}

@app.post("/api/recording/load-replay")
def load_replay_trajectory(req: LoadReplayRequest):
    # Search in workspace root if not absolute
    filepath = req.filepath
    if not os.path.isabs(filepath):
        out_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        filepath = os.path.join(out_dir, filepath)
        
    success = telemetry_manager.load_replay(filepath)
    if not success:
        raise HTTPException(status_code=400, detail=f"Could not load trajectory log at {filepath}")
        
    # Trigger replay loop
    telemetry_manager.start_replay()
    return {"status": "success"}

# Core Digital Twin Sync configs
@app.post("/api/simulation/sync-mode")
def set_digital_twin_sync_mode(data: Dict[str, str] = Body(...)):
    mode = data.get("mode", "hardware")
    dt = plugin_manager.simulation_modules.get("digital_twin")
    if dt:
        dt.set_sync_mode(mode)
        return {"status": "success", "sync_mode": dt.sync_mode}
    raise HTTPException(status_code=400, detail="Digital twin adaptation layer offline.")

# Async Telemetry Stream Broadcast Loop
async def telemetry_broadcast_loop():
    last_frame_sent_time = 0.0
    latest_sent_base64_frame = None
    latest_realsense_data = None
    
    # Retrieve vision references
    vision = plugin_manager.perception_modules.get("vision")
    balancer = plugin_manager.research_modules.get("ball_balancer")
    dt_layer = plugin_manager.simulation_modules.get("digital_twin")
    
    # Listen to twin sync updates
    cached_twin_joints = {}
    def on_twin_update(joints):
        nonlocal cached_twin_joints
        cached_twin_joints = joints
    event_bus.subscribe("digital_twin_updated", on_twin_update)

    # Listen to balancer updates
    cached_balancer_frame = {}
    def on_balancer_update(frame):
        nonlocal cached_balancer_frame
        cached_balancer_frame = frame
    event_bus.subscribe("balancer_frame", on_balancer_update)

    while True:
        if not websocket_manager.active_connections:
            await asyncio.sleep(0.1)
            continue
            
        if robot_manager.camera_active and vision:
            # Auto-switch modes dynamically
            required_mode = "hand_tracker" if robot_manager.tracking_enabled else "realsense"
            if getattr(vision, "mode", None) != required_mode:
                logger.log(f"Switching vision mode to '{required_mode}'")
                vision.set_mode(required_mode)

            curr_t = time.time()
            if curr_t - last_frame_sent_time >= 0.05: # 20 FPS limit
                frame, tracker_data, world_lms, tracker_fps = vision.get_latest_data()
                robot_manager.fps = int(tracker_fps)
                
                if frame is not None:
                    last_frame_sent_time = curr_t
                    latest_sent_base64_frame = vision.get_latest_base64_frame()
                        
                # 1. Hand tracking autopilot
                if tracker_data is not None and required_mode == "hand_tracker":
                    if robot_manager.tracking_enabled and robot_manager.active_robot:
                        robot_manager.target_positions = robot_manager.active_robot.process_pose(tracker_data)
                        
                        # Fallback feed to balancer if hand is active
                        if balancer and balancer.active_provider == balancer.vision_provider:
                            if len(tracker_data) > 0:
                                palm_pt = tracker_data[0]["landmarks"][0]
                                sim_x = (palm_pt.x - 0.5) * 0.4
                                sim_y = (palm_pt.y - 0.5) * 0.4
                                balancer.vision_provider.set_measured_position(sim_x, sim_y)
                                
                # 2. RealSense ball tracker
                elif tracker_data is not None and required_mode == "realsense":
                    latest_realsense_data = tracker_data
                    if balancer and balancer.active_provider == balancer.vision_provider:
                        # Feed the exact 3D physical ball position
                        ball_y_3d = tracker_data.get("ball_y_3d", None)
                        if ball_y_3d is not None:
                            balancer.vision_provider.set_measured_position(0.0, ball_y_3d)
                        else:
                            # Fallback if 3D coordinates are missing
                            ball_error = tracker_data.get("ball_error", 0.0)
                            ball_y = ball_error * 0.22
                            balancer.vision_provider.set_measured_position(0.0, ball_y)
        else:
            latest_realsense_data = None

        # Step active research tasks dynamically using generic interface
        for task_name, task in plugin_manager.research_modules.items():
            if task.is_active:
                task_res = task.step(dt=0.033)
                if task_res and robot_manager.connected and robot_manager.active_robot:
                    offsets = task_res.get("offsets", {})
                    with robot_manager.dxl_lock:
                        for offset_name, val in offsets.items():
                            robot_manager.active_robot.apply_control_offset(offset_name, val, robot_manager.manual_positions)


        logs_slice = logger.get_logs(30)

        # Build telemetry state payload
        payload = {
            "telemetry": robot_manager.latest_telemetry,
            "connected": robot_manager.connected,
            "estop_active": robot_manager.estop_active,
            "tracking_enabled": robot_manager.tracking_enabled,
            "camera_active": robot_manager.camera_active,
            "mirror_sync_active": robot_manager.mirror_sync_active,
            "system": {
                "health": robot_manager.system_health if not robot_manager.estop_active else 40,
                "cpu": robot_manager.cpu_usage,
                "ram": robot_manager.ram_usage,
                "latency": robot_manager.latency,
                "fps": robot_manager.fps
            },
            "calibration": {
                "running": robot_manager.calib_running,
                "progress": robot_manager.calib_progress,
                "status_msg": robot_manager.calib_status_msg,
                "paused": robot_manager.calib_paused,
                "fault_reason": robot_manager.calib_fault_reason
            },
            "logs": logs_slice,
            
            # New Telemetry data variables
            "digital_twin": {
                "sync_mode": dt_layer.sync_mode if dt_layer else "hardware",
                "joints": cached_twin_joints,
                "model_geometry": robot_manager.active_robot.get_digital_twin_model() if robot_manager.active_robot else {}
            },
            "balancer": {
                "is_active": balancer.is_active if balancer else False,
                "data": cached_balancer_frame,
                "kp": balancer.kp if balancer else 0.8,
                "kd": balancer.kd if balancer else 0.3,
                "ki": balancer.ki if balancer else 0.05,
                "provider": "vision" if balancer and balancer.active_provider == balancer.vision_provider else "force" if balancer and balancer.active_provider == balancer.force_provider else "fusion",
                "vision_details": latest_realsense_data,
                "ball_error": float(latest_realsense_data.get("ball_error", 0.0) if latest_realsense_data else 0.0),
                "speed_multiplier": balancer.speed_multiplier if balancer else 1.0,
                "max_tilt_positive": balancer.max_tilt_positive if balancer else 150.0,
                "max_tilt_negative": balancer.max_tilt_negative if balancer else 178.0,
                "auto_tune_enabled": balancer.auto_tune_enabled if balancer else False,
                "loadcell": balancer.force_sensor.get_telemetry() if (balancer and balancer.force_sensor) else {},
                "loadcell_mode": balancer.loadcell_mode if balancer else 2,
                "loadcell_arm": balancer.loadcell_arm if balancer else "left",
                "ball_weight_ref": balancer.ball_weight_ref if balancer else 100.0,
                "invert_output": balancer.invert_output if balancer else False,
                "ball_type": balancer.ball_type if balancer else "green_ping_pong",
                "avg_mapping_error": balancer.avg_mapping_error if balancer else 0.1,
                "exploration_mode": balancer.exploration_mode if balancer else False,
                "exploration_progress": float(balancer.balanced_time / 1.5) if (balancer and balancer.exploration_mode) else 0.0,
                "sequence_status": {
                    "is_playing": robot_manager.is_balancer_seq_playing,
                    "current_sequence": robot_manager.balancer_seq_name,
                    "current_step": robot_manager.balancer_seq_step,
                    "total_steps": robot_manager.balancer_seq_total
                }
            },
            "recorder": {
                "is_recording": telemetry_manager.is_recording,
                "recorded_frames": len(telemetry_manager.recorded_frames),
                "is_replaying": telemetry_manager.is_replaying
            }
        }
        
        if robot_manager.camera_active:
            payload["video_frame"] = latest_sent_base64_frame
        else:
            payload["video_frame"] = None
            
        await websocket_manager.broadcast(payload)
        await asyncio.sleep(0.033) # 30Hz

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telemetry_broadcast_loop())
    
    # Auto-open browser in 1.5 seconds
    def launch_browser():
        import webbrowser
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")
        
    threading.Thread(target=launch_browser, daemon=True).start()

@app.on_event("shutdown")
def shutdown_event():
    robot_manager.disconnect()
    vision = plugin_manager.perception_modules.get("vision")
    if vision:
        vision.stop()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    await websocket_manager.handle_incoming(websocket)

# Serve client files from frontend build
dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {
            "message": "OSRS Server online. Frontend not built. Run 'npm run build' inside /frontend directory to build client."
        }
