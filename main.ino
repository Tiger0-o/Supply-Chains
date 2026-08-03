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
int varVar = 0;

void setup () {
    pinMode(A0, INPUT_PULLUP);
    pinMode(A1, INPUT_PULLUP);
    pinMode(A2, INPUT_PULLUP);
    pinMode(A3, INPUT_PULLUP);
    pinMode(2, INPUT_PULLUP);
    pinMode(4, INPUT_PULLUP);
    pinMode(5, INPUT_PULLUP);
    pinMode(6, INPUT_PULLUP);
    
    pinMode(buzzerPin, OUTPUT);
    pinMode(varPin, INPUT);
}

void loop() {
    if (digitalRead(A0) == LOW) {
        tone(buzzerPin, C4 + varVar, 100);
    } else if (digitalRead(A1) == LOW) {
        tone(buzzerPin, D4 + varVar, 100);
    } else if (digitalRead(A2) == LOW) {
        tone(buzzerPin, E4 + varVar, 100);
    } else if (digitalRead(A3) == LOW) {
        tone(buzzerPin, F4 + varVar, 100);
    } else if (digitalRead(2) == LOW) {
        tone(buzzerPin, G4 + varVar, 100);
    } else if (digitalRead(4) == LOW) {
        tone(buzzerPin, A4 + varVar, 100);
    } else if (digitalRead(5) == LOW) {
        tone(buzzerPin, B4 + varVar, 100);
    } else if (digitalRead(6) == LOW) {
        tone(buzzerPin, C5 + varVar, 100);
    }
}
