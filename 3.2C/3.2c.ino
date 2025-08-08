#include "thingProperties.h"
#include <Arduino_LSM6DS3.h>
#include <math.h>

void setup() {
  Serial.begin(9600);
  delay(3000);  // 3-second delay at startup
  initProperties();  // initializes cloud properties
  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
}

void loop() {
  float x, y, z;
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(x, y, z);
    float magnitude = sqrt(x * x + y * y + z * z);

    Serial.print("X: "); Serial.print(x, 3);
    Serial.print(" Y: "); Serial.print(y, 3);
    Serial.print(" Z: "); Serial.print(z, 3);
    Serial.print(" | Magnitude: "); Serial.println(magnitude, 3);

    if (magnitude > 1.2) {   // lower threshold for sensitivity
      alarmShake = true;
      alarmStatus = "WARNING: Vibration Detected!";
    } else {
      alarmShake = false;
      alarmStatus = "OFF";
    }

    ArduinoCloud.update();
  }

  delay(1000);
}

void onResetAlarmChange() {
  if (resetAlarm) {
    alarmShake = false;
    alarmStatus = "OK";
    resetAlarm = false;
  }
}
