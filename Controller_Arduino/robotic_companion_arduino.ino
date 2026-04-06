#include <Wire.h>
#include <U8g2lib.h>

#define BUTTON_PIN      7
#define SERVO_HEAD_PIN  9
#define SERVO_ARM1_PIN  10
#define SERVO_ARM2_PIN  11

#define HEAD_CENTER     90
#define HEAD_NOD_DOWN   65
#define ARM1_REST       90
#define ARM1_UP         45
#define ARM1_WAVE_A     60
#define ARM1_WAVE_B     120
#define ARM2_REST       90
#define ARM2_UP         45
#define ARM2_WAVE_A     60
#define ARM2_WAVE_B     120

U8G2_SH1106_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);

char buf[32];
char currentEmotion[12] = "neutral";

// ── SERVO ─────────────────────────────────────────────
void servoWrite(int pin, int degrees) {
  degrees = constrain(degrees, 0, 180);
  int pulseUs = map(degrees, 0, 180, 1000, 2000);
  for (int i = 0; i < 30; i++) {
    digitalWrite(pin, HIGH);
    delayMicroseconds(pulseUs);
    digitalWrite(pin, LOW);
    delayMicroseconds(20000 - pulseUs);
  }
}

// ── THICK LINE HELPER ─────────────────────────────────
// U8g2 has no lineWidth — draw N parallel lines for thickness
void thickLine(int x0, int y0, int x1, int y1, int t) {
  for (int i = -(t/2); i <= t/2; i++) {
    // Offset perpendicular to line direction
    bool steep = abs(y1-y0) > abs(x1-x0);
    if (steep) {
      oled.drawLine(x0+i, y0, x1+i, y1);
    } else {
      oled.drawLine(x0, y0+i, x1, y1+i);
    }
  }
}

// Thick filled ellipse outline — draw concentric ellipses
void thickEllipse(int cx, int cy, int rx, int ry, int t) {
  for (int i = 0; i < t; i++) {
    oled.drawEllipse(cx, cy, rx+i, ry+i);
  }
}

// ── FACE DRAWING ──────────────────────────────────────
void drawFace(const char* emotion, bool blink) {
  oled.clearBuffer();

  if (strcmp(emotion, "happy") == 0) {

    // Eyes — big filled discs with shine
    if (!blink) {
      oled.drawDisc(38, 24, 9);
      oled.drawDisc(90, 24, 9);
      // Shine dot (black cutout)
      oled.setDrawColor(0);
      oled.drawDisc(41, 21, 2);
      oled.drawDisc(93, 21, 2);
      oled.setDrawColor(1);
    } else {
      thickLine(28, 24, 48, 24, 4);
      thickLine(80, 24, 100, 24, 4);
    }

    // Big bold smile
    thickLine(28, 42, 34, 50, 4);
    thickLine(34, 50, 42, 55, 4);
    thickLine(42, 55, 52, 58, 4);
    thickLine(52, 58, 64, 59, 4);
    thickLine(64, 59, 76, 58, 4);
    thickLine(76, 58, 86, 55, 4);
    thickLine(86, 55, 94, 50, 4);
    thickLine(94, 50, 100, 42, 4);

  } else if (strcmp(emotion, "excited") == 0) {

    // Bold raised eyebrows
    thickLine(26, 10, 48, 5, 4);
    thickLine(80, 5, 102, 10, 4);

    // Big eyes
    if (!blink) {
      oled.drawDisc(38, 27, 10);
      oled.drawDisc(90, 27, 10);
      oled.setDrawColor(0);
      oled.drawDisc(42, 23, 3);
      oled.drawDisc(94, 23, 3);
      oled.setDrawColor(1);
    } else {
      thickLine(27, 27, 49, 27, 4);
      thickLine(79, 27, 101, 27, 4);
    }

    // Open oval mouth — thick outline
    thickEllipse(64, 50, 15, 9, 3);

  } else if (strcmp(emotion, "calm") == 0) {

    // Half-closed eyes
    if (!blink) {
      oled.drawDisc(38, 28, 8);
      oled.drawDisc(90, 28, 8);
      // Black eyelid over top half
      oled.setDrawColor(0);
      oled.drawBox(28, 18, 22, 11);
      oled.drawBox(80, 18, 22, 11);
      oled.setDrawColor(1);
      // Redraw bottom eyelid line thick
      thickLine(28, 29, 50, 29, 3);
      thickLine(80, 29, 102, 29, 3);
    } else {
      thickLine(28, 28, 50, 28, 4);
      thickLine(80, 28, 102, 28, 4);
    }

    // Gentle slight smile
    thickLine(40, 46, 52, 51, 3);
    thickLine(52, 51, 64, 52, 3);
    thickLine(64, 52, 76, 51, 3);
    thickLine(76, 51, 88, 46, 3);

  } else if (strcmp(emotion, "concerned") == 0) {

    // Worried inward brows — thick and angled
    thickLine(26, 12, 50, 20, 4);
    thickLine(78, 20, 102, 12, 4);

    // Eyes
    if (!blink) {
      oled.drawDisc(38, 31, 8);
      oled.drawDisc(90, 31, 8);
      oled.setDrawColor(0);
      oled.drawDisc(41, 28, 2);
      oled.drawDisc(93, 28, 2);
      oled.setDrawColor(1);
    } else {
      thickLine(28, 31, 48, 31, 4);
      thickLine(80, 31, 100, 31, 4);
    }

    // Bold frown
    thickLine(28, 56, 34, 47, 4);
    thickLine(34, 47, 42, 41, 4);
    thickLine(42, 41, 52, 38, 4);
    thickLine(52, 38, 64, 37, 4);
    thickLine(64, 37, 76, 38, 4);
    thickLine(76, 38, 86, 41, 4);
    thickLine(86, 41, 94, 47, 4);
    thickLine(94, 47, 100, 56, 4);

  } else {
    // neutral
    if (!blink) {
      oled.drawDisc(38, 26, 8);
      oled.drawDisc(90, 26, 8);
      oled.setDrawColor(0);
      oled.drawDisc(41, 23, 2);
      oled.drawDisc(93, 23, 2);
      oled.setDrawColor(1);
    } else {
      thickLine(28, 26, 48, 26, 4);
      thickLine(80, 26, 100, 26, 4);
    }
    // Double thick flat mouth
    thickLine(40, 46, 88, 46, 4);
  }

  oled.sendBuffer();
}

// ── BLINK ─────────────────────────────────────────────
unsigned long nextBlink = 0;
unsigned long blinkAt   = 0;
bool eyesOpen = true;

void updateBlink() {
  unsigned long now = millis();
  if (eyesOpen && now >= nextBlink) {
    eyesOpen = false;
    blinkAt  = now;
    drawFace(currentEmotion, true);
  } else if (!eyesOpen && now - blinkAt > 130) {
    eyesOpen = true;
    nextBlink = now + 2000 + random(2500);
    drawFace(currentEmotion, false);
  }
}

// ── SETUP ─────────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  delay(500);

  pinMode(SERVO_HEAD_PIN, OUTPUT);
  pinMode(SERVO_ARM1_PIN, OUTPUT);
  pinMode(SERVO_ARM2_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  servoWrite(SERVO_HEAD_PIN, HEAD_CENTER);
  servoWrite(SERVO_ARM1_PIN, ARM1_REST);
  servoWrite(SERVO_ARM2_PIN, ARM2_REST);

  Wire.begin();
  oled.begin();
  randomSeed(analogRead(0));
  nextBlink = 2500 + random(2000);

  strcpy(currentEmotion, "neutral");
  drawFace(currentEmotion, false);

  Serial.println("READY");
}

// ── LOOP ──────────────────────────────────────────────
void loop() {
  updateBlink();

  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("BUTTON PRESSED");
    delay(300);
  }

  if (Serial.available()) {
    memset(buf, 0, sizeof(buf));
    int len = Serial.readBytesUntil('\n', buf, sizeof(buf) - 1);
    if (len > 0 && buf[len-1] == '\r') { buf[len-1] = '\0'; len--; }
    if (len == 0) return;

    Serial.print("GOT: "); Serial.println(buf);

    if      (strcmp(buf, "happy") == 0)     { setEmotion("happy");     doGesture("nod");   }
    else if (strcmp(buf, "excited") == 0)   { setEmotion("excited");   doGesture("cheer"); }
    else if (strcmp(buf, "calm") == 0)      { setEmotion("calm");      doGesture("idle");  }
    else if (strcmp(buf, "neutral") == 0)   { setEmotion("neutral");   doGesture("idle");  }
    else if (strcmp(buf, "concerned") == 0) { setEmotion("concerned"); doGesture("nod");   }
    else if (strncmp(buf, "GESTURE:", 8) == 0) { doGesture(buf + 8); }
    else if (strncmp(buf, "SPEAK:", 6) == 0)   { setEmotion("happy"); }
    else if (strcmp(buf, "test") == 0)      { runHardwareTest(); }
    else if (strcmp(buf, "END") == 0)       { returnToRest(); setEmotion("neutral"); }
    else { Serial.print("UNKNOWN: "); Serial.println(buf); }
  }
}

void setEmotion(const char* emotion) {
  strncpy(currentEmotion, emotion, 11);
  currentEmotion[11] = '\0';
  eyesOpen = true;
  nextBlink = millis() + 2000 + random(2000);
  drawFace(currentEmotion, false);
  Serial.print("FACE: "); Serial.println(currentEmotion);
}

void doGesture(const char* gesture) {
  Serial.print("GESTURE: "); Serial.println(gesture);

  if (strcmp(gesture, "nod") == 0) {
    servoWrite(SERVO_HEAD_PIN, HEAD_NOD_DOWN); delay(100);
    servoWrite(SERVO_HEAD_PIN, HEAD_CENTER);   delay(100);
    servoWrite(SERVO_HEAD_PIN, HEAD_NOD_DOWN); delay(100);
    servoWrite(SERVO_HEAD_PIN, HEAD_CENTER);

  } else if (strcmp(gesture, "wave") == 0) {
    servoWrite(SERVO_ARM2_PIN, ARM2_WAVE_A); delay(100);
    servoWrite(SERVO_ARM2_PIN, ARM2_WAVE_B); delay(100);
    servoWrite(SERVO_ARM2_PIN, ARM2_WAVE_A); delay(100);
    servoWrite(SERVO_ARM2_PIN, ARM2_WAVE_B); delay(100);
    servoWrite(SERVO_ARM2_PIN, ARM2_REST);

  } else if (strcmp(gesture, "shake") == 0) {
    servoWrite(SERVO_ARM1_PIN, ARM1_WAVE_A);
    servoWrite(SERVO_ARM2_PIN, ARM2_WAVE_B); delay(100);
    servoWrite(SERVO_ARM1_PIN, ARM1_WAVE_B);
    servoWrite(SERVO_ARM2_PIN, ARM2_WAVE_A); delay(100);
    servoWrite(SERVO_ARM1_PIN, ARM1_WAVE_A);
    servoWrite(SERVO_ARM2_PIN, ARM2_WAVE_B); delay(100);
    servoWrite(SERVO_ARM1_PIN, ARM1_REST);
    servoWrite(SERVO_ARM2_PIN, ARM2_REST);

  } else if (strcmp(gesture, "cheer") == 0) {
    servoWrite(SERVO_ARM1_PIN, ARM1_UP);
    servoWrite(SERVO_ARM2_PIN, ARM2_UP);   delay(200);
    servoWrite(SERVO_ARM1_PIN, ARM1_REST);
    servoWrite(SERVO_ARM2_PIN, ARM2_REST); delay(100);
    servoWrite(SERVO_ARM1_PIN, ARM1_UP);
    servoWrite(SERVO_ARM2_PIN, ARM2_UP);   delay(200);
    servoWrite(SERVO_ARM1_PIN, ARM1_REST);
    servoWrite(SERVO_ARM2_PIN, ARM2_REST);

  } else if (strcmp(gesture, "point") == 0) {
    servoWrite(SERVO_ARM1_PIN, ARM1_UP);   delay(300);
    servoWrite(SERVO_ARM1_PIN, ARM1_REST);

  } else {
    returnToRest();
  }
}

void returnToRest() {
  servoWrite(SERVO_HEAD_PIN, HEAD_CENTER);
  servoWrite(SERVO_ARM1_PIN, ARM1_REST);
  servoWrite(SERVO_ARM2_PIN, ARM2_REST);
  Serial.println("REST");
}

void runHardwareTest() {
  Serial.println("TEST: starting...");
  const char* emos[] = {"happy","excited","calm","concerned","neutral"};
  for (int i = 0; i < 5; i++) {
    setEmotion(emos[i]);
    for (int b = 0; b < 2; b++) {
      delay(700);
      drawFace(currentEmotion, true);  delay(130);
      drawFace(currentEmotion, false);
    }
  }
  const char* gestures[] = {"nod","wave","shake","cheer","point"};
  for (int i = 0; i < 5; i++) {
    Serial.print("Testing: "); Serial.println(gestures[i]);
    doGesture(gestures[i]); delay(300);
  }
  returnToRest();
  setEmotion("neutral");
  Serial.println("TEST: complete");
}
