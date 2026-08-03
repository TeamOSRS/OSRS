# HX711 Moving Average Scale on Arduino Uno

This directory contains a PlatformIO project for an Arduino Uno interfacing with an HX711 load cell amplifier.

## Files
* [platformio.ini](file:///e:/Projects/OSRS/OSRS/LOAD%20CELL/platformio.ini) - PlatformIO configuration file.
* [src/main.cpp](file:///e:/Projects/OSRS/OSRS/LOAD%20CELL/src/main.cpp) - Arduino firmware with moving average.
* [serial_monitor.py](file:///e:/Projects/OSRS/OSRS/LOAD%20CELL/serial_monitor.py) - Python 3 serial monitor script.
* **[Hardware Wiring & Connection Guide](../docs/HARDWARE_CONNECTIONS.md)** - Complete wiring schematic, pinouts, and Wheatstone bridge wire colors.

---

## How to Find Your Zero Offset and Calibration Factor

Because every physical load cell and scale setup has slightly different characteristics, you must calibrate it to display exact weights.

### Step 1: Find the Zero Offset (Tare Value)
1. Open [src/main.cpp](file:///e:/Projects/OSRS/OSRS/LOAD%20CELL/src/main.cpp) and set the constants at the top to:
   ```cpp
   const long ZERO_OFFSET = 0L;
   const float CALIBRATION_FACTOR = 1.0f;
   ```
2. Upload this code to the Arduino.
3. Make sure the scale is **completely empty** (nothing placed on the load cell).
4. Run the Python serial monitor (`python "LOAD CELL/serial_monitor.py"`) and write down the value that is printed.
   * *Example: Let's say the monitor prints `142530.00`.*
5. This value is your **Zero Offset**. Update `ZERO_OFFSET` in [src/main.cpp](file:///e:/Projects/OSRS/OSRS/LOAD%20CELL/src/main.cpp#L15) with this number:
   ```cpp
   const long ZERO_OFFSET = 142530L; // Replace with your empty scale reading
   ```

### Step 2: Find the Calibration Factor
1. Upload the updated code (with your new `ZERO_OFFSET` set and `CALIBRATION_FACTOR` still set to `1.0f`).
2. The empty scale should now read close to `0.00` in the monitor.
3. Place an object of **known weight** on the scale (for example, a calibration weight, a coin, or any item whose exact mass you know, e.g., 500 grams).
4. Look at the reading printed in the serial monitor. Write this number down.
   * *Example: Placing a 500g weight prints `210000.00`.*
5. Calculate your calibration factor using this formula:
   $$\text{CALIBRATION\_FACTOR} = \frac{\text{Printed Reading}}{\text{Known Weight}}$$
   * *Example: $\frac{210000.00}{500} = 420.0$*
6. Update `CALIBRATION_FACTOR` in [src/main.cpp](file:///e:/Projects/OSRS/OSRS/LOAD%20CELL/src/main.cpp#L20) with this calculated value:
   ```cpp
   const float CALIBRATION_FACTOR = 420.0f; // Replace with your calculated factor
   ```
7. Re-upload the code. Your scale is now fully calibrated!

---

## Commands Reference

### Compile Firmware
```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -d "LOAD CELL"
```

### Upload Firmware
```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -d "LOAD CELL" --target upload
```

### Run Python Serial Monitor
```powershell
python "LOAD CELL/serial_monitor.py"
```
