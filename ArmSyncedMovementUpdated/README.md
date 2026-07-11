# OSRS Cybernetic Servo Controller GUI

A premium, shareable graphical dashboard for the Open-Source Robotic System (OSRS), customized with quick target preset poses for the robotic arms and hand grip.

## Quick Target Presets Included
- **GO TO BOTH ARMS POSE**
- **LEFT POSE** & **RIGHT POSE**
- **UP** (`-150` on joint `L5Y`), **centre** (`-50`), and **down** (`50`)
- **open** (`-286` on joint `L8G`) & **closed** (`-685`)

## Setup Instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the GUI**:
   ```bash
   python gui.py
   ```

## File Structure
- `gui.py` - CustomTkinter application interface.
- `dynamixel_driver.py` - Protocol 2.0 Dynamixel servo controller driver.
