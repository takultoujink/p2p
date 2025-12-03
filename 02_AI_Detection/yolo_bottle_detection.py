"""
YOLO Bottle Detection with Arduino Integration
ตรวจจับขวดด้วย YOLO และส่งสัญญาณไป Arduino R4
"""

import cv2
import numpy as np
import serial
import time
import requests
import json
from datetime import datetime
import threading

# Configuration
ARDUINO_PORT = 'COM3'  # เปลี่ยนตาม port ของ Arduino
ARDUINO_BAUD_RATE = 115200
CAMERA_INDEX = 0  # Camera index (usually 0 for default camera)

# Firebase Configuration
FIREBASE_URL = "https://takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app"
USER_ID = "YOUR_USER_ID_HERE"  # จะได้จาก web login

# YOLO Configuration
YOLO_CONFIG_PATH = "yolo/yolov3.cfg"  # Path to YOLO config file
YOLO_WEIGHTS_PATH = "yolo/yolov3.weights"  # Path to YOLO weights
YOLO_CLASSES_PATH = "yolo/coco.names"  # Path to class names

class BottleDetector:
    def __init__(self):
        self.bottle_count = 0
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # seconds
        self.arduino_connected = False
        
        # Initialize Arduino connection
        self.init_arduino()
        
        # Initialize YOLO
        self.init_yolo()
        
        # Initialize camera
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    def init_arduino(self):
        """Initialize Arduino serial connection"""
        try:
            self.arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD_RATE, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            self.arduino_connected = True
            print("✅ Arduino connected successfully!")
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            print("Will continue without Arduino connection...")
            self.arduino_connected = False
    
    def init_yolo(self):
        """Initialize YOLO model"""
        try:
            # Load YOLO
            self.net = cv2.dnn.readNet(YOLO_WEIGHTS_PATH, YOLO_CONFIG_PATH)
            
            # Load class names
            with open(YOLO_CLASSES_PATH, "r") as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            # Get output layer names
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
            
            print("✅ YOLO model loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            print("Please download YOLO files and update paths in the configuration")
            exit(1)
    
    def detect_bottles(self, frame):
        """Detect bottles in frame using YOLO"""
        height, width, channels = frame.shape
        
        # Prepare frame for YOLO
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)
        
        # Information to show on screen
        class_ids = []
        confidences = []
        boxes = []
        
        # Process detections
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # Filter for bottles (class_id might be 39 for 'bottle' in COCO dataset)
                if confidence > 0.5 and self.classes[class_id] == "bottle":
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Non-maximum suppression
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        bottle_detected = False
        if len(indexes) > 0:
            bottle_detected = True
            
            # Draw bounding boxes
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                label = f"{self.classes[class_ids[i]]}: {confidences[i]:.2f}"
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame, bottle_detected, len(indexes) if len(indexes) > 0 else 0
    
    def send_to_arduino(self, signal):
        """Send signal to Arduino"""
        if self.arduino_connected:
            try:
                self.arduino.write(signal.encode())
                print(f"📡 Sent to Arduino: {signal}")
            except Exception as e:
                print(f"❌ Error sending to Arduino: {e}")
    
    def send_to_firebase_direct(self, count):
        """Send data directly to Firebase (backup method)"""
        try:
            url = f"{FIREBASE_URL}/live_count/{USER_ID}.json"
            response = requests.put(url, json=count, timeout=5)
            if response.status_code == 200:
                print(f"✅ Sent to Firebase: {count}")
            else:
                print(f"❌ Firebase error: {response.status_code}")
        except Exception as e:
            print(f"❌ Firebase connection error: {e}")
    
    def on_bottle_detected(self, bottles_count):
        """Handle bottle detection event"""
        current_time = time.time()
        
        # Prevent spam detections
        if current_time - self.last_detection_time < self.detection_cooldown:
            return
        
        self.last_detection_time = current_time
        self.bottle_count += bottles_count
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🍼 [{timestamp}] Bottles detected: {bottles_count}, Total: {self.bottle_count}")
        
        # Send to Arduino
        self.send_to_arduino("BOTTLE_DETECTED\n")
        
        # Send to Firebase as backup
        self.send_to_firebase_direct(self.bottle_count)
    
    def run(self):
        """Main detection loop"""
        print("🎯 Starting bottle detection...")
        print("Press 'q' to quit, 'r' to reset counter")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Failed to grab frame")
                break
            
            # Detect bottles
            frame, bottle_detected, bottles_count = self.detect_bottles(frame)
            
            # Handle detection
            if bottle_detected:
                self.on_bottle_detected(bottles_count)
            
            # Display info on frame
            cv2.putText(frame, f"Total Bottles: {self.bottle_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Current Detection: {bottles_count}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Show frame
            cv2.imshow('Bottle Detection', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.bottle_count = 0
                print("🔄 Counter reset!")
                self.send_to_firebase_direct(0)
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        if self.arduino_connected:
            self.arduino.close()

def download_yolo_files():
    """Download YOLO files if not present"""
    import os
    import urllib.request
    
    yolo_dir = "yolo"
    if not os.path.exists(yolo_dir):
        os.makedirs(yolo_dir)
    
    files_to_download = [
        ("https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg", "yolo/yolov3.cfg"),
        ("https://pjreddie.com/media/files/yolov3.weights", "yolo/yolov3.weights"),
        ("https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names", "yolo/coco.names")
    ]
    
    for url, filename in files_to_download:
        if not os.path.exists(filename):
            print(f"📥 Downloading {filename}...")
            urllib.request.urlretrieve(url, filename)
            print(f"✅ Downloaded {filename}")

if __name__ == "__main__":
    print("🚀 YOLO Bottle Detection System")
    print("=" * 40)
    
    # Download YOLO files if needed
    try:
        download_yolo_files()
    except Exception as e:
        print(f"⚠️  Could not download YOLO files automatically: {e}")
        print("Please download manually from:")
        print("1. https://pjreddie.com/media/files/yolov3.weights")
        print("2. https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg")
        print("3. https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names")
    
    # Start detection
    detector = BottleDetector()
    detector.run()
