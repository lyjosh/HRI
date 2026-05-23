#include <Servo.h>

const int NUM_PINS = 6;

Servo servos[NUM_PINS];
int servoPins[NUM_PINS] = {3, 5, 6, 9, 10, 11};
int values[NUM_PINS];

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < NUM_PINS; i++) {
    servos[i].attach(servoPins[i]);
  }
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    parseValues(line);
    updateServos();
  }
}

void parseValues(String line) {
  int index = 0;
  int start = 0;

  while (index < NUM_PINS) {
    int commaIndex = line.indexOf(',', start);

    String valueStr;
    if (commaIndex == -1) {
      valueStr = line.substring(start);
    } else {
      valueStr = line.substring(start, commaIndex);
    }

    values[index] = valueStr.toInt();
    index++;

    if (commaIndex == -1) {
      break;
    }

    start = commaIndex + 1;
  }
}

void updateServos() {
  for (int i = 0; i < NUM_PINS; i++) {
    if (values[i] == 0) {
      servos[i].write(0);
    } else if (values[i] == 1) {
      servos[i].write(90);
    } else {
      servos[i].write(180);
    }
  }
}