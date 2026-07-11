from typing import Any, Dict

from src.core.logging import logger

class ReplayEngine:
    """
    Simulation adaptor managing replay data loading, stepping, 
    and timeline position requests.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus

    def trigger_replay_step(self, frame_data: Dict[str, Any]):
        """Publish a loaded data frame to sync the digital twin visuals."""
        self.event_bus.publish("replay_frame", frame_data)
