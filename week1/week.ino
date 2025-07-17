void setup() {
  Serial.begin(4800);               // Start serial communication
  pinMode(LED_BUILTIN, OUTPUT);    // Initialize LED pin
  randomSeed(analogRead(0));       // Seed for random()
}

void loop() {
  if (Serial.available() > 0) {
    int blinkCount = Serial.parseInt();  // Receiving a number from Python

    if (blinkCount > 0) {
      // Blink LED that many times (1-second interval)
      for (int i = 0; i < blinkCount; i++) {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(1000);
        digitalWrite(LED_BUILTIN, LOW);
        delay(1000);
      }

      // Send a random delay back to Python
      int delayTime = random(1, 6);
      Serial.println(delayTime);
    }
  }
}
