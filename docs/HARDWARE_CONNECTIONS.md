# HX711, Arduino, and Load Cell Hardware Wiring Guide

This document details the complete hardware connections, pinout tables, Wheatstone bridge wire color coding, and communication specs for interfacing dual/single **HX711 Load Cell Amplifiers** with an **Arduino (Uno/Nano)** in the OSRS force-sensing and ball balancer module.

---

## 🛠️ Hardware Components Required

| Component | Description / Specification | Quantity |
| :--- | :--- | :--- |
| **Arduino Microcontroller** | Arduino Uno R3, Nano, or compatible ATmega328P board | 1 |
| **HX711 Amplifier Module** | 24-Bit Analog-to-Digital Converter (ADC) for weigh scales | 2 (Left & Right) |
| **Strain Gauge Load Cell** | 4-wire Wheatstone bridge bar load cell (1kg / 5kg / 10kg) | 2 (Left & Right) |
| **Power Supply** | 5V DC via USB or External 5V Regulated Power Supply | 1 |
| **Jumper Wires & Breadboard** | Male-to-Female / Male-to-Male jumper cables | As needed |

---

## 🎨 1. Load Cell to HX711 Amplifier Wiring (Wheatstone Bridge)

Standard 4-wire and 5-wire strain gauge load cells connect to the HX711 terminal block as follows:

| Load Cell Wire Color | HX711 Terminal Pin | Function |
| :--- | :--- | :--- |
| 🔴 **Red** | **E+** (or VCC) | Excitation Positive (+5V to Wheatstone bridge) |
| 🖤 **Black** | **E-** (or GND) | Excitation Negative (Ground to Wheatstone bridge) |
| 🟢 **Green** | **A+** | Signal Output Positive (Differential +) |
| ⚪ **White** | **A-** | Signal Output Negative (Differential -) |
| 🟡 **Yellow / Bare** *(if present)* | **GND / SHIELD** | Electromagnetic Shielding Wire |

> [!NOTE]
> If your scale reads negative weights when a downward force is applied, swap the **Green (A+)** and **White (A-)** signal wires on the HX711 terminal.

---

## 🔌 2. HX711 Amplifier to Arduino Pinout

The OSRS dual-scale firmware ([`LOAD CELL/src/main.cpp`](file:///c:/Users/Adi/Downloads/OSRS/OSRS/OSRS/LOAD%20CELL/src/main.cpp)) reads both Left and Right load cells asynchronously over digital GPIO pins:

### Left Scale (HX711 #1)
| HX711 Pin | Arduino Pin | Wire / Function |
| :--- | :--- | :--- |
| **VCC** | **5V** | Power Supply (+5V DC) |
| **GND** | **GND** | Common Ground |
| **DT / DOUT** | **D2** | Data Line (Serial Data Out) |
| **SCK / CLK** | **D3** | Serial Clock Input |

### Right Scale (HX711 #2)
| HX711 Pin | Arduino Pin | Wire / Function |
| :--- | :--- | :--- |
| **VCC** | **5V** | Power Supply (+5V DC) |
| **GND** | **GND** | Common Ground |
| **DT / DOUT** | **D4** | Data Line (Serial Data Out) |
| **SCK / CLK** | **D5** | Serial Clock Input |

---

## ⚡ Complete System Schematic Overview

```
 +------------------------+              +-----------------------+              +-----------------------+
 |  Left Strain Gauge     |              |  HX711 Left Module    |              |     Arduino Uno       |
 |  (Load Cell #1)        |              |                       |              |                       |
 |                        |              |  E+ <--- 5V Power     |              |                       |
 |  Red (Excitation +)  --+------------->|  E+                   |              |                       |
 |  Black (Excitation -)+------------->|  E-                   |              |                       |
 |  Green (Signal +)   --+------------->|  A+                   |              |                       |
 |  White (Signal -)   --+------------->|  A-                   |              |                       |
 |                        |              |  VCC <----------------+--------------+-- 5V                  |
 |                        |              |  GND <----------------+--------------+-- GND                 |
 |                        |              |  DOUT --------------->+------------->|  Pin D2 (Left Data)   |
 |                        |              |  SCK  <---------------+--------------+-- Pin D3 (Left Clock)  |
 +------------------------+              +-----------------------+              |                       |
                                                                                |                       |
 +------------------------+              +-----------------------+              |                       |
 |  Right Strain Gauge    |              |  HX711 Right Module   |              |                       |
 |  (Load Cell #2)        |              |                       |              |                       |
 |                        |              |                       |              |                       |
 |  Red (Excitation +)  --+------------->|  E+                   |              |                       |
 |  Black (Excitation -)+------------->|  E-                   |              |                       |
 |  Green (Signal +)   --+------------->|  A+                   |              |                       |
 |  White (Signal -)   --+------------->|  A-                   |              |                       |
 |                        |              |  VCC <----------------+--------------+-- 5V                  |
 |                        |              |  GND <----------------+--------------+-- GND                 |
 |                        |              |  DOUT --------------->+------------->|  Pin D4 (Right Data)  |
 |                        |              |  SCK  <---------------+--------------+-- Pin D5 (Right Clock) |
 +------------------------+              +-----------------------+              +----------+------------+
                                                                                           |
                                                                                           v (USB Serial)
                                                                                  PC / OSRS Backend Server
                                                                                  Baud: 57600
```

---

## 📡 3. Serial Communication Protocol

- **Baud Rate**: `57600 baud`
- **Output Format**: ASCII Comma-Separated Values (`Left_Raw_Count,Right_Raw_Count\n`)
- **Sampling Frequency**: 50 Hz (transmits once every 20 milliseconds)
- **Example Data Stream**:
  ```text
  142530.00,138210.50
  142532.10,138211.00
  142529.80,138209.70
  ```

---

## ❓ Troubleshooting & Hardware Verification

1. **Floating Pins / Noise Errors**:
   - The Arduino firmware uses internal `INPUT_PULLUP` on DOUT pins (`pinMode(DOUT_PIN, INPUT_PULLUP)`) to prevent random floating data when a scale is disconnected.
2. **No Data Received**:
   - Ensure the correct COM port is selected in `osrs_config.json` or through the OSRS GUI.
   - Verify both HX711 VCC modules share a solid common ground with the Arduino.
3. **Inverted Force Readings**:
   - Swap the `A+` (Green) and `A-` (White) wires on the HX711 module.
