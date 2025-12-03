#!/usr/bin/env python3
"""
YOLOv11 Arduino Firebase Bridge
ปรับปรุงจากโค้ดเดิมให้รองรับ YOLOv11 และเชื่อมต่อ Firebase
รวมฟีเจอร์จากระบบ P2P Detection System

Author: P2P Team
Version: 3.0 (YOLOv11 Edition)
"""

import serial
import time
from ultralytics import YOLO
import cv2
import requests
import json
from datetime import datetime
import os
import sys
import threading

# ========================================
# Configuration Class
# ========================================
class Config:
    # Arduino Settings
    ARDUINO_PORT = "COM5"  # แก้ตามพอร์ต Arduino ของคุณ
    ARDUINO_BAUD_RATE = 9600
    ARDUINO_TIMEOUT = 1
    SEND_DELAY = 1.0  # เวลาระหว่างส่งค่าไป Arduino (วินาที)
    
    # YOLOv11 Settings
    MODEL_PATH = "best.pt"  # path ไปยัง YOLOv11 model ของคุณ
    TARGET_CLASS_ID = 0     # ID ของ plastic bottle ใน dataset ของคุณ
    CONF_THRESHOLD = 0.80   # Confidence ขั้นต่ำ
    
    # Camera Settings
    CAM_ID = 1
    DEVICE = "cpu"  # หรือ "cuda" ถ้ามี GPU
    IMG_SIZE = 640
    
    # Firebase Settings
    FIREBASE_URL = "https://takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app"
    USER_ID = "yolo_v11_user"
    
    # Display Settings
    WINDOW_NAME = "YOLOv11 P2P Detection (ESC to quit)"
    
    # Detection Settings
    DETECTION_COOLDOWN = 2.0  # เวลารอระหว่างการนับขวด (วินาที)
    POINTS_PER_BOTTLE = 10    # คะแนนต่อขวด

class ArduinoManager:
    """จัดการการเชื่อมต่อกับ Arduino"""
    
    def __init__(self, port=Config.ARDUINO_PORT, baud_rate=Config.ARDUINO_BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.arduino = None
        self.connected = False
        self.last_send_time = 0
        self.connect()
    
    def connect(self):
        """เชื่อมต่อกับ Arduino"""
        try:
            self.arduino = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=Config.ARDUINO_TIMEOUT
            )
            time.sleep(2)  # รอให้ Arduino reset
            self.connected = True
            print(f"✅ Arduino connected on {self.port}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            print("💡 Tips:")
            print("   - ตรวจสอบว่า Arduino เสียบ USB แล้ว")
            print(f"   - ตรวจสอบ COM port: {self.port}")
            print("   - ปิด Arduino IDE หรือ Serial Monitor")
            self.connected = False
    
    def send_signal(self, detected):
        """ส่งสัญญาณไป Arduino ตามเวลาที่กำหนด"""
        current_time = time.time()
        
        if current_time - self.last_send_time >= Config.SEND_DELAY:
            if not self.connected:
                return False
            
            try:
                if detected:
                    self.arduino.write(b"90\n")
                    print("📡 → Arduino: 90 (Plastic bottle detected)")
                else:
                    self.arduino.write(b"0\n")
                    print("📡 → Arduino: 0 (No plastic bottle detected)")
                
                self.last_send_time = current_time
                return True
                
            except Exception as e:
                print(f"❌ Error sending to Arduino: {e}")
                return False
        
        return True  # ยังไม่ถึงเวลาส่ง
    
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
                "unix_timestamp": int(time.time()),
                "model_version": "YOLOv11"
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

class YOLOv11DetectionSystem:
    """ระบบตรวจจับขวดด้วย YOLOv11"""
    
    def __init__(self):
        # สถิติการตรวจจับ
        self.bottle_count = 0
        self.total_points = 0
        self.last_detection_time = 0
        
        # เริ่มต้นระบบย่อย
        self.arduino = ArduinoManager()
        self.firebase = FirebaseManager()
        
        # โหลด YOLOv11 model
        self.load_model()
        
        print("🎯 YOLOv11 Detection System initialized!")
    
    def load_model(self):
        """โหลด YOLOv11 model"""
        try:
            if not os.path.exists(Config.MODEL_PATH):
                print(f"❌ Model file not found: {Config.MODEL_PATH}")
                print("💡 กรุณาวาง YOLOv11 model (.pt file) ในโฟลเดอร์นี้")
                print("📥 หรือเปลี่ยน MODEL_PATH ใน Config")
                sys.exit(1)
            
            self.model = YOLO(Config.MODEL_PATH)
            print(f"✅ YOLOv11 model loaded: {Config.MODEL_PATH}")
            print(f"🎯 Target class ID: {Config.TARGET_CLASS_ID}")
            print(f"📊 Confidence threshold: {Config.CONF_THRESHOLD}")
            
        except Exception as e:
            print(f"❌ Failed to load YOLOv11 model: {e}")
            sys.exit(1)
    
    def on_bottle_detected(self, count=1):
        """จัดการเมื่อตรวจพบขวด"""
        current_time = time.time()
        
        # ป้องกันการตรวจจับซ้ำเร็วเกินไป
        if current_time - self.last_detection_time < Config.DETECTION_COOLDOWN:
            return
        
        self.last_detection_time = current_time
        self.bottle_count += count
        self.total_points = self.bottle_count * Config.POINTS_PER_BOTTLE
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🍼 [{timestamp}] Bottles detected: {count}, Total: {self.bottle_count}, Points: {self.total_points}")
        
        # ส่งไป Firebase
        data = {
            "bottle_count": self.bottle_count,
            "total_points": self.total_points,
            "last_detection": count,
            "device": "yolo_v11_python",
            "confidence_threshold": Config.CONF_THRESHOLD,
            "model_path": Config.MODEL_PATH
        }
        self.firebase.send_data(data)
    
    def reset_counter(self):
        """รีเซ็ตตัวนับ"""
        self.bottle_count = 0
        self.total_points = 0
        print("🔄 Counter reset!")
        
        # อัปเดต Firebase
        data = {
            "bottle_count": 0,
            "total_points": 0,
            "last_detection": 0,
            "device": "yolo_v11_python",
            "action": "reset"
        }
        self.firebase.send_data(data)
    
    def draw_info(self, frame, detected, confidence=0.0):
        """วาดข้อมูลบนเฟรม"""
        # พื้นหลังสำหรับข้อความ
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (450, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # ข้อความสถานะ
        texts = [
            f"YOLOv11 P2P Detection System",
            f"Total Bottles: {self.bottle_count}",
            f"Total Points: {self.total_points}",
            f"Detection: {'YES' if detected else 'NO'} ({confidence:.2f})",
            f"Arduino: {'Connected' if self.arduino.connected else 'Disconnected'}"
        ]
        
        for i, text in enumerate(texts):
            y = 25 + (i * 22)
            color = (0, 255, 0) if i == 0 else (255, 255, 255)
            cv2.putText(frame, text, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame
    
    def run(self):
        """เริ่มการทำงานหลัก"""
        print("🚀 Starting YOLOv11 bottle detection system...")
        print("Controls:")
        print("  'ESC' - Quit")
        print("  'r' - Reset counter")
        print("  's' - Show status")
        print("="*60)
        
        try:
            # ใช้โหมด stream ของ YOLOv11
            for r in self.model.predict(
                source=Config.CAM_ID, 
                stream=True, 
                device=Config.DEVICE,
                conf=Config.CONF_THRESHOLD, 
                imgsz=Config.IMG_SIZE, 
                verbose=False
            ):
                frame = r.plot()  # วาดกล่องลงเฟรมแล้ว
                
                # ตรวจสอบว่ามี plastic bottle ปรากฏ
                detected = False
                max_confidence = 0.0
                bottle_count_in_frame = 0
                
                if r.boxes is not None:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        if cls_id == Config.TARGET_CLASS_ID and conf >= Config.CONF_THRESHOLD:
                            detected = True
                            bottle_count_in_frame += 1
                            max_confidence = max(max_confidence, conf)
                
                # ส่งสัญญาณไป Arduino
                self.arduino.send_signal(detected)
                
                # จัดการการตรวจจับ
                if detected:
                    self.on_bottle_detected(bottle_count_in_frame)
                
                # วาดข้อมูลบนเฟรม
                frame = self.draw_info(frame, detected, max_confidence)
                
                # แสดงผลภาพ
                cv2.imshow(Config.WINDOW_NAME, frame)
                
                # จัดการคีย์บอร์ด
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC เพื่อออก
                    break
                elif key == ord('r'):
                    self.reset_counter()
                elif key == ord('s'):
                    self.show_status()
        
        except KeyboardInterrupt:
            print("\n🛑 System interrupted by user")
        
        except Exception as e:
            print(f"❌ System error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()
    
    def show_status(self):
        """แสดงสถานะระบบ"""
        print("\n" + "="*60)
        print("📊 YOLOv11 SYSTEM STATUS")
        print("="*60)
        print(f"🤖 Model: {Config.MODEL_PATH}")
        print(f"🎯 Target Class ID: {Config.TARGET_CLASS_ID}")
        print(f"📊 Confidence Threshold: {Config.CONF_THRESHOLD}")
        print(f"🍼 Total Bottles: {self.bottle_count}")
        print(f"⭐ Total Points: {self.total_points}")
        print(f"🔌 Arduino: {'Connected' if self.arduino.connected else 'Disconnected'}")
        print(f"🔥 Firebase: Ready")
        print(f"📹 Camera ID: {Config.CAM_ID}")
        print(f"💻 Device: {Config.DEVICE}")
        print("="*60 + "\n")
    
    def cleanup(self):
        """ทำความสะอาดเมื่อปิดระบบ"""
        print("🧹 Cleaning up...")
        
        cv2.destroyAllWindows()
        
        if hasattr(self, 'arduino'):
            self.arduino.close()
        
        print("✅ Cleanup completed")

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 YOLOv11 Arduino Firebase Bridge v3.0")
    print("🎯 P2P (Plastic to Point) Detection System")
    print("🤖 Powered by YOLOv11")
    print("="*70)
    
    # ตรวจสอบ dependencies
    try:
        import ultralytics
        print(f"✅ Ultralytics version: {ultralytics.__version__}")
    except ImportError:
        print("❌ Ultralytics not found!")
        print("📦 Install with: pip install ultralytics")
        return
    
    try:
        system = YOLOv11DetectionSystem()
        system.run()
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()