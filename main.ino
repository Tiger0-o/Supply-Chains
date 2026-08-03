#include <Arduino.h>

#define C4 262
#define D4 294
#define E4 330
#define F4 349
#define G4 392
#define A4 440
#define B4 494
#define C5 523

int varPin = A5;
int buzzerPin = 3;
int varChange = 0;
int ledPins[] = {D8, D9, D10, D11, D12, D13};

void setup () {
    pinMode(A0, INPUT_PULLUP);
    pinMode(A1, INPUT_PULLUP);
    pinMode(A2, INPUT_PULLUP);
    pinMode(A3, INPUT_PULLUP);
    pinMode(2, INPUT_PULLUP);
    pinMode(4, INPUT_PULLUP);
    pinMode(5, INPUT_PULLUP);
    pinMode(6, INPUT_PULLUP);

    for (int i = 0; i < 6; i++) {
        pinMode(ledPins[i], OUTPUT);
    }
    pinMode(buzzerPin, OUTPUT);
    pinMode(varPin, INPUT);
    Serial.begin(9600);
}

void loop() {
    varChange = analogRead(varPin);
    if (digitalRead(A0) == LOW) {
        tone(buzzerPin, C4 + varChange, 100);
        digitalWrite(ledPins[0], HIGH);
    } else if (digitalRead(A1) == LOW) {
        tone(buzzerPin, D4 + varChange, 100);
        digitalWrite(ledPins[1], HIGH);
    } else if (digitalRead(A2) == LOW) {
        tone(buzzerPin, E4 + varChange, 100);
        digitalWrite(ledPins[2], HIGH);
    } else if (digitalRead(A3) == LOW) {
        tone(buzzerPin, F4 + varChange, 100);
        digitalWrite(ledPins[3], HIGH);
    } else if (digitalRead(2) == LOW) {
        tone(buzzerPin, G4 + varChange, 100);
        digitalWrite(ledPins[4], HIGH);
    } else if (digitalRead(4) == LOW) {
        tone(buzzerPin, A4 + varChange, 100);
        digitalWrite(ledPins[5], HIGH);
    } else if (digitalRead(5) == LOW) {
        tone(buzzerPin, B4 + varChange, 100);
        digitalWrite(ledPins[6], HIGH);
    } else if (digitalRead(6) == LOW) {
        tone(buzzerPin, C5 + varChange, 100);
        digitalWrite(ledPins[7], HIGH);
    }
    delay(10)
    for (int i = 0; i < 6; i++) {
        digitalWrite(ledPins[i], LOW);
    }
}
