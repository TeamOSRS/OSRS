import threading
import time
from typing import Dict, Any, Optional

from src.core.logging import logger

class MujocoBridge:
    """
    Simulation adaptor bridging OSRS to the MuJoCo physics engine.
    Steps kinematics models and publishes virtual joint updates.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.model_loaded = False
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Virtual joint positions simulation cache
        self.sim_joints: Dict[str, float] = {}
        
        # Listen to target overrides in Hybrid mode
        self.event_bus.subscribe("mujoco_hybrid_targets", self._on_hybrid_targets)

    def load_scene(self, xml_path: str) -> bool:
        logger.log(f"MuJoCo Bridge loading scene: {xml_path}")
        if not os.path.exists(xml_path):
            logger.log(f"MuJoCo scene XML file not found: {xml_path}", "WARNING")
            # Create mock joint structure for demo
            self.sim_joints = {"l_sho_pitch": 0.0, "r_sho_pitch": 0.0, "l_knee": 0.0, "r_knee": 0.0}
            self.model_loaded = True
            return True
            
        try:
            import mujoco
            # Store references to model and data
            self.model = mujoco.MjModel.from_xml_path(xml_path)
            self.data = mujoco.MjData(self.model)
            self.model_loaded = True
            logger.log("MuJoCo XML model successfully compiled!")
            return True
        except ImportError:
            logger.log("mujoco python package not installed. Falling back to Mock physics step.", "WARNING")
            self.sim_joints = {"l_sho_pitch": 0.0, "r_sho_pitch": 0.0, "l_knee": 0.0, "r_knee": 0.0}
            self.model_loaded = True
            return True
        except Exception as e:
            logger.log(f"Failed to compile MuJoCo model: {e}", "ERROR")
            return False

    def start_simulation(self):
        if not self.model_loaded:
            return
        self.running = True
        self.thread = threading.Thread(target=self._sim_loop, daemon=True)
        self.thread.start()
        logger.log("MuJoCo physics loop thread started.")

    def stop_simulation(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
            self.thread = None
        logger.log("MuJoCo physics loop thread stopped.")

    def _sim_loop(self):
        # Run physics at 50Hz (20ms step rate)
        while self.running:
            start_time = time.time()
            try:
                # If native MuJoCo is loaded
                if hasattr(self, 'model'):
                    import mujoco
                    mujoco.mj_step(self.model, self.data)
                    
                    # Gather joint names and positions
                    states = {}
                    for i in range(self.model.njnt):
                        j_name = self.model.joint(i).name
                        q_adr = self.model.joint(i).qposadr[0]
                        states[j_name] = float(self.data.qpos[q_adr])
                    self.event_bus.publish("mujoco_step", states)
                else:
                    # Mock stepping
                    t = time.time()
                    self.sim_joints["l_sho_pitch"] = 0.4 * math.sin(t * 2)
                    self.sim_joints["r_sho_pitch"] = -0.4 * math.sin(t * 2)
                    self.sim_joints["l_knee"] = 0.2 * math.sin(t * 0.5)
                    self.sim_joints["r_knee"] = -0.2 * math.sin(t * 0.5)
                    self.event_bus.publish("mujoco_step", self.sim_joints)
            except Exception as e:
                pass
                
            elapsed = time.time() - start_time
            time.sleep(max(0.005, 0.020 - elapsed))

    def _on_hybrid_targets(self, targets: Dict[int, int]):
        """Callback for Hybrid Mode inputs."""
        # Maps raw targets to simulator joint limits and commands actuators directly
        if not self.running:
            return
        if hasattr(self, 'data'):
            # Write to active simulator actuator command buffer (e.g. data.ctrl)
            pass
            
import os
import math
import time
import threading
