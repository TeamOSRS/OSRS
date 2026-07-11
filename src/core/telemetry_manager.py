import time
import json
import csv
import os
import threading
from typing import Dict, List, Any, Optional

from src.core.logging import logger

class TelemetryManager:
    """
    Manages telemetry logging, real-time trajectory recording, 
    and handles file exports (CSV/JSON) and replaying data frames.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._lock = threading.Lock()
        
        # Recording state
        self.is_recording = False
        self.recorded_frames: List[Dict[str, Any]] = []
        self.recording_start_time = 0.0
        self.experiment_name = "default"

        # Replay state
        self.is_replaying = False
        self.replay_frames: List[Dict[str, Any]] = []
        self.replay_index = 0
        self.replay_thread: Optional[threading.Thread] = None

        # Subscribe to telemetry updates from RobotManager
        self.event_bus.subscribe("telemetry_updated", self._on_telemetry_updated)
        self.event_bus.subscribe("mujoco_step", self._on_mujoco_step)

    def start_recording(self, experiment_name: str = "telemetry"):
        with self._lock:
            self.is_recording = True
            self.recorded_frames.clear()
            self.recording_start_time = time.time()
            self.experiment_name = experiment_name
        logger.log(f"Started telemetry recording for experiment: {experiment_name}")

    def stop_recording(self) -> Dict[str, Any]:
        with self._lock:
            self.is_recording = False
            count = len(self.recorded_frames)
        logger.log(f"Stopped telemetry recording. Captured {count} frames.")
        return {"experiment": self.experiment_name, "frames": count}

    def _on_telemetry_updated(self, telemetry_data: Dict[int, Dict[str, Any]]):
        if not self.is_recording:
            return
            
        frame = {
            "timestamp": time.time() - self.recording_start_time,
            "joints": {str(mid): val["present"] for mid, val in telemetry_data.items() if isinstance(val.get("present"), (int, float))},
            "currents": {str(mid): val["current"] for mid, val in telemetry_data.items() if isinstance(val.get("current"), (int, float))}
        }
        with self._lock:
            self.recorded_frames.append(frame)

    def _on_mujoco_step(self, sim_joint_states: Dict[str, float]):
        if not self.is_recording:
            return
            
        frame = {
            "timestamp": time.time() - self.recording_start_time,
            "joints": {name: float(val) for name, val in sim_joint_states.items() if isinstance(val, (int, float))},
            "currents": {}
        }
        with self._lock:
            self.recorded_frames.append(frame)

    def record_experiment_frame(self, state_dict: Dict[str, Any]):
        """Allows research tasks to store specialized variables during tracking."""
        if not self.is_recording:
            return
        frame = {
            "timestamp": time.time() - self.recording_start_time,
            **state_dict
        }
        with self._lock:
            self.recorded_frames.append(frame)

    def export_json(self, filepath: str) -> bool:
        try:
            with open(filepath, "w") as f:
                json.dump(self.recorded_frames, f, indent=4)
            logger.log(f"Exported telemetry to JSON: {filepath}")
            return True
        except Exception as e:
            logger.log(f"Failed to export JSON: {e}", "ERROR")
            return False

    def export_csv(self, filepath: str) -> bool:
        if not self.recorded_frames:
            return False
        try:
            # Flatten structures: timestamp, joint_X_present, joint_X_current, etc.
            keys = ["timestamp"]
            first_frame = self.recorded_frames[0]
            
            # Find dynamic keys
            joint_ids = list(first_frame.get("joints", {}).keys())
            for jid in joint_ids:
                keys.append(f"joint_{jid}_pos")
                keys.append(f"joint_{jid}_cur")
                
            for k in first_frame.keys():
                if k not in ["timestamp", "joints", "currents"]:
                    keys.append(k)

            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for frame in self.recorded_frames:
                    row = {"timestamp": frame["timestamp"]}
                    for jid in joint_ids:
                        row[f"joint_{jid}_pos"] = frame.get("joints", {}).get(jid, "")
                        row[f"joint_{jid}_cur"] = frame.get("currents", {}).get(jid, "")
                    for k, v in frame.items():
                        if k not in ["timestamp", "joints", "currents"]:
                            row[k] = v
                    writer.writerow(row)
            logger.log(f"Exported telemetry to CSV: {filepath}")
            return True
        except Exception as e:
            logger.log(f"Failed to export CSV: {e}", "ERROR")
            return False

    def load_replay(self, filepath: str) -> bool:
        # Try appending extensions if not present
        target_path = filepath
        if not os.path.exists(target_path):
            if not target_path.endswith((".json", ".csv")):
                if os.path.exists(target_path + ".json"):
                    target_path = target_path + ".json"
                elif os.path.exists(target_path + ".csv"):
                    target_path = target_path + ".csv"
                else:
                    return False
            else:
                return False

        try:
            if target_path.endswith(".json"):
                with open(target_path, "r") as f:
                    self.replay_frames = json.load(f)
            elif target_path.endswith(".csv"):
                frames = []
                with open(target_path, "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        timestamp = float(row.get("timestamp", 0.0))
                        joints = {}
                        currents = {}
                        other_data = {}
                        
                        for k, v in row.items():
                            if k == "timestamp":
                                continue
                            if k.startswith("joint_") and k.endswith("_pos"):
                                jid = k.split("_")[1]
                                if v != "":
                                    joints[jid] = float(v) if "." in v else int(v)
                            elif k.startswith("joint_") and k.endswith("_cur"):
                                jid = k.split("_")[1]
                                if v != "":
                                    currents[jid] = float(v) if "." in v else int(v)
                            else:
                                if v != "":
                                    try:
                                        other_data[k] = float(v) if "." in v else int(v)
                                    except ValueError:
                                        other_data[k] = v
                                        
                        frames.append({
                            "timestamp": timestamp,
                            "joints": joints,
                            "currents": currents,
                            **other_data
                        })
                self.replay_frames = frames
            else:
                return False
                
            logger.log(f"Loaded {len(self.replay_frames)} frames for replay from {target_path}")
            return True
        except Exception as e:
            logger.log(f"Failed to load replay file {target_path}: {e}", "ERROR")
            return False


    def start_replay(self, playback_speed: float = 1.0):
        if not self.replay_frames:
            return
        self.is_replaying = True
        self.replay_index = 0
        self.replay_thread = threading.Thread(target=self._replay_loop, args=(playback_speed,), daemon=True)
        self.replay_thread.start()
        logger.log("Started telemetry playback.")

    def stop_replay(self):
        self.is_replaying = False
        if self.replay_thread:
            self.replay_thread.join(timeout=0.5)
            self.replay_thread = None
        logger.log("Stopped telemetry playback.")

    def _replay_loop(self, playback_speed: float):
        last_t = 0.0
        while self.is_replaying and self.replay_index < len(self.replay_frames):
            frame = self.replay_frames[self.replay_index]
            curr_t = frame["timestamp"]
            
            if self.replay_index > 0:
                sleep_duration = (curr_t - last_t) / playback_speed
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

            # Publish joints positions to simulate live values on the Digital Twin
            self.event_bus.publish("replay_frame", frame)
            
            last_t = curr_t
            self.replay_index += 1
        
        self.is_replaying = False
        logger.log("Replay trajectory finished.")
