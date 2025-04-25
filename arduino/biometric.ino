/**
 * Arduino Fingerprint Controller
 * Interfaces with R307 Fingerprint sensor and communicates with Python
 */

 #include <SoftwareSerial.h>
 #include <Adafruit_Fingerprint.h>
 
 // Pin definitions
 #define FINGERPRINT_RX 2
 #define FINGERPRINT_TX 3
 
 // Communication protocol constants
 #define CMD_ENROLL 'E'
 #define CMD_VERIFY 'V'
 #define CMD_DELETE 'D'
 #define CMD_COUNT  'C'
 #define CMD_EMPTY  'X'
 #define CMD_CHECK  'P'
 
 // Response codes
 #define RESP_OK    "OK"
 #define RESP_ERROR "ER"
 
 SoftwareSerial mySerial(FINGERPRINT_RX, FINGERPRINT_TX);
 Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);
 
 uint8_t lastId = 0;
 char command;
 uint16_t param;
 
 void setup() {
   Serial.begin(9600);
   mySerial.begin(57600);
   
   // Initialize fingerprint sensor
   if (!finger.verifyPassword()) {
     Serial.println("F:SENSOR_ERROR");
     while (1); // Stop if sensor not found
   }
   
   Serial.println("F:READY");
 }
 
 void loop() {
   // Check for commands from Python
   if (Serial.available() >= 2) {
     command = Serial.read();
     param = Serial.parseInt();
     
     processCommand(command, param);
   }
 }
 
 void processCommand(char cmd, uint16_t p) {
   switch (cmd) {
     case CMD_ENROLL:
       enrollFingerprint(p);
       break;
       
     case CMD_VERIFY:
       verifyFingerprint();
       break;
       
     case CMD_DELETE:
       deleteFingerprint(p);
       break;
       
     case CMD_COUNT:
       getTemplateCount();
       break;
       
     case CMD_EMPTY:
       emptyDatabase();
       break;
       
     case CMD_CHECK:
       checkSensor();
       break;
       
     default:
       Serial.println("F:INVALID_COMMAND");
       break;
   }
 }
 
 void enrollFingerprint(uint16_t id) {
   Serial.println("F:PLACE_FINGER");
   
   // Wait for finger to be placed
   int p = -1;
   while (p != FINGERPRINT_OK) {
     p = finger.getImage();
     if (p == FINGERPRINT_OK) {
       break;
     }
     delay(100);
   }
   
   // First image captured
   Serial.println("F:IMAGE_TAKEN");
   
   // Convert image to template
   p = finger.image2Tz(1);
   if (p != FINGERPRINT_OK) {
     Serial.println("F:CONVERT_ERROR");
     return;
   }
   
   Serial.println("F:REMOVE_FINGER");
   delay(2000);
   
   // Wait until finger is removed
   while (finger.getImage() != FINGERPRINT_NOFINGER) {
     delay(100);
   }
   
   Serial.println("F:PLACE_AGAIN");
   
   // Wait for finger placement again
   p = -1;
   while (p != FINGERPRINT_OK) {
     p = finger.getImage();
     if (p == FINGERPRINT_OK) {
       break;
     }
     delay(100);
   }
   
   // Second image captured
   Serial.println("F:IMAGE_TAKEN");
   
   // Convert second image
   p = finger.image2Tz(2);
   if (p != FINGERPRINT_OK) {
     Serial.println("F:CONVERT_ERROR");
     return;
   }
   
   // Create model from two images
   p = finger.createModel();
   if (p != FINGERPRINT_OK) {
     Serial.println("F:MODEL_ERROR");
     return;
   }
   
   // Store model in designated slot
   p = finger.storeModel(id);
   if (p == FINGERPRINT_OK) {
     Serial.print("F:ENROLLED:");
     Serial.println(id);
   } else {
     Serial.println("F:STORE_ERROR");
   }
 }
 
 void verifyFingerprint() {
   Serial.println("F:WAITING_FINGER");
   
   // Get image
   int p = -1;
   while (p != FINGERPRINT_OK) {
     p = finger.getImage();
     if (p == FINGERPRINT_OK) {
       break;
     }
     delay(100);
   }
   
   // Convert image
   p = finger.image2Tz();
   if (p != FINGERPRINT_OK) {
     Serial.println("F:CONVERT_ERROR");
     return;
   }
   
   // Search database
   p = finger.fingerSearch();
   if (p == FINGERPRINT_OK) {
     // Found a match
     Serial.print("F:MATCH:");
     Serial.println(finger.fingerID);
   } else {
     Serial.println("F:NO_MATCH");
   }
 }
 
 void deleteFingerprint(uint16_t id) {
   int p = finger.deleteModel(id);
   
   if (p == FINGERPRINT_OK) {
     Serial.print("F:DELETED:");
     Serial.println(id);
   } else {
     Serial.println("F:DELETE_ERROR");
   }
 }
 
 void getTemplateCount() {
   finger.getTemplateCount();
   Serial.print("F:COUNT:");
   Serial.println(finger.templateCount);
 }
 
 void emptyDatabase() {
   int p = finger.emptyDatabase();
   
   if (p == FINGERPRINT_OK) {
     Serial.println("F:DB_CLEARED");
   } else {
     Serial.println("F:CLEAR_ERROR");
   }
 }
 
 void checkSensor() {
   if (finger.verifyPassword()) {
     Serial.println("F:SENSOR_OK");
   } else {
     Serial.println("F:SENSOR_ERROR");
   }
 }