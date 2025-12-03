/*
  YOLOv11 Arduino Firebase Bridge with Servo Control
  รวม Servo motor สำหรับปัดขวดเข้ากับระบบ YOLOv11
  
  Hardware Requirements:
  - Arduino R4 WiFi
  - Servo Motor (Pin 9)
  - LED (Pin 13 - built-in)
  - Buzzer (Pin 8)
  - Optional: External LED (Pin 12)
  
  Communication:
  - Serial: 9600 baud
  - Commands: "90" = bottle detected, "0" = no bottle
  - Servo Commands: "SERVO:angle" (0-180)
  
  Author: P2P Team
  Version: 3.1 (YOLOv11 + Servo Edition)
*/

#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <Servo.h>

// ========================================
// Pin Definitions
// ========================================
const int LED_BUILTIN_PIN = 13;  // Built-in LED
const int BUZZER_PIN = 8;        // Buzzer
const int EXTERNAL_LED_PIN = 12; // External LED (optional)
const int SERVO_PIN = 9;         // Servo motor

// ========================================
// WiFi Configuration
// ========================================
const char* ssid = "YOUR_WIFI_SSID";        // เปลี่ยนเป็น WiFi ของคุณ
const char* password = "YOUR_WIFI_PASSWORD"; // เปลี่ยนเป็นรหัสผ่าน WiFi

// ========================================
// Firebase Configuration
// ========================================
const char* firebase_host = "takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app";
const int firebase_port = 443;
const char* firebase_path = "/arduino_data/yolo_v11_servo_device.json";

// ========================================
// Global Variables
// ========================================
WiFiSSLClient wifi;
HttpClient client = HttpClient(wifi, firebase_host, firebase_port);
Servo bottleServo;

int bottle_count = 0;
int total_points = 0;
const int POINTS_PER_BOTTLE = 10;

bool detection_state = false;
bool last_detection_state = false;
unsigned long last_detection_time = 0;
unsigned long last_firebase_update = 0;
unsigned long last_status_print = 0;
unsigned long last_servo_action = 0;

const unsigned long DETECTION_COOLDOWN = 2000;     // 2 seconds
const unsigned long FIREBASE_UPDATE_INTERVAL = 5000;  // 5 seconds
const unsigned long STATUS_PRINT_INTERVAL = 10000;    // 10 seconds
const unsigned long SERVO_ACTION_DELAY = 1000;        // 1 second delay for servo action

// Servo positions
const int SERVO_REST_POSITION = 90;    // ตำแหน่งพัก
const int SERVO_SWEEP_POSITION = 45;   // ตำแหน่งปัดขวด
const int SERVO_RETURN_POSITION = 135; // ตำแหน่งกลับ

String inputString = "";  // สำหรับรับคำสั่ง Serial

// ========================================
// Setup Function
// ========================================
void setup() {
  // Initialize Serial
  Serial.begin(9600);
  while (!Serial) {
    delay(10);
  }
  
  Serial.println("🚀 YOLOv11 Arduino Firebase Bridge v3.1 (Servo Edition)");
  Serial.println("🤖 P2P (Plastic to Point) Detection System with Servo Control");
  Serial.println("===============================================================");
  
  // Initialize pins
  pinMode(LED_BUILTIN_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(EXTERNAL_LED_PIN, OUTPUT);
  
  // Initialize servo
  bottleServo.attach(SERVO_PIN);
  bottleServo.write(SERVO_REST_POSITION);
  Serial.println("🔧 Servo initialized at rest position (90°)");
  
  // Test hardware
  testHardware();
  
  // Connect to WiFi
  connectToWiFi();
  
  Serial.println("✅ Arduino ready for YOLOv11 commands!");
  Serial.println("📡 Waiting for Python detection signals...");
  Serial.println("Commands:");
  Serial.println("  '90' = bottle detected");
  Serial.println("  '0' = no bottle");
  Serial.println("  'SERVO:angle' = move servo to angle (0-180)");
  Serial.println("  'SWEEP' = perform bottle sweep action");
  Serial.println("  'reset' = reset counter");
  Serial.println("  'status' = show status");
  Serial.println("===============================================================");
}

// ========================================
// Main Loop
// ========================================
void loop() {
  // Check for serial commands from Python
  checkSerialCommands();
  
  // Update Firebase periodically
  updateFirebasePeriodically();
  
  // Print status periodically
  printStatusPeriodically();
  
  // Small delay
  delay(50);
}

// ========================================
// Serial Communication Functions
// ========================================
void checkSerialCommands() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      inputString.trim();
      processCommand(inputString);
      inputString = "";
    } else {
      inputString += c;
    }
  }
}

void processCommand(String command) {
  if (command == "90") {
    handleBottleDetected();
  } else if (command == "0") {
    handleNoBottle();
  } else if (command == "reset") {
    resetCounter();
  } else if (command == "status") {
    printDetailedStatus();
  } else if (command == "SWEEP") {
    performBottleSweep();
  } else if (command.startsWith("SERVO:")) {
    // Extract angle from command
    int angle = command.substring(6).toInt();
    if (angle >= 0 && angle <= 180) {
      moveServoToAngle(angle);
    } else {
      Serial.println("❌ Invalid servo angle. Use 0-180.");
    }
  } else {
    // Try to parse as direct angle (for compatibility)
    int angle = command.toInt();
    if (angle >= 0 && angle <= 180 && command.length() > 0) {
      moveServoToAngle(angle);
    } else {
      Serial.println("❓ Unknown command: " + command);
      Serial.println("💡 Available commands: 90, 0, SERVO:angle, SWEEP, reset, status");
    }
  }
}

void handleBottleDetected() {
  unsigned long current_time = millis();
  
  // Prevent rapid duplicate detections
  if (current_time - last_detection_time < DETECTION_COOLDOWN) {
    return;
  }
  
  detection_state = true;
  
  // Only count if this is a new detection
  if (!last_detection_state) {
    bottle_count++;
    total_points = bottle_count * POINTS_PER_BOTTLE;
    last_detection_time = current_time;
    
    Serial.println("🍼 Bottle detected! Count: " + String(bottle_count) + ", Points: " + String(total_points));
    
    // Activate indicators
    activateIndicators();
    
    // Perform bottle sweep action
    performBottleSweep();
    
    // Send to Firebase immediately
    sendToFirebase("detection");
  }
  
  last_detection_state = true;
}

void handleNoBottle() {
  detection_state = false;
  
  if (last_detection_state) {
    // Turn off indicators
    deactivateIndicators();
    Serial.println("👁️ No bottle detected");
  }
  
  last_detection_state = false;
}

void resetCounter() {
  bottle_count = 0;
  total_points = 0;
  detection_state = false;
  last_detection_state = false;
  
  deactivateIndicators();
  
  // Return servo to rest position
  bottleServo.write(SERVO_REST_POSITION);
  
  Serial.println("🔄 Counter reset! Servo returned to rest position.");
  sendToFirebase("reset");
}

// ========================================
// Servo Control Functions
// ========================================
void moveServoToAngle(int angle) {
  bottleServo.write(angle);
  Serial.println("🔧 Servo moved to: " + String(angle) + "°");
  
  // Update Firebase with servo position
  sendServoDataToFirebase(angle);
}

void performBottleSweep() {
  unsigned long current_time = millis();
  
  // Prevent too frequent servo actions
  if (current_time - last_servo_action < SERVO_ACTION_DELAY) {
    return;
  }
  
  Serial.println("🧹 Performing bottle sweep sequence...");
  
  // Sweep sequence: Rest → Sweep → Return → Rest
  bottleServo.write(SERVO_SWEEP_POSITION);
  delay(500);
  
  bottleServo.write(SERVO_RETURN_POSITION);
  delay(500);
  
  bottleServo.write(SERVO_REST_POSITION);
  
  Serial.println("✅ Bottle sweep completed!");
  last_servo_action = current_time;
  
  // Send sweep action to Firebase
  sendToFirebase("bottle_sweep");
}

void testServo() {
  Serial.println("🔧 Testing servo motor...");
  
  // Test sequence
  int testPositions[] = {0, 45, 90, 135, 180, 90};
  int numPositions = sizeof(testPositions) / sizeof(testPositions[0]);
  
  for (int i = 0; i < numPositions; i++) {
    bottleServo.write(testPositions[i]);
    Serial.println("   Servo at " + String(testPositions[i]) + "°");
    delay(500);
  }
  
  Serial.println("✅ Servo test completed");
}

// ========================================
// Hardware Control Functions
// ========================================
void activateIndicators() {
  // Turn on LEDs
  digitalWrite(LED_BUILTIN_PIN, HIGH);
  digitalWrite(EXTERNAL_LED_PIN, HIGH);
  
  // Buzzer beep pattern
  for (int i = 0; i < 2; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
    delay(100);
  }
}

void deactivateIndicators() {
  digitalWrite(LED_BUILTIN_PIN, LOW);
  digitalWrite(EXTERNAL_LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void testHardware() {
  Serial.println("🔧 Testing hardware...");
  
  // Test LEDs
  digitalWrite(LED_BUILTIN_PIN, HIGH);
  digitalWrite(EXTERNAL_LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN_PIN, LOW);
  digitalWrite(EXTERNAL_LED_PIN, LOW);
  
  // Test buzzer
  digitalWrite(BUZZER_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZER_PIN, LOW);
  
  // Test servo
  testServo();
  
  Serial.println("✅ Hardware test completed");
}

// ========================================
// WiFi Functions
// ========================================
void connectToWiFi() {
  Serial.println("🌐 Connecting to WiFi...");
  Serial.println("SSID: " + String(ssid));
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected!");
    Serial.println("📡 IP address: " + WiFi.localIP().toString());
    Serial.println("📶 Signal strength: " + String(WiFi.RSSI()) + " dBm");
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
    Serial.println("💡 Please check SSID and password");
  }
}

// ========================================
// Firebase Functions
// ========================================
void sendToFirebase(String action) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected, skipping Firebase update");
    return;
  }
  
  // Create JSON data
  StaticJsonDocument<300> doc;
  doc["bottle_count"] = bottle_count;
  doc["total_points"] = total_points;
  doc["detection_state"] = detection_state;
  doc["device"] = "arduino_yolo_v11_servo";
  doc["action"] = action;
  doc["timestamp"] = millis();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["servo_position"] = bottleServo.read();
  doc["has_servo"] = true;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send HTTP PUT request
  client.beginRequest();
  client.put(firebase_path);
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", jsonString.length());
  client.beginBody();
  client.print(jsonString);
  client.endRequest();
  
  // Read response
  int statusCode = client.responseStatusCode();
  String response = client.responseBody();
  
  if (statusCode == 200) {
    Serial.println("✅ Firebase: Data sent (" + action + ")");
  } else {
    Serial.println("❌ Firebase error: " + String(statusCode));
  }
}

void sendServoDataToFirebase(int angle) {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  
  // Create JSON data for servo position
  StaticJsonDocument<200> doc;
  doc["servo_angle"] = angle;
  doc["device"] = "arduino_yolo_v11_servo";
  doc["action"] = "servo_move";
  doc["timestamp"] = millis();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send to servo-specific path
  String servo_path = "/servo_data/yolo_v11_servo_device.json";
  
  client.beginRequest();
  client.put(servo_path);
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", jsonString.length());
  client.beginBody();
  client.print(jsonString);
  client.endRequest();
  
  int statusCode = client.responseStatusCode();
  if (statusCode == 200) {
    Serial.println("✅ Servo data sent to Firebase");
  }
}

void updateFirebasePeriodically() {
  unsigned long current_time = millis();
  
  if (current_time - last_firebase_update >= FIREBASE_UPDATE_INTERVAL) {
    sendToFirebase("periodic_update");
    last_firebase_update = current_time;
  }
}

// ========================================
// Status Functions
// ========================================
void printStatusPeriodically() {
  unsigned long current_time = millis();
  
  if (current_time - last_status_print >= STATUS_PRINT_INTERVAL) {
    printDetailedStatus();
    last_status_print = current_time;
  }
}

void printDetailedStatus() {
  Serial.println();
  Serial.println("===============================================================");
  Serial.println("📊 ARDUINO YOLO V11 SERVO STATUS");
  Serial.println("===============================================================");
  Serial.println("🍼 Total Bottles: " + String(bottle_count));
  Serial.println("⭐ Total Points: " + String(total_points));
  Serial.println("👁️ Detection State: " + String(detection_state ? "ACTIVE" : "INACTIVE"));
  Serial.println("🔧 Servo Position: " + String(bottleServo.read()) + "°");
  Serial.println("🌐 WiFi Status: " + String(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected"));
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("📡 IP Address: " + WiFi.localIP().toString());
    Serial.println("📶 Signal: " + String(WiFi.RSSI()) + " dBm");
  }
  Serial.println("⏱️ Uptime: " + String(millis() / 1000) + " seconds");
  Serial.println("🔥 Firebase Host: " + String(firebase_host));
  Serial.println("===============================================================");
  Serial.println();
}

// ========================================
// Utility Functions
// ========================================
void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_BUILTIN_PIN, LOW);
    delay(delayMs);
  }
}