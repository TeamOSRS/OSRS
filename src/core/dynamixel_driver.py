import time
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DynamixelDriver:
    """
    A robust Python interface for controlling Dynamixel servos using the Dynamixel SDK.
    Supports Protocol 2.0, Sync Write, and Sync Read.
    Includes a 'Mock Mode' for simulation testing when no hardware is connected.
    """
    
    # Dynamixel X-Series Control Table Addresses
    ADDR_OPERATING_MODE = 11      # 1 byte
    ADDR_CURRENT_LIMIT = 38       # 2 bytes
    ADDR_TORQUE_ENABLE = 64       # 1 byte
    ADDR_HARDWARE_ERROR_STATUS = 85 # 1 byte
    ADDR_K_P = 84                 # 2 bytes
    ADDR_K_I = 82                 # 2 bytes
    ADDR_K_D = 80                 # 2 bytes
    ADDR_PROFILE_VELOCITY = 112   # 4 bytes
    ADDR_GOAL_CURRENT = 102       # 2 bytes
    ADDR_GOAL_POSITION = 116      # 4 bytes
    ADDR_PRESENT_POSITION = 132   # 4 bytes
    ADDR_PRESENT_VELOCITY = 128   # 4 bytes
    ADDR_PRESENT_CURRENT = 126    # 2 bytes
    ADDR_PRESENT_TEMPERATURE = 146 # 1 byte
    
    # Data Byte Lengths
    LEN_OPERATING_MODE = 1
    LEN_CURRENT_LIMIT = 2
    LEN_TORQUE_ENABLE = 1
    LEN_HARDWARE_ERROR_STATUS = 1
    LEN_GOAL_CURRENT = 2
    LEN_GOAL_POSITION = 4
    LEN_PRESENT_POSITION = 4
    LEN_PRESENT_VELOCITY = 4
    LEN_PRESENT_CURRENT = 2
    LEN_PROFILE_VELOCITY = 4
    LEN_PRESENT_TEMPERATURE = 1


    def __init__(self, port="COM3", baudrate=1000000, motor_ids=None, mock_mode=False):
        self.port_name = port
        self.baudrate = baudrate
        self.motor_ids = motor_ids if motor_ids is not None else list(range(16))
        self.mock_mode = mock_mode
        self.is_connected = False
        
        # SDK Handlers
        self.port_handler = None
        self.packet_handler = None
        
        # State Cache (for Mock Mode and feedback)
        self.mock_positions = {mid: 2048 for mid in self.motor_ids}
        self.mock_currents = {mid: 0 for mid in self.motor_ids}
        self.torque_state = {mid: False for mid in self.motor_ids}
        
    def connect(self):
        """Establishes connection to the Dynamixel port."""
        if self.mock_mode:
            logging.info(f"[Mock Mode] Connected to port {self.port_name} at {self.baudrate} bps")
            self.is_connected = True
            return True

        try:
            import dynamixel_sdk as dxl
        except ImportError:
            logging.error("dynamixel_sdk is not installed. Falling back to Mock Mode.")
            self.mock_mode = True
            self.is_connected = True
            return True

        self.port_handler = dxl.PortHandler(self.port_name)
        self.packet_handler = dxl.PacketHandler(2.0) # LEAP Hand uses Protocol 2.0

        # Open Port
        if not self.port_handler.openPort():
            logging.error(f"Failed to open port {self.port_name}")
            return False

        # Set Baudrate
        if not self.port_handler.setBaudRate(self.baudrate):
            logging.error(f"Failed to set baudrate {self.baudrate}")
            self.port_handler.closePort()
            return False

        logging.info(f"Successfully connected to port {self.port_name} at {self.baudrate} bps")
        self.is_connected = True
        return True

    def disconnect(self):
        """Closes the connection to the Dynamixel port."""
        if not self.is_connected:
            return
            
        if self.mock_mode:
            logging.info("[Mock Mode] Disconnected.")
            self.is_connected = False
            return

        # Only disable torque for motors that currently have torque enabled
        active_torqued_ids = [mid for mid, state in self.torque_state.items() if state]
        if active_torqued_ids:
            self.disable_torque(active_torqued_ids)
        
        if self.port_handler is not None:
            self.port_handler.closePort()
            logging.info(f"Port {self.port_name} closed.")
            
        self.is_connected = False

    def reboot(self, motor_ids):
        """Reboots the specified motors to clear error shutdown status."""
        if self.mock_mode:
            logging.info(f"[Mock Mode] Rebooted motors {motor_ids}")
            return True

        success = True
        for mid in motor_ids:
            dxl_comm_result, dxl_error = self.packet_handler.reboot(self.port_handler, mid)
            if dxl_comm_result != 0:
                logging.error(f"Reboot error on motor {mid}: {self.packet_handler.getTxRxResult(dxl_comm_result)}")
                success = False
            elif dxl_error != 0:
                logging.error(f"Reboot status error on motor {mid}: {self.packet_handler.getRxPacketError(dxl_error)}")
                success = False
            else:
                logging.info(f"Successfully rebooted motor {mid}")
        
        # Give motors a moment to boot back up
        if success and motor_ids:
            time.sleep(1.0)
        return success

    def ping(self, motor_id):
        """Pings a specific motor to check if it's responsive."""
        if self.mock_mode:
            return motor_id in self.motor_ids

        model_number, dxl_comm_result, dxl_error = self.packet_handler.ping(self.port_handler, motor_id)
        if dxl_comm_result != 0:
            return False
        return True

    def scan(self):
        """Scans the bus for active motors."""
        active_ids = []
        logging.info("Scanning Dynamixel bus...")
        for mid in self.motor_ids:
            if self.ping(mid):
                active_ids.append(mid)
        logging.info(f"Scan complete. Found {len(active_ids)} active motor(s): {active_ids}")
        return active_ids

    def set_operating_mode(self, motor_ids, mode=5):
        """
        Sets the operating mode for multiple motors.
        Modes:
          3: Position Control Mode
          5: Current-based Position Control Mode (Recommended for LEAP Hand safety)
        """
        if self.mock_mode:
            logging.info(f"[Mock Mode] Operating Mode for motors {motor_ids} set to {mode}")
            return True

        success = True
        for mid in motor_ids:
            # Operating mode can only be written when torque is disabled
            self.packet_handler.write1ByteTxRx(self.port_handler, mid, self.ADDR_OPERATING_MODE, mode)
            # Verify write
            val, result, err = self.packet_handler.read1ByteTxRx(self.port_handler, mid, self.ADDR_OPERATING_MODE)
            if val != mode:
                logging.error(f"Failed to set Operating Mode to {mode} for motor {mid}. Current: {val}")
                success = False
        return success

    def set_torque_limits(self, motor_ids, limit_ma=250):
        """
        Sets Current Limit (Address 38) to limit max current/torque in all modes.
        Only writable when torque is disabled.
        """
        if self.mock_mode:
            logging.info(f"[Mock Mode] Torque limits for motors {motor_ids} set to {limit_ma} mA")
            return True

        success = True
        limit_val = int(np.clip(limit_ma, 0, 1947))
        for mid in motor_ids:
            self.packet_handler.write2ByteTxRx(self.port_handler, mid, self.ADDR_CURRENT_LIMIT, limit_val)
            val, result, err = self.packet_handler.read2ByteTxRx(self.port_handler, mid, self.ADDR_CURRENT_LIMIT)
            if val != limit_val:
                logging.error(f"Failed to set Current Limit to {limit_val} for motor {mid}. Current: {val}")
                success = False
        return success

    def set_current_limits(self, motor_ids, limit_ma=250):
        """
        Sets Goal Current (Address 102) for torque safety.
        For XC330, current unit is 1.0 mA. Value range is 0 to 1950.
        """
        if self.mock_mode:
            logging.info(f"[Mock Mode] Current limits for motors {motor_ids} set to {limit_ma} mA")
            return True

        success = True
        # Clamp to a safe range
        limit_val = int(np.clip(limit_ma, 0, 1000))
        for mid in motor_ids:
            self.packet_handler.write2ByteTxRx(self.port_handler, mid, self.ADDR_GOAL_CURRENT, limit_val)
            val, result, err = self.packet_handler.read2ByteTxRx(self.port_handler, mid, self.ADDR_GOAL_CURRENT)
            if val != limit_val:
                logging.error(f"Failed to set Goal Current to {limit_val} for motor {mid}. Current: {val}")
                success = False
        return success

    def set_pid_gains(self, motor_ids, kp=250, ki=0, kd=100):
        """Sets the PID position gains (addresses 84, 82, 80)."""
        if self.mock_mode:
            logging.info(f"[Mock Mode] PID gains for motors {motor_ids} set to P={kp}, I={ki}, D={kd}")
            return True

        success = True
        for mid in motor_ids:
            # Write KP
            self.packet_handler.write2ByteTxRx(self.port_handler, mid, self.ADDR_K_P, kp)
            # Write KI
            self.packet_handler.write2ByteTxRx(self.port_handler, mid, self.ADDR_K_I, ki)
            # Write KD
            self.packet_handler.write2ByteTxRx(self.port_handler, mid, self.ADDR_K_D, kd)
        return success

    def set_profile_velocity(self, motor_ids, velocity=100):
        """
        Sets Profile Velocity (Address 112) for speed control.
        For XC330, unit is 0.229 rpm. Value range is 0 to 32767.
        """
        if self.mock_mode:
            logging.info(f"[Mock Mode] Profile velocity for motors {motor_ids} set to {velocity}")
            return True

        success = True
        val = int(np.clip(velocity, 0, 32767))
        for mid in motor_ids:
            dxl_comm_result, dxl_error = self.packet_handler.write4ByteTxRx(self.port_handler, mid, self.ADDR_PROFILE_VELOCITY, val)
            if dxl_comm_result != 0:
                logging.error(f"Profile velocity write error on motor {mid}: {self.packet_handler.getTxRxResult(dxl_comm_result)}")
                success = False
            elif dxl_error != 0:
                logging.error(f"Profile velocity status error on motor {mid}: {self.packet_handler.getRxPacketError(dxl_error)}")
                success = False
        return success

    def read_hardware_errors(self, motor_ids):
        """
        Reads the hardware error status (Address 85) for multiple motors.
        Returns a dict: {motor_id: error_byte}
        """
        if not self.is_connected:
            return {}

        if self.mock_mode:
            return {mid: 0 for mid in motor_ids}

        errors = {}
        for mid in motor_ids:
            val, result, err = self.packet_handler.read1ByteTxRx(self.port_handler, mid, self.ADDR_HARDWARE_ERROR_STATUS)
            if result == 0:
                errors[mid] = val
        return errors

    def read_hardware_errors_sync(self, motor_ids):
        """
        Reads the hardware error status (Address 85) for multiple motors using GroupSyncRead.
        Returns a dict: {motor_id: error_byte}
        """
        if not self.is_connected:
            return {}

        if self.mock_mode:
            return {mid: 0 for mid in motor_ids}

        import dynamixel_sdk as dxl

        errors = {}
        groupSyncRead = dxl.GroupSyncRead(
            self.port_handler, 
            self.packet_handler, 
            self.ADDR_HARDWARE_ERROR_STATUS, 
            self.LEN_HARDWARE_ERROR_STATUS
        )

        for mid in motor_ids:
            groupSyncRead.addParam(mid)

        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result == 0:
            for mid in motor_ids:
                if groupSyncRead.isAvailable(mid, self.ADDR_HARDWARE_ERROR_STATUS, self.LEN_HARDWARE_ERROR_STATUS):
                    errors[mid] = groupSyncRead.getData(mid, self.ADDR_HARDWARE_ERROR_STATUS, self.LEN_HARDWARE_ERROR_STATUS)
        else:
            # Fallback to sequential read
            for mid in motor_ids:
                val, result, err = self.packet_handler.read1ByteTxRx(self.port_handler, mid, self.ADDR_HARDWARE_ERROR_STATUS)
                if result == 0:
                    errors[mid] = val
                else:
                    errors[mid] = 0

        groupSyncRead.clearParam()
        return errors

    def enable_torque(self, motor_ids, enable=True):
        """Enables or disables torque for a list of motors."""
        if self.mock_mode:
            for mid in motor_ids:
                self.torque_state[mid] = enable
            logging.info(f"[Mock Mode] Torque {'ENABLED' if enable else 'DISABLED'} for motors {motor_ids}")
            return True

        val = 1 if enable else 0
        success = True
        for mid in motor_ids:
            dxl_comm_result, dxl_error = self.packet_handler.write1ByteTxRx(self.port_handler, mid, self.ADDR_TORQUE_ENABLE, val)
            if dxl_comm_result != 0:
                logging.error(f"Torque write error on motor {mid}: {self.packet_handler.getTxRxResult(dxl_comm_result)}")
                success = False
            elif dxl_error != 0:
                logging.error(f"Torque status error on motor {mid}: {self.packet_handler.getRxPacketError(dxl_error)}")
                success = False
            else:
                self.torque_state[mid] = enable
        return success

    def disable_torque(self, motor_ids):
        return self.enable_torque(motor_ids, enable=False)

    def write_positions(self, position_dict):
        """
        Writes target positions to multiple motors synchronously using Sync Write.
        position_dict: {motor_id: tick_value_0_4095}
        """
        if not self.is_connected:
            return False

        if self.mock_mode:
            for mid, pos in position_dict.items():
                self.mock_positions[mid] = pos
            return True

        import dynamixel_sdk as dxl
        
        groupSyncWrite = dxl.GroupSyncWrite(
            self.port_handler, 
            self.packet_handler, 
            self.ADDR_GOAL_POSITION, 
            self.LEN_GOAL_POSITION
        )

        for mid, pos in position_dict.items():
            # Support extended multi-turn positions (range -256000 to 256000)
            tick = int(np.clip(pos, -256000, 256000))
            if tick < 0:
                tick = (1 << 32) + tick
            param_goal_position = [
                dxl.DXL_LOBYTE(dxl.DXL_LOWORD(tick)),
                dxl.DXL_HIBYTE(dxl.DXL_LOWORD(tick)),
                dxl.DXL_LOBYTE(dxl.DXL_HIWORD(tick)),
                dxl.DXL_HIBYTE(dxl.DXL_HIWORD(tick))
            ]
            groupSyncWrite.addParam(mid, param_goal_position)

        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != 0:
            logging.error(f"Sync position write failed: {self.packet_handler.getTxRxResult(dxl_comm_result)}")
            success = False
        else:
            success = True

        groupSyncWrite.clearParam()
        return success

    def read_positions(self, motor_ids):
        """
        Reads current positions of multiple motors using Sync Read (or sequential read if sync read fails).
        Returns a dict: {motor_id: present_position_ticks}
        """
        if not self.is_connected:
            return {}

        if self.mock_mode:
            # Return cached mock positions with a tiny bit of noise
            return {mid: int(self.mock_positions[mid] + np.random.normal(0, 1)) for mid in motor_ids}

        import dynamixel_sdk as dxl

        positions = {}
        groupSyncRead = dxl.GroupSyncRead(
            self.port_handler, 
            self.packet_handler, 
            self.ADDR_PRESENT_POSITION, 
            self.LEN_PRESENT_POSITION
        )

        for mid in motor_ids:
            groupSyncRead.addParam(mid)

        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result == 0:
            for mid in motor_ids:
                if groupSyncRead.isAvailable(mid, self.ADDR_PRESENT_POSITION, self.LEN_PRESENT_POSITION):
                    val = groupSyncRead.getData(mid, self.ADDR_PRESENT_POSITION, self.LEN_PRESENT_POSITION)
                    if val >= 0x80000000:
                        val -= 0x100000000
                    positions[mid] = val
        else:
            # Fallback to sequential read
            for mid in motor_ids:
                val, result, err = self.packet_handler.read4ByteTxRx(self.port_handler, mid, self.ADDR_PRESENT_POSITION)
                if result == 0:
                    if val >= 0x80000000:
                        val -= 0x100000000
                    positions[mid] = val

        groupSyncRead.clearParam()
        return positions

    def read_currents(self, motor_ids):
        """
        Reads current currents of multiple motors.
        Returns a dict: {motor_id: current_ma}
        """
        if not self.is_connected:
            return {}

        if self.mock_mode:
            return {mid: int(self.mock_currents[mid] + np.random.normal(0, 2)) for mid in motor_ids}

        import dynamixel_sdk as dxl

        currents = {}
        groupSyncRead = dxl.GroupSyncRead(
            self.port_handler, 
            self.packet_handler, 
            self.ADDR_PRESENT_CURRENT, 
            self.LEN_PRESENT_CURRENT
        )

        for mid in motor_ids:
            groupSyncRead.addParam(mid)

        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result == 0:
            for mid in motor_ids:
                if groupSyncRead.isAvailable(mid, self.ADDR_PRESENT_CURRENT, self.LEN_PRESENT_CURRENT):
                    val = groupSyncRead.getData(mid, self.ADDR_PRESENT_CURRENT, self.LEN_PRESENT_CURRENT)
                    # Convert to signed 16-bit
                    if val & (1 << 15):
                        val = val - (1 << 16)
                    # Convert unit: 1 unit = 1 mA for XC330 series
                    currents[mid] = val
        else:
            # Fallback to sequential read
            for mid in motor_ids:
                val, result, err = self.packet_handler.read2ByteTxRx(self.port_handler, mid, self.ADDR_PRESENT_CURRENT)
                if result == 0:
                    if val & (1 << 15):
                        val = val - (1 << 16)
                    currents[mid] = val

        groupSyncRead.clearParam()
        return currents

    def read_temperatures(self, motor_ids):
        """
        Reads the present temperatures (Address 146) for multiple motors.
        Returns a dict: {motor_id: temp_celsius}
        """
        if not self.is_connected:
            return {}

        if self.mock_mode:
            return {mid: 32 for mid in motor_ids}

        import dynamixel_sdk as dxl

        temps = {}
        groupSyncRead = dxl.GroupSyncRead(
            self.port_handler,
            self.packet_handler,
            self.ADDR_PRESENT_TEMPERATURE,
            self.LEN_PRESENT_TEMPERATURE
        )

        for mid in motor_ids:
            groupSyncRead.addParam(mid)

        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result == 0:
            for mid in motor_ids:
                if groupSyncRead.isAvailable(mid, self.ADDR_PRESENT_TEMPERATURE, self.LEN_PRESENT_TEMPERATURE):
                    temps[mid] = groupSyncRead.getData(mid, self.ADDR_PRESENT_TEMPERATURE, self.LEN_PRESENT_TEMPERATURE)
        else:
            # Fallback to sequential read
            for mid in motor_ids:
                val, result, err = self.packet_handler.read1ByteTxRx(self.port_handler, mid, self.ADDR_PRESENT_TEMPERATURE)
                if result == 0:
                    temps[mid] = val
                else:
                    temps[mid] = 32

        groupSyncRead.clearParam()
        return temps

