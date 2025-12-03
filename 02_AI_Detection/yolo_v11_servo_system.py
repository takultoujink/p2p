#!/usr/bin/env python3
"""
YOLOv11 Arduino Firebase Bridge with Servo Control
รวม Servo motor control เข้ากับระบบ YOLOv11 Detection
รองรับการปัดขวดอัตโนมัติเมื่อตรวจพบ

Author: P2P Team
Version: 3.1 (YOLOv11 + Servo Edition)
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
import numpy as np

# ========================================
# Configuration Class
# ========================================
class ServoConfig:
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
    USER_ID = "yolo_v11_servo_user"
    
    # Display Settings
    WINDOW_NAME = "YOLOv11 P2P Detection with Servo Control (ESC to quit)"
    
    # Detection Settings
    DETECTION_COOLDOWN = 2.0  # เวลารอระหว่างการนับขวด (วินาที)
    POINTS_PER_BOTTLE = 10    # คะแนนต่อขวด
    
    # Servo Settings
    SERVO_REST_POSITION = 90    # ตำแหน่งพัก
    SERVO_SWEEP_POSITION = 45   # ตำแหน่งปัดขวด
    SERVO_RETURN_POSITION = 135 # ตำแหน่งกลับ
    AUTO_SERVO_SWEEP = True     # เปิดใช้การปัดขวดอัตโนมัติ
    SERVO_DELAY = 0.5          # เวลาหน่วงระหว่างการเคลื่อนไหว Servo

class ArduinoServoManager:
    """จัดการการเชื่อมต่อกับ Arduino และควบคุม Servo"""
    
    def __init__(self, port=ServoConfig.ARDUINO_PORT, baud_rate=ServoConfig.ARDUINO_BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.arduino = None
        self.connected = False
        self.last_send_time = 0
        self.servo_position = ServoConfig.SERVO_REST_POSITION
        self.connect()
    
    def connect(self):
        """เชื่อมต่อกับ Arduino"""
        try:
            self.arduino = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=ServoConfig.ARDUINO_TIMEOUT
            )
            time.sleep(2)  # รอให้ Arduino reset
            self.connected = True
            print(f"✅ Arduino with Servo connected on {self.port}")
            
            # Initialize servo to rest position
            self.move_servo_to_rest()
            
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            print("💡 Tips:")
            print("   - ตรวจสอบว่า Arduino เสียบ USB แล้ว")
            print(f"   - ตรวจสอบ COM port: {self.port}")
            print("   - ปิด Arduino IDE หรือ Serial Monitor")
            print("   - ตรวจสอบว่า Servo เชื่อมต่อที่ pin 9")
            self.connected = False
    
    def send_signal(self, detected):
        """ส่งสัญญาณไป Arduino ตามเวลาที่กำหนด"""
        current_time = time.time()
        
        if current_time - self.last_send_time >= ServoConfig.SEND_DELAY:
            if not self.connected:
                return False
            
            try:
                if detected:
                    self.arduino.write(b"90\n")
                    print("📡 → Arduino: 90 (Plastic bottle detected)")
                    
                    # Auto servo sweep if enabled
                    if ServoConfig.AUTO_SERVO_SWEEP:
                        self.perform_bottle_sweep()
                else:
                    self.arduino.write(b"0\n")
                    print("📡 → Arduino: 0 (No plastic bottle detected)")
                
                self.last_send_time = current_time
                return True
                
            except Exception as e:
                print(f"❌ Error sending to Arduino: {e}")
                return False
        
        return True  # ยังไม่ถึงเวลาส่ง
    
    def move_servo_to_angle(self, angle):
        """เคลื่อนไหว Servo ไปยังมุมที่กำหนด"""
        if not self.connected:
            return False
        
        if not 0 <= angle <= 180:
            print(f"❌ Invalid servo angle: {angle}. Must be 0-180.")
            return False
        
        try:
            command = f"SERVO:{angle}\n"
            self.arduino.write(command.encode())
            self.servo_position = angle
            print(f"🔧 Servo moved to: {angle}°")
            time.sleep(ServoConfig.SERVO_DELAY)
            return True
            
        except Exception as e:
            print(f"❌ Error moving servo: {e}")
            return False
    
    def perform_bottle_sweep(self):
        """ทำการปัดขวดแบบอัตโนมัติ"""
        if not self.connected:
            return False
        
        try:
            print("🧹 Performing automatic bottle sweep...")
            self.arduino.write(b"SWEEP\n")
            print("✅ Bottle sweep command sent")
            return True
            
        except Exception as e:
            print(f"❌ Error performing sweep: {e}")
            return False
    
    def move_servo_to_rest(self):
        """เคลื่อนไหว Servo ไปยังตำแหน่งพัก"""
        return self.move_servo_to_angle(ServoConfig.SERVO_REST_POSITION)
    
    def test_servo(self):
        """ทดสอบการทำงานของ Servo"""
        if not self.connected:
            print("❌ Arduino not connected")
            return False
        
        print("🔧 Testing servo motor...")
        test_angles = [0, 45, 90, 135, 180, 90]  # กลับไปตำแหน่งพัก
        
        for angle in test_angles:
            if self.move_servo_to_angle(angle):
                time.sleep(1)
            else:
                return False
        
        print("✅ Servo test completed")
        return True
    
    def reset_servo(self):
        """รีเซ็ต Servo กลับไปตำแหน่งเริ่มต้น"""
        print("🔄 Resetting servo to rest position...")
        return self.move_servo_to_rest()
    
    def close(self):
        """ปิดการเชื่อมต่อ"""
        if self.arduino and self.connected:
            # Return servo to rest position before closing
            self.move_servo_to_rest()
            time.sleep(1)
            self.arduino.close()
            print("🔌 Arduino connection closed")

class FirebaseServoManager:
    """จัดการการเชื่อมต่อกับ Firebase รวมข้อมูล Servo"""
    
    def __init__(self, base_url=ServoConfig.FIREBASE_URL, user_id=ServoConfig.USER_ID):
        self.base_url = base_url
        self.user_id = user_id
    
    def send_data(self, data, path="bottle_servo_data"):
        """ส่งข้อมูลไป Firebase"""
        try:
            url = f"{self.base_url}/{path}/{self.user_id}.json"
            
            # เพิ่ม timestamp และข้อมูล servo
            data_with_timestamp = {
                **data,
                "timestamp": datetime.now().isoformat(),
                "unix_timestamp": int(time.time()),
                "model_version": "YOLOv11",
                "has_servo": True
            }
            
            print(f"📡 Sending to Firebase: {url}")
            print(f"📄 Data: {json.dumps(data_with_timestamp, indent=2)}")
            
            response = requests.put(url, json=data_with_timestamp, timeout=10)
            
            print(f"📊 Firebase Response Status: {response.status_code}")
            print(f"📊 Firebase Response: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ Firebase: Data sent successfully to {path}")
                return True
            else:
                print(f"❌ Firebase error: {response.status_code}")
                print(f"❌ Response text: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"❌ Firebase timeout: Request took longer than 10 seconds")
            return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Firebase connection error: Cannot connect to Firebase")
            print(f"💡 Check internet connection and Firebase URL")
            return False
        except Exception as e:
            print(f"❌ Firebase unexpected error: {e}")
            print(f"💡 Error type: {type(e).__name__}")
            return False
    
    def send_servo_data(self, servo_angle, action="servo_move"):
        """ส่งข้อมูล Servo เฉพาะไป Firebase"""
        servo_data = {
            "servo_angle": servo_angle,
            "action": action,
            "device": "python_yolo_v11_servo"
        }
        return self.send_data(servo_data, "servo_data")

class YOLOv11ServoDetectionSystem:
    """ระบบตรวจจับขวดด้วย YOLOv11 พร้อม Servo Control"""
    
    def __init__(self):
        # สถิติการตรวจจับ
        self.bottle_count = 0
        self.total_points = 0
        self.last_detection_time = 0
        self.servo_actions = 0
        
        # เริ่มต้นระบบย่อย
        self.arduino = ArduinoServoManager()
        self.firebase = FirebaseServoManager()
        
        # โหลด YOLOv11 model
        self.load_model()
        
        print("🎯 YOLOv11 Servo Detection System initialized!")
        print(f"🔧 Servo auto-sweep: {'Enabled' if ServoConfig.AUTO_SERVO_SWEEP else 'Disabled'}")
    
    def load_model(self):
        """โหลด YOLOv11 model"""
        try:
            if not os.path.exists(ServoConfig.MODEL_PATH):
                print(f"❌ Model file not found: {ServoConfig.MODEL_PATH}")
                print("💡 กรุณาวาง YOLOv11 model (.pt file) ในโฟลเดอร์นี้")
                print("📥 หรือเปลี่ยน MODEL_PATH ใน ServoConfig")
                sys.exit(1)
            
            self.model = YOLO(ServoConfig.MODEL_PATH)
            print(f"✅ YOLOv11 model loaded: {ServoConfig.MODEL_PATH}")
            print(f"🎯 Target class ID: {ServoConfig.TARGET_CLASS_ID}")
            print(f"📊 Confidence threshold: {ServoConfig.CONF_THRESHOLD}")
            
        except Exception as e:
            print(f"❌ Failed to load YOLOv11 model: {e}")
            sys.exit(1)
    
    def on_bottle_detected(self, count=1):
        """จัดการเมื่อตรวจพบขวด"""
        current_time = time.time()
        
        # ป้องกันการตรวจจับซ้ำเร็วเกินไป
        if current_time - self.last_detection_time < ServoConfig.DETECTION_COOLDOWN:
            return
        
        print(f"\n🔍 Bottle Detection Event:")
        print(f"   - Bottles detected: {count}")
        
        self.last_detection_time = current_time
        self.bottle_count += count
        self.total_points = self.bottle_count * ServoConfig.POINTS_PER_BOTTLE
        
        print(f"   - Total count: {self.bottle_count}")
        print(f"   - Total points: {self.total_points}")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🍼 [{timestamp}] Bottles detected: {count}, Total: {self.bottle_count}, Points: {self.total_points}")
        
        # นับการทำงานของ Servo
        if ServoConfig.AUTO_SERVO_SWEEP:
            self.servo_actions += 1
            print(f"🧹 Servo sweep #{self.servo_actions} initiated")
        
        print(f"\n💾 Preparing to save data to Firebase...")
        
        # ส่งไป Firebase
        data = {
            "bottle_count": self.bottle_count,
            "total_points": self.total_points,
            "last_detection": count,
            "servo_actions": self.servo_actions,
            "servo_position": self.arduino.servo_position,
            "auto_sweep_enabled": ServoConfig.AUTO_SERVO_SWEEP,
            "device": "yolo_v11_servo_python",
            "confidence_threshold": ServoConfig.CONF_THRESHOLD,
            "model_path": ServoConfig.MODEL_PATH
        }
        
        success = self.firebase.send_data(data)
        
        if success:
            print(f"✅ Data saved successfully!")
        else:
            print(f"❌ Failed to save data to Firebase!")
        
        # ควบคุม Servo
        if ServoConfig.AUTO_SERVO_SWEEP and self.arduino:
            print(f"🔄 Auto sweep enabled - moving servo...")
        else:
            print(f"⏸️ Auto sweep disabled - servo stays at position {self.arduino.servo_position}°")
    
    def reset_counter(self):
        """รีเซ็ตตัวนับ"""
        print(f"\n🔄 Resetting all counters...")
        
        old_count = self.bottle_count
        old_points = self.total_points
        old_actions = self.servo_actions
        
        self.bottle_count = 0
        self.total_points = 0
        self.servo_actions = 0
        
        print(f"   - Bottle count: {old_count} → 0")
        print(f"   - Total points: {old_points} → 0")
        print(f"   - Servo actions: {old_actions} → 0")
        
        # รีเซ็ต Servo
        self.arduino.reset_servo()
        
        print(f"\n💾 Saving reset data to Firebase...")
        
        # อัปเดต Firebase
        data = {
            "bottle_count": 0,
            "total_points": 0,
            "servo_actions": 0,
            "servo_position": ServoConfig.SERVO_REST_POSITION,
            "last_detection": 0,
            "device": "yolo_v11_servo_python",
            "action": "reset",
            "previous_count": old_count,
            "previous_points": old_points,
            "previous_actions": old_actions
        }
        
        success = self.firebase.send_data(data)
        
        if success:
            print(f"✅ Reset data saved successfully!")
        else:
            print(f"❌ Failed to save reset data to Firebase!")
        
        print("🔄 Counter and servo reset completed!")
    
    def draw_info(self, frame, detected, confidence=0.0):
        """วาดข้อมูลบนเฟรม"""
        # พื้นหลังสำหรับข้อความ
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (500, 180), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # ข้อความสถานะ
        texts = [
            f"YOLOv11 P2P Detection + Servo Control",
            f"Total Bottles: {self.bottle_count}",
            f"Total Points: {self.total_points}",
            f"Servo Actions: {self.servo_actions}",
            f"Detection: {'YES' if detected else 'NO'} ({confidence:.2f})",
            f"Arduino: {'Connected' if self.arduino.connected else 'Disconnected'}",
            f"Servo Position: {self.arduino.servo_position}°",
            f"Auto Sweep: {'ON' if ServoConfig.AUTO_SERVO_SWEEP else 'OFF'}"
        ]
        
        for i, text in enumerate(texts):
            y = 25 + (i * 20)
            color = (0, 255, 0) if i == 0 else (255, 255, 255)
            if i == 6:  # Servo position
                color = (0, 255, 255)  # เหลือง
            cv2.putText(frame, text, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        
        return frame
    
    def run(self):
        """เริ่มการทำงานหลัก"""
        print("🚀 Starting YOLOv11 Servo Detection System...")
        print("Controls:")
        print("  'ESC' - Quit")
        print("  'r' - Reset counter and servo")
        print("  's' - Show status")
        print("  't' - Test servo")
        print("  'w' - Manual sweep")
        print("  '1-9' - Move servo to preset positions")
        print("  'h' - Move servo to rest position")
        print("="*70)
        
        try:
            # ใช้โหมด stream ของ YOLOv11
            for r in self.model.predict(
                source=ServoConfig.CAM_ID, 
                stream=True, 
                device=ServoConfig.DEVICE,
                conf=ServoConfig.CONF_THRESHOLD, 
                imgsz=ServoConfig.IMG_SIZE, 
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
                        
                        if cls_id == ServoConfig.TARGET_CLASS_ID and conf >= ServoConfig.CONF_THRESHOLD:
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
                cv2.imshow(ServoConfig.WINDOW_NAME, frame)
                
                # จัดการคีย์บอร์ด
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC เพื่อออก
                    break
                elif key == ord('r'):
                    self.reset_counter()
                elif key == ord('s'):
                    self.show_status()
                elif key == ord('t'):
                    self.arduino.test_servo()
                elif key == ord('w'):
                    self.arduino.perform_bottle_sweep()
                elif key == ord('h'):
                    self.arduino.move_servo_to_rest()
                elif key >= ord('1') and key <= ord('9'):
                    # Preset positions
                    angle = (key - ord('1')) * 20  # 0, 20, 40, ..., 160
                    self.arduino.move_servo_to_angle(angle)
        
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
        print("\n" + "="*70)
        print("📊 YOLOv11 SERVO SYSTEM STATUS")
        print("="*70)
        print(f"🤖 Model: {ServoConfig.MODEL_PATH}")
        print(f"🎯 Target Class ID: {ServoConfig.TARGET_CLASS_ID}")
        print(f"📊 Confidence Threshold: {ServoConfig.CONF_THRESHOLD}")
        print(f"🍼 Total Bottles: {self.bottle_count}")
        print(f"⭐ Total Points: {self.total_points}")
        print(f"🧹 Servo Actions: {self.servo_actions}")
        print(f"🔧 Servo Position: {self.arduino.servo_position}°")
        print(f"🔄 Auto Sweep: {'Enabled' if ServoConfig.AUTO_SERVO_SWEEP else 'Disabled'}")
        print(f"🔌 Arduino: {'Connected' if self.arduino.connected else 'Disconnected'}")
        print(f"🔥 Firebase: Ready")
        print(f"📹 Camera ID: {ServoConfig.CAM_ID}")
        print(f"💻 Device: {ServoConfig.DEVICE}")
        print("="*70 + "\n")
    
    def cleanup(self):
        """ทำความสะอาดเมื่อปิดระบบ"""
        print("🧹 Cleaning up...")
        
        cv2.destroyAllWindows()
        
        if hasattr(self, 'arduino'):
            self.arduino.close()
        
        print("✅ Cleanup completed")

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 YOLOv11 Arduino Firebase Bridge v3.1 (Servo Edition)")
    print("🎯 P2P (Plastic to Point) Detection System with Servo Control")
    print("🤖 Powered by YOLOv11 + Arduino Servo")
    print("="*80)
    
    # ตรวจสอบ dependencies
    try:
        import ultralytics
        print(f"✅ Ultralytics version: {ultralytics.__version__}")
    except ImportError:
        print("❌ Ultralytics not found!")
        print("📦 Install with: pip install ultralytics")
        return
    
    try:
        system = YOLOv11ServoDetectionSystem()
        
        # ทดสอบการเชื่อมต่อ Firebase
        print("\n🔗 Testing Firebase connection...")
        test_data = {
            "test": True,
            "system_start": True,
            "bottle_count": 0
        }
        
        firebase_success = system.firebase.send_data(test_data, "system_test")
        
        if firebase_success:
            print("✅ Firebase connection successful!")
        else:
            print("❌ Firebase connection failed! Data will not be saved.")
            print("💡 Please check your internet connection and Firebase configuration.")
        
        system.run()
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()