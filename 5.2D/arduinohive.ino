#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <Arduino_LSM6DS3.h>

// ===== Wi-Fi =====
const char* ssid     = "iPhone";        // your WiFi SSID
const char* password = "12345678";     // your WiFi password

// ===== HiveMQ Cloud (TLS) =====
const char* mqtt_server = "48dc58d1ec874196bad88e5cee2158b3.s1.eu.hivemq.cloud";
const int   mqtt_port   = 8883;   // TLS port
const char* mqtt_user   = "nano33";     // HiveMQ username (credential)
const char* mqtt_pass   = "Atharva1234"; // HiveMQ password (copy from console)
const char* mqtt_topic  = "gyro/data";  // publish topic

WiFiSSLClient sslClient;   // TLS client for WiFiNINA
PubSubClient  client(sslClient);

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("ArduinoNano33-01", mqtt_user, mqtt_pass)) {
      Serial.println("connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2 seconds");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }

  // Wi-Fi
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nWi-Fi connected. IP: ");
  Serial.println(WiFi.localIP());

  // MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setKeepAlive(30);
  client.setBufferSize(256);

  // IMU
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1) { delay(10); }
  }
  Serial.println("IMU initialized!");
}

void loop() {
  if (!client.connected()) connectMQTT();
  client.loop();

  float x, y, z;

  if (IMU.gyroscopeAvailable()) {
    IMU.readGyroscope(x, y, z);

    char message[128];
    snprintf(message, sizeof(message),
             "{\"x\": %.3f, \"y\": %.3f, \"z\": %.3f}", x, y, z);

    if (client.publish(mqtt_topic, message)) {
      Serial.print("Published: ");
      Serial.println(message);
    } else {
      Serial.println("Publish failed");
    }
  }

  delay(100); // send at ~10 Hz
}
