import time
import json
import collections

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

class MovingAverageFilter:
    """
    A simple moving average filter for smoothing target 3D coordinates.
    """
    def __init__(self, window_size=10):
        self.window_size = max(1, window_size)
        self.history = collections.deque(maxlen=self.window_size)

    def set_window_size(self, size):
        self.window_size = max(1, size)
        # Recreate deque while maintaining existing history up to the new size limit
        old_history = list(self.history)
        self.history = collections.deque(old_history, maxlen=self.window_size)

    def filter(self, x, y, z):
        self.history.append((x, y, z))
        xs = [pt[0] for pt in self.history]
        ys = [pt[1] for pt in self.history]
        zs = [pt[2] for pt in self.history]
        return sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)

    def reset(self):
        self.history.clear()


class KalmanFilter1D:
    """
    A simple 1D Kalman filter to estimate coordinate states.
    """
    def __init__(self, process_noise=1e-4, measurement_noise=1e-2):
        self.Q = process_noise      # Process noise covariance
        self.R = measurement_noise  # Measurement noise covariance
        self.x = None               # Estimated value
        self.P = 1.0                # Estimation error covariance

    def set_parameters(self, process_noise, measurement_noise):
        self.Q = process_noise
        self.R = measurement_noise

    def filter(self, measurement):
        if self.x is None:
            self.x = measurement
            self.P = 1.0
            return self.x

        # Prediction phase
        # x_pred = x (state model is constant position)
        # P_pred = P + Q
        P_pred = self.P + self.Q

        # Correction/Update phase
        # K = P_pred / (P_pred + R)
        # x = x_pred + K * (measurement - x_pred)
        # P = (1 - K) * P_pred
        K = P_pred / (P_pred + self.R)
        self.x = self.x + K * (measurement - self.x)
        self.P = (1.0 - K) * P_pred

        return self.x

    def reset(self):
        self.x = None
        self.P = 1.0


class CoordinateFilter3D:
    """
    A wrapper class running three independent filters for X, Y, Z.
    """
    def __init__(self, filter_type="moving_average", window_size=8, process_noise=1e-4, measurement_noise=1e-2):
        self.filter_type = filter_type
        self.window_size = window_size
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

        self.ma_filter = MovingAverageFilter(window_size)
        self.kf_x = KalmanFilter1D(process_noise, measurement_noise)
        self.kf_y = KalmanFilter1D(process_noise, measurement_noise)
        self.kf_z = KalmanFilter1D(process_noise, measurement_noise)

    def set_filter_type(self, filter_type):
        self.filter_type = filter_type

    def set_ma_window(self, size):
        self.window_size = size
        self.ma_filter.set_window_size(size)

    def set_kf_parameters(self, process_noise, measurement_noise):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.kf_x.set_parameters(process_noise, measurement_noise)
        self.kf_y.set_parameters(process_noise, measurement_noise)
        self.kf_z.set_parameters(process_noise, measurement_noise)

    def filter(self, x, y, z):
        if self.filter_type == "none":
            return x, y, z
        elif self.filter_type == "moving_average":
            return self.ma_filter.filter(x, y, z)
        elif self.filter_type == "kalman":
            fx = self.kf_x.filter(x)
            fy = self.kf_y.filter(y)
            fz = self.kf_z.filter(z)
            return fx, fy, fz
        return x, y, z

    def reset(self):
        self.ma_filter.reset()
        self.kf_x.reset()
        self.kf_y.reset()
        self.kf_z.reset()


class RobotCommunicator:
    """
    Handles serial connection and G-Code/JSON target coordinate transmission to a bot.
    Includes simulation fallback when no physical hardware is present.
    """
    def __init__(self, port="Mock/Simulated", baudrate=115200, protocol="G-Code"):
        self.port = port
        self.baudrate = baudrate
        self.protocol = protocol
        self.ser = None
        self.last_sent_time = 0.0
        self.min_send_interval = 0.05  # Max 20 Hz transmission rate to avoid choking UART buffers

    @classmethod
    def get_available_ports(cls):
        """Scans the system for active COM/serial ports."""
        ports = ["Mock/Simulated"]
        if SERIAL_AVAILABLE:
            try:
                available_ports = serial.tools.list_ports.comports()
                for p in available_ports:
                    ports.append(p.device)
            except Exception:
                pass
        return ports

    def connect(self):
        """Establishes connection. Returns (success, status_message)."""
        if self.port == "Mock/Simulated":
            return True, "Mock Connection Active (Simulation mode)"

        if not SERIAL_AVAILABLE:
            return False, "pyserial library is unavailable."

        try:
            # Open serial port
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=1.0
            )
            return True, f"Connected to {self.port} at {self.baudrate} bps."
        except Exception as e:
            self.ser = None
            return False, f"Failed to connect to {self.port}: {e}"

    def disconnect(self):
        """Closes connection."""
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
        return True, "Disconnected successfully."

    def is_connected(self):
        if self.port == "Mock/Simulated":
            return True
        return self.ser is not None and self.ser.is_open

    def send_coordinates(self, x, y, z):
        """
        Formats coordinates and sends them over serial or mock console.
        Returns: (success, command_string_sent)
        """
        if not self.is_connected():
            return False, "Not Connected"

        # Limit transmission rate
        current_time = time.time()
        if current_time - self.last_sent_time < self.min_send_interval:
            return False, "Rate-limited"

        self.last_sent_time = current_time

        # Format based on protocol
        if self.protocol == "G-Code":
            # G0 linear fast motion in Cartesian space (coordinates in meters)
            cmd = f"G0 X{x:.4f} Y{y:.4f} Z{z:.4f}\n"
        elif self.protocol == "JSON":
            # Send standard JSON structure
            cmd = json.dumps({"x": round(x, 4), "y": round(y, 4), "z": round(z, 4)}) + "\n"
        else:
            cmd = f"{x:.4f},{y:.4f},{z:.4f}\n"

        if self.port == "Mock/Simulated":
            # In simulation mode, write to stdout/console (it gets captured in the process log)
            print(f"[Simulated Robot TX]: {cmd.strip()}")
            return True, cmd.strip()

        # Physical serial write
        if self.ser:
            try:
                self.ser.write(cmd.encode("utf-8"))
                self.ser.flush()
                return True, cmd.strip()
            except Exception as e:
                # Handle communication drop
                self.disconnect()
                print(f"[COM ERR] Serial write failed, disconnected: {e}")
                return False, f"Error: {e}"

        return False, "Write Error"
