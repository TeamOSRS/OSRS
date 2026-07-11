from typing import Dict, Any

from src.core.logging import logger

class DigitalTwin:
    """
    Manages synchronization between physical servos, MuJoCo simulation state, 
    and the 3D Digital Twin visualization. Supports:
    1. Hardware Mode (Real Robot -> Digital Twin)
    2. Simulation Mode (MuJoCo -> Digital Twin)
    3. Hybrid Mode (Real Robot -> MuJoCo -> Digital Twin)
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.sync_mode = "hardware"  # "hardware", "simulation", "hybrid"
        self.joint_states: Dict[str, float] = {}

        # Subscribe to relevant events
        self.event_bus.subscribe("telemetry_updated", self._on_hardware_telemetry)
        self.event_bus.subscribe("mujoco_step", self._on_simulation_step)
        self.event_bus.subscribe("replay_frame", self._on_replay_frame)

    def set_sync_mode(self, mode: str):
        if mode in ["hardware", "simulation", "hybrid"]:
            self.sync_mode = mode
            logger.log(f"Digital Twin synchronization mode switched to: {mode}")

    def _on_hardware_telemetry(self, telemetry_data: Dict[int, Dict[str, Any]]):
        if self.sync_mode == "hardware":
            # Extract joint positions and convert to radian/tick representations
            for jid, info in telemetry_data.items():
                if "present" in info and isinstance(info["present"], (int, float)):
                    self.joint_states[str(jid)] = float(info["present"])
            self._broadcast_twin_state()
            
        elif self.sync_mode == "hybrid":
            # Direct physical joints targets to simulation solver before rendering
            target_positions = {}
            for jid, info in telemetry_data.items():
                if "present" in info and isinstance(info["present"], (int, float)):
                    target_positions[jid] = info["present"]
            # Publish event to notify MuJoCo solver to apply these targets
            self.event_bus.publish("mujoco_hybrid_targets", target_positions)

    def _on_simulation_step(self, sim_joint_states: Dict[str, float]):
        if self.sync_mode in ["simulation", "hybrid"]:
            # Pull solved states from MuJoCo physics steps
            for name, val in sim_joint_states.items():
                self.joint_states[name] = float(val)
            self._broadcast_twin_state()

    def _on_replay_frame(self, frame_data: Dict[str, Any]):
        # Replay overrides visual twin states directly
        joints = frame_data.get("joints", {})
        for jid, val in joints.items():
            if isinstance(val, (int, float)):
                self.joint_states[str(jid)] = float(val)
        self._broadcast_twin_state()

    def _broadcast_twin_state(self):
        # Notify the websocket broadcast loop that a new visual state is ready
        self.event_bus.publish("digital_twin_updated", self.joint_states)

    def get_state(self) -> Dict[str, Any]:
        return {
            "sync_mode": self.sync_mode,
            "joints": self.joint_states
        }
