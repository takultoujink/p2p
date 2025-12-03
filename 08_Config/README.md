# ⚙️ Configuration

โฟลเดอร์นี้เก็บไฟล์การตั้งค่าและ Dependencies ทั้งหมดสำหรับโปรเจกต์

## 📋 ไฟล์ในโฟลเดอร์

### 🐍 Python Configuration
- `config_template.py` - Template สำหรับการตั้งค่าระบบ
- `config_yolo_v11.py` - การตั้งค่าเฉพาะสำหรับ YOLO v11
- `config_yolo_v11_servo.py` - การตั้งค่า YOLO v11 พร้อม Servo Control

### 📦 Dependencies
- `requirements.txt` - Python packages สำหรับโปรเจกต์ทั่วไป
- `requirements_yolo_v11.txt` - Python packages เฉพาะสำหรับ YOLO v11

## 🔧 Configuration Files

### 📝 config_template.py
```python
# Firebase Configuration
FIREBASE_CONFIG = {
    'apiKey': 'your-api-key',
    'authDomain': 'your-project.firebaseapp.com',
    'databaseURL': 'your-database-url',
    'projectId': 'your-project-id',
    'storageBucket': 'your-project.appspot.com',
    'messagingSenderId': 'your-sender-id',
    'appId': 'your-app-id'
}

# Arduino Configuration
ARDUINO_CONFIG = {
    'port': 'COM3',
    'baudrate': 9600,
    'timeout': 1
}

# YOLO Configuration
YOLO_CONFIG = {
    'model_path': 'models/yolo_v11.pt',
    'confidence_threshold': 0.5,
    'device': 'cpu'  # or 'cuda' for GPU
}
```

### 🎯 config_yolo_v11.py
```python
# YOLO v11 Specific Configuration
MODEL_CONFIG = {
    'model_name': 'yolo_v11_bottle_detection.pt',
    'input_size': 640,
    'confidence': 0.6,
    'iou_threshold': 0.45,
    'max_detections': 100
}

# Detection Classes
DETECTION_CLASSES = {
    0: 'plastic_bottle',
    1: 'glass_bottle',
    2: 'can',
    3: 'other'
}

# Camera Configuration
CAMERA_CONFIG = {
    'source': 0,  # 0 for webcam, or video file path
    'fps': 30,
    'resolution': (1280, 720)
}
```

### 🔧 config_yolo_v11_servo.py
```python
# Servo Control Configuration
SERVO_CONFIG = {
    'servo_pins': {
        'main_servo': 9,
        'secondary_servo': 10
    },
    'servo_angles': {
        'plastic_bottle': 90,
        'glass_bottle': 45,
        'can': 135,
        'default': 0
    },
    'servo_speed': 50  # degrees per second
}

# Sorting Logic
SORTING_CONFIG = {
    'enable_sorting': True,
    'sort_by_material': True,
    'sort_by_size': False,
    'delay_between_sorts': 2.0  # seconds
}
```

## 📦 Dependencies

### 🐍 requirements.txt
```txt
# Core Dependencies
numpy>=1.21.0
opencv-python>=4.5.0
Pillow>=8.3.0
requests>=2.26.0

# Firebase
firebase-admin>=5.4.0
google-cloud-firestore>=2.3.0

# Serial Communication
pyserial>=3.5

# Data Processing
pandas>=1.3.0
matplotlib>=3.4.0

# Web Framework
flask>=2.0.0
flask-cors>=3.0.0

# Utilities
python-dotenv>=0.19.0
pyyaml>=5.4.0
```

### 🎯 requirements_yolo_v11.txt
```txt
# YOLO v11 Specific Dependencies
ultralytics>=8.0.0
torch>=1.12.0
torchvision>=0.13.0

# Computer Vision
opencv-python>=4.6.0
opencv-contrib-python>=4.6.0

# Image Processing
albumentations>=1.2.0
imgaug>=0.4.0

# Deep Learning Utilities
tensorboard>=2.9.0
wandb>=0.12.0

# Performance
onnx>=1.12.0
onnxruntime>=1.12.0

# GPU Support (optional)
# torch-audio>=0.12.0  # for CUDA
# torchaudio>=0.12.0   # for CUDA
```

## 🔧 Environment Setup

### 📁 Environment Variables
สร้างไฟล์ `.env` ในโฟลเดอร์ root:
```bash
# Firebase
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=your-app-id

# Arduino
ARDUINO_PORT=COM3
ARDUINO_BAUDRATE=9600

# YOLO
YOLO_MODEL_PATH=models/yolo_v11.pt
YOLO_CONFIDENCE=0.6
YOLO_DEVICE=cpu

# System
DEBUG_MODE=True
LOG_LEVEL=INFO
```

### 🐍 Virtual Environment
```bash
# สร้าง Virtual Environment
python -m venv venv

# เปิดใช้งาน (Windows)
venv\Scripts\activate

# เปิดใช้งาน (Linux/Mac)
source venv/bin/activate

# ติดตั้ง Dependencies
pip install -r requirements.txt
pip install -r requirements_yolo_v11.txt
```

## 🔄 Configuration Management

### 📝 Config Loading
```python
# config_loader.py
import os
import yaml
from dotenv import load_dotenv

def load_config():
    # โหลด Environment Variables
    load_dotenv()
    
    # โหลด YAML Config
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Override ด้วย Environment Variables
    config['firebase']['api_key'] = os.getenv('FIREBASE_API_KEY', config['firebase']['api_key'])
    config['arduino']['port'] = os.getenv('ARDUINO_PORT', config['arduino']['port'])
    
    return config
```

### 🔧 Dynamic Configuration
```python
# dynamic_config.py
class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
    
    def save(self):
        with open('config.yaml', 'w') as file:
            yaml.dump(self.config, file)

# การใช้งาน
config = ConfigManager()
firebase_key = config.get('firebase.api_key')
config.set('yolo.confidence', 0.7)
config.save()
```

## 🔍 Validation

### ✅ Config Validation
```python
# config_validator.py
def validate_config(config):
    errors = []
    
    # ตรวจสอบ Firebase Config
    required_firebase_keys = ['api_key', 'project_id', 'auth_domain']
    for key in required_firebase_keys:
        if not config.get(f'firebase.{key}'):
            errors.append(f'Missing Firebase {key}')
    
    # ตรวจสอบ YOLO Config
    if not os.path.exists(config.get('yolo.model_path', '')):
        errors.append('YOLO model file not found')
    
    # ตรวจสอบ Arduino Config
    arduino_port = config.get('arduino.port')
    if arduino_port and not is_port_available(arduino_port):
        errors.append(f'Arduino port {arduino_port} not available')
    
    return errors

def is_port_available(port):
    try:
        import serial
        ser = serial.Serial(port, timeout=1)
        ser.close()
        return True
    except:
        return False
```

## 🚀 Deployment Configurations

### 🏭 Production Config
```python
# production_config.py
PRODUCTION_CONFIG = {
    'debug': False,
    'log_level': 'WARNING',
    'firebase': {
        'use_emulator': False,
        'timeout': 30
    },
    'yolo': {
        'device': 'cuda',  # ใช้ GPU ใน Production
        'batch_size': 16
    },
    'performance': {
        'enable_caching': True,
        'cache_ttl': 3600
    }
}
```

### 🧪 Development Config
```python
# development_config.py
DEVELOPMENT_CONFIG = {
    'debug': True,
    'log_level': 'DEBUG',
    'firebase': {
        'use_emulator': True,
        'timeout': 10
    },
    'yolo': {
        'device': 'cpu',  # ใช้ CPU ใน Development
        'batch_size': 1
    },
    'performance': {
        'enable_caching': False,
        'cache_ttl': 60
    }
}
```

## 🔒 Security

### 🛡️ Secure Configuration
- ไม่เก็บ API Keys ใน Code
- ใช้ Environment Variables
- เข้ารหัสข้อมูลสำคัญ
- ใช้ Secret Management Services

### 🔐 Best Practices
- แยก Config ตาม Environment
- ใช้ Configuration Validation
- สำรองข้อมูล Configuration
- ตรวจสอบ Configuration ก่อนใช้งาน