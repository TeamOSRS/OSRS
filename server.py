# Compatibility layer: exposes Fastapi 'app' from src.core.server
from src.core.server import app, robot_manager, telemetry_manager, plugin_manager

# Expose a global state mock for backward compatibility if needed
state = robot_manager
