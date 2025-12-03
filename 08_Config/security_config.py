# ========================================
# Security Configuration for YOLO Arduino Firebase Bridge
# ========================================

import os
import json
import base64
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecurityConfig:
    """
    การจัดการความปลอดภัยและการเข้ารหัสข้อมูล
    """
    
    def __init__(self, env_file=".env", secrets_file="secrets.enc"):
        self.env_file = Path(env_file)
        self.secrets_file = Path(secrets_file)
        self.logger = logging.getLogger("security")
        self._cipher_suite = None
        self._load_environment()
    
    def _load_environment(self):
        """โหลด environment variables จากไฟล์ .env"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    def generate_key(self, password: str, salt: bytes = None) -> bytes:
        """สร้าง encryption key จาก password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def init_encryption(self, password: str):
        """เริ่มต้นระบบเข้ารหัส"""
        try:
            # ลองโหลด salt ที่มีอยู่
            salt_file = Path("encryption.salt")
            if salt_file.exists():
                with open(salt_file, 'rb') as f:
                    salt = f.read()
            else:
                salt = os.urandom(16)
                with open(salt_file, 'wb') as f:
                    f.write(salt)
            
            key, _ = self.generate_key(password, salt)
            self._cipher_suite = Fernet(key)
            self.logger.info("Encryption initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt_data(self, data: str) -> str:
        """เข้ารหัสข้อมูล"""
        if self._cipher_suite is None:
            raise ValueError("Encryption not initialized")
        
        encrypted_data = self._cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """ถอดรหัสข้อมูล"""
        if self._cipher_suite is None:
            raise ValueError("Encryption not initialized")
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {e}")
            raise
    
    def save_secrets(self, secrets: Dict[str, Any], password: str):
        """บันทึกข้อมูลลับแบบเข้ารหัส"""
        if self._cipher_suite is None:
            self.init_encryption(password)
        
        try:
            secrets_json = json.dumps(secrets, indent=2)
            encrypted_secrets = self.encrypt_data(secrets_json)
            
            with open(self.secrets_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_secrets)
            
            self.logger.info("Secrets saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save secrets: {e}")
            raise
    
    def load_secrets(self, password: str) -> Dict[str, Any]:
        """โหลดข้อมูลลับที่เข้ารหัส"""
        if not self.secrets_file.exists():
            return {}
        
        if self._cipher_suite is None:
            self.init_encryption(password)
        
        try:
            with open(self.secrets_file, 'r', encoding='utf-8') as f:
                encrypted_secrets = f.read()
            
            decrypted_secrets = self.decrypt_data(encrypted_secrets)
            return json.loads(decrypted_secrets)
            
        except Exception as e:
            self.logger.error(f"Failed to load secrets: {e}")
            return {}

class EnvironmentManager:
    """
    การจัดการ Environment Variables
    """
    
    def __init__(self):
        self.logger = logging.getLogger("environment")
        self.required_vars = set()
        self.optional_vars = set()
    
    def add_required_var(self, var_name: str, description: str = ""):
        """เพิ่ม environment variable ที่จำเป็น"""
        self.required_vars.add((var_name, description))
    
    def add_optional_var(self, var_name: str, default_value: str = "", description: str = ""):
        """เพิ่ม environment variable ที่เป็น optional"""
        self.optional_vars.add((var_name, default_value, description))
    
    def validate_environment(self) -> bool:
        """ตรวจสอบ environment variables"""
        missing_vars = []
        
        for var_name, description in self.required_vars:
            if not os.getenv(var_name):
                missing_vars.append(f"{var_name} - {description}")
        
        if missing_vars:
            self.logger.error("Missing required environment variables:")
            for var in missing_vars:
                self.logger.error(f"  - {var}")
            return False
        
        # ตั้งค่า default values สำหรับ optional variables
        for var_name, default_value, description in self.optional_vars:
            if not os.getenv(var_name):
                os.environ[var_name] = default_value
                self.logger.info(f"Set default value for {var_name}: {default_value}")
        
        self.logger.info("Environment validation passed")
        return True
    
    def get_env(self, var_name: str, default: str = None, required: bool = False) -> str:
        """ดึงค่า environment variable อย่างปลอดภัย"""
        value = os.getenv(var_name, default)
        
        if required and not value:
            raise ValueError(f"Required environment variable {var_name} not found")
        
        return value
    
    def get_env_bool(self, var_name: str, default: bool = False) -> bool:
        """ดึงค่า boolean จาก environment variable"""
        value = os.getenv(var_name, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_env_int(self, var_name: str, default: int = 0) -> int:
        """ดึงค่า integer จาก environment variable"""
        try:
            return int(os.getenv(var_name, str(default)))
        except ValueError:
            self.logger.warning(f"Invalid integer value for {var_name}, using default: {default}")
            return default
    
    def get_env_float(self, var_name: str, default: float = 0.0) -> float:
        """ดึงค่า float จาก environment variable"""
        try:
            return float(os.getenv(var_name, str(default)))
        except ValueError:
            self.logger.warning(f"Invalid float value for {var_name}, using default: {default}")
            return default
    
    def create_env_template(self, output_file: str = ".env.template"):
        """สร้างไฟล์ template สำหรับ environment variables"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Environment Variables Template\n")
            f.write("# Copy this file to .env and fill in your values\n\n")
            
            f.write("# Required Variables\n")
            for var_name, description in self.required_vars:
                f.write(f"# {description}\n")
                f.write(f"{var_name}=\n\n")
            
            f.write("# Optional Variables\n")
            for var_name, default_value, description in self.optional_vars:
                f.write(f"# {description}\n")
                f.write(f"{var_name}={default_value}\n\n")
        
        self.logger.info(f"Environment template created: {output_file}")

class SecureConfig:
    """
    การจัดการ Configuration แบบปลอดภัย
    """
    
    def __init__(self, config_name: str = "yolo_bridge"):
        self.config_name = config_name
        self.security = SecurityConfig()
        self.env_manager = EnvironmentManager()
        self.logger = logging.getLogger("secure_config")
        self._setup_required_vars()
    
    def _setup_required_vars(self):
        """ตั้งค่า environment variables ที่จำเป็น"""
        # Firebase Configuration
        self.env_manager.add_required_var("FIREBASE_API_KEY", "Firebase API Key")
        self.env_manager.add_required_var("FIREBASE_AUTH_DOMAIN", "Firebase Auth Domain")
        self.env_manager.add_required_var("FIREBASE_DATABASE_URL", "Firebase Database URL")
        self.env_manager.add_required_var("FIREBASE_PROJECT_ID", "Firebase Project ID")
        self.env_manager.add_required_var("FIREBASE_STORAGE_BUCKET", "Firebase Storage Bucket")
        self.env_manager.add_required_var("FIREBASE_MESSAGING_SENDER_ID", "Firebase Messaging Sender ID")
        self.env_manager.add_required_var("FIREBASE_APP_ID", "Firebase App ID")
        
        # Optional Configuration
        self.env_manager.add_optional_var("ARDUINO_PORT", "COM3", "Arduino COM Port")
        self.env_manager.add_optional_var("ARDUINO_BAUDRATE", "9600", "Arduino Baud Rate")
        self.env_manager.add_optional_var("CAMERA_ID", "0", "Camera ID")
        self.env_manager.add_optional_var("YOLO_MODEL_PATH", "best.pt", "YOLO Model Path")
        self.env_manager.add_optional_var("CONFIDENCE_THRESHOLD", "0.5", "YOLO Confidence Threshold")
        self.env_manager.add_optional_var("DEBUG_MODE", "false", "Enable Debug Mode")
        self.env_manager.add_optional_var("LOG_LEVEL", "INFO", "Logging Level")
    
    def validate_config(self) -> bool:
        """ตรวจสอบ configuration ทั้งหมด"""
        return self.env_manager.validate_environment()
    
    def get_firebase_config(self) -> Dict[str, str]:
        """ดึง Firebase configuration"""
        return {
            'apiKey': self.env_manager.get_env('FIREBASE_API_KEY', required=True),
            'authDomain': self.env_manager.get_env('FIREBASE_AUTH_DOMAIN', required=True),
            'databaseURL': self.env_manager.get_env('FIREBASE_DATABASE_URL', required=True),
            'projectId': self.env_manager.get_env('FIREBASE_PROJECT_ID', required=True),
            'storageBucket': self.env_manager.get_env('FIREBASE_STORAGE_BUCKET', required=True),
            'messagingSenderId': self.env_manager.get_env('FIREBASE_MESSAGING_SENDER_ID', required=True),
            'appId': self.env_manager.get_env('FIREBASE_APP_ID', required=True)
        }
    
    def get_arduino_config(self) -> Dict[str, Any]:
        """ดึง Arduino configuration"""
        return {
            'port': self.env_manager.get_env('ARDUINO_PORT'),
            'baudrate': self.env_manager.get_env_int('ARDUINO_BAUDRATE'),
            'timeout': 1
        }
    
    def get_yolo_config(self) -> Dict[str, Any]:
        """ดึง YOLO configuration"""
        return {
            'model_path': self.env_manager.get_env('YOLO_MODEL_PATH'),
            'confidence_threshold': self.env_manager.get_env_float('CONFIDENCE_THRESHOLD'),
            'camera_id': self.env_manager.get_env_int('CAMERA_ID')
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """ดึง System configuration"""
        return {
            'debug_mode': self.env_manager.get_env_bool('DEBUG_MODE'),
            'log_level': self.env_manager.get_env('LOG_LEVEL')
        }
    
    def create_config_template(self):
        """สร้างไฟล์ template สำหรับ configuration"""
        self.env_manager.create_env_template()
        
        # สร้าง example secrets file
        example_secrets = {
            "firebase": {
                "api_key": "your-firebase-api-key",
                "auth_domain": "your-project.firebaseapp.com",
                "database_url": "https://your-project-default-rtdb.firebaseio.com/",
                "project_id": "your-project-id",
                "storage_bucket": "your-project.appspot.com",
                "messaging_sender_id": "123456789",
                "app_id": "1:123456789:web:abcdef123456"
            },
            "arduino": {
                "port": "COM3",
                "baudrate": 9600
            },
            "yolo": {
                "model_path": "models/best.pt",
                "confidence_threshold": 0.5
            }
        }
        
        with open("secrets.example.json", 'w', encoding='utf-8') as f:
            json.dump(example_secrets, f, indent=2)
        
        self.logger.info("Configuration templates created")

def hash_password(password: str, salt: bytes = None) -> tuple:
    """สร้าง hash ของ password"""
    if salt is None:
        salt = os.urandom(32)
    
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwdhash, salt

def verify_password(password: str, salt: bytes, pwdhash: bytes) -> bool:
    """ตรวจสอบ password"""
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000) == pwdhash

def sanitize_input(input_string: str, max_length: int = 255) -> str:
    """ทำความสะอาด input เพื่อป้องกัน injection"""
    if not isinstance(input_string, str):
        return ""
    
    # ลบ characters ที่อันตราย
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
    for char in dangerous_chars:
        input_string = input_string.replace(char, '')
    
    # จำกัดความยาว
    return input_string[:max_length]

def validate_firebase_url(url: str) -> bool:
    """ตรวจสอบ Firebase URL"""
    import re
    pattern = r'^https://[\w-]+-default-rtdb\.firebaseio\.com/$'
    return bool(re.match(pattern, url))

def validate_com_port(port: str) -> bool:
    """ตรวจสอบ COM Port"""
    import re
    pattern = r'^COM\d+$'
    return bool(re.match(pattern, port.upper()))

# ========================================
# Testing Functions
# ========================================

if __name__ == "__main__":
    # ทดสอบ security system
    
    # ตั้งค่า logging
    logging.basicConfig(level=logging.INFO)
    
    # ทดสอบ SecureConfig
    config = SecureConfig()
    
    # สร้าง template files
    config.create_config_template()
    
    # ทดสอบ password hashing
    password = "test_password"
    pwdhash, salt = hash_password(password)
    print(f"Password verified: {verify_password(password, salt, pwdhash)}")
    
    # ทดสอบ input sanitization
    dangerous_input = "<script>alert('xss')</script>"
    safe_input = sanitize_input(dangerous_input)
    print(f"Sanitized input: {safe_input}")
    
    # ทดสอบ URL validation
    valid_url = "https://test-project-default-rtdb.firebaseio.com/"
    invalid_url = "http://malicious-site.com"
    print(f"Valid Firebase URL: {validate_firebase_url(valid_url)}")
    print(f"Invalid URL rejected: {not validate_firebase_url(invalid_url)}")
    
    print("Security configuration test completed")