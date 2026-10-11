# Robotics Hardware Safety & Operational Disclaimer

> [!WARNING]
> **IMPORTANT SAFETY NOTICE:** Operating robotic mechanisms, high-torque servomotors, and high-voltage power supplies involves inherent physical risks. Read this disclaimer thoroughly prior to powering or commanding hardware.

---

## 1. Mechanical Hazards & Pinch Points

- Robotic arms, linkages, and end-effectors can accelerate rapidly without audible warning.
- **Maintain a Safe Perimeter**: Always keep hands, hair, clothing, and sensitive measurement tools outside the robot's physical reach envelope when the serial link is active or motor torque is engaged.
- **Pinch Points**: Multi-axis arm joints (e.g., shoulder, elbow, wrist linkages) produce significant clamping force capable of causing severe pinching or crushing injuries.

---

## 2. Electrical & Power Precautions

- Ensure all motor power supplies (12V–24V DC) are properly grounded and regulated.
- **Current Limiting**: Operate benchtop DC power supplies with current limits enabled (recommended: 3.0A max during initial testing) to mitigate sudden current spikes during motor stalls or unexpected load events.
- **Torque Cut (E-Stop)**: Familiarize yourself with emergency stop procedures. In the OSRS interface, press **`Alt + S`** or click the header **ESTOP** button to instantly release motor torque globally.

---

## 3. Simulation-First Testing Rule

Before deploying custom motion sequences, novel inverse kinematics trajectories, or experimental PID controller gains to physical hardware:

1. **Verify in Mock Mode**: Enable *Mock Mode* in the OSRS dashboard to simulate communication responses without physical bus transmission.
2. **Validate in MuJoCo Physics**: Launch the MuJoCo simulation environment (`simulation_ref/`) to test trajectory stability, singularity avoidance, and dynamic balance behavior in a simulated physics engine.
3. **Inspect Hardware Limits**: Check that configured software travel limits in `osrs_config.json` and robot profile definitions strictly match your physical linkage limits.

---

## 4. Limitation of Liability

THE SOFTWARE AND HARDWARE DESIGNS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. 

IN NO EVENT SHALL THE AUTHORS, CONTRIBUTORS, OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, LOSS OF EQUIPMENT, PERSONAL INJURY, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
