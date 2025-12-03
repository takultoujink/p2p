# ========================================
# Test Utilities and Helper Functions
# ========================================

import pytest
import numpy as np
import cv2
import os
import sys
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from contextlib import contextmanager

class TestDataGenerator:
    """สร้างข้อมูลทดสอบสำหรับ unit tests"""
    
    @staticmethod
    def create_test_image(width=640, height=480, channels=3, dtype=np.uint8):
        """สร้างภาพทดสอบ"""
        if channels == 1:
            return np.random.randint(0, 255, (height, width), dtype=dtype)
        else:
            return np.random.randint(0, 255, (height, width, channels), dtype=dtype)
    
    @staticmethod
    def create_test_detection_data(count=1):
        """สร้างข้อมูล detection ทดสอบ"""
        detections = []
        for i in range(count):
            detection = {
                "timestamp": datetime.now().isoformat(),
                "object_type": f"object_{i}",
                "confidence": round(0.5 + (i * 0.1) % 0.5, 2),
                "bbox": [i*10, i*10, (i+1)*50, (i+1)*50],
                "image_path": f"test_image_{i}.jpg"
            }
            detections.append(detection)
        return detections if count > 1 else detections[0]
    
    @staticmethod
    def create_test_config():
        """สร้าง configuration ทดสอบ"""
        return {
            "MODEL_PATH": "test_model.pt",
            "CONF_THRESHOLD": 0.5,
            "CAM_ID": 0,
            "ARDUINO_PORT": "COM3",
            "ARDUINO_BAUDRATE": 9600,
            "ARDUINO_TIMEOUT": 1.0,
            "CLASS_NAMES": ["bottle", "can", "plastic", "paper"],
            "FIREBASE_CONFIG": {
                "project_id": "test-project",
                "private_key": "test-key"
            }
        }
    
    @staticmethod
    def create_mock_yolo_results(num_detections=1):
        """สร้าง mock YOLO results"""
        mock_results = Mock()
        mock_results.boxes = Mock()
        
        # สร้าง bounding boxes
        bboxes = []
        confidences = []
        classes = []
        
        for i in range(num_detections):
            bboxes.append([i*50, i*50, (i+1)*100, (i+1)*100])
            confidences.append(0.8 - i*0.1)
            classes.append(i % 4)  # 4 classes
        
        mock_results.boxes.xyxy = np.array(bboxes)
        mock_results.boxes.conf = np.array(confidences)
        mock_results.boxes.cls = np.array(classes)
        
        return [mock_results]

class TestFileManager:
    """จัดการไฟล์ทดสอบ"""
    
    def __init__(self):
        self.temp_dirs = []
        self.temp_files = []
    
    def create_temp_dir(self, prefix="test_"):
        """สร้าง temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, content="", suffix=".txt", prefix="test_"):
        """สร้าง temporary file"""
        fd, temp_file = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        self.temp_files.append(temp_file)
        return temp_file
    
    def create_test_image_file(self, width=640, height=480, filename=None):
        """สร้างไฟล์ภาพทดสอบ"""
        if filename is None:
            filename = self.create_temp_file(suffix=".jpg")
        
        # สร้างภาพทดสอบ
        image = TestDataGenerator.create_test_image(width, height)
        cv2.imwrite(filename, image)
        return filename
    
    def create_test_config_file(self, config_data=None):
        """สร้างไฟล์ config ทดสอบ"""
        if config_data is None:
            config_data = TestDataGenerator.create_test_config()
        
        config_file = self.create_temp_file(suffix=".json")
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        return config_file
    
    def cleanup(self):
        """ลบไฟล์และโฟลเดอร์ทดสอบ"""
        # ลบไฟล์
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not remove {temp_file}: {e}")
        
        # ลบโฟลเดอร์
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not remove {temp_dir}: {e}")
        
        self.temp_files.clear()
        self.temp_dirs.clear()

class MockFactory:
    """สร้าง mock objects สำหรับ testing"""
    
    @staticmethod
    def create_mock_camera():
        """สร้าง mock camera"""
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, TestDataGenerator.create_test_image())
        mock_camera.release.return_value = None
        mock_camera.set.return_value = True
        mock_camera.get.return_value = 30.0  # FPS
        return mock_camera
    
    @staticmethod
    def create_mock_serial():
        """สร้าง mock serial connection"""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.write.return_value = 10
        mock_serial.read.return_value = b'OK\n'
        mock_serial.readline.return_value = b'OK\n'
        mock_serial.in_waiting = 0
        mock_serial.close.return_value = None
        return mock_serial
    
    @staticmethod
    def create_mock_firebase_client():
        """สร้าง mock Firebase client"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_document = Mock()
        
        # Setup mock chain
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_document
        mock_collection.add.return_value = (None, Mock(id="test_doc_id"))
        mock_document.set.return_value = None
        mock_document.get.return_value = Mock(
            exists=True, 
            to_dict=lambda: TestDataGenerator.create_test_detection_data()
        )
        mock_document.update.return_value = None
        mock_document.delete.return_value = None
        
        return mock_client
    
    @staticmethod
    def create_mock_yolo_model():
        """สร้าง mock YOLO model"""
        mock_model = Mock()
        mock_model.predict.return_value = TestDataGenerator.create_mock_yolo_results()
        return mock_model

class PerformanceTimer:
    """วัดประสิทธิภาพการทำงาน"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.measurements = []
    
    def start(self):
        """เริ่มวัดเวลา"""
        self.start_time = time.time()
    
    def stop(self):
        """หยุดวัดเวลา"""
        self.end_time = time.time()
        if self.start_time:
            duration = self.end_time - self.start_time
            self.measurements.append(duration)
            return duration
        return None
    
    @contextmanager
    def measure(self):
        """Context manager สำหรับวัดเวลา"""
        self.start()
        try:
            yield self
        finally:
            self.stop()
    
    def get_average(self):
        """คำนวณเวลาเฉลี่ย"""
        if not self.measurements:
            return 0
        return sum(self.measurements) / len(self.measurements)
    
    def get_stats(self):
        """ได้สถิติการวัดเวลา"""
        if not self.measurements:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "count": len(self.measurements),
            "avg": self.get_average(),
            "min": min(self.measurements),
            "max": max(self.measurements),
            "total": sum(self.measurements)
        }

class TestValidator:
    """ตรวจสอบความถูกต้องของข้อมูลทดสอบ"""
    
    @staticmethod
    def validate_image(image):
        """ตรวจสอบความถูกต้องของภาพ"""
        if image is None:
            return False, "Image is None"
        
        if not isinstance(image, np.ndarray):
            return False, "Image is not numpy array"
        
        if len(image.shape) not in [2, 3]:
            return False, "Image must be 2D or 3D array"
        
        if len(image.shape) == 3 and image.shape[2] not in [1, 3, 4]:
            return False, "Image must have 1, 3, or 4 channels"
        
        return True, "Valid image"
    
    @staticmethod
    def validate_detection_result(result):
        """ตรวจสอบผลลัพธ์การ detect"""
        if not isinstance(result, list):
            return False, "Result must be a list"
        
        for i, detection in enumerate(result):
            if not isinstance(detection, dict):
                return False, f"Detection {i} must be a dictionary"
            
            required_fields = ["bbox", "confidence", "class_name"]
            for field in required_fields:
                if field not in detection:
                    return False, f"Detection {i} missing field: {field}"
            
            # ตรวจสอบ bbox
            bbox = detection["bbox"]
            if not isinstance(bbox, list) or len(bbox) != 4:
                return False, f"Detection {i} bbox must be list of 4 numbers"
            
            try:
                x1, y1, x2, y2 = bbox
                if x1 >= x2 or y1 >= y2:
                    return False, f"Detection {i} bbox coordinates invalid"
            except (ValueError, TypeError):
                return False, f"Detection {i} bbox contains non-numeric values"
            
            # ตรวจสอบ confidence
            confidence = detection["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                return False, f"Detection {i} confidence must be between 0 and 1"
        
        return True, "Valid detection result"
    
    @staticmethod
    def validate_arduino_response(response):
        """ตรวจสอบ response จาก Arduino"""
        if response is None:
            return False, "Response is None"
        
        if not isinstance(response, str):
            return False, "Response must be string"
        
        valid_responses = ["OK", "ERROR", "READY", "SERVO_MOVED"]
        
        for valid_resp in valid_responses:
            if valid_resp in response.upper():
                return True, "Valid Arduino response"
        
        return False, "Unknown Arduino response"

class TestReporter:
    """รายงานผลการทดสอบ"""
    
    def __init__(self):
        self.test_results = []
        self.performance_data = []
    
    def add_test_result(self, test_name, status, duration=None, error=None):
        """เพิ่มผลการทดสอบ"""
        result = {
            "test_name": test_name,
            "status": status,  # "PASS", "FAIL", "SKIP"
            "duration": duration,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
    
    def add_performance_data(self, test_name, metric_name, value, unit="ms"):
        """เพิ่มข้อมูลประสิทธิภาพ"""
        perf_data = {
            "test_name": test_name,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        self.performance_data.append(perf_data)
    
    def generate_summary(self):
        """สร้างสรุปผลการทดสอบ"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        # คำนวณเวลารวม
        total_duration = sum(r["duration"] for r in self.test_results if r["duration"])
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "average_duration": total_duration / total_tests if total_tests > 0 else 0
        }
        
        return summary
    
    def save_report(self, filename):
        """บันทึกรายงานเป็นไฟล์"""
        report = {
            "summary": self.generate_summary(),
            "test_results": self.test_results,
            "performance_data": self.performance_data,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

# ========================================
# Pytest Fixtures
# ========================================

@pytest.fixture(scope="session")
def test_data_generator():
    """Fixture สำหรับ TestDataGenerator"""
    return TestDataGenerator()

@pytest.fixture(scope="function")
def test_file_manager():
    """Fixture สำหรับ TestFileManager"""
    manager = TestFileManager()
    yield manager
    manager.cleanup()

@pytest.fixture(scope="function")
def mock_factory():
    """Fixture สำหรับ MockFactory"""
    return MockFactory()

@pytest.fixture(scope="function")
def performance_timer():
    """Fixture สำหรับ PerformanceTimer"""
    return PerformanceTimer()

@pytest.fixture(scope="function")
def test_validator():
    """Fixture สำหรับ TestValidator"""
    return TestValidator()

@pytest.fixture(scope="session")
def test_reporter():
    """Fixture สำหรับ TestReporter"""
    return TestReporter()

# ========================================
# Custom Pytest Markers
# ========================================

def pytest_configure(config):
    """กำหนด custom markers"""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "hardware: mark test as requiring hardware"
    )

# ========================================
# Test Decorators
# ========================================

def requires_hardware(func):
    """Decorator สำหรับ tests ที่ต้องใช้ hardware"""
    return pytest.mark.hardware(func)

def performance_test(func):
    """Decorator สำหรับ performance tests"""
    return pytest.mark.performance(func)

def integration_test(func):
    """Decorator สำหรับ integration tests"""
    return pytest.mark.integration(func)

def slow_test(func):
    """Decorator สำหรับ slow tests"""
    return pytest.mark.slow(func)

# ========================================
# Helper Functions
# ========================================

def skip_if_no_camera():
    """Skip test ถ้าไม่มีกล้อง"""
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            pytest.skip("No camera available")
        cap.release()
    except Exception:
        pytest.skip("Camera not accessible")

def skip_if_no_arduino():
    """Skip test ถ้าไม่มี Arduino"""
    try:
        import serial
        # ลองเชื่อมต่อ Arduino
        ser = serial.Serial('COM3', 9600, timeout=1)
        ser.close()
    except Exception:
        pytest.skip("Arduino not available")

def skip_if_no_internet():
    """Skip test ถ้าไม่มี internet"""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
    except OSError:
        pytest.skip("No internet connection")

def assert_image_equal(img1, img2, tolerance=0):
    """เปรียบเทียบภาพ"""
    assert img1.shape == img2.shape, "Image shapes don't match"
    
    if tolerance == 0:
        assert np.array_equal(img1, img2), "Images are not identical"
    else:
        diff = np.abs(img1.astype(float) - img2.astype(float))
        max_diff = np.max(diff)
        assert max_diff <= tolerance, f"Images differ by {max_diff}, tolerance is {tolerance}"

def assert_detection_valid(detection):
    """ตรวจสอบความถูกต้องของ detection"""
    validator = TestValidator()
    is_valid, message = validator.validate_detection_result([detection])
    assert is_valid, message

if __name__ == "__main__":
    # ทดสอบ utilities
    print("Testing utilities...")
    
    # ทดสอบ TestDataGenerator
    generator = TestDataGenerator()
    test_image = generator.create_test_image()
    print(f"Generated test image shape: {test_image.shape}")
    
    # ทดสอบ TestFileManager
    file_manager = TestFileManager()
    temp_file = file_manager.create_temp_file("test content")
    print(f"Created temp file: {temp_file}")
    file_manager.cleanup()
    
    print("Utilities test completed!")