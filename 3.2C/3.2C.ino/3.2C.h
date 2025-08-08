#ifndef THINGPROPERTIES_H
#define THINGPROPERTIES_H

#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>

void onResetAlarmChange();

const char SSID[] = "iPhone";
const char PASS[] = "12345678";

// Use correct Arduino IoT Cloud types
CloudBool alarmShake;
CloudString alarmStatus;
CloudBool resetAlarm;

void initProperties() {
  ArduinoCloud.addProperty(alarmShake, READWRITE, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(alarmStatus, READWRITE, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(resetAlarm, READWRITE, ON_CHANGE, onResetAlarmChange);
}

WiFiConnectionHandler ArduinoIoTPreferredConnection(SSID, PASS);

#endif
