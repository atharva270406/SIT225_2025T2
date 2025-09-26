#include "thingProperties.h"
#include <Arduino_LSM6DS3.h>  // IMU library for Nano 33 IoT

void setup() {
  Serial.begin(9600);
  delay(1500);

  initProperties();
  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(0);  // Suppress MQTT debug messages

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
}

void loop() {
  ArduinoCloud.update();

  float x, y, z;
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(x, y, z);

    Accelerometer_X = x;
    Accelerometer_Y = y;
    Accelerometer_Z = z;

    float linearAccel = sqrt(x * x + y * y + z * z);

    if (linearAccel > 20) {
      crashStatus = "Crash Detected";
    } else if (linearAccel > 10) {
      crashStatus = "Sudden Movement";
    } else {
      crashStatus = "Normal";
    }

    // Structured Serial output for CSV logging
    Serial.print("Timestamp: ");
    Serial.print(millis());
    Serial.print(", X: ");
    Serial.print(x, 2);
    Serial.print(", Y: ");
    Serial.print(y, 2);
    Serial.print(", Z: ");
    Serial.print(z, 2);
    Serial.print(", Status: ");
    Serial.println(crashStatus);
  }

  delay(500);
}
