#include <Wire.h>
#include <Adafruit_LiquidCrystal.h>
#include <ESP32Servo.h>

// ---------- PIN DEFINITIONS ----------
#define BUTTON_PIN 2
#define SERVO_PIN  3
#define SDA_PIN    4
#define SCL_PIN    5

// ---------- STATES ----------
#define STATE_IDLE 0
#define STATE_LISTENING 1

int robotState = STATE_IDLE;

// ---------- LCD & SERVO ----------
Adafruit_LiquidCrystal lcd(0);
Servo headServo;

void setup() {
  Serial.begin(115200);
  delay(1000);

  // ---------- I2C ----------
  Wire.begin(SDA_PIN, SCL_PIN);

  // ---------- SERVO ----------
  headServo.setPeriodHertz(50);      // Standard servo frequency
  headServo.attach(SERVO_PIN, 500, 2400);
  headServo.write(90);

  // ---------- LCD ----------
  lcd.begin(16, 2);
  lcd.setBacklight(1);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Robot Ready");

  // ---------- BUTTON ----------
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.println("Robotic Companion - ESP32-C3 Ready");

  delay(1000);
  showIdle();
}

void loop() {
  // ---------- BUTTON ----------
  if (digitalRead(BUTTON_PIN) == LOW && robotState == STATE_IDLE) {
    robotState = STATE_LISTENING;
    showListening();
    Serial.println("STATE → LISTENING");
    delay(300); // debounce
  }

  // ---------- SERIAL COMMANDS ----------
  if (robotState == STATE_LISTENING && Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.startsWith("EMOTION:")) {
      setEmotion(line.substring(8));
    }
    else if (line.startsWith("GESTURE:")) {
      doGesture(line.substring(8));
    }
    else if (line.startsWith("SPEAK:")) {
      speak(line.substring(6));
    }
    else if (line == "END") {
      robotState = STATE_IDLE;
      showIdle();
      Serial.println("STATE → IDLE");
    }
  }
}

// ==============================
// UI HELPERS
// ==============================

void showIdle() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Status:");
  lcd.setCursor(0, 1);
  lcd.print("IDLE");
}

void showListening() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Status:");
  lcd.setCursor(0, 1);
  lcd.print("LISTENING");
}

// ==============================
// ACTION FUNCTIONS
// ==============================

void setEmotion(String emotion) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Emotion:");

  lcd.setCursor(0, 1);

  if (emotion == "happy")       lcd.print(":) HAPPY");
  else if (emotion == "excited") lcd.print(":D EXCITED");
  else if (emotion == "concerned") lcd.print(":( CARE");
  else if (emotion == "calm")   lcd.print("- CALM -");
  else                          lcd.print(":| NEUTRAL");

  Serial.println("LCD → " + emotion);
}

void doGesture(String gesture) {
  if (gesture == "wave") {
    headServo.write(30); delay(300);
    headServo.write(150); delay(300);
    headServo.write(90);
  }
  else if (gesture == "nod") {
    headServo.write(60); delay(300);
    headServo.write(90);
  }
  else if (gesture == "shake") {
    headServo.write(70); delay(200);
    headServo.write(110); delay(200);
    headServo.write(90);
  }
  else {
    headServo.write(90);
  }

  Serial.println("SERVO → " + gesture);
}

void speak(String text) {
  Serial.println("AUDIO → " + text);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Speaking...");

  lcd.setCursor(0, 1);
  lcd.print(text.substring(0, 16));

  delay(1500);
  showListening();
}
