# C.H.I.M.A.N Servo Control Suite

A premium, high-performance desktop controller for Dynamixel Actuators (specifically fine-tuned for Humanoid V1 arms).

## ⚡ Quick Start

1. **Install Python 3.8+**
   Ensure Python is installed and added to your system path.

2. **Install Dependencies**
   Open a terminal/PowerShell in this directory and run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Connect Hardware**
   * Connect your U2D2 serial-to-USB adapter to your computer.
   * Connect your 12V DC power supply to the Dynamixel power hub board.
   * Ensure your servos are daisy-chained and plugged into the U2D2 adapter.

4. **Launch the Controller**
   Run the GUI using Python:
   ```bash
   python chiman_gui.py
   ```

## ⚙️ How to Use

1. **Configuration:**
   * Enter the active COM Port (e.g. `COM14` on Windows or `/dev/ttyUSB0` on Linux/macOS) in the sidebar.
   * Verify the Baud Rate is set to `4000000` (Universal universal baud rate for the servos).
   * Click **CONNECT BUS** to start scanning.

2. **Dashboard Overview:**
   * **Connection Info Card:** Shows active serial connection details.
   * **Active Nodes Card:** Shows count of online joints.
   * **Performance Latency Card:** Shows the real-time USB loop cycle time (in milliseconds).

3. **Controlling Joints:**
   * **Quick Navigation Tree (Left):** Jump directly to any group of joints (Left Arm, Right Arm, Head, General) by clicking the node.
   * **Joint Feeds (Right):**
     * **Telemetry Label:** Displays present read coordinates vs goal commands in real-time.
     * **Sliders:** Drag to rotate the joint.
     * **Fine-Tuning Buttons:** Step offsets of `-4k`, `-1k`, `0`, `+1k`, `+4k` for precise control.
     * **Entry Box:** Type an exact coordinate tick value and press **Enter** to apply.
     * **Torque Switch:** Toggle arming/disarming holding torque for each individual joint.
     * **Reboot Button:** If a servo experiences a mechanical shutdown/overload error, click **Reboot** to clear the fault packet.

4. **Preset Actions (Sidebar):**
   * **TORQUE ENABLED (ON):** Enables torque globally for all online joints.
   * **RELAX ALL (OFF):** Disables holding torque globally.
   * **GO TO BOTH ARMS POSE:** Commands both arms to go to home/starting poses simultaneously.
   * **LEFT POSE / RIGHT POSE:** Moves the respective arm to its calibrated starting offset pose.
   * **UP / centre / down:** Synchronizes movements between Left Forearm Yaw (L5) and Right Elbow Flex (R4) symmetrically.
   * **open / closed:** Opens or closes the left arm gripper.
   * **🚨 EMERGENCY E-STOP:** Instantly relaxes torque globally and terminates connection.

## 📂 File Directory

* `chiman_gui.py`: Main desktop control suite window.
* `dynamixel_driver.py`: Dynamixel Protocol 2.0 communication engine utilizing Sync Reads & Sync Writes.
* `requirements.txt`: Python package manifest.
* `README.md`: Setup and user instructions.
