#include <Arduino.h>

// ==========================================
// Hardware Configuration (Pins from LOAD CELL)
// ==========================================
const int DOUT_PIN_L = 2; // Left scale data pin
const int SCK_PIN_L = 3;  // Left scale clock pin
const int DOUT_PIN_R = 4; // Right scale data pin
const int SCK_PIN_R = 5;  // Right scale clock pin

// ==========================================
// Filtering Configuration
// ==========================================
const int WINDOW_SIZE = 10;
long circularBufferL[WINDOW_SIZE];
long circularBufferR[WINDOW_SIZE];
int bufferIndex = 0;
long long runningSumL = 0;
long long runningSumR = 0;
bool isBufferInitializedL = false;
bool isBufferInitializedR = false;

// Output rate: 50 Hz (once every 20ms) for real-time control loops
unsigned long lastPrintTime = 0;
const unsigned long PRINT_INTERVAL_MS = 20;

void setup() {
  Serial.begin(57600);
  
  // Initialize scale pins with internal pullups for DOUT to prevent floating noise
  pinMode(DOUT_PIN_L, INPUT_PULLUP);
  pinMode(SCK_PIN_L, OUTPUT);
  pinMode(DOUT_PIN_R, INPUT_PULLUP);
  pinMode(SCK_PIN_R, OUTPUT);
  
  // Set SCK low
  digitalWrite(SCK_PIN_L, LOW);
  digitalWrite(SCK_PIN_R, LOW);
}

// 100% Non-blocking raw read for HX711
long read_hx711_raw(int dout, int sck) {
  // If DOUT is HIGH, the chip is not ready (or disconnected). Return 0 immediately.
  if (digitalRead(dout) == HIGH) {
    return 0;
  }

  unsigned long value = 0;
  
  // Shift in 24 bits
  for (int i = 0; i < 24; i++) {
    digitalWrite(sck, HIGH);
    delayMicroseconds(1);
    value = (value << 1) | digitalRead(dout);
    digitalWrite(sck, LOW);
    delayMicroseconds(1);
  }

  // Set gain to 128 (1 pulse) for next reading
  digitalWrite(sck, HIGH);
  delayMicroseconds(1);
  digitalWrite(sck, LOW);
  delayMicroseconds(1);

  // Sign extension for 24-bit two's complement to 32-bit signed long
  if (value & 0x800000) {
    value |= 0xFF000000;
  }
  
  return (long)value;
}

void loop() {
  // Sample Left Scale
  long rawL = read_hx711_raw(DOUT_PIN_L, SCK_PIN_L);
  if (rawL != 0) {
    if (!isBufferInitializedL) {
      for (int i = 0; i < WINDOW_SIZE; i++) {
        circularBufferL[i] = rawL;
      }
      runningSumL = (long long)rawL * WINDOW_SIZE;
      isBufferInitializedL = true;
    } else {
      runningSumL -= circularBufferL[bufferIndex];
      circularBufferL[bufferIndex] = rawL;
      runningSumL += rawL;
    }
  }

  // Sample Right Scale
  long rawR = read_hx711_raw(DOUT_PIN_R, SCK_PIN_R);
  if (rawR != 0) {
    if (!isBufferInitializedR) {
      for (int i = 0; i < WINDOW_SIZE; i++) {
        circularBufferR[i] = rawR;
      }
      runningSumR = (long long)rawR * WINDOW_SIZE;
      isBufferInitializedR = true;
    } else {
      runningSumR -= circularBufferR[bufferIndex];
      circularBufferR[bufferIndex] = rawR;
      runningSumR += rawR;
    }
  }

  // Always increment the circular buffer index to keep values moving
  bufferIndex = (bufferIndex + 1) % WINDOW_SIZE;

  // Periodic transmission at 50Hz
  unsigned long currentMillis = millis();
  if (currentMillis - lastPrintTime >= PRINT_INTERVAL_MS) {
    lastPrintTime = currentMillis;
    
    double avgL = isBufferInitializedL ? ((double)runningSumL / WINDOW_SIZE) : 0.0;
    double avgR = isBufferInitializedR ? ((double)runningSumR / WINDOW_SIZE) : 0.0;
    
    // Comma-separated counts: Left,Right
    Serial.print(avgL, 2);
    Serial.print(",");
    Serial.println(avgR, 2);
  }
}
