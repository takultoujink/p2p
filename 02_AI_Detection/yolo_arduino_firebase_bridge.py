#!/usr/bin/env python3
"""
YOLO Arduino Firebase Bridge
ระบบเชื่อมต่อ YOLO -> Arduino R4 -> Firebase
ปรับปรุงจากไฟล์เดิมเพื่อการทำงานที่ดีขึ้น

Author: P2P Team
Version: 2.0
"""

import cv2
import numpy as np
import serial
import time
import requests
import json
from datetime import datetime
import threading
import os
import sys
from pathlib import Path

# Configuration
class Config:
    # Arduino Settings
    ARDUINO_PORT = 'COM3'  # เปลี่ยนตาม port ของ Arduino R4
    ARDUINO_BAUD_RATE = 115200
    ARDUINO_TIMEOUT = 2
    
    # Camera Settings
    CAMERA_INDEX = 0
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    
    # Firebase Settings
    FIREBASE_URL = "https://takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app"
    USER_ID = "yolo_user"  # จะได้จาก web login หรือกำหนดเอง
    
    # YOLO Settings
    YOLO_DIR = "yolo"
    YOLO_CONFIG = os.path.join(YOLO_DIR, "yolov3.cfg")
    YOLO_WEIGHTS = os.path.join(YOLO_DIR, "yolov3.weights")
    YOLO_CLASSES = os.path.join(YOLO_DIR, "coco.names")
    
    # Detection Settings
    CONFIDENCE_THRESHOLD = 0.5
    NMS_THRESHOLD = 0.4
    DETECTION_COOLDOWN = 2.0  # seconds
    BOTTLE_CLASS_ID = 39  # 'bottle' in COCO dataset

class ArduinoManager:
    """จัดการการเชื่อมต่อกับ Arduino R4"""
    
    def __init__(self, port=Config.ARDUINO_PORT, baud_rate=Config.ARDUINO_BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.arduino = None
        self.connected = False
        self.connect()
    
    def connect(self):
        """เชื่อมต่อกับ Arduino"""
        try:
            self.arduino = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=Config.ARDUINO_TIMEOUT
            )
            time.sleep(2)  # รอให้ Arduino เริ่มต้น
            self.connected = True
            print(f"✅ Arduino connected on {self.port}")
            
            # ส่งคำสั่งทดสอบ
            self.send_command("TEST")
            
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            print("💡 Tips:")
            print("   - ตรวจสอบว่า Arduino เสียบ USB แล้ว")
            print("   - ตรวจสอบ COM port ใน Device Manager")
            print("   - ปิด Arduino IDE หรือ Serial Monitor")
            self.connected = False
    
    def send_command(self, command):
        """ส่งคำสั่งไป Arduino"""
        if not self.connected:
            return False
        
        try:
            message = f"{command}\n"
            self.arduino.write(message.encode())
            print(f"📡 → Arduino: {command}")
            return True
        except Exception as e:
            print(f"❌ Error sending to Arduino: {e}")
            return False
    
    def read_response(self):
        """อ่านข้อมูลจาก Arduino"""
        if not self.connected:
            return None
        
        try:
            if self.arduino.in_waiting > 0:
                response = self.arduino.readline().decode().strip()
                if response:
                    print(f"📡 ← Arduino: {response}")
                return response
        except Exception as e:
            print(f"❌ Error reading from Arduino: {e}")
        return None
    
    def close(self):
        """ปิดการเชื่อมต่อ"""
        if self.arduino and self.connected:
            self.arduino.close()
            print("🔌 Arduino connection closed")

class FirebaseManager:
    """จัดการการเชื่อมต่อกับ Firebase"""
    
    def __init__(self, base_url=Config.FIREBASE_URL, user_id=Config.USER_ID):
        self.base_url = base_url
        self.user_id = user_id
    
    def send_data(self, data, path="bottle_data"):
        """ส่งข้อมูลไป Firebase"""
        try:
            url = f"{self.base_url}/{path}/{self.user_id}.json"
            
            # เพิ่ม timestamp
            data_with_timestamp = {
                **data,
                "timestamp": datetime.now().isoformat(),
                "unix_timestamp": int(time.time())
            }
            
            response = requests.put(url, json=data_with_timestamp, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Firebase: Data sent successfully")
                return True
            else:
                print(f"❌ Firebase error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Firebase connection error: {e}")
            return False
    
    def get_data(self, path="bottle_data"):
        """ดึงข้อมูลจาก Firebase"""
        try:
            url = f"{self.base_url}/{path}/{self.user_id}.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Firebase get error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Firebase get error: {e}")
            return None

class YOLODetector:
    """YOLO Object Detection สำหรับขวด"""
    
    def __init__(self):
        self.net = None
        self.classes = []
        self.output_layers = []
        self.load_model()
    
    def load_model(self):
        """โหลด YOLO model"""
        try:
            # ตรวจสอบไฟล์ YOLO
            if not all(os.path.exists(f) for f in [Config.YOLO_CONFIG, Config.YOLO_WEIGHTS, Config.YOLO_CLASSES]):
                print("❌ YOLO files not found!")
                self.download_yolo_files()
            
            # โหลด YOLO network
            self.net = cv2.dnn.readNet(Config.YOLO_WEIGHTS, Config.YOLO_CONFIG)
            
            # โหลด class names
            with open(Config.YOLO_CLASSES, "r") as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            # รับ output layer names
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
            
            print("✅ YOLO model loaded successfully!")
            print(f"📊 Classes loaded: {len(self.classes)}")
            
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            sys.exit(1)
    
    def download_yolo_files(self):
        """ดาวน์โหลดไฟล์ YOLO"""
        import urllib.request
        
        if not os.path.exists(Config.YOLO_DIR):
            os.makedirs(Config.YOLO_DIR)
        
        files_to_download = [
            ("https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg", Config.YOLO_CONFIG),
            ("https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names", Config.YOLO_CLASSES),
        ]
        
        for url, filename in files_to_download:
            if not os.path.exists(filename):
                print(f"📥 Downloading {filename}...")
                urllib.request.urlretrieve(url, filename)
                print(f"✅ Downloaded {filename}")
        
        # Weights file ใหญ่มาก ต้องดาวน์โหลดแยก
        if not os.path.exists(Config.YOLO_WEIGHTS):
            print("⚠️  Please download yolov3.weights manually:")
            print("   https://pjreddie.com/media/files/yolov3.weights")
            print(f"   Save to: {Config.YOLO_WEIGHTS}")
            input("Press Enter after downloading...")
    
    def detect_bottles(self, frame):
        """ตรวจจับขวดในเฟรม"""
        height, width, channels = frame.shape
        
        # เตรียมเฟรมสำหรับ YOLO
        blob = cv2.dnn.blobFromImage(
            frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False
        )
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)
        
        # ข้อมูลสำหรับแสดงผล
        class_ids = []
        confidences = []
        boxes = []
        
        # ประมวลผลการตรวจจับ
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # กรองเฉพาะขวดที่มีความมั่นใจสูง
                if class_id == Config.BOTTLE_CLASS_ID and confidence > Config.CONFIDENCE_THRESHOLD:
                    # คำนวณตำแหน่ง bounding box
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
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, Config.CONFIDENCE_THRESHOLD, Config.NMS_THRESHOLD)
        
        # วาด bounding boxes
        bottle_count = 0
        if len(indexes) > 0:
            bottle_count = len(indexes.flatten())
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                confidence = confidences[i]
                
                # วาดกรอบและข้อความ
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    frame, 
                    f"Bottle {confidence:.2f}", 
                    (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (0, 255, 0), 
                    2
                )
        
        return frame, bottle_count > 0, bottle_count

class BottleDetectionSystem:
    """ระบบตรวจจับขวดแบบครบวงจร"""
    
    def __init__(self):
        self.bottle_count = 0
        self.total_points = 0
        self.last_detection_time = 0
        
        # เริ่มต้นระบบย่อย
        self.arduino = ArduinoManager()
        self.firebase = FirebaseManager()
        self.yolo = YOLODetector()
        
        # เริ่มต้นกล้อง
        self.init_camera()
        
        print("🎯 Bottle Detection System initialized!")
    
    def init_camera(self):
        """เริ่มต้นกล้อง"""
        self.cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        
        if not self.cap.isOpened():
            print("❌ Cannot open camera")
            sys.exit(1)
        
        print("📹 Camera initialized")
    
    def on_bottle_detected(self, count):
        """จัดการเมื่อตรวจพบขวด"""
        current_time = time.time()
        
        # ป้องกันการตรวจจับซ้ำเร็วเกินไป
        if current_time - self.last_detection_time < Config.DETECTION_COOLDOWN:
            return
        
        self.last_detection_time = current_time
        self.bottle_count += count
        self.total_points = self.bottle_count * 10  # 10 แต้มต่อขวด
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🍼 [{timestamp}] Bottles detected: {count}, Total: {self.bottle_count}, Points: {self.total_points}")
        
        # ส่งไป Arduino
        if self.arduino.connected:
            self.arduino.send_command("BOTTLE_DETECTED")
            self.arduino.send_command(f"COUNT:{self.bottle_count}")
        
        # ส่งไป Firebase
        data = {
            "bottle_count": self.bottle_count,
            "total_points": self.total_points,
            "last_detection": count,
            "device": "yolo_python"
        }
        self.firebase.send_data(data)
    
    def reset_counter(self):
        """รีเซ็ตตัวนับ"""
        self.bottle_count = 0
        self.total_points = 0
        print("🔄 Counter reset!")
        
        # แจ้ง Arduino
        if self.arduino.connected:
            self.arduino.send_command("RESET")
        
        # อัปเดต Firebase
        data = {
            "bottle_count": 0,
            "total_points": 0,
            "last_detection": 0,
            "device": "yolo_python",
            "action": "reset"
        }
        self.firebase.send_data(data)
    
    def run(self):
        """เริ่มการทำงานหลัก"""
        print("🚀 Starting bottle detection system...")
        print("Controls:")
        print("  'q' - Quit")
        print("  'r' - Reset counter")
        print("  's' - Show status")
        print("="*50)
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to grab frame")
                    break
                
                # ตรวจจับขวด
                frame, bottle_detected, bottles_count = self.yolo.detect_bottles(frame)
                
                # จัดการการตรวจจับ
                if bottle_detected:
                    self.on_bottle_detected(bottles_count)
                
                # แสดงข้อมูลบนเฟรม
                self.draw_info(frame, bottles_count)
                
                # แสดงเฟรม
                cv2.imshow('YOLO Bottle Detection - P2P System', frame)
                
                # อ่านข้อมูลจาก Arduino
                if self.arduino.connected:
                    response = self.arduino.read_response()
                    if response:
                        self.handle_arduino_response(response)
                
                # จัดการคีย์บอร์ด
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.reset_counter()
                elif key == ord('s'):
                    self.show_status()
        
        except KeyboardInterrupt:
            print("\n🛑 System interrupted by user")
        
        finally:
            self.cleanup()
    
    def draw_info(self, frame, current_bottles):
        """วาดข้อมูลบนเฟรม"""
        # พื้นหลังสำหรับข้อความ
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # ข้อความสถานะ
        texts = [
            f"Total Bottles: {self.bottle_count}",
            f"Total Points: {self.total_points}",
            f"Current Detection: {current_bottles}",
            f"Arduino: {'Connected' if self.arduino.connected else 'Disconnected'}"
        ]
        
        for i, text in enumerate(texts):
            y = 30 + (i * 25)
            cv2.putText(frame, text, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    def handle_arduino_response(self, response):
        """จัดการข้อมูลจาก Arduino"""
        if response.startswith("STATUS:"):
            # Arduino ส่งสถานะมา
            status_data = response[7:].split(",")
            if len(status_data) >= 2:
                arduino_count = int(status_data[0])
                arduino_points = int(status_data[1])
                print(f"📊 Arduino Status - Count: {arduino_count}, Points: {arduino_points}")
    
    def show_status(self):
        """แสดงสถานะระบบ"""
        print("\n" + "="*50)
        print("📊 SYSTEM STATUS")
        print("="*50)
        print(f"🍼 Total Bottles: {self.bottle_count}")
        print(f"⭐ Total Points: {self.total_points}")
        print(f"🔌 Arduino: {'Connected' if self.arduino.connected else 'Disconnected'}")
        print(f"🔥 Firebase: Ready")
        print(f"📹 Camera: Active")
        print(f"🤖 YOLO: Active")
        print("="*50 + "\n")
    
    def cleanup(self):
        """ทำความสะอาดเมื่อปิดระบบ"""
        print("🧹 Cleaning up...")
        
        if hasattr(self, 'cap'):
            self.cap.release()
        
        cv2.destroyAllWindows()
        
        if hasattr(self, 'arduino'):
            self.arduino.close()
        
        print("✅ Cleanup completed")

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 YOLO Arduino Firebase Bridge v2.0")
    print("🎯 P2P (Plastic to Point) Detection System")
    print("="*60)
    
    try:
        system = BottleDetectionSystem()
        system.run()
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()