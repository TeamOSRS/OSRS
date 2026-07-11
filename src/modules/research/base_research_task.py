from typing import Dict, Any, Optional

class BaseResearchTask:
    """
    Abstract base class for all research modules in OSRS.
    Defines the standard lifecycle interface: start(), stop(), step(dt).
    """
    def __init__(self, name: str):
        self.name = name
        self.is_active = False

    def start(self):
        self.is_active = True

    def stop(self):
        self.is_active = False

    def step(self, dt: float) -> Optional[Dict[str, Any]]:
        """
        Executes a single control/estimation step.
        Returns optional dict of telemetry or results to be broadcast, 
        such as target actuator offsets.
        """
        raise NotImplementedError("Research tasks must implement step(dt)")
