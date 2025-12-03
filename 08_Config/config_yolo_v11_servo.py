#!/usr/bin/env python3
"""
YOLOv11 Arduino Firebase Bridge Configuration (Servo Edition)
ไฟล์ config แยกสำหรับระบบ YOLOv11 พร้อม Servo Control

Author: P2P Team
Version: 3.1 (Servo Edition)
"""

import os
import json
import serial.tools.list_ports
import cv2
import platform
from typing import Dict, List, Optional, Tuple

class YOLOv11ServoConfig:
    """การตั้งค่าหลักสำหรับระบบ YOLOv11 Servo Detection"""
    
    # ========================================
    # Arduino & Servo Settings
    # ========================================
    ARDUINO_PORT = "COM5"  # แก้ตามพอร์ต Arduino ของคุณ
    ARDUINO_BAUD_RATE = 9600
    ARDUINO_TIMEOUT = 1
    SEND_DELAY = 1.0  # เวลาระหว่างส่งค่าไป Arduino (วินาที)
    
    # Servo Motor Settings
    SERVO_REST_POSITION = 90      # ตำแหน่งพัก (องศา)
    SERVO_SWEEP_POSITION = 45     # ตำแหน่งปัดขวด (องศา)
    SERVO_RETURN_POSITION = 135   # ตำแหน่งกลับ (องศา)
    SERVO_DELAY = 0.5            # เวลาหน่วงระหว่างการเคลื่อนไหว (วินาที)
    AUTO_SERVO_SWEEP = True       # เปิดใช้การปัดขวดอัตโนมัติ
    SERVO_TEST_ANGLES = [0, 45, 90, 135, 180]  # มุมสำหรับทดสอบ
    
    # ========================================
    # YOLOv11 Settings
    # ========================================
    MODEL_PATH = "best.pt"        # path ไปยัง YOLOv11 model
    TARGET_CLASS_ID = 0           # ID ของ plastic bottle ใน dataset
    CONF_THRESHOLD = 0.80         # Confidence ขั้นต่ำ
    IOU_THRESHOLD = 0.45          # IoU threshold สำหรับ NMS
    MAX_DETECTIONS = 300          # จำนวนการตรวจจับสูงสุด
    
    # ========================================
    # Camera Settings
    # ========================================
    CAM_ID = 1                    # Camera ID (0, 1, 2...)
    IMG_SIZE = 640                # ขนาดภาพสำหรับ inference
    FPS_TARGET = 30               # FPS เป้าหมาย
    DEVICE = "cpu"                # "cpu" หรือ "cuda" สำหรับ GPU
    
    # Camera Resolution
    CAM_WIDTH = 1280
    CAM_HEIGHT = 720
    
    # ========================================
    # Firebase Settings
    # ========================================
    FIREBASE_URL = "https://takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app"
    USER_ID = "yolo_v11_servo_user"
    FIREBASE_TIMEOUT = 10         # Timeout สำหรับ Firebase requests
    
    # Firebase Paths
    BOTTLE_DATA_PATH = "bottle_servo_data"
    SERVO_DATA_PATH = "servo_data"
    SYSTEM_STATUS_PATH = "system_status"
    
    # ========================================
    # Performance Settings
    # ========================================
    DETECTION_COOLDOWN = 2.0      # เวลารอระหว่างการนับขวด (วินาที)
    POINTS_PER_BOTTLE = 10        # คะแนนต่อขวด
    MAX_BOTTLE_COUNT = 9999       # จำนวนขวดสูงสุด
    
    # Threading Settings
    USE_THREADING = True          # ใช้ threading สำหรับ Firebase
    THREAD_TIMEOUT = 5.0          # Timeout สำหรับ threads
    
    # ========================================
    # Display Settings
    # ========================================
    WINDOW_NAME = "YOLOv11 P2P Detection with Servo Control (ESC to quit)"
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    
    # Colors (BGR format)
    COLOR_GREEN = (0, 255, 0)
    COLOR_RED = (0, 0, 255)
    COLOR_BLUE = (255, 0, 0)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    
    # Font Settings
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.45
    FONT_THICKNESS = 1
    
    # ========================================
    # Logging Settings
    # ========================================
    LOG_LEVEL = "INFO"            # DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE = True            # บันทึก log ลงไฟล์
    LOG_FILE = "yolo_v11_servo.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    
    # ========================================
    # Advanced Settings
    # ========================================
    ENABLE_GPU = True             # พยายามใช้ GPU ถ้ามี
    ENABLE_HALF_PRECISION = False # ใช้ FP16 (ต้องมี GPU)
    ENABLE_TensorRT = False       # ใช้ TensorRT optimization
    
    # Error Handling
    MAX_RETRIES = 3               # จำนวนครั้งที่ลองใหม่
    RETRY_DELAY = 1.0             # เวลารอระหว่างการลองใหม่
    
    # System Monitoring
    MONITOR_SYSTEM = True         # ติดตาม CPU, Memory usage
    MONITOR_INTERVAL = 30.0       # ช่วงเวลาการติดตาม (วินาที)
    
    @classmethod
    def auto_detect_camera(cls) -> int:
        """ตรวจหา Camera ID ที่ใช้งานได้"""
        print("🔍 Auto-detecting camera...")
        
        for cam_id in range(5):  # ทดสอบ camera 0-4
            try:
                cap = cv2.VideoCapture(cam_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✅ Camera found at ID: {cam_id}")
                        cap.release()
                        return cam_id
                cap.release()
            except Exception as e:
                continue
        
        print("❌ No camera detected, using default ID: 0")
        return 0
    
    @classmethod
    def auto_detect_arduino_port(cls) -> str:
        """ตรวจหา Arduino port อัตโนมัติ"""
        print("🔍 Auto-detecting Arduino port...")
        
        ports = serial.tools.list_ports.comports()
        arduino_ports = []
        
        for port in ports:
            # ค้นหา Arduino ตาม description
            if any(keyword in port.description.lower() for keyword in 
                   ['arduino', 'ch340', 'cp210', 'ftdi', 'usb serial']):
                arduino_ports.append(port.device)
                print(f"✅ Potential Arduino port: {port.device} - {port.description}")
        
        if arduino_ports:
            return arduino_ports[0]  # ใช้พอร์ตแรกที่เจอ
        
        # ถ้าไม่เจอ ใช้ default ตาม OS
        if platform.system() == "Windows":
            default_port = "COM5"
        else:
            default_port = "/dev/ttyUSB0"
        
        print(f"❌ No Arduino detected, using default: {default_port}")
        return default_port
    
    @classmethod
    def detect_gpu_support(cls) -> str:
        """ตรวจสอบการรองรับ GPU"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"✅ CUDA GPU detected: {gpu_name}")
                return "cuda"
        except ImportError:
            pass
        
        print("💻 Using CPU for inference")
        return "cpu"
    
    @classmethod
    def create_optimized_config(cls) -> 'YOLOv11ServoConfig':
        """สร้าง config ที่เหมาะสมกับระบบ"""
        config = cls()
        
        # Auto-detect settings
        config.CAM_ID = cls.auto_detect_camera()
        config.ARDUINO_PORT = cls.auto_detect_arduino_port()
        config.DEVICE = cls.detect_gpu_support()
        
        # Optimize based on device
        if config.DEVICE == "cuda":
            config.IMG_SIZE = 640
            config.FPS_TARGET = 30
            config.ENABLE_HALF_PRECISION = True
        else:
            config.IMG_SIZE = 416  # เล็กลงสำหรับ CPU
            config.FPS_TARGET = 15
            config.ENABLE_HALF_PRECISION = False
        
        return config
    
    def get_servo_preset_positions(self) -> Dict[str, int]:
        """ตำแหน่ง Servo ที่กำหนดไว้"""
        return {
            "rest": self.SERVO_REST_POSITION,
            "sweep": self.SERVO_SWEEP_POSITION,
            "return": self.SERVO_RETURN_POSITION,
            "left_max": 0,
            "left_mid": 45,
            "center": 90,
            "right_mid": 135,
            "right_max": 180
        }
    
    def get_keyboard_controls(self) -> Dict[str, str]:
        """คำอธิบายการควบคุมด้วยคีย์บอร์ด"""
        return {
            "ESC": "Quit system",
            "r": "Reset counter and servo",
            "s": "Show system status",
            "t": "Test servo motor",
            "w": "Manual bottle sweep",
            "h": "Move servo to rest position",
            "1-9": "Move servo to preset positions (0°-160°)",
            "q": "Quick servo test",
            "p": "Toggle auto-sweep mode",
            "c": "Calibrate servo",
            "d": "Debug mode toggle"
        }
    
    def validate_config(self) -> List[str]:
        """ตรวจสอบความถูกต้องของ config"""
        errors = []
        
        # ตรวจสอบ Model file
        if not os.path.exists(self.MODEL_PATH):
            errors.append(f"Model file not found: {self.MODEL_PATH}")
        
        # ตรวจสอบ Servo angles
        if not 0 <= self.SERVO_REST_POSITION <= 180:
            errors.append(f"Invalid servo rest position: {self.SERVO_REST_POSITION}")
        
        if not 0 <= self.SERVO_SWEEP_POSITION <= 180:
            errors.append(f"Invalid servo sweep position: {self.SERVO_SWEEP_POSITION}")
        
        if not 0 <= self.SERVO_RETURN_POSITION <= 180:
            errors.append(f"Invalid servo return position: {self.SERVO_RETURN_POSITION}")
        
        # ตรวจสอบ Confidence threshold
        if not 0.0 <= self.CONF_THRESHOLD <= 1.0:
            errors.append(f"Invalid confidence threshold: {self.CONF_THRESHOLD}")
        
        # ตรวจสอบ Firebase URL
        if not self.FIREBASE_URL.startswith("https://"):
            errors.append(f"Invalid Firebase URL: {self.FIREBASE_URL}")
        
        return errors
    
    def save_to_file(self, filename: str = "config_local.json") -> bool:
        """บันทึก config ลงไฟล์"""
        try:
            config_dict = {
                "arduino_port": self.ARDUINO_PORT,
                "model_path": self.MODEL_PATH,
                "target_class_id": self.TARGET_CLASS_ID,
                "conf_threshold": self.CONF_THRESHOLD,
                "cam_id": self.CAM_ID,
                "device": self.DEVICE,
                "firebase_url": self.FIREBASE_URL,
                "user_id": self.USER_ID,
                "servo_rest_position": self.SERVO_REST_POSITION,
                "servo_sweep_position": self.SERVO_SWEEP_POSITION,
                "servo_return_position": self.SERVO_RETURN_POSITION,
                "auto_servo_sweep": self.AUTO_SERVO_SWEEP,
                "servo_delay": self.SERVO_DELAY
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Config saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save config: {e}")
            return False
    
    def print_config_summary(self):
        """แสดงสรุป config"""
        print("\n" + "="*80)
        print("📋 YOLOv11 SERVO SYSTEM CONFIGURATION")
        print("="*80)
        print(f"🤖 Model: {self.MODEL_PATH}")
        print(f"🎯 Target Class: {self.TARGET_CLASS_ID}")
        print(f"📊 Confidence: {self.CONF_THRESHOLD}")
        print(f"📹 Camera: {self.CAM_ID}")
        print(f"💻 Device: {self.DEVICE}")
        print(f"🔌 Arduino: {self.ARDUINO_PORT}")
        print(f"🔧 Servo Rest: {self.SERVO_REST_POSITION}°")
        print(f"🧹 Servo Sweep: {self.SERVO_SWEEP_POSITION}°")
        print(f"↩️  Servo Return: {self.SERVO_RETURN_POSITION}°")
        print(f"🔄 Auto Sweep: {'Enabled' if self.AUTO_SERVO_SWEEP else 'Disabled'}")
        print(f"🔥 Firebase: {self.FIREBASE_URL.split('.')[0]}...")
        print(f"👤 User ID: {self.USER_ID}")
        print("="*80 + "\n")

def load_local_config(filename: str = "config_local.json") -> Optional[YOLOv11ServoConfig]:
    """โหลด config จากไฟล์ local"""
    if not os.path.exists(filename):
        print(f"📄 Local config not found: {filename}")
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        config = YOLOv11ServoConfig()
        
        # อัปเดต config จากไฟล์
        for key, value in config_dict.items():
            if hasattr(config, key.upper()):
                setattr(config, key.upper(), value)
        
        print(f"✅ Local config loaded: {filename}")
        return config
        
    except Exception as e:
        print(f"❌ Failed to load local config: {e}")
        return None

def validate_config(config: YOLOv11ServoConfig) -> bool:
    """ตรวจสอบความถูกต้องของ config"""
    errors = config.validate_config()
    
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Configuration validation passed")
    return True

def create_default_config() -> YOLOv11ServoConfig:
    """สร้าง config เริ่มต้น"""
    print("🔧 Creating default configuration...")
    return YOLOv11ServoConfig.create_optimized_config()

if __name__ == "__main__":
    # ทดสอบ config
    print("🧪 Testing YOLOv11 Servo Configuration...")
    
    # สร้าง config เริ่มต้น
    config = create_default_config()
    
    # แสดงสรุป
    config.print_config_summary()
    
    # ตรวจสอบความถูกต้อง
    if validate_config(config):
        print("✅ Configuration test passed!")
        
        # บันทึกลงไฟล์
        config.save_to_file("config_test.json")
    else:
        print("❌ Configuration test failed!")
    
    # แสดงการควบคุม
    print("\n🎮 Keyboard Controls:")
    controls = config.get_keyboard_controls()
    for key, description in controls.items():
        print(f"   {key:8} - {description}")
    
    # แสดงตำแหน่ง Servo
    print("\n🔧 Servo Preset Positions:")
    positions = config.get_servo_preset_positions()
    for name, angle in positions.items():
        print(f"   {name:12} - {angle:3}°")