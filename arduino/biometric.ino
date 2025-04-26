#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(2, 3); // RX, TX
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

void setup() {
  Serial.begin(9600);
  while (!Serial);

  finger.begin(57600);

  if (finger.verifyPassword()) {
    Serial.println("Fingerprint sensor found");
  } else {
    Serial.println("Sensor not found");
    while (1);
  }
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'S') { // Scan fingerprint
      int fingerprintID = getFingerprintID();
      Serial.print("ID:");
      Serial.println(fingerprintID);
    }
    else if (command == 'E') { // Enroll new fingerprint
      enrollFingerprint();
    }
  }
}

int getFingerprintID() {
  int p = finger.getImage();
  if (p != FINGERPRINT_OK) return -1;

  p = finger.image2Tz();
  if (p != FINGERPRINT_OK) return -1;

  p = finger.fingerFastSearch();
  if (p != FINGERPRINT_OK) return -1;

  return finger.fingerID;
}

void enrollFingerprint() {
  int id = Serial.parseInt();
  int p = -1;

  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
  }

  p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) return;

  // Remove finger and get second image
  delay(2000);
  p = 0;
  while (p != FINGERPRINT_NOFINGER) {
    p = finger.getImage();
  }

  p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
  }

  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) return;

  p = finger.createModel();
  if (p != FINGERPRINT_OK) return;

  p = finger.storeModel(id);
  if (p != FINGERPRINT_OK) return;

  Serial.println("Enrolled successfully!");
}