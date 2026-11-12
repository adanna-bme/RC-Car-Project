
#include <SoftwareSerial.h>

// ===== HC-05 BLUETOOTH =====
// Arduino RX = D10
// Arduino TX = D11
SoftwareSerial BT(10, 11);

// ===== L298N MOTOR PINS =====
const int ENA = 5;
const int IN1 = 2;
const int IN2 = 4;

const int ENB = 6;
const int IN3 = 7;
const int IN4 = 8;

// ===== MOTOR SETTINGS =====
const int MOTOR_SPEED = 140;

// Stop if no valid movement command arrives within 700 ms.
const unsigned long TIMEOUT = 700;

bool carMoving = false;
char activeCommand = 'S';
unsigned long lastCommandTime = 0;

// ===== STOP MOTORS =====
void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  carMoving = false;
  activeCommand = 'S';
}

// ===== MOVE FORWARD =====
void moveForward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);

  carMoving = true;
}

// ===== MOVE BACKWARD =====
void moveBackward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);

  carMoving = true;
}

// Pivot turns assume motor A is on the left and motor B on the right.
// ===== TURN LEFT =====
void turnLeft() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);

  carMoving = true;
}

// ===== TURN RIGHT =====
void turnRight() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);

  carMoving = true;
}

// ===== SETUP =====
void setup() {
  // Configure motors
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();

  // Start serial communication
  Serial.begin(9600);
  BT.begin(9600);
}

// ===== MAIN LOOP =====
void loop() {

  // Read Bluetooth commands
  while (BT.available()) {
    char command = BT.read();

    if (command == 'F' || command == 'B' ||
        command == 'L' || command == 'R') {
      // Repeated direction commands are the controller's heartbeat.
      lastCommandTime = millis();

      if (command != activeCommand) {
        // Disable both motors before changing their direction pins.
        stopMotors();

        switch (command) {
          case 'F':
            moveForward();
            Serial.println("FORWARD");
            break;
          case 'B':
            moveBackward();
            Serial.println("BACKWARD");
            break;
          case 'L':
            turnLeft();
            Serial.println("LEFT");
            break;
          case 'R':
            turnRight();
            Serial.println("RIGHT");
            break;
        }

        activeCommand = command;
      }
    }

    else if (command == 'S') {
      stopMotors();
      Serial.println("STOP");
    }
  }

  // Automatic safety stop
  if (carMoving &&
      millis() - lastCommandTime > TIMEOUT) {

    stopMotors();
    Serial.println("SAFETY STOP: Signal timeout");
  }
}
