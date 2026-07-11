import sys
import time
import logging

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[-] pyserial is required. Please install it with 'pip install pyserial'")
    sys.exit(1)

try:
    import dynamixel_sdk as dxl
except ImportError:
    print("[-] dynamixel_sdk is required. Please install it with 'pip install dynamixel_sdk'")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def detect_leap_hand():
    print("====================================================")
    print("          LEAP HAND HARDWARE AUTO-DETECTOR          ")
    print("====================================================")
    
    # 1. Get all available COM ports
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if not ports:
        print("[-] No active COM ports detected. Check USB connections.")
        return
        
    print(f"[+] Available COM ports: {ports}")
    
    # 2. Define baudrates to test (highest to lowest for quick detection of high-speed ports)
    baudrates = [1000000, 4000000, 2000000, 57600, 115200, 9600]
    
    # Typical motor IDs to ping for verification (pinging a few helps avoid missing if one motor is dead)
    ids_to_check = [0, 1, 2, 12, 13, 15] 
    
    found_port = None
    found_baud = None
    found_motors = []
    
    print("\nScanning ports and baudrates (Protocol 2.0)...")
    for port in ports:
        print(f"\nChecking port: {port}")
        for baud in baudrates:
            print(f"  Testing baudrate: {baud} bps... ", end="", flush=True)
            
            # Initialize SDK handlers
            port_handler = dxl.PortHandler(port)
            packet_handler = dxl.PacketHandler(2.0) # Protocol 2.0
            
            # Attempt to open port
            if not port_handler.openPort():
                print("Failed (Port Busy/Unavailable)")
                continue
                
            # Attempt to set baudrate
            if not port_handler.setBaudRate(baud):
                print("Failed (Unsupported Baud)")
                port_handler.closePort()
                continue
                
            # Test pinging verification motor IDs
            hand_detected = False
            detected_ids = []
            
            for mid in ids_to_check:
                model_number, dxl_comm_result, dxl_error = packet_handler.ping(port_handler, mid)
                if dxl_comm_result == 0:
                    hand_detected = True
                    detected_ids.append(mid)
                    
            port_handler.closePort()
            
            if hand_detected:
                print(f"SUCCESS! (Motors responded: {detected_ids})")
                found_port = port
                found_baud = baud
                break
            else:
                print("No response")
                
        if found_port:
            break
            
    # 3. Full scan on the detected port
    if found_port and found_baud:
        print("\n====================================================")
        print(f"[+] DETECTED HARDWARE ON PORT: {found_port} at {found_baud} bps")
        print("====================================================")
        print("Scanning all possible motor IDs (0 to 20) on this port...")
        
        port_handler = dxl.PortHandler(found_port)
        packet_handler = dxl.PacketHandler(2.0)
        
        if port_handler.openPort() and port_handler.setBaudRate(found_baud):
            for mid in range(21):
                model_number, dxl_comm_result, dxl_error = packet_handler.ping(port_handler, mid)
                if dxl_comm_result == 0:
                    found_motors.append(mid)
            port_handler.closePort()
            
        print(f"[+] Total motors responding: {len(found_motors)}")
        print(f"[+] Motor IDs: {found_motors}")
        
        # Give hints based on motor counts
        if len(found_motors) == 16:
            print("[Info] Detected configuration fits standard LEAP Hand V1 (16 motors).")
        elif len(found_motors) == 8:
            print("[Info] Detected configuration fits LEAP Hand V2 (8 motors).")
        elif len(found_motors) == 17:
            print("[Info] Detected configuration fits LEAP Hand V2 Advanced (17 motors).")
            
        print("\nTo use these settings, start your scripts with:")
        print(f"  COM Port: {found_port}")
        print(f"  Baudrate: {found_baud}")
    else:
        print("\n[-] Hardware auto-detection finished. No LEAP Hand was found.")
        print("    1. Ensure the hand is powered (Check external power supply LEDs).")
        print("    2. Verify U2D2 / USB serial device is plugged in.")
        print("    3. Ensure no other scripts or Dynamixel Wizard is occupying the COM port.")

if __name__ == "__main__":
    detect_leap_hand()
