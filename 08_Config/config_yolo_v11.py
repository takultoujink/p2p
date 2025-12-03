#!/usr/bin/env python3
"""
YOLOv11 Arduino Firebase Bridge - Configuration File
ไฟล์ config แยกสำหรับการตั้งค่าระบบ

การใช้งาน:
1. คัดลอกไฟล์นี้เป็น config_yolo_v11_local.py
2. แก้ไขค่าต่างๆ ตามต้องการ
3. ระบบจะใช้ค่าจาก local config อัตโนมัติ

Author: P2P Team
Version: 3.0
"""

import os

class YOLOv11Config:
    """
    การตั้งค่าหลักสำหรับระบบ YOLOv11 Detection
    """
    
    # ========================================
    # Arduino Communication Settings
    # ========================================
    
    # COM Port Settings
    ARDUINO_PORT = "COM5"  # เปลี่ยนตาม COM port ของคุณ
    # วิธีหา COM port:
    # Windows: Device Manager → Ports (COM & LPT)
    # หรือใช้คำสั่ง: mode ใน Command Prompt
    
    ARDUINO_BAUD_RATE = 9600
    ARDUINO_TIMEOUT = 1
    SEND_DELAY = 1.0  # เวลาระหว่างส่งสัญญาณไป Arduino (วินาที)
    
    # ========================================
    # YOLOv11 Model Settings
    # ========================================
    
    # Model Configuration
    MODEL_PATH = "best.pt"  # path ไปยัง YOLOv11 model
    # ตัวอย่าง paths:
    # "best.pt" - custom trained model
    # "yolov8n.pt" - nano model (เร็ว, แม่นยำน้อย)
    # "yolov8s.pt" - small model (สมดุล)
    # "yolov8m.pt" - medium model (ช้า, แม่นยำมาก)
    # "models/bottle_detection.pt" - model ในโฟลเดอร์ย่อย
    
    TARGET_CLASS_ID = 0  # Class ID ของขวดพลาสติกใน dataset
    # หาก train เอง ให้ตรวจสอบใน classes.txt หรือ yaml file
    # COCO dataset: 0=person, 39=bottle, 44=cup
    
    CONF_THRESHOLD = 0.80  # Confidence threshold (0.0-1.0)
    # 0.90 = แม่นยำมาก, false positive น้อย
    # 0.70 = แม่นยำปานกลาง, ตรวจจับได้มากขึ้น
    # 0.50 = แม่นยำน้อย, ตรวจจับได้เยอะ
    
    # ========================================
    # Camera Settings
    # ========================================
    
    CAM_ID = 1  # Camera index
    # 0 = กล้องหลัก (built-in webcam)
    # 1 = กล้องรอง (USB camera)
    # 2, 3, ... = กล้องเพิ่มเติม
    
    DEVICE = "cpu"  # Processing device
    # "cpu" = ใช้ CPU (ช้ากว่า แต่ทำงานได้ทุกเครื่อง)
    # "cuda" = ใช้ NVIDIA GPU (เร็วมาก ต้องมี CUDA)
    # "mps" = ใช้ Apple Silicon GPU (สำหรับ Mac M1/M2)
    
    IMG_SIZE = 640  # Input image size
    # 320 = เร็วมาก, แม่นยำน้อย
    # 640 = สมดุล (แนะนำ)
    # 1280 = ช้า, แม่นยำมาก
    
    # ========================================
    # Firebase Settings
    # ========================================
    
    FIREBASE_URL = "https://takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app"
    # เปลี่ยนเป็น Firebase URL ของคุณ
    # รูปแบบ: https://your-project-name-default-rtdb.region.firebasedatabase.app
    
    USER_ID = "yolo_v11_user"  # User identifier สำหรับ Firebase
    # เปลี่ยนเป็นชื่อที่ต้องการ เช่น "john_doe", "station_01"
    
    # ========================================
    # Display Settings
    # ========================================
    
    WINDOW_NAME = "YOLOv11 P2P Detection (ESC to quit)"
    WINDOW_WIDTH = 1280  # ความกว้างหน้าต่าง (0 = auto)
    WINDOW_HEIGHT = 720  # ความสูงหน้าต่าง (0 = auto)
    
    # UI Colors (BGR format)
    UI_COLOR_PRIMARY = (0, 255, 0)    # เขียว
    UI_COLOR_SECONDARY = (255, 255, 255)  # ขาว
    UI_COLOR_WARNING = (0, 165, 255)   # ส้ม
    UI_COLOR_ERROR = (0, 0, 255)      # แดง
    
    # ========================================
    # Detection Settings
    # ========================================
    
    DETECTION_COOLDOWN = 2.0  # เวลารอระหว่างการนับขวด (วินาที)
    # 1.0 = ตอบสนองเร็ว, อาจนับซ้ำ
    # 3.0 = ตอบสนองช้า, ไม่นับซ้ำ
    
    POINTS_PER_BOTTLE = 10  # คะแนนต่อขวด
    
    # Multi-object detection
    COUNT_MULTIPLE_BOTTLES = True  # นับขวดหลายใบในเฟรมเดียว
    MAX_BOTTLES_PER_FRAME = 5      # จำนวนขวดสูงสุดที่นับในเฟรมเดียว
    
    # ========================================
    # Performance Settings
    # ========================================
    
    # Frame processing
    SKIP_FRAMES = 0  # ข้ามเฟรมเพื่อเพิ่มความเร็ว (0 = ไม่ข้าม)
    MAX_FPS = 30     # FPS สูงสุด (0 = ไม่จำกัด)
    
    # Memory management
    CLEAR_CACHE_INTERVAL = 100  # ล้าง cache ทุกกี่เฟรม
    
    # ========================================
    # Logging Settings
    # ========================================
    
    VERBOSE_LOGGING = True   # แสดง log ละเอียด
    LOG_DETECTIONS = True    # log การตรวจจับ
    LOG_FIREBASE = True      # log การส่ง Firebase
    LOG_ARDUINO = True       # log การส่ง Arduino
    
    # ========================================
    # Advanced Settings
    # ========================================
    
    # YOLO Advanced
    IOU_THRESHOLD = 0.45     # IoU threshold สำหรับ NMS
    MAX_DETECTIONS = 300     # จำนวน detection สูงสุดต่อเฟรม
    
    # Firebase Advanced
    FIREBASE_TIMEOUT = 10    # Timeout สำหรับ Firebase (วินาที)
    FIREBASE_RETRY_COUNT = 3 # จำนวนครั้งที่ลองใหม่
    
    # Arduino Advanced
    ARDUINO_RETRY_COUNT = 3  # จำนวนครั้งที่ลองเชื่อมต่อใหม่
    ARDUINO_RESET_DELAY = 2  # เวลารอหลัง Arduino reset (วินาที)
    
    # ========================================
    # Experimental Features
    # ========================================
    
    ENABLE_TRACKING = False  # เปิดใช้ object tracking
    ENABLE_ANALYTICS = False # เปิดใช้ analytics
    SAVE_DETECTIONS = False  # บันทึกภาพที่ตรวจจับได้
    
    # ========================================
    # Auto-detection Settings
    # ========================================
    
    @classmethod
    def auto_detect_camera(cls):
        """หา camera ID ที่ใช้งานได้อัตโนมัติ"""
        import cv2
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                if ret:
                    print(f"📹 Found working camera at index {i}")
                    return i
        print("❌ No working camera found")
        return 0
    
    @classmethod
    def auto_detect_arduino_port(cls):
        """หา Arduino COM port อัตโนมัติ (Windows)"""
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'Arduino' in port.description or 'CH340' in port.description:
                print(f"🔌 Found Arduino at {port.device}")
                return port.device
        
        if ports:
            print(f"🔌 Using first available port: {ports[0].device}")
            return ports[0].device
        
        print("❌ No COM ports found")
        return "COM1"
    
    @classmethod
    def detect_gpu_support(cls):
        """ตรวจสอบการรองรับ GPU"""
        try:
            import torch
            if torch.cuda.is_available():
                print(f"🚀 CUDA GPU detected: {torch.cuda.get_device_name()}")
                return "cuda"
        except ImportError:
            pass
        
        try:
            import platform
            if platform.system() == "Darwin" and "arm" in platform.machine().lower():
                print("🍎 Apple Silicon detected")
                return "mps"
        except:
            pass
        
        print("💻 Using CPU")
        return "cpu"
    
    @classmethod
    def get_optimal_config(cls):
        """สร้าง config ที่เหมาะสมอัตโนมัติ"""
        config = cls()
        
        # Auto-detect settings
        config.CAM_ID = cls.auto_detect_camera()
        config.ARDUINO_PORT = cls.auto_detect_arduino_port()
        config.DEVICE = cls.detect_gpu_support()
        
        # Adjust settings based on device
        if config.DEVICE == "cpu":
            config.IMG_SIZE = 416  # ลดขนาดสำหรับ CPU
            config.SKIP_FRAMES = 1  # ข้ามเฟรมเพื่อเพิ่มความเร็ว
        
        return config

# ========================================
# Local Configuration Override
# ========================================

def load_local_config():
    """
    โหลด config จากไฟล์ local (ถ้ามี)
    ไฟล์ local จะ override ค่า default
    """
    try:
        from config_yolo_v11_local import YOLOv11LocalConfig
        print("✅ Local configuration loaded")
        return YOLOv11LocalConfig()
    except ImportError:
        print("💡 Using default configuration")
        print("💡 Create 'config_yolo_v11_local.py' to customize settings")
        return YOLOv11Config()

# ========================================
# Configuration Validation
# ========================================

def validate_config(config):
    """
    ตรวจสอบความถูกต้องของ configuration
    """
    errors = []
    warnings = []
    
    # ตรวจสอบ model file
    if not os.path.exists(config.MODEL_PATH):
        errors.append(f"Model file not found: {config.MODEL_PATH}")
    
    # ตรวจสอบ confidence threshold
    if not 0.0 <= config.CONF_THRESHOLD <= 1.0:
        errors.append(f"Invalid confidence threshold: {config.CONF_THRESHOLD}")
    
    # ตรวจสอบ camera ID
    if config.CAM_ID < 0:
        warnings.append(f"Negative camera ID: {config.CAM_ID}")
    
    # ตรวจสอบ Firebase URL
    if not config.FIREBASE_URL.startswith("https://"):
        warnings.append("Firebase URL should start with https://")
    
    # แสดงผลลัพธ์
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    if warnings:
        print("⚠️  Configuration warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    print("✅ Configuration validated")
    return True

# ========================================
# Export for use in main script
# ========================================

if __name__ == "__main__":
    # ทดสอบ configuration
    print("🔧 Testing YOLOv11 Configuration")
    print("=" * 50)
    
    config = load_local_config()
    
    print(f"Model Path: {config.MODEL_PATH}")
    print(f"Arduino Port: {config.ARDUINO_PORT}")
    print(f"Camera ID: {config.CAM_ID}")
    print(f"Device: {config.DEVICE}")
    print(f"Firebase URL: {config.FIREBASE_URL}")
    
    validate_config(config)
    
    print("\n💡 To customize settings:")
    print("1. Copy this file to 'config_yolo_v11_local.py'")
    print("2. Rename class to 'YOLOv11LocalConfig'")
    print("3. Modify values as needed")