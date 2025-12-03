# ========================================
# Pytest Configuration and Shared Fixtures
# ========================================

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# เพิ่ม project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "02_AI_Detection"))
sys.path.insert(0, str(project_root / "03_Arduino_Control"))
sys.path.insert(0, str(project_root / "04_Firebase_Integration"))
sys.path.insert(0, str(project_root / "08_Config"))

# Import test utilities
from test_utilities import (
    TestDataGenerator, TestFileManager, MockFactory, 
    PerformanceTimer, TestValidator, TestReporter
)

# ========================================
# Pytest Configuration
# ========================================

def pytest_configure(config):
    """กำหนดค่า pytest"""
    # เพิ่ม custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )
    config.addinivalue_line(
        "markers", "hardware: mark test as requiring hardware"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network connection"
    )

def pytest_collection_modifyitems(config, items):
    """ปรับแต่ง test collection"""
    # เพิ่ม marker ให้ tests ตามชื่อไฟล์
    for item in items:
        # Unit tests
        if "test_" in item.nodeid and not any(marker in item.nodeid for marker in ["integration", "performance"]):
            item.add_marker(pytest.mark.unit)
        
        # Integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Hardware tests
        if any(keyword in item.nodeid for keyword in ["arduino", "camera", "hardware"]):
            item.add_marker(pytest.mark.hardware)
        
        # Network tests
        if any(keyword in item.nodeid for keyword in ["firebase", "network", "api"]):
            item.add_marker(pytest.mark.network)

def pytest_runtest_setup(item):
    """Setup ก่อนรัน test แต่ละตัว"""
    # Skip hardware tests ถ้าไม่มี hardware
    if "hardware" in item.keywords:
        if not _check_hardware_available():
            pytest.skip("Hardware not available")
    
    # Skip network tests ถ้าไม่มี network
    if "network" in item.keywords:
        if not _check_network_available():
            pytest.skip("Network not available")

def _check_hardware_available():
    """ตรวจสอบว่ามี hardware หรือไม่"""
    # ตรวจสอบกล้อง
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True
    except Exception:
        pass
    
    # ตรวจสอบ Arduino
    try:
        import serial
        ser = serial.Serial('COM3', 9600, timeout=1)
        ser.close()
        return True
    except Exception:
        pass
    
    return False

def _check_network_available():
    """ตรวจสอบการเชื่อมต่อ network"""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# ========================================
# Session-scoped Fixtures
# ========================================

@pytest.fixture(scope="session")
def project_root_path():
    """Path ของ project root"""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def test_data_generator():
    """Generator สำหรับสร้างข้อมูลทดสอบ"""
    return TestDataGenerator()

@pytest.fixture(scope="session")
def mock_factory():
    """Factory สำหรับสร้าง mock objects"""
    return MockFactory()

@pytest.fixture(scope="session")
def test_validator():
    """Validator สำหรับตรวจสอบข้อมูล"""
    return TestValidator()

@pytest.fixture(scope="session")
def test_reporter():
    """Reporter สำหรับรายงานผลการทดสอบ"""
    return TestReporter()

# ========================================
# Function-scoped Fixtures
# ========================================

@pytest.fixture(scope="function")
def test_file_manager():
    """Manager สำหรับจัดการไฟล์ทดสอบ"""
    manager = TestFileManager()
    yield manager
    manager.cleanup()

@pytest.fixture(scope="function")
def performance_timer():
    """Timer สำหรับวัดประสิทธิภาพ"""
    return PerformanceTimer()

@pytest.fixture(scope="function")
def temp_dir():
    """Temporary directory สำหรับ testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def sample_image(test_data_generator):
    """ภาพตัวอย่างสำหรับ testing"""
    return test_data_generator.create_test_image()

@pytest.fixture(scope="function")
def sample_detection_data(test_data_generator):
    """ข้อมูล detection ตัวอย่าง"""
    return test_data_generator.create_test_detection_data()

@pytest.fixture(scope="function")
def sample_config(test_data_generator):
    """Configuration ตัวอย่าง"""
    return test_data_generator.create_test_config()

# ========================================
# Mock Fixtures
# ========================================

@pytest.fixture(scope="function")
def mock_camera(mock_factory):
    """Mock camera object"""
    return mock_factory.create_mock_camera()

@pytest.fixture(scope="function")
def mock_serial(mock_factory):
    """Mock serial connection"""
    return mock_factory.create_mock_serial()

@pytest.fixture(scope="function")
def mock_firebase_client(mock_factory):
    """Mock Firebase client"""
    return mock_factory.create_mock_firebase_client()

@pytest.fixture(scope="function")
def mock_yolo_model(mock_factory):
    """Mock YOLO model"""
    return mock_factory.create_mock_yolo_model()

# ========================================
# Configuration Fixtures
# ========================================

@pytest.fixture(scope="function")
def yolo_config():
    """YOLO configuration สำหรับ testing"""
    return {
        "MODEL_PATH": "test_model.pt",
        "CONF_THRESHOLD": 0.5,
        "CAM_ID": 0,
        "CLASS_NAMES": ["bottle", "can", "plastic", "paper"]
    }

@pytest.fixture(scope="function")
def arduino_config():
    """Arduino configuration สำหรับ testing"""
    return {
        "ARDUINO_PORT": "COM3",
        "ARDUINO_BAUDRATE": 9600,
        "ARDUINO_TIMEOUT": 1.0
    }

@pytest.fixture(scope="function")
def firebase_config():
    """Firebase configuration สำหรับ testing"""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }

# ========================================
# Patch Fixtures
# ========================================

@pytest.fixture(scope="function")
def patch_cv2_videocapture(mock_camera):
    """Patch cv2.VideoCapture"""
    with patch('cv2.VideoCapture', return_value=mock_camera) as mock_patch:
        yield mock_patch

@pytest.fixture(scope="function")
def patch_serial_connection(mock_serial):
    """Patch serial.Serial"""
    with patch('serial.Serial', return_value=mock_serial) as mock_patch:
        yield mock_patch

@pytest.fixture(scope="function")
def patch_firebase_init():
    """Patch Firebase initialization"""
    with patch('firebase_admin.initialize_app') as mock_init, \
         patch('firebase_admin.credentials.Certificate') as mock_cert:
        mock_init.return_value = Mock()
        mock_cert.return_value = Mock()
        yield mock_init, mock_cert

@pytest.fixture(scope="function")
def patch_yolo_model(mock_yolo_model):
    """Patch YOLO model"""
    with patch('ultralytics.YOLO', return_value=mock_yolo_model) as mock_patch:
        yield mock_patch

# ========================================
# Environment Fixtures
# ========================================

@pytest.fixture(scope="function")
def clean_environment():
    """สภาพแวดล้อมที่สะอาดสำหรับ testing"""
    # บันทึก environment variables เดิม
    original_env = dict(os.environ)
    
    # ลบ environment variables ที่อาจรบกวน
    test_env_vars = [
        'FIREBASE_CONFIG_PATH',
        'ARDUINO_PORT',
        'MODEL_PATH',
        'CAM_ID'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # คืนค่า environment variables
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture(scope="function")
def test_environment_variables():
    """ตั้งค่า environment variables สำหรับ testing"""
    test_vars = {
        'FIREBASE_CONFIG_PATH': 'test_firebase_config.json',
        'ARDUINO_PORT': 'COM3',
        'MODEL_PATH': 'test_model.pt',
        'CAM_ID': '0',
        'CONF_THRESHOLD': '0.5'
    }
    
    # บันทึกค่าเดิม
    original_values = {}
    for key in test_vars:
        original_values[key] = os.environ.get(key)
    
    # ตั้งค่าใหม่
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield test_vars
    
    # คืนค่าเดิม
    for key, original_value in original_values.items():
        if original_value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = original_value

# ========================================
# Parametrize Fixtures
# ========================================

@pytest.fixture(params=[
    (320, 240), (640, 480), (1280, 720), (1920, 1080)
])
def image_sizes(request):
    """ขนาดภาพต่างๆ สำหรับ testing"""
    return request.param

@pytest.fixture(params=[0, 45, 90, 135, 180])
def servo_angles(request):
    """มุม servo ต่างๆ สำหรับ testing"""
    return request.param

@pytest.fixture(params=[0.1, 0.3, 0.5, 0.7, 0.9])
def confidence_thresholds(request):
    """Confidence thresholds ต่างๆ สำหรับ testing"""
    return request.param

@pytest.fixture(params=["bottle", "can", "plastic", "paper"])
def object_types(request):
    """ประเภทของ objects สำหรับ testing"""
    return request.param

# ========================================
# Cleanup Hooks
# ========================================

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """ทำความสะอาดไฟล์ทดสอบหลังจากเสร็จสิ้น"""
    yield
    
    # ลบไฟล์ทดสอบที่อาจเหลือค้าง
    test_patterns = [
        "test_*.jpg", "test_*.png", "test_*.json", 
        "test_*.txt", "test_*.log", "temp_*"
    ]
    
    import glob
    for pattern in test_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
            except Exception:
                pass

# ========================================
# Custom Assertions
# ========================================

def pytest_assertrepr_compare(op, left, right):
    """Custom assertion representations"""
    if op == "==" and hasattr(left, 'shape') and hasattr(right, 'shape'):
        # สำหรับเปรียบเทียบ numpy arrays
        return [
            f"Image comparison failed:",
            f"  Left shape: {left.shape}",
            f"  Right shape: {right.shape}",
            f"  Left dtype: {left.dtype}",
            f"  Right dtype: {right.dtype}"
        ]

# ========================================
# Test Data Paths
# ========================================

@pytest.fixture(scope="session")
def test_data_paths(project_root_path):
    """Paths สำหรับข้อมูลทดสอบ"""
    return {
        "test_images": project_root_path / "09_Testing" / "test_data" / "images",
        "test_configs": project_root_path / "09_Testing" / "test_data" / "configs",
        "test_models": project_root_path / "09_Testing" / "test_data" / "models",
        "test_outputs": project_root_path / "09_Testing" / "test_outputs"
    }

# ========================================
# Logging Configuration for Tests
# ========================================

@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """กำหนดค่า logging สำหรับ testing"""
    import logging
    
    # ตั้งค่า logging level สำหรับ testing
    logging.getLogger().setLevel(logging.WARNING)
    
    # ปิด logging ของ libraries ที่ไม่จำเป็น
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('firebase_admin').setLevel(logging.WARNING)
    
    yield
    
    # Reset logging configuration
    logging.getLogger().setLevel(logging.INFO)