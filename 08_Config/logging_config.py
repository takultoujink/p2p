# ========================================
# Logging Configuration for YOLO Arduino Firebase Bridge
# ========================================

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

class LoggingConfig:
    """
    การตั้งค่า Logging ที่ครอบคลุมสำหรับระบบ
    """
    
    def __init__(self, log_dir="logs", app_name="yolo_bridge"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.log_dir.mkdir(exist_ok=True)
        
        # สร้างไฟล์ log ต่างๆ
        self.main_log = self.log_dir / f"{app_name}.log"
        self.error_log = self.log_dir / f"{app_name}_error.log"
        self.debug_log = self.log_dir / f"{app_name}_debug.log"
        self.performance_log = self.log_dir / f"{app_name}_performance.log"
        
    def setup_logging(self, level=logging.INFO, console_output=True):
        """
        ตั้งค่า logging system
        """
        # สร้าง root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # ลบ handlers เก่า
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Formatter สำหรับ log
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | Line:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File Handler สำหรับ main log
        main_handler = logging.handlers.RotatingFileHandler(
            self.main_log,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(level)
        main_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(main_handler)
        
        # File Handler สำหรับ error log
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Console Handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(simple_formatter)
            root_logger.addHandler(console_handler)
        
        # Debug Handler (เฉพาะเมื่อ DEBUG mode)
        if level == logging.DEBUG:
            debug_handler = logging.FileHandler(
                self.debug_log,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(debug_handler)
        
        logging.info(f"Logging system initialized - Level: {logging.getLevelName(level)}")
        return root_logger

class PerformanceLogger:
    """
    Logger สำหรับติดตาม Performance
    """
    
    def __init__(self, log_file="logs/performance.log"):
        self.logger = logging.getLogger("performance")
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # สร้าง handler สำหรับ performance log
        handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_detection_time(self, detection_time, objects_count):
        """บันทึกเวลาการ detect"""
        self.logger.info(f"DETECTION | Time: {detection_time:.3f}s | Objects: {objects_count}")
    
    def log_firebase_time(self, upload_time, success=True):
        """บันทึกเวลาการอัปโหลด Firebase"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"FIREBASE | Time: {upload_time:.3f}s | Status: {status}")
    
    def log_arduino_time(self, response_time, success=True):
        """บันทึกเวลาการตอบสนอง Arduino"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"ARDUINO | Time: {response_time:.3f}s | Status: {status}")

class ErrorHandler:
    """
    Class สำหรับจัดการ Error ที่เกิดขึ้น
    """
    
    def __init__(self):
        self.logger = logging.getLogger("error_handler")
        self.error_count = {}
    
    def handle_camera_error(self, error):
        """จัดการ Error จากกล้อง"""
        self.logger.error(f"Camera Error: {error}")
        self._increment_error_count("camera")
        
        # แนะนำการแก้ไข
        suggestions = [
            "ตรวจสอบการเชื่อมต่อกล้อง",
            "ลองเปลี่ยน camera ID",
            "รีสตาร์ทโปรแกรม"
        ]
        self.logger.info(f"Suggestions: {', '.join(suggestions)}")
    
    def handle_arduino_error(self, error):
        """จัดการ Error จาก Arduino"""
        self.logger.error(f"Arduino Error: {error}")
        self._increment_error_count("arduino")
        
        suggestions = [
            "ตรวจสอบการเชื่อมต่อ USB",
            "ตรวจสอบ COM Port",
            "รีเซ็ต Arduino"
        ]
        self.logger.info(f"Suggestions: {', '.join(suggestions)}")
    
    def handle_firebase_error(self, error):
        """จัดการ Error จาก Firebase"""
        self.logger.error(f"Firebase Error: {error}")
        self._increment_error_count("firebase")
        
        suggestions = [
            "ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต",
            "ตรวจสอบ Firebase URL",
            "ตรวจสอบ Database Rules"
        ]
        self.logger.info(f"Suggestions: {', '.join(suggestions)}")
    
    def handle_yolo_error(self, error):
        """จัดการ Error จาก YOLO"""
        self.logger.error(f"YOLO Error: {error}")
        self._increment_error_count("yolo")
        
        suggestions = [
            "ตรวจสอบไฟล์ model",
            "ตรวจสอบ GPU/CPU memory",
            "ลดขนาดภาพ input"
        ]
        self.logger.info(f"Suggestions: {', '.join(suggestions)}")
    
    def _increment_error_count(self, error_type):
        """นับจำนวน Error แต่ละประเภท"""
        self.error_count[error_type] = self.error_count.get(error_type, 0) + 1
        
        # แจ้งเตือนเมื่อ Error เกินขีดจำกัด
        if self.error_count[error_type] > 5:
            self.logger.warning(f"High error count for {error_type}: {self.error_count[error_type]}")
    
    def get_error_summary(self):
        """สรุปจำนวน Error"""
        return self.error_count

# ========================================
# Utility Functions
# ========================================

def setup_project_logging(debug_mode=False, console_output=True):
    """
    ตั้งค่า logging สำหรับทั้งโปรเจกต์
    """
    level = logging.DEBUG if debug_mode else logging.INFO
    
    config = LoggingConfig()
    logger = config.setup_logging(level=level, console_output=console_output)
    
    # สร้าง performance logger
    perf_logger = PerformanceLogger()
    
    # สร้าง error handler
    error_handler = ErrorHandler()
    
    logging.info("Project logging system initialized successfully")
    
    return logger, perf_logger, error_handler

def log_system_info():
    """บันทึกข้อมูลระบบ"""
    import platform
    import psutil
    
    logger = logging.getLogger("system_info")
    
    logger.info(f"System: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"CPU: {platform.processor()}")
    logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    
    try:
        import cv2
        logger.info(f"OpenCV: {cv2.__version__}")
    except ImportError:
        logger.warning("OpenCV not installed")
    
    try:
        import torch
        logger.info(f"PyTorch: {torch.__version__}")
        logger.info(f"CUDA Available: {torch.cuda.is_available()}")
    except ImportError:
        logger.warning("PyTorch not installed")

if __name__ == "__main__":
    # ทดสอบ logging system
    logger, perf_logger, error_handler = setup_project_logging(debug_mode=True)
    
    # ทดสอบ logs ต่างๆ
    logging.info("Testing logging system")
    logging.warning("This is a warning")
    logging.error("This is an error")
    
    # ทดสอบ performance logging
    perf_logger.log_detection_time(0.123, 3)
    perf_logger.log_firebase_time(0.456, True)
    
    # ทดสอบ error handling
    error_handler.handle_camera_error("Camera not found")
    
    # บันทึกข้อมูลระบบ
    log_system_info()
    
    print("Logging test completed. Check logs/ directory for output files.")