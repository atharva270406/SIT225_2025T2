#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Arduino_LSM6DS3.h>  // built-in IMU for Nano 33 IoT

// === WiFi Settings ===
const char* ssid     = "S23 FE";
const char* password = "Atharva1234";

// === MQTT Settings (HiveMQ) ===
const char* mqtt_server = "48dc58d1ec874196bad88e5cee2158b3.s1.eu.hivemq.cloud";
const int   mqtt_port   = 8883;
const char* mqtt_user   = "nano33";
const char* mqtt_pass   = "Atharva1234";
const char* mqtt_topic  = "gyro/data";  // must match Python subscriber

WiFiClientSecure espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  
  // Initialize IMU
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
  Serial.println("IMU initialized");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" ✅ Connected to WiFi");

  // Configure MQTT
  client.setServer(mqtt_server, mqtt_port);
  espClient.setInsecure(); // Accept HiveMQ TLS certificate
}

void loop() {
  // Reconnect if disconnected
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float x, y, z;

  // Read real accelerometer values
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(x, y, z);  // x, y, z in m/s^2

    // Build JSON
    StaticJsonDocument<200> doc;
    doc["x"] = x;
    doc["y"] = y;
    doc["z"] = z;

    char buffer[256];
    serializeJson(doc, buffer);

    // Publish to HiveMQ
    client.publish(mqtt_topic, buffer);
    Serial.print("Published: ");
    Serial.println(buffer);
  }

  delay(1000);  // publish every 1 second
}

// --- MQTT reconnect ---
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("arduino-client", mqtt_user, mqtt_pass)) {
      Serial.println(" ✅ Connected");
    } else {
      Serial.print(" ❌ Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2 seconds");
      delay(2000);
    }
  }
}
