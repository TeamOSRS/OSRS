import time
import sys
import argparse
import serial.tools.list_ports
from dynamixel_driver import DynamixelDriver

def get_error_description(error_byte):
    """Translates the Hardware Error Status byte (Address 85) into human-readable details."""
    errors = []
    if error_byte & 0x01:
        errors.append("Input Voltage Error (Voltage out of range)")
    if error_byte & 0x04:
        errors.append("Overheating Error (Temperature exceeded safety limit)")
    if error_byte & 0x08:
        errors.append("Motor Encoder Error (Sensor failure/position lost)")
    if error_byte & 0x10:
        errors.append("Electrical Shock Error / ES (Overcurrent detected - potential short circuit or major electrical issue)")
    if error_byte & 0x20:
        errors.append("Overload Error / OL (Excessive load sustained for too long)")
    return ", ".join(errors) if errors else "None"

def test_motor_id9():
    parser = argparse.ArgumentParser(description="LEAP Hand ID 9 (Index DIP) Diagnostic Tool")
    parser.add_argument("--port", type=str, default=None, help="COM port to use (e.g. COM13)")
    parser.add_argument("--baud", type=int, default=None, help="Baudrate to use (e.g. 4000000)")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (simulated hardware)")
    args = parser.parse_args()

    print("======================================================================")
    print("           LEAP HAND: MOTOR ID 009 (INDEX DIP) DIAGNOSTIC TOOL        ")
    print("======================================================================")
    print("This script helps diagnose electrical shock (ES) and overload (OL) errors.")
    print("It will ping ID 9, reboot it if needed, test torque enablement, and")
    print("conduct a safe, slow motion test within bounds with real-time telemetry.")
    print("======================================================================\n")

    if args.mock:
        print("[*] Running in MOCK (simulation) mode.")
        port = "MOCK_PORT"
        baud = 4000000
    else:
        # 1. Select COM Port
        if args.port:
            port = args.port
            print(f"Using COM port specified via argument: {port}")
        else:
            ports = [p.device for p in serial.tools.list_ports.comports()]
            print("Available COM ports:")
            for p in ports:
                print(f"  - {p}")
            
            default_port = "COM13" if "COM13" in ports or not ports else (ports[0] if ports else "COM13")
            port = input(f"Enter COM port to use [Default: {default_port}]: ").strip()
            if not port:
                port = default_port

        # 2. Select Baudrate
        if args.baud:
            baud = args.baud
            print(f"Using Baudrate specified via argument: {baud}")
        else:
            default_baud = 4000000
            baud_str = input(f"Enter Baudrate [Default: {default_baud}]: ").strip()
            if baud_str:
                try:
                    baud = int(baud_str)
                except ValueError:
                    print("Invalid baudrate. Using default.")
                    baud = default_baud
            else:
                baud = default_baud

    TARGET_ID = 9
    print(f"\n[*] Initializing connection to {port} at {baud} bps...")
    driver = DynamixelDriver(port=port, baudrate=baud, motor_ids=[TARGET_ID], mock_mode=args.mock)

    if not driver.connect():
        print(f"\n[-] ERROR: Could not open port {port}.")
        print("    Please verify that:")
        print("    1. The U2D2 is plugged in and recognized under this port name.")
        print("    2. All other applications using this port (e.g. Dynamixel Wizard, main GUI) are fully closed.")
        sys.exit(1)

    print(f"[+] Successfully opened port {port}.")
    print(f"[*] Pinging Motor ID {TARGET_ID}...")
    
    if not driver.ping(TARGET_ID):
        print(f"\n[-] ERROR: Motor ID {TARGET_ID} did not respond to ping.")
        print("    This usually means:")
        print("    1. The motor has no power (check the 12V power supply to the hand/U2D2 board).")
        print("    2. The daisy chain cables are disconnected or damaged before ID 9.")
        print("    3. The motor ID is configured incorrectly on the hardware.")
        driver.disconnect()
        sys.exit(1)

    print(f"[+] Motor ID {TARGET_ID} responded successfully to ping!")

    # 3. Read Hardware Error Status
    print(f"\n[*] Reading Hardware Error Status for Motor ID {TARGET_ID}...")
    val = 0
    if args.mock:
        # Simulate a mock error to test reboot path if user wants to test it, 
        # but by default mock is clean.
        val = 0
    else:
        val_read, result, err = driver.packet_handler.read1ByteTxRx(driver.port_handler, TARGET_ID, driver.ADDR_HARDWARE_ERROR_STATUS)
        if result == 0:
            val = val_read
        else:
            print("[-] Failed to read hardware error status register. Proceeding...")
            val = 0

    desc = get_error_description(val)
    print(f"[+] Hardware Error Status Registry: Code {val} ({desc})")
    
    if val != 0:
        print("\n[!] DETECTED HARDWARE ERROR STATE!")
        if val & 0x10:
            print("    --> ES (Electrical Shock) Error detected.")
            print("        This indicates an overcurrent 