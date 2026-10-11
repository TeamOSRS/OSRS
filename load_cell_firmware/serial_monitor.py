#!/usr/bin/env python3
"""
Serial Monitor Script for HX711 Arduino Scale

This script connects to an Arduino Uno over a serial port, continuously reads
the incoming weight data, and displays it in the terminal. It includes robust
error handling and an automatic reconnection loop to ensure reliability if the
connection is disrupted.

Dependencies:
    pyserial (Install via `pip install pyserial`)
"""

import time
import sys
import serial

# ==============================================================================
# Configuration Constants
# ==============================================================================
# Serial Port: Set this to match your system's Arduino Uno port.
# Windows: 'COM3', 'COM4', etc.
# Linux/macOS: '/dev/ttyUSB0', '/dev/ttyACM0', '/dev/tty.usbmodem...'
SERIAL_PORT = 'COM11'

# Baud Rate: Must match the baud rate defined in the Arduino firmware (setup() Serial.begin)
BAUD_RATE = 57600

# Reconnection Delay (seconds): Time to wait before attempting to reconnect after failure
RECONNECT_DELAY = 3.0

# Timeout (seconds): Serial port read timeout
SERIAL_TIMEOUT = 1.0


def read_serial_stream(ser):
    """
    Reads incoming lines from the open serial connection, parses the float values,
    and displays them in the terminal.
    
    Args:
        ser (serial.Serial): The active open serial connection.
    """
    # Flush input buffer on startup to clear any stale data
    ser.reset_input_buffer()
    
    print("[INFO] Connection established. Reading weight data...")
    print("-" * 40)
    
    while True:
        # Read a line ending with '\n'
        line = ser.readline()
        if not line:
            # Timeout reached, no data received. Just keep waiting.
            continue
            
        try:
            # Decode binary string to utf-8 text and strip whitespace
            decoded_line = line.decode('utf-8').strip()
            
            # Skip empty lines
            if not decoded_line:
                continue
                
            try:
                # Parse the incoming string to a float value
                weight = float(decoded_line)
                
                # Print the parsed weight with exactly two decimal places
                print(f"Weight: {weight:.2f}")
            except ValueError:
                # If the line contains non-float values (like startup messages or noise)
                print(f"[RAW]: {decoded_line}")
                
        except UnicodeDecodeError:
            # Handle transmission noise or encoding issues gracefully
            print("[WARNING] Could not decode incoming serial data. Skipping line.")


def main():
    """
    Main loop to handle serial port initialization, execution, and automatic
    reconnection on communication errors.
    """
    print("==================================================")
    print("             HX711 Serial Weight Monitor          ")
    print("==================================================")
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print("Press Ctrl+C to stop.")
    print("-" * 50)

    while True:
        try:
            # Open the serial port
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT) as ser:
                read_serial_stream(ser)
                
        except (serial.SerialException, OSError) as e:
            # Catch serial interface or port availability errors (e.g. port unplugged or busy)
            print(f"[ERROR] Serial port error: {e}")
            print(f"Attempting to reconnect in {RECONNECT_DELAY} seconds...")
            time.sleep(RECONNECT_DELAY)
            
        except KeyboardInterrupt:
            # Graceful shutdown on Ctrl+C
            print("\n[INFO] Exiting Serial Monitor. Goodbye!")
            sys.exit(0)


if __name__ == '__main__':
    main()
