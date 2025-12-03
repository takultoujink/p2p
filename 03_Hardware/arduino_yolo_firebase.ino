/*
  Arduino R4 WiFi - YOLO to Firebase Integration
  รับข้อมูลจาก YOLO Python script และส่งไปยัง Firebase
  
  Hardware Requirements:
  - Arduino UNO R4 WiFi
  - LED (optional for status indication)
  - Buzzer (optional for audio feedback)
  
  Connections:
  - LED: Pin 13 (built-in LED)
  - Buzzer: Pin 8 (optional)
*/

#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";     // เปลี่ยนเป็น WiFi ของคุณ
const char* password = "YOUR_WIFI_PASSWORD"; // เปลี่ยนเป็นรหัสผ่าน WiFi

// Firebase Configuration
const char* firebase_host = "takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app";
const int firebase_port = 443;
const String firebase_path = "/bottle_data";
const String user_id = "arduino_user"; // หรือใช้ USER_ID จาก web

// Pin Configuration
const int LED_PIN = 13;        // Built-in LED
const int BUZZER_PIN = 8;      // Buzzer (optional)
const int STATUS_LED = 12;     // Status LED (optional)

// Variables
int bottle_count = 0;
int total_points = 0;
WiFiSSLClient wifi;
HttpClient client = HttpClient(wifi, firebase_host, firebase_port);
String incoming_data = "";

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(STATUS_LED, OUTPUT);
  
  // Initial LED state
  digitalWrite(LED_PIN, LOW);
  digitalWrite(STATUS_LED, LOW);
  
  Serial.println("🚀 Arduino R4 - YOLO to Firebase Bridge");
  Serial.println("=======================================");
  
  // Connect to WiFi
  connectToWiFi();
  
  // Test Firebase connection
  testFirebaseConnection();
  
  Serial.println("✅ System ready! Waiting for YOLO data...");
  digitalWrite(STATUS_LED, HIGH); // System ready indicator
}

void loop() {
  // Check for data from YOLO Python script
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "BOTTLE_DETECTED") {
      handleBottleDetection();
    } else if (command.startsWith("COUNT:")) {
      int count = command.substring(6).toInt();
      updateBottleCount(count);
    } else if (command == "RESET") {
      resetCounter();
    }
  }
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️  WiFi disconnected. Reconnecting...");
    connectToWiFi();
  }
  
  delay(100);
}

void connectToWiFi() {
  Serial.print("🔗 Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected!");
    Serial.print("📡 IP address: ");
    Serial.println(WiFi.localIP());
    
    // Blink LED to indicate WiFi connection
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(200);
      digitalWrite(LED_PIN, LOW);
      delay(200);
    }
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
  }
}

void testFirebaseConnection() {
  Serial.println("🧪 Testing Firebase connection...");
  
  String test_data = "{\"test\":\"arduino_connection\",\"timestamp\":" + String(millis()) + "}";
  
  if (sendToFirebase("/test/arduino.json", test_data)) {
    Serial.println("✅ Firebase connection successful!");
  } else {
    Serial.println("❌ Firebase connection failed!");
  }
}

void handleBottleDetection() {
  bottle_count++;
  total_points += 10; // 10 points per bottle
  
  Serial.println("🍼 Bottle detected!");
  Serial.println("Count: " + String(bottle_count));
  Serial.println("Points: " + String(total_points));
  
  // Visual feedback
  digitalWrite(LED_PIN, HIGH);
  
  // Audio feedback (if buzzer connected)
  tone(BUZZER_PIN, 1000, 200);
  
  // Send to Firebase
  sendBottleDataToFirebase();
  
  // Turn off LED after 1 second
  delay(1000);
  digitalWrite(LED_PIN, LOW);
}

void updateBottleCount(int count) {
  bottle_count = count;
  total_points = count * 10;
  
  Serial.println("📊 Count updated: " + String(bottle_count));
  sendBottleDataToFirebase();
}

void resetCounter() {
  bottle_count = 0;
  total_points = 0;
  
  Serial.println("🔄 Counter reset!");
  sendBottleDataToFirebase();
  
  // Blink LED to indicate reset
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}

void sendBottleDataToFirebase() {
  // Create JSON data
  StaticJsonDocument<200> doc;
  doc["user_id"] = user_id;
  doc["bottle_count"] = bottle_count;
  doc["total_points"] = total_points;
  doc["timestamp"] = millis();
  doc["device"] = "arduino_r4";
  
  String json_string;
  serializeJson(doc, json_string);
  
  // Send to Firebase
  String path = firebase_path + "/" + user_id + ".json";
  
  if (sendToFirebase(path, json_string)) {
    Serial.println("✅ Data sent to Firebase successfully!");
  } else {
    Serial.println("❌ Failed to send data to Firebase!");
  }
}

bool sendToFirebase(String path, String data) {
  Serial.println("📤 Sending to Firebase: " + path);
  
  client.beginRequest();
  client.put(path);
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", data.length());
  client.beginBody();
  client.print(data);
  client.endRequest();
  
  int statusCode = client.responseStatusCode();
  String response = client.responseBody();
  
  Serial.println("📥 Response code: " + String(statusCode));
  Serial.println("📥 Response: " + response);
  
  return (statusCode == 200);
}

// Function to handle commands from web interface
void handleWebCommand(String command) {
  if (command == "GET_STATUS") {
    // Send current status back
    Serial.println("STATUS:" + String(bottle_count) + "," + String(total_points));
  } else if (command == "RESET_COUNT") {
    resetCounter();
  }
}

// Function to send status updates to web
void sendStatusUpdate() {
  Serial.println("UPDATE:" + String(bottle_count) + "," + String(total_points));
}