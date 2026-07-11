import sys
import time
import argparse
from dynamixel_driver import DynamixelDriver

def get_error_description(error_byte):
    errors = []
    if error_byte & 0x01:
        errors.append("Input Voltage Error (Voltage out of range)")
    if error_byte & 0x04:
        errors.append("Overheating Error (Temperature exceeded safety limit)")
    if error_byte & 0x08:
        errors.append("Motor Encoder Error (Sensor failure/position lost)")
    if error_byte & 0x10:
        errors.append("Electrical Shock Error (Overcurrent detected)")
    if error_byte & 0x20:
        errors.append("Overload Error (OL - excessive load sustained/current limit too low)")
    return ", ".join(errors) if errors else "None"

def main():
    parser = argparse.ArgumentParser(description="Directly move OSRS Humanoid Bot arms to target calibration positions.")
    parser.add_argument("--port", type=str, default="COM14", help="Serial port of the Dynamixel USB interface (e.g. COM14 or /dev/ttyUSB0)")
    parser.add_argument("--baudrate", type=int, default=4000000, help="Baudrate of the Dynamixel bus (default: 4000000)")
    parser.add_argument("--current-limit", type=int, default=250, help="Current limit in mA to protect servos (default: 250)")
    parser.add_argument("--mock", action="store_true", help="Run in mock/simulation mode without physical hardware")
    args = parser.parse_args()

    # Target values from user request image:
    # Left Arm Pose Target Values:
    # - ID 24 (Left Elbow Flex / L4F): 2990
    # - ID 25 (Left Forearm Yaw / L5Y): -40
    # - ID 26 (Left Wrist Roll / L6R): -983
    # - ID 27 (Left Wrist Pitch / L7P): 2088
    #
    # Right Arm Pose Target Values:
    # - ID 14 (Right Elbow Flex / R4F): 1720
    # - ID 15 (Right Forearm Yaw / R5Y): -5
    # - ID 16 (Right Wrist Roll / R6R): 1007
    # - ID 17 (Right Wrist Pitch / R7P): -174
    targets = {
        24: 2990,
        25: -40,
        26: -983,
        27: 2088,
        14: 1720,
        15: -5,
        16: 1007,
        17: -174
    }

    motor_ids = list(targets.keys())

    print(f"OSRS Standalone Arm Initializer")
    print(f"==============================")
    print(f"Port: {args.port}")
    print(f"Baudrate: {args.baudrate}")
    print(f"Current Limit: {args.current_limit} mA")
    print(f"Mock Mode: {args.mock}")
    print("------------------------------")
    print("Target Positions:")
    for mid, val in targets.items():
        side = "Left" if mid >= 20 else "Right"
        print(f"  ID {mid:2d} ({side} Arm): {val:5d}")
    print("------------------------------")

    # Initialize Dynamixel driver using target IDs
    driver = DynamixelDriver(port=args.port, baudrate=args.baudrate, motor_ids=motor_ids, mock_mode=args.mock)

    print("Connecting to Dynamixel bus...")
    if not driver.connect():
        print("Error: Could not connect to serial port. Make sure no other program (like OSRS server) is using it.", file=sys.stderr)
        sys.exit(1)

    try:
        active_ids = []
        if not args.mock:
            print("Scanning for active motor IDs...")
            active_ids = driver.scan()
            print(f"Scanned active motor IDs: {active_ids}")
            
            # Filter targets to only those that are present on the bus
            missing_ids = [mid for mid in motor_ids if mid not in active_ids]
            if missing_ids:
                print(f"Warning: Servos {missing_ids} were not detected on the bus.")
                # We will only command the detected servos to prevent errors
                motor_ids = [mid for mid in motor_ids if mid in active_ids]
                if not motor_ids:
                    print("Error: None of the target arm servos were detected on the bus. Aborting.", file=sys.stderr)
                    sys.exit(1)
        else:
            active_ids = motor_ids

        # 1. Reboot servos to clear any hardware error shutdown status
        print("Rebooting servos to clear any hardware error shutdowns...")
        driver.reboot(motor_ids)
        time.sleep(1.5)  # Wait for servos to boot back up

        # 2. Disable torque to configure EEPROM registers
        print("Disabling torque to configure motor settings...")
        driver.enable_torque(motor_ids, False)
        for mid in motor_ids:
            driver.torque_state[mid] = False
        time.sleep(0.1)

        # 3. Set operating mode to Mode 4 (Extended Position Control for multi-turn support)
        print("Setting operating mode to Mode 4 (Extended Position Control)...")
        driver.set_operating_mode(motor_ids, mode=4)

        # 4. Set current limits to protect hardware
        print(f"Setting current limits to {args.current_limit} mA...")
        driver.set_torque_limits(motor_ids, limit_ma=args.current_limit)
        driver.set_current_limits(motor_ids, limit_ma=args.current_limit)

        # 5. Enable torque
        print("Enabling torque...")
        driver.enable_torque(motor_ids, True)
        for mid in motor_ids:
            driver.torque_state[mid] = True
        time.sleep(0.1)

        # 6. Write target positions smoothly
        print("Moving to target coordinates...")
        write_targets = {mid: targets[mid] for mid in motor_ids}
        driver.write_positions(write_targets)

        # 7. Monitor progress for a few seconds
        print("Monitoring position convergence (Ctrl+C to stop)...")
        pres_pos = {}
        for _ in range(30):
            pres_pos = driver.read_positions(motor_ids)
            print("Current Positions:")
            for mid in motor_ids:
                target = targets[mid]
                present = pres_pos.get(mid, "??")
                present_str = f"{present:5d}" if isinstance(present, int) else f"{present:>5s}"
                diff_str = f" (Diff: {target - present:5d})" if isinstance(present, int) else ""
                print(f"  ID {mid:2d}: Target={target:5d}, Present={present_str}{diff_str}")
            print("-" * 30)
            time.sleep(0.2)

        # 8. Check final convergence and diagnose failures
        print("\nChecking final calibration status:")
        has_failures = False
        for mid in motor_ids:
            target = targets[mid]
            present = pres_pos.get(mid)
            if not isinstance(present, int) or abs(target - present) > 100:
                has_failures = True
                side = "Left" if mid >= 20 else "Right"
                present_desc = f"{present}" if present is not None else "Communication Failed / Off"
                print(f"[!] ID {mid:2d} ({side} Arm) did not reach target position (Target: {target:5d}, Present: {present_desc})")
                
                if not args.mock:
                    err_byte, res, err = driver.packet_handler.read1ByteTxRx(driver.port_handler, mid, driver.ADDR_HARDWARE_ERROR_STATUS)
                    if res == 0:
                        desc = get_error_description(err_byte)
                        print(f"    -> Hardware Error Status: Code {err_byte} ({desc})")
                        if err_byte & 0x20 or err_byte & 0x10:
                            print(f"    -> DIAGNOSIS: Servo overloaded/shut down. Try running the script with a higher current limit (e.g. --current-limit 800).")
                    else:
                        print("    -> Could not read hardware error register.")
        
        if not has_failures:
            print("[+] All active arm joints reached target positions successfully!")
        else:
            print("\n[TIP] If you saw 'Overload Error' or motors failed to move fully, increase --current-limit (e.g. to 800 or 1000).")

    except KeyboardInterrupt:
        print("\nMotion monitor interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}", file=sys.stderr)
    finally:
        print("Closing port connection...")
        driver.disconnect()
        print("Done.")

if __name__ == "__main__":
    main()
