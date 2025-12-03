# ========================================
# Error Handling Utilities for YOLO Arduino Firebase Bridge
# ========================================

import logging
import time
import functools
import traceback
from typing import Callable, Any, Optional, Dict, List
from enum import Enum

class ErrorSeverity(Enum):
    """ระดับความรุนแรงของ Error"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """หมวดหมู่ของ Error"""
    CAMERA = "CAMERA"
    ARDUINO = "ARDUINO"
    FIREBASE = "FIREBASE"
    YOLO = "YOLO"
    NETWORK = "NETWORK"
    SYSTEM = "SYSTEM"
    CONFIG = "CONFIG"

class RetryConfig:
    """การตั้งค่าสำหรับ Retry mechanism"""
    
    def __init__(self, max_attempts=3, delay=1.0, backoff_factor=2.0, max_delay=60.0):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay

class ErrorHandler:
    """
    Class หลักสำหรับจัดการ Error ทั้งหมด
    """
    
    def __init__(self):
        self.logger = logging.getLogger("error_handler")
        self.error_stats = {}
        self.recovery_strategies = {}
        self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self):
        """ตั้งค่ากลยุทธ์การกู้คืนสำหรับ Error แต่ละประเภท"""
        self.recovery_strategies = {
            ErrorCategory.CAMERA: self._recover_camera,
            ErrorCategory.ARDUINO: self._recover_arduino,
            ErrorCategory.FIREBASE: self._recover_firebase,
            ErrorCategory.YOLO: self._recover_yolo,
            ErrorCategory.NETWORK: self._recover_network,
            ErrorCategory.SYSTEM: self._recover_system,
            ErrorCategory.CONFIG: self._recover_config
        }
    
    def handle_error(self, error: Exception, category: ErrorCategory, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Dict = None) -> bool:
        """
        จัดการ Error หลัก
        
        Returns:
            bool: True หากกู้คืนสำเร็จ, False หากไม่สำเร็จ
        """
        context = context or {}
        
        # บันทึก Error
        self._log_error(error, category, severity, context)
        
        # อัปเดตสถิติ
        self._update_error_stats(category, severity)
        
        # พยายามกู้คืน
        if category in self.recovery_strategies:
            try:
                return self.recovery_strategies[category](error, context)
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed for {category.value}: {recovery_error}")
                return False
        
        return False
    
    def _log_error(self, error: Exception, category: ErrorCategory, 
                   severity: ErrorSeverity, context: Dict):
        """บันทึก Error ลงใน log"""
        error_msg = f"[{category.value}] [{severity.value}] {str(error)}"
        
        if context:
            error_msg += f" | Context: {context}"
        
        # เพิ่ม stack trace สำหรับ error ที่รุนแรง
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            error_msg += f"\nStack trace:\n{traceback.format_exc()}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(error_msg)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(error_msg)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(error_msg)
        else:
            self.logger.info(error_msg)
    
    def _update_error_stats(self, category: ErrorCategory, severity: ErrorSeverity):
        """อัปเดตสถิติ Error"""
        key = f"{category.value}_{severity.value}"
        self.error_stats[key] = self.error_stats.get(key, 0) + 1
        
        # แจ้งเตือนเมื่อ Error เกินขีดจำกัด
        if self.error_stats[key] > 10:
            self.logger.warning(f"High error count: {key} = {self.error_stats[key]}")
    
    # Recovery Strategies
    def _recover_camera(self, error: Exception, context: Dict) -> bool:
        """กู้คืนปัญหากล้อง"""
        self.logger.info("Attempting camera recovery...")
        
        try:
            import cv2
            
            # ลองเปิดกล้องใหม่
            for cam_id in range(3):  # ลอง camera ID 0, 1, 2
                cap = cv2.VideoCapture(cam_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        self.logger.info(f"Camera recovered on ID {cam_id}")
                        context['recovered_camera_id'] = cam_id
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Camera recovery failed: {e}")
            return False
    
    def _recover_arduino(self, error: Exception, context: Dict) -> bool:
        """กู้คืนปัญหา Arduino"""
        self.logger.info("Attempting Arduino recovery...")
        
        try:
            import serial
            import serial.tools.list_ports
            
            # หา COM ports ที่ใช้ได้
            ports = serial.tools.list_ports.comports()
            for port in ports:
                try:
                    ser = serial.Serial(port.device, 9600, timeout=1)
                    time.sleep(2)  # รอ Arduino reset
                    ser.write(b"TEST\n")
                    response = ser.readline()
                    ser.close()
                    
                    if response:
                        self.logger.info(f"Arduino recovered on {port.device}")
                        context['recovered_port'] = port.device
                        return True
                        
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Arduino recovery failed: {e}")
            return False
    
    def _recover_firebase(self, error: Exception, context: Dict) -> bool:
        """กู้คืนปัญหา Firebase"""
        self.logger.info("Attempting Firebase recovery...")
        
        try:
            import requests
            
            # ทดสอบการเชื่อมต่อ
            firebase_url = context.get('firebase_url', '')
            if firebase_url:
                response = requests.get(f"{firebase_url}/.json", timeout=10)
                if response.status_code == 200:
                    self.logger.info("Firebase connection recovered")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Firebase recovery failed: {e}")
            return False
    
    def _recover_yolo(self, error: Exception, context: Dict) -> bool:
        """กู้คืนปัญหา YOLO"""
        self.logger.info("Attempting YOLO recovery...")
        
        try:
            # ลองโหลด model ใหม่
            model_path = context.get('model_path', '')
            if model_path:
                # ตรวจสอบว่าไฟล์ model มีอยู่
                import os
                if os.path.exists(model_path):
                    self.logger.info("YOLO model file exists, attempting reload...")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"YOLO recovery failed: {e}")
            return False
    
    def _recover_network(self, error: Exception, context: Dict) -> bool:
        """กู้คืนปัญหาเครือข่าย"""
        self.logger.info("Attempting network recovery...")
        
        try:
            import requests
            
            # ทดสอบการเชื่อมต่ออินเทอร์เน็ต
            response = requests.get("https://www.google.com", timeout=5)
            if response.status_code == 200:
                self.logger.info("Network connection recovered")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Network recovery failed: {e}")
            return False
    
    def _recover_system(self, error: Exception, context: Dict) -> bool:
        """กู้คืนปัญหาระบบ"""
        self.logger.info("Attempting system recovery...")
        
        try:
            import gc
            import psutil
            
            # ล้าง memory
            gc.collect()
            
            # ตรวจสอบ memory usage
            memory_percent = psutil.virtual_memory().percent
            if memory_percent < 90:
                self.logger.info("System memory recovered")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"System recovery failed: {e}")
            return False
    
    def _recover_config(self, error: Exception, context: Dict) -> bool:
        """กู้คืนปัญหา Configuration"""
        self.logger.info("Attempting config recovery...")
        
        try:
            # ใช้ default configuration
            self.logger.info("Using default configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Config recovery failed: {e}")
            return False
    
    def get_error_summary(self) -> Dict:
        """สรุปสถิติ Error"""
        return {
            "error_stats": self.error_stats,
            "total_errors": sum(self.error_stats.values()),
            "categories": list(set(key.split('_')[0] for key in self.error_stats.keys()))
        }

def retry_on_error(retry_config: RetryConfig = None, 
                  error_types: tuple = (Exception,),
                  category: ErrorCategory = ErrorCategory.SYSTEM):
    """
    Decorator สำหรับ retry function เมื่อเกิด error
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = retry_config.delay
            
            for attempt in range(retry_config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except error_types as e:
                    last_exception = e
                    
                    if attempt < retry_config.max_attempts - 1:
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        logging.info(f"Retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        delay = min(delay * retry_config.backoff_factor, retry_config.max_delay)
                    else:
                        logging.error(f"All {retry_config.max_attempts} attempts failed for {func.__name__}")
            
            # หากทุก attempt ล้มเหลว
            error_handler = ErrorHandler()
            error_handler.handle_error(
                last_exception, 
                category, 
                ErrorSeverity.HIGH,
                {"function": func.__name__, "attempts": retry_config.max_attempts}
            )
            
            raise last_exception
        
        return wrapper
    return decorator

def safe_execute(func: Callable, default_return=None, 
                error_category: ErrorCategory = ErrorCategory.SYSTEM,
                error_severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Any:
    """
    Execute function safely with error handling
    """
    try:
        return func()
    except Exception as e:
        error_handler = ErrorHandler()
        error_handler.handle_error(e, error_category, error_severity)
        return default_return

# ========================================
# Specific Error Classes
# ========================================

class CameraError(Exception):
    """Error เฉพาะสำหรับกล้อง"""
    pass

class ArduinoError(Exception):
    """Error เฉพาะสำหรับ Arduino"""
    pass

class FirebaseError(Exception):
    """Error เฉพาะสำหรับ Firebase"""
    pass

class YOLOError(Exception):
    """Error เฉพาะสำหรับ YOLO"""
    pass

class ConfigError(Exception):
    """Error เฉพาะสำหรับ Configuration"""
    pass

# ========================================
# Context Managers
# ========================================

class ErrorContext:
    """Context manager สำหรับจัดการ error ในบล็อกโค้ด"""
    
    def __init__(self, category: ErrorCategory, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.category = category
        self.severity = severity
        self.error_handler = ErrorHandler()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_handler.handle_error(exc_val, self.category, self.severity)
            return True  # Suppress the exception
        return False

# ========================================
# Testing Functions
# ========================================

if __name__ == "__main__":
    # ทดสอบ error handling system
    
    # ตั้งค่า logging
    logging.basicConfig(level=logging.INFO)
    
    # ทดสอบ ErrorHandler
    error_handler = ErrorHandler()
    
    # ทดสอบ error ต่างๆ
    try:
        raise CameraError("Camera not found")
    except CameraError as e:
        error_handler.handle_error(e, ErrorCategory.CAMERA, ErrorSeverity.HIGH)
    
    # ทดสอบ retry decorator
    @retry_on_error(RetryConfig(max_attempts=3, delay=0.1), (ValueError,))
    def test_function():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Random error")
        return "Success!"
    
    try:
        result = test_function()
        print(f"Function result: {result}")
    except ValueError:
        print("Function failed after all retries")
    
    # ทดสอบ safe_execute
    def risky_function():
        raise RuntimeError("Something went wrong")
    
    result = safe_execute(risky_function, default_return="Default value")
    print(f"Safe execute result: {result}")
    
    # ทดสอบ ErrorContext
    with ErrorContext(ErrorCategory.SYSTEM):
        raise SystemError("System error in context")
    
    print("Error handling test completed")
    print("Error summary:", error_handler.get_error_summary())