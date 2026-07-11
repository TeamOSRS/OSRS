import threading
from typing import Callable, Dict, List, Any

class EventBus:
    """
    Lightweight, thread-safe publish-subscribe event bus for modular communication.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Subscribe to an event type with a callback function."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Unsubscribe a callback function from an event type."""
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, data: Any = None):
        """Publish an event to all subscribed callbacks."""
        callbacks = []
        with self._lock:
            if event_type in self._subscribers:
                callbacks = list(self._subscribers[event_type])
        
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                # Basic fallback print, logging module will handle this globally
                print(f"[EventBus] Error in handler for '{event_type}': {e}")
