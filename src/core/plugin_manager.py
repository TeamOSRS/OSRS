import os
import importlib
from typing import Dict, List, Any, Optional

from src.core.logging import logger
from src.modules.robots.base_robot import BaseRobot

class PluginManager:
    """
    Manages registration, lifecycle, and query interfaces for:
    - Robots (Humanoid, LEAP, etc.)
    - Perception (Vision, Force, IMU)
    - Research modules (Ball Balancer)
    - Simulation adaptors (MuJoCo, digital twin sync, replay)
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.robots: Dict[str, BaseRobot] = {}
        self.perception_modules: Dict[str, Any] = {}
        self.research_modules: Dict[str, Any] = {}
        self.simulation_modules: Dict[str, Any] = {}

    def register_robot(self, robot_profile: BaseRobot):
        """Self-registration API for Robot classes."""
        self.robots[robot_profile.version] = robot_profile
        logger.log(f"Registered robot plugin: {robot_profile.name} (profile ID: {robot_profile.version})")

    def register_perception(self, name: str, module: Any):
        self.perception_modules[name] = module
        logger.log(f"Registered perception module: {name}")

    def register_research(self, name: str, module: Any):
        self.research_modules[name] = module
        logger.log(f"Registered research module: {name}")

    def register_simulation(self, name: str, module: Any):
        self.simulation_modules[name] = module
        logger.log(f"Registered simulation module: {name}")

    def load_builtins(self):
        """
        Dynamically discovers and loads OSRS modules, perception nodes, 
        research tasks, and simulation adapters without hardcoded imports.
        """
        import os
        import importlib
        import inspect
        import re
        from src.modules.research.base_research_task import BaseResearchTask
        from src.modules.robots.base_robot import BaseRobot

        logger.log("OSRS dynamic plugin auto-discovery initiated...")

        # 1. Scan and register Robots dynamically
        robots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "robots")
        if os.path.exists(robots_dir):
            for file in os.listdir(robots_dir):
                if file.endswith(".py") and not file.startswith("__") and file != "base_robot.py":
                    module_name = f"src.modules.robots.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for class_name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseRobot) and obj != BaseRobot:
                                # Special case for multi-profile LeapHandRobot
                                if class_name == "LeapHandRobot":
                                    self.register_robot(obj(version="V1"))
                                    self.register_robot(obj(version="V2"))
                                else:
                                    self.register_robot(obj())
                    except Exception as e:
                        logger.log(f"Failed to dynamically load robot module {module_name}: {e}", "ERROR")

        # 2. Scan and register Perception modules dynamically
        perception_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "perception")
        if os.path.exists(perception_dir):
            for file in os.listdir(perception_dir):
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = f"src.modules.perception.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for class_name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and not class_name.startswith("_"):
                                # Register if class name matches expected plugins
                                if class_name in ["VisionPerception", "ForceSensing", "ImuFusion"]:
                                    reg_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
                                    if class_name == "VisionPerception":
                                        reg_name = "vision"
                                    self.register_perception(reg_name, obj())
                    except Exception as e:
                        logger.log(f"Failed to dynamically load perception module {module_name}: {e}", "ERROR")

        # 3. Scan and register Research modules dynamically
        research_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "research")
        if os.path.exists(research_dir):
            for file in os.listdir(research_dir):
                if file.endswith(".py") and not file.startswith("__") and file != "base_research_task.py":
                    module_name = f"src.modules.research.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for class_name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseResearchTask) and obj != BaseResearchTask:
                                # Instantiate passing event_bus
                                self.register_research(
                                    re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower(),
                                    obj(self.event_bus)
                                )
                    except Exception as e:
                        logger.log(f"Failed to dynamically load research module {module_name}: {e}", "ERROR")

        # 4. Scan and register Simulation adapters dynamically
        simulation_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "simulation")
        if os.path.exists(simulation_dir):
            for file in os.listdir(simulation_dir):
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = f"src.modules.simulation.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for class_name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and not class_name.startswith("_"):
                                if class_name in ["DigitalTwin", "MujocoBridge", "ReplayEngine"]:
                                    reg_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
                                    if class_name == "ReplayEngine":
                                        reg_name = "replay"
                                    self.register_simulation(reg_name, obj(self.event_bus))
                    except Exception as e:
                        logger.log(f"Failed to dynamically load simulation module {module_name}: {e}", "ERROR")

        logger.log("OSRS dynamic plugin auto-discovery sequence complete.")

