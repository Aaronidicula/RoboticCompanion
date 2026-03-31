#include <Wire.h>
#include <Adafruit_LiquidCrystal.h>
#include <Servo.h>

#define BUTTON_PIN 7

#define STATE_IDLE 0
#define STATE_LISTENING 1

int robotState = STATE_IDLE;


// MCP23008-based LCD
Adafruit_LiquidCrystal lcd(0);
Servo headServo;

void setup() {
  Serial.begin(9600);

  // Servo
  headServo.attach(9);
  headServo.write(90); // center position

  // LCD
  lcd.begin(16, 2);
  lcd.setBacklight(1);

  lcd.setCursor(0, 0);
  lcd.print("Robot Ready");

  Serial.println("Robotic Companion - Arduino Ready");
  
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Status:");
  lcd.setCursor(0, 1);
  lcd.print("IDLE");

}

void loop() {
  // ---------- BUTTON CHECK ----------
  if (digitalRead(BUTTON_PIN) == LOW && robotState == STATE_IDLE) {
    robotState = STATE_LISTENING;
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Status:");
    
    lcd.setCursor(0, 1);
    lcd.print("LISTENING");

    Serial.println("STATE → LISTENING");
    delay(300); // debounce
  }
  if (robotState == STATE_LISTENING && Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.startsWith("EMOTION:")) {
      String emotion = line.substring(8);
      setEmotion(emotion);
    }
    else if (line.startsWith("GESTURE:")) {
      String gesture = line.substring(8);
      doGesture(gesture);
    }
    else if (line.startsWith("SPEAK:")) {
      String speech = line.substring(6);
      speak(speech);
    }
    else if (line == "END") {
      robotState = STATE_IDLE;
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Status:");
      lcd.setCursor(0, 1);
      lcd.print("IDLE");
      
      Serial.println("STATE → IDLE");
    }
  }
}

// ---------- ACTION FUNCTIONS ----------

void setEmotion(String emotion) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Emotion:");

  lcd.setCursor(0, 1);

  if (emotion == "happy") {
    lcd.print(":) HAPPY");
  }
  else if (emotion == "excited") {
    lcd.print(":D EXCITED");
  }
  else if (emotion == "concerned") {
    lcd.print(":( CARE");
  }
  else if (emotion == "calm") {
    lcd.print("- CALM -");
  }
  else {
    lcd.print(":| NEUTRAL");
  }

  Serial.print("LCD → ");
  Serial.println(emotion);
}

void doGesture(String gesture) {
  if (gesture == "wave") {
    headServo.write(30);
    delay(300);
    headServo.write(150);
    delay(300);
    headServo.write(90);
  }
  else if (gesture == "nod") {
    headServo.write(60);
    delay(300);
    headServo.write(90);
  }
  else if (gesture == "shake") {
    headServo.write(70);
    delay(200);
    headServo.write(110);
    delay(200);
    headServo.write(90);
  }
  else {
    headServo.write(90);
  }

  Serial.print("SERVO → ");
  Serial.println(gesture);
}

void speak(String text) {
  Serial.print("AUDIO → ");
  Serial.println(text);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Speaking...");

  lcd.setCursor(0, 1);
  if (text.length() > 16) {
    lcd.print(text.substring(0, 16));
  } else {
    lcd.print(text);
  }

  delay(1500);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Status:");
  lcd.setCursor(0, 1);
  lcd.print("LISTENING");
}



