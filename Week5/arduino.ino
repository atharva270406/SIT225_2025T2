#include <Arduino_LSM6DS3.h>

void setup() {
  Serial.begin(9600);
  while (!Serial); // Waiting for serial monitor
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
  Serial.println("Gyroscope initialized.");
}

void loop() {
  float x, y, z;

  if (IMU.gyroscopeAvailable()) {
    IMU.readGyroscope(x, y, z);
    
    // Print in format: x:val,y:val,z:val
    Serial.print("x:");
    Serial.print(x, 2);
    Serial.print(",y:");
    Serial.print(y, 2);
    Serial.print(",z:");
    Serial.println(z, 2);
  }

  delay(50); // ~20Hz sampling rate
}
