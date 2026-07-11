import logging
import uvicorn
import socket
import os
import sys
import subprocess
import webbrowser
import time

def is_port_in_use(port):
    """Checks if a local socket port is currently bound/in-use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def kill_process_on_port(port):
    """Finds and terminates the process occupying the specified port."""
    print(f"\nAttempting to stop process on port {port}...")
    if sys.platform.startswith('win'):
        try:
            # Find matching network connection records
            output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
            pids = set()
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pids.add(parts[-1])
            for pid in pids:
                if pid != '0':
                    print(f"Terminating process PID {pid}...")
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
            print("Successfully cleared port address binding!")
            return True
        except Exception as e:
            print(f"Failed to clear port process: {e}")
            return False
    else:
        try:
            subprocess.run(f'fuser -k {port}/tcp', shell=True)
            print("Successfully cleared port address binding!")
            return True
        except Exception as e:
            print(f"Failed to clear port process: {e}")
            return False

def port_conflict_menu(default_port=8000):
    """Renders a CLI interactive option deck to resolve port collisions."""
    port = default_port
    while is_port_in_use(port):
        print("\n" + "="*60)
        print(f"⚠️  PORT CONFLICT: Socket address port {port} is already in use!")
        print("="*60)
        print("Please choose an option to resolve:")
        print("1) Stop the current process and start a new server")
        print("2) Start a new server on a different port")
        print("3) Open the GUI dashboard on the browser again")
        print("4) Cancel")
        print("="*60)
        
        try:
            choice = input("Enter choice (1-4): ").strip()
        except KeyboardInterrupt:
            print("\nOperation aborted.")
            sys.exit(0)
            
        if choice == '1':
            if kill_process_on_port(port):
                time.sleep(1.0)
                break
        elif choice == '2':
            try:
                new_port = input(f"Enter new port number (default: {port+1}): ").strip()
                if not new_port:
                    port = port + 1
                else:
                    port = int(new_port)
            except ValueError:
                print("Invalid port number. Try again.")
            except KeyboardInterrupt:
                print("\nOperation aborted.")
                sys.exit(0)
        elif choice == '3':
            url = f"http://localhost:{port}"
            print(f"Opening GUI dashboard: {url}")
            webbrowser.open(url)
        elif choice == '4':
            print("Operation aborted.")
            sys.exit(0)
        else:
            print("Invalid selection. Enter 1, 2, 3, or 4.")
            
    return port

def main():
    # Set up basic logging details
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    port = 8000
    if is_port_in_use(port):
        port = port_conflict_menu(port)
        
    logging.info(f"Starting LeapVisionController FastAPI Server on port {port}...")
    
    # Launch uvicorn web server
    uvicorn.run("src.core.server:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()
