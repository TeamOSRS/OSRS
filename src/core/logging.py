import logging
import time
import sys
import threading
from typing import List

class OSRSLogger:
    """
    OSRS Logging system. Maintains a sliding in-memory buffer of the latest 100 logs 
    to feed live telemetry streams, in addition to writing to stdout/files.
    """
    def __init__(self, name="OSRS"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent adding handlers multiple times
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self._logs: List[str] = []
        self._lock = threading.Lock()

    def log(self, message: str, level: str = "INFO"):
        t_str = time.strftime("%H:%M:%S")
        log_entry = f"[{t_str}] {level}: {message}"
        
        with self._lock:
            self._logs.append(log_entry)
            if len(self._logs) > 100:
                self._logs.pop(0)

        # Forward to native Python logging
        lvl = level.upper()
        if lvl == "ERROR":
            self.logger.error(message)
        elif lvl == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def get_logs(self, limit: int = 30) -> List[str]:
        """Returns the latest 'limit' logs."""
        with self._lock:
            return self._logs[-limit:]

# Global logger instance
logger = OSRSLogger()
