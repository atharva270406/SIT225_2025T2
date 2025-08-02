#include "thingProperties.h"
#include <Arduino_LSM6DS3.h>

void setup() {
  Serial.begin(9600);
  delay(1500);

  initProperties();
  ArduinoCloud.begin(ArduinoIoTPreferredConnection);

  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  if (!IMU.begin()) {
    Serial.println("IMU initialization failed!");
    while (true);
  }

  Serial.println("IMU successfully initialized.");
}

void loop() {
  ArduinoCloud.update();

  float accel_x, accel_y, accel_z;

  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(accel_x, accel_y, accel_z);

    accelX = accel_x;
    accelY = accel_y;
    accelZ = accel_z;

    Serial.print("Accel X: "); Serial.print(accel_x, 3);
    Serial.print(" | Y: "); Serial.print(accel_y, 3);
    Serial.print(" | Z: "); Serial.println(accel_z, 3);
  }

  delay(500);
}

void onAccelXChange() {
  Serial.println("Cloud variable accelX updated.");
}

void onAccelYChange() {
  Serial.println("Cloud variable accelY updated.");
}

void onAccelZChange() {
  Serial.println("Cloud variable accelZ updated.");
}
