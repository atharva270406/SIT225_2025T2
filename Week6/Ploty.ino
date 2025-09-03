#include <Arduino_LSM6DS3.h>

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (true) { ; }
  }
}

void loop() {
  float gx = 0.0, gy = 0.0, gz = 0.0;

  if (IMU.gyroscopeAvailable()) {
    IMU.readGyroscope(gx, gy, gz);

    Serial.print(millis());
    Serial.print(',');
    Serial.print(gx);
    Serial.print(',');
    Serial.print(gy);
    Serial.print(',');
    Serial.println(gz);
  }

  delay(100);
}
