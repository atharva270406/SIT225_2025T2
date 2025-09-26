#ifndef thingProperties_h
#define thingProperties_h

#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>

// Cloud variables
String crashStatus;
float Accelerometer_X;
float Accelerometer_Y;
float Accelerometer_Z;

const char SSID[] = "iPhone";     // 🔧 Replace with your Wi-Fi name
const char PASS[] = "12345678"; // 🔧 Replace with your Wi-Fi password

void initProperties() {
  ArduinoCloud.addProperty(crashStatus, READWRITE, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(Accelerometer_X, READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(Accelerometer_Y, READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(Accelerometer_Z, READ, ON_CHANGE, NULL);
}

WiFiConnectionHandler ArduinoIoTPreferredConnection(SSID, PASS);

#endif
