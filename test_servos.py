import time
import sys
import logging
from dynamixel_driver import DynamixelDriver

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_servo_movement():
    print("====================================================")
    print("           LEAP HAND SERVO TEST UTILITY             ")
    print("====================================================")
    
    # Autodetect COM port and Baudrate
    import serial.tools.list_ports
    import dynamixel_sdk as dxl
    
    print("[*] Scanning COM ports for LEAP Hand...")
    ports = [p.device for p in serial.tools.list_ports.comports()]
    detected_port = None
    detected_baud = None
    detected_ids = []
    
    if ports:
        baudrates = [4000000, 1000000, 2000000, 57600]
        ids_to_check = [0, 1, 12, 15]
        
        for port in ports:
            for baud in baudrates:
                port_handler = dxl.PortHandler(port)
                packet_handler = dxl.PacketHandler(2.0)
                
                if port_handler.openPort() and port_handler.setBaudRate(baud):
                    for mid in ids_to_check:
                        model, result, err = packet_handler.ping(port_handler, mid)
                        if result == 0:
                            detected_port = port
                            detected_baud = baud
                            detected_ids.append(mid)
                    port_handler.closePort()
                if detected_port:
                    break
            if detected_port:
                break
                
    if detected_port and detected_baud:
        print(f"[+] Found LEAP Hand on {detected_port} at {detected_baud} bps (responding IDs: {detected_ids})")
        use_auto = input("Use these settings? (Y/n): ").strip().lower()
        if use_auto != 'n':
            port = detected_port
            baud = detected_baud
        else:
            port = input(f"Enter COM Port [Default: {detected_port}]: ").strip() or detected_port
            baud_str = input(f"Enter Baudrate [Default: {detected_baud}]: ").strip()
            baud = int(baud_str) if baud_str else detected_baud
    else:
        print("[-] Auto-detection found no responsive hardware.")
        port = input("Enter your U2D2 COM Port (e.g. COM13): ").strip()
        if not port:
            port = "COM13"
        baud_str = input("Enter Baudrate [Default: 4000000]: ").strip()
        baud = int(baud_str) if baud_str else 4000000

    # Initialize driver (Mock Mode = False to connect to real hardware)
    driver = DynamixelDriver(port=port, baudrate=baud, motor_ids=list(range(16)), mock_mode=False)
    
    print(f"\nAttempting to connect to {port} at {baud} bps...")
    if not driver.connect():
        print("[-] Connection failed. Check USB connection and COM port assignment.")
        sys.exit(1)

    # Scan active IDs
    active_ids = driver.scan()
    if not active_ids:
        print("[-] No responsive motors found. Check power supply (5V/7.6V) and motor daisy chains.")
        driver.disconnect()
        sys.exit(1)

    print(f"\n[+] Found {len(active_ids)} active motor(s): {active_ids}")
    
    # Ask user to verify they want to enable torque
    input("\nWARNING: Enabling torque. Make sure the hand is clear of obstacles.\nPress Enter to continue...")
    
    # Set to current-based position control mode (Mode 5)
    print("[*] Setting Operating Mode to Current-Based Position Control (Mode 5)...")
    driver.set_operating_mode(active_ids, mode=5)
    
    # Set a very safe current limit to prevent damage during testing
    safe_current_ma = 200
    print(f"[*] Setting safe current limit to {safe_current_ma} mA...")
    driver.set_current_limits(active_ids, limit_ma=safe_current_ma)

    # Set default safe PID gains
    print("[*] Applying safe PID gains...")
    driver.set_pid_gains(active_ids, kp=200, ki=0, kd=80)

    # Set safe profile velocity
    safe_speed = 100
    print(f"[*] Setting safe profile velocity to {safe_speed}...")
    driver.set_profile_velocity(active_ids, velocity=safe_speed)

    # Enable torque with automatic reboot recovery for hardware errors
    print("[+] Enabling motor torque...")
    failed_motors = []
    for mid in active_ids:
        if not driver.enable_torque([mid], True):
            failed_motors.append(mid)
            
    if failed_motors:
        print(f"\n[-] Failed to enable torque on motor(s): {failed_motors}")
        print("[*] Attempting to reboot failed motor(s) to clear hardware error status...")
        driver.reboot(failed_motors)
        
        print("[*] Retrying to enable torque after reboot...")
        retry_failed = []
        for mid in failed_motors:
            if not driver.enable_torque([mid], True):
                retry_failed.append(mid)
                
        if retry_failed:
            print(f"\n[!] WARNING: Could not enable torque on motor(s): {retry_failed}.")
            print("    Please check motor cabling, voltage, or if it is physically jammed.")
            # Remove failed motors from active list to proceed with remaining ones
            active_ids = [mid for mid in active_ids if mid not in retry_failed]
            if not active_ids:
                print("[-] Error: All active motors failed. Exiting.")
                driver.disconnect()
                sys.exit(1)
            else:
                print(f"[+] Continuing test sequence with remaining working motor(s): {active_ids}")
        else:
            print("[+] Successfully recovered and enabled torque on all motors!")

    print("\n[+] Torque enabled. Servos should be locked in place.")
    
    # Read and print present positions
    print("\nReading initial positions:")
    positions = driver.read_positions(active_ids)
    for mid, pos in positions.items():
        print(f"  Motor ID {mid}: {pos} ticks")
        
    print("\nStarting test sequence (press Ctrl+C to abort)...")
    print("1. Testing manual input:")
    
    try:
        while True:
            choice = input("\nEnter 't' to run a gentle back-and-forth movement, 'w' to write custom positions, or 'q' to quit: ").strip().lower()
            
            if choice == 'q':
                break
                
            elif choice == 't':
                # Read start positions
                start_positions = driver.read_positions(active_ids)
                
                # Perform a gentle swing test (+200 ticks, then back to original)
                print("\nMoving active joints +200 ticks...")
                swing_pos = {mid: pos + 200 for mid, pos in start_positions.items()}
                driver.write_positions(swing_pos)
                time.sleep(1.0)
                
                # Read present position
                print("Reading feedback during movement:")
                pres = driver.read_positions(active_ids)
                for mid in active_ids:
                    print(f"  Motor ID {mid}: Target {swing_pos[mid]} -> Present {pres.get(mid, 'N/A')}")
                
                time.sleep(0.5)
                
                print("\nReturning to original positions...")
                driver.write_positions(start_positions)
                time.sleep(1.0)
                
            elif choice == 'w':
                try:
                    target_id = int(input(f"Enter Motor ID to write to {active_ids}: "))
                    if target_id not in active_ids:
                        print("ID is not in active motor list.")
                        continue
                    target_tick = int(input("Enter goal position (0-4095 ticks, typical center is 2048): "))
                    if not (0 <= target_tick <= 4095):
                        print("Tick value must be between 0 and 4095.")
                        continue
                        
                    print(f"Moving Motor {target_id} to {target_tick} ticks...")
                    driver.write_positions({target_id: target_tick})
                    time.sleep(0.5)
                    pres = driver.read_positions([target_id])
                    print(f"Motor {target_id} present position: {pres.get(target_id, 'N/A')}")
                except ValueError:
                    print("Invalid input format.")
            else:
                print("Unknown choice.")
                
    except KeyboardInterrupt:
        print("\nTest aborted by user.")

    # Cleanup
    print("\n[-] Disabling torque...")
    driver.disable_torque(active_ids)
    print("[-] Disconnecting port...")
    driver.disconnect()
    print("[+] Test completed.")

if __name__ == "__main__":
    test_servo_movement()
