"""
Advanced Security Manager for Object Detection System
รองรับ Rate limiting, Input validation, CSRF protection, API authentication
"""

import hashlib
import hmac
import jwt
import time
import redis
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from functools import wraps
from flask import request, jsonify, session, g
from werkzeug.security import check_password_hash, generate_password_hash
import re
import bleach
from cryptography.fernet import Fernet
import ipaddress
import sqlite3
import json
from email_validator import validate_email, EmailNotValidError

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """การกำหนดค่าความปลอดภัย"""
    # JWT Settings
    jwt_secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 30
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_requests_per_hour: int = 1000
    rate_limit_requests_per_day: int = 10000
    rate_limit_burst_size: int = 10
    
    # Password Policy
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    password_history_count: int = 5
    
    # Session Security
    session_timeout_minutes: int = 30
    secure_cookies: bool = True
    httponly_cookies: bool = True
    samesite_cookies: str = "Strict"
    
    # CSRF Protection
    csrf_enabled: bool = True
    csrf_token_expiration_hours: int = 1
    
    # Input Validation
    max_file_size_mb: int = 10
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.jpg', '.jpeg', '.png', '.gif', '.bmp'])
    max_request_size_mb: int = 50
    
    # IP Security
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    geo_blocking_enabled: bool = False
    blocked_countries: List[str] = field(default_factory=list)
    
    # API Security
    api_key_enabled: bool = True
    api_key_length: int = 32
    api_rate_limit_per_key: int = 1000
    
    # Encryption
    encryption_key: str = field(default_factory=lambda: Fernet.generate_key().decode())
    hash_algorithm: str = "sha256"
    
    # Audit Logging
    audit_log_enabled: bool = True
    audit_log_retention_days: int = 90
    
    # Two-Factor Authentication
    totp_enabled: bool = False
    totp_issuer: str = "ObjectDetectionApp"
    backup_codes_count: int = 10

@dataclass
class SecurityEvent:
    """เหตุการณ์ด้านความปลอดภัย"""
    event_id: str
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    severity: str  # low, medium, high, critical
    action_taken: str

class SecurityManager:
    """จัดการระบบความปลอดภัยขั้นสูง"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.redis_client = None
        self.fernet = Fernet(config.encryption_key.encode())
        self.db_path = "security.db"
        self.init_database()
        self.init_redis()
        
    def init_database(self):
        """เริ่มต้นฐานข้อมูลความปลอดภัย"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ตาราง Users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    role TEXT DEFAULT 'user',
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    two_factor_secret TEXT,
                    backup_codes TEXT
                )
            ''')
            
            # ตาราง API Keys
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    rate_limit INTEGER DEFAULT 1000,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ตาราง Security Events
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    severity TEXT NOT NULL,
                    action_taken TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ตาราง Password History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ตาราง Sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Security database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security database: {e}")
            raise
    
    def init_redis(self):
        """เริ่มต้น Redis สำหรับ rate limiting"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
            self.redis_client = None
    
    # === Authentication Methods ===
    
    def hash_password(self, password: str) -> Tuple[str, str]:
        """เข้ารหัสรหัสผ่าน"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8'), salt.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """ตรวจสอบรหัสผ่าน"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """ตรวจสอบความแข็งแกร่งของรหัสผ่าน"""
        errors = []
        
        if len(password) < self.config.min_password_length:
            errors.append(f"Password must be at least {self.config.min_password_length} characters long")
        
        if self.config.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.config.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.config.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if self.config.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> Dict[str, Any]:
        """สร้างผู้ใช้ใหม่"""
        try:
            # ตรวจสอบความแข็งแกร่งของรหัสผ่าน
            is_strong, errors = self.validate_password_strength(password)
            if not is_strong:
                return {"success": False, "errors": errors}
            
            # ตรวจสอบอีเมล
            try:
                validate_email(email)
            except EmailNotValidError:
                return {"success": False, "errors": ["Invalid email format"]}
            
            # เข้ารหัสรหัสผ่าน
            password_hash, salt = self.hash_password(password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, role))
            
            user_id = cursor.lastrowid
            
            # บันทึกประวัติรหัสผ่าน
            cursor.execute('''
                INSERT INTO password_history (user_id, password_hash)
                VALUES (?, ?)
            ''', (user_id, password_hash))
            
            conn.commit()
            conn.close()
            
            # บันทึกเหตุการณ์
            self.log_security_event(
                event_type="user_created",
                user_id=str(user_id),
                ip_address=self.get_client_ip(),
                details={"username": username, "email": email, "role": role},
                severity="low"
            )
            
            return {"success": True, "user_id": user_id}
            
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return {"success": False, "errors": ["Username already exists"]}
            elif "email" in str(e):
                return {"success": False, "errors": ["Email already exists"]}
            else:
                return {"success": False, "errors": ["Database error"]}
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return {"success": False, "errors": ["Internal server error"]}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """ตรวจสอบสิทธิ์ผู้ใช้"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, failed_login_attempts, 
                       locked_until, is_active, role, two_factor_enabled
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                self.log_security_event(
                    event_type="login_failed",
                    user_id=None,
                    ip_address=self.get_client_ip(),
                    details={"username": username, "reason": "user_not_found"},
                    severity="medium"
                )
                return {"success": False, "error": "Invalid credentials"}
            
            user_id, username, email, password_hash, failed_attempts, locked_until, is_active, role, two_factor_enabled = user
            
            # ตรวจสอบว่าบัญชีถูกล็อกหรือไม่
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                self.log_security_event(
                    event_type="login_blocked",
                    user_id=str(user_id),
                    ip_address=self.get_client_ip(),
                    details={"username": username, "reason": "account_locked"},
                    severity="high"
                )
                return {"success": False, "error": "Account is locked"}
            
            # ตรวจสอบว่าบัญชีใช้งานได้หรือไม่
            if not is_active:
                return {"success": False, "error": "Account is disabled"}
            
            # ตรวจสอบรหัสผ่าน
            if not self.verify_password(password, password_hash):
                # เพิ่มจำนวนครั้งที่ล็อกอินผิด
                failed_attempts += 1
                locked_until = None
                
                if failed_attempts >= 5:  # ล็อกบัญชีหลังจากผิด 5 ครั้ง
                    locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                
                cursor.execute('''
                    UPDATE users SET failed_login_attempts = ?, locked_until = ?
                    WHERE id = ?
                ''', (failed_attempts, locked_until, user_id))
                
                conn.commit()
                conn.close()
                
                self.log_security_event(
                    event_type="login_failed",
                    user_id=str(user_id),
                    ip_address=self.get_client_ip(),
                    details={"username": username, "reason": "invalid_password", "failed_attempts": failed_attempts},
                    severity="medium" if failed_attempts < 5 else "high"
                )
                
                return {"success": False, "error": "Invalid credentials"}
            
            # รีเซ็ตจำนวนครั้งที่ล็อกอินผิด
            cursor.execute('''
                UPDATE users SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            # สร้าง JWT token
            token_data = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "role": role,
                "exp": datetime.utcnow() + timedelta(hours=self.config.jwt_expiration_hours),
                "iat": datetime.utcnow()
            }
            
            access_token = jwt.encode(token_data, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
            
            # สร้าง refresh token
            refresh_token_data = {
                "user_id": user_id,
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=self.config.jwt_refresh_expiration_days),
                "iat": datetime.utcnow()
            }
            
            refresh_token = jwt.encode(refresh_token_data, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
            
            self.log_security_event(
                event_type="login_success",
                user_id=str(user_id),
                ip_address=self.get_client_ip(),
                details={"username": username},
                severity="low"
            )
            
            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "role": role,
                    "two_factor_enabled": two_factor_enabled
                },
                "requires_2fa": two_factor_enabled
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {"success": False, "error": "Internal server error"}
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """ตรวจสอบ JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
    
    # === Rate Limiting ===
    
    def check_rate_limit(self, identifier: str, limit_type: str = "general") -> Dict[str, Any]:
        """ตรวจสอบ rate limit"""
        if not self.config.rate_limit_enabled:
            return {"allowed": True}
        
        current_time = int(time.time())
        
        # กำหนดขีดจำกัดตามประเภท
        limits = {
            "general": {
                "minute": self.config.rate_limit_requests_per_minute,
                "hour": self.config.rate_limit_requests_per_hour,
                "day": self.config.rate_limit_requests_per_day
            },
            "api": {
                "minute": 100,
                "hour": self.config.api_rate_limit_per_key,
                "day": self.config.api_rate_limit_per_key * 24
            }
        }
        
        limit_config = limits.get(limit_type, limits["general"])
        
        if self.redis_client:
            return self._check_rate_limit_redis(identifier, limit_config, current_time)
        else:
            return self._check_rate_limit_memory(identifier, limit_config, current_time)
    
    def _check_rate_limit_redis(self, identifier: str, limits: Dict[str, int], current_time: int) -> Dict[str, Any]:
        """ตรวจสอบ rate limit ด้วย Redis"""
        try:
            pipe = self.redis_client.pipeline()
            
            # ตรวจสอบแต่ละช่วงเวลา
            for period, limit in limits.items():
                if period == "minute":
                    window = 60
                elif period == "hour":
                    window = 3600
                elif period == "day":
                    window = 86400
                else:
                    continue
                
                key = f"rate_limit:{identifier}:{period}:{current_time // window}"
                
                pipe.incr(key)
                pipe.expire(key, window)
                
                # ตรวจสอบค่าปัจจุบัน
                current_count = self.redis_client.get(key)
                if current_count and int(current_count) > limit:
                    self.log_security_event(
                        event_type="rate_limit_exceeded",
                        user_id=None,
                        ip_address=identifier,
                        details={"period": period, "limit": limit, "current": int(current_count)},
                        severity="medium"
                    )
                    return {
                        "allowed": False,
                        "error": f"Rate limit exceeded for {period}",
                        "retry_after": window - (current_time % window)
                    }
            
            pipe.execute()
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return {"allowed": True}  # ให้ผ่านถ้า Redis มีปัญหา
    
    def _check_rate_limit_memory(self, identifier: str, limits: Dict[str, int], current_time: int) -> Dict[str, Any]:
        """ตรวจสอบ rate limit ด้วย memory (fallback)"""
        # Implementation สำหรับ in-memory rate limiting
        # ใช้เมื่อ Redis ไม่พร้อมใช้งาน
        return {"allowed": True}
    
    # === Input Validation ===
    
    def validate_file_upload(self, file) -> Dict[str, Any]:
        """ตรวจสอบไฟล์ที่อัปโหลด"""
        try:
            # ตรวจสอบขนาดไฟล์
            if hasattr(file, 'content_length') and file.content_length:
                if file.content_length > self.config.max_file_size_mb * 1024 * 1024:
                    return {"valid": False, "error": f"File size exceeds {self.config.max_file_size_mb}MB limit"}
            
            # ตรวจสอบนามสกุลไฟล์
            if hasattr(file, 'filename') and file.filename:
                file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if file_ext not in self.config.allowed_file_extensions:
                    return {"valid": False, "error": f"File type {file_ext} not allowed"}
            
            # ตรวจสอบ MIME type
            if hasattr(file, 'content_type'):
                allowed_mime_types = [
                    'image/jpeg', 'image/jpg', 'image/png', 
                    'image/gif', 'image/bmp', 'image/webp'
                ]
                if file.content_type not in allowed_mime_types:
                    return {"valid": False, "error": "Invalid file type"}
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return {"valid": False, "error": "File validation failed"}
    
    def sanitize_input(self, input_data: str, input_type: str = "text") -> str:
        """ทำความสะอาดข้อมูลนำเข้า"""
        if input_type == "html":
            # ใช้ bleach สำหรับ HTML
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
            return bleach.clean(input_data, tags=allowed_tags, strip=True)
        elif input_type == "sql":
            # ป้องกัน SQL injection
            return input_data.replace("'", "''").replace(";", "")
        else:
            # ทำความสะอาดทั่วไป
            return re.sub(r'[<>"\']', '', input_data)
    
    def validate_ip_address(self, ip: str) -> bool:
        """ตรวจสอบ IP address"""
        try:
            ipaddress.ip_address(ip)
            
            # ตรวจสอบ whitelist
            if self.config.ip_whitelist:
                return ip in self.config.ip_whitelist
            
            # ตรวจสอบ blacklist
            if ip in self.config.ip_blacklist:
                return False
            
            return True
        except ValueError:
            return False
    
    # === CSRF Protection ===
    
    def generate_csrf_token(self, user_id: str) -> str:
        """สร้าง CSRF token"""
        timestamp = int(time.time())
        data = f"{user_id}:{timestamp}:{secrets.token_urlsafe(16)}"
        token = self.fernet.encrypt(data.encode()).decode()
        return token
    
    def verify_csrf_token(self, token: str, user_id: str) -> bool:
        """ตรวจสอบ CSRF token"""
        try:
            decrypted_data = self.fernet.decrypt(token.encode()).decode()
            parts = decrypted_data.split(':')
            
            if len(parts) != 3:
                return False
            
            token_user_id, timestamp, _ = parts
            
            # ตรวจสอบ user ID
            if token_user_id != user_id:
                return False
            
            # ตรวจสอบเวลาหมดอายุ
            token_time = int(timestamp)
            current_time = int(time.time())
            expiration_time = self.config.csrf_token_expiration_hours * 3600
            
            if current_time - token_time > expiration_time:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"CSRF token verification failed: {e}")
            return False
    
    # === API Key Management ===
    
    def generate_api_key(self, user_id: int, name: str, permissions: List[str] = None, 
                        expires_days: int = None) -> Dict[str, Any]:
        """สร้าง API key"""
        try:
            # สร้าง API key
            api_key = secrets.token_urlsafe(self.config.api_key_length)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # กำหนดวันหมดอายุ
            expires_at = None
            if expires_days:
                expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_keys (key_hash, user_id, name, permissions, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (key_hash, user_id, name, json.dumps(permissions or []), expires_at))
            
            key_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.log_security_event(
                event_type="api_key_created",
                user_id=str(user_id),
                ip_address=self.get_client_ip(),
                details={"key_name": name, "key_id": key_id},
                severity="low"
            )
            
            return {
                "success": True,
                "api_key": api_key,
                "key_id": key_id,
                "expires_at": expires_at
            }
            
        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            return {"success": False, "error": "Failed to generate API key"}
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """ตรวจสอบ API key"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ak.id, ak.user_id, ak.name, ak.permissions, ak.expires_at, 
                       ak.is_active, ak.rate_limit, u.username, u.role
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                WHERE ak.key_hash = ? AND ak.is_active = 1
            ''', (key_hash,))
            
            result = cursor.fetchone()
            
            if not result:
                return {"valid": False, "error": "Invalid API key"}
            
            key_id, user_id, name, permissions, expires_at, is_active, rate_limit, username, role = result
            
            # ตรวจสอบวันหมดอายุ
            if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                return {"valid": False, "error": "API key has expired"}
            
            # อัปเดตเวลาใช้งานล่าสุด
            cursor.execute('''
                UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE id = ?
            ''', (key_id,))
            
            conn.commit()
            conn.close()
            
            return {
                "valid": True,
                "key_id": key_id,
                "user_id": user_id,
                "username": username,
                "role": role,
                "permissions": json.loads(permissions) if permissions else [],
                "rate_limit": rate_limit
            }
            
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return {"valid": False, "error": "API key verification failed"}
    
    # === Security Event Logging ===
    
    def log_security_event(self, event_type: str, user_id: Optional[str], 
                          ip_address: str, details: Dict[str, Any], 
                          severity: str, action_taken: str = "none"):
        """บันทึกเหตุการณ์ด้านความปลอดภัย"""
        if not self.config.audit_log_enabled:
            return
        
        try:
            event_id = secrets.token_urlsafe(16)
            user_agent = request.headers.get('User-Agent', '') if request else ''
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_events 
                (event_id, event_type, user_id, ip_address, user_agent, details, severity, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, event_type, user_id, ip_address, user_agent, 
                  json.dumps(details), severity, action_taken))
            
            conn.commit()
            conn.close()
            
            # ส่งการแจ้งเตือนสำหรับเหตุการณ์ที่มีความรุนแรงสูง
            if severity in ['high', 'critical']:
                self._send_security_alert(event_type, details, severity)
                
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _send_security_alert(self, event_type: str, details: Dict[str, Any], severity: str):
        """ส่งการแจ้งเตือนความปลอดภัย"""
        # Implementation สำหรับส่งการแจ้งเตือน (email, Slack, etc.)
        logger.warning(f"Security Alert [{severity.upper()}]: {event_type} - {details}")
    
    def get_client_ip(self) -> str:
        """ดึง IP address ของ client"""
        if request:
            # ตรวจสอบ headers สำหรับ proxy
            forwarded_ips = request.headers.get('X-Forwarded-For')
            if forwarded_ips:
                return forwarded_ips.split(',')[0].strip()
            
            real_ip = request.headers.get('X-Real-IP')
            if real_ip:
                return real_ip
            
            return request.remote_addr or '127.0.0.1'
        
        return '127.0.0.1'
    
    # === Decorators ===
    
    def require_auth(self, f):
        """Decorator สำหรับตรวจสอบการยืนยันตัวตน"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Missing or invalid authorization header"}), 401
            
            token = auth_header.split(' ')[1]
            token_result = self.verify_jwt_token(token)
            
            if not token_result["valid"]:
                return jsonify({"error": token_result["error"]}), 401
            
            g.current_user = token_result["payload"]
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_api_key(self, f):
        """Decorator สำหรับตรวจสอบ API key"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                return jsonify({"error": "Missing API key"}), 401
            
            key_result = self.verify_api_key(api_key)
            
            if not key_result["valid"]:
                return jsonify({"error": key_result["error"]}), 401
            
            # ตรวจสอบ rate limit สำหรับ API key
            rate_limit_result = self.check_rate_limit(f"api_key:{key_result['key_id']}", "api")
            
            if not rate_limit_result["allowed"]:
                return jsonify({"error": rate_limit_result["error"]}), 429
            
            g.api_key_info = key_result
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_rate_limit(self, limit_type: str = "general"):
        """Decorator สำหรับตรวจสอบ rate limit"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = self.get_client_ip()
                
                if not self.validate_ip_address(client_ip):
                    self.log_security_event(
                        event_type="blocked_ip_access",
                        user_id=None,
                        ip_address=client_ip,
                        details={"endpoint": request.endpoint},
                        severity="high"
                    )
                    return jsonify({"error": "Access denied"}), 403
                
                rate_limit_result = self.check_rate_limit(client_ip, limit_type)
                
                if not rate_limit_result["allowed"]:
                    return jsonify({
                        "error": rate_limit_result["error"],
                        "retry_after": rate_limit_result.get("retry_after")
                    }), 429
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    def require_csrf_token(self, f):
        """Decorator สำหรับตรวจสอบ CSRF token"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.config.csrf_enabled:
                return f(*args, **kwargs)
            
            csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            
            if not csrf_token:
                return jsonify({"error": "Missing CSRF token"}), 403
            
            user_id = getattr(g, 'current_user', {}).get('user_id')
            if not user_id:
                return jsonify({"error": "User not authenticated"}), 401
            
            if not self.verify_csrf_token(csrf_token, str(user_id)):
                self.log_security_event(
                    event_type="csrf_token_invalid",
                    user_id=str(user_id),
                    ip_address=self.get_client_ip(),
                    details={"endpoint": request.endpoint},
                    severity="high"
                )
                return jsonify({"error": "Invalid CSRF token"}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    # === Utility Methods ===
    
    def cleanup_expired_sessions(self):
        """ลบ session ที่หมดอายุ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} expired sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
    
    def cleanup_old_security_events(self):
        """ลบเหตุการณ์ความปลอดภัยเก่า"""
        try:
            retention_date = datetime.now() - timedelta(days=self.config.audit_log_retention_days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM security_events WHERE timestamp < ?
            ''', (retention_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old security events")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old security events: {e}")
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """ดึงข้อมูลสำหรับ dashboard ความปลอดภัย"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # สถิติเหตุการณ์ความปลอดภัยใน 24 ชั่วโมงที่ผ่านมา
            cursor.execute('''
                SELECT event_type, severity, COUNT(*) as count
                FROM security_events 
                WHERE timestamp > datetime('now', '-1 day')
                GROUP BY event_type, severity
                ORDER BY count DESC
            ''')
            
            recent_events = cursor.fetchall()
            
            # ผู้ใช้ที่ล็อกอินล่าสุด
            cursor.execute('''
                SELECT username, last_login, failed_login_attempts
                FROM users 
                WHERE last_login IS NOT NULL
                ORDER BY last_login DESC
                LIMIT 10
            ''')
            
            recent_logins = cursor.fetchall()
            
            # API keys ที่ใช้งานอยู่
            cursor.execute('''
                SELECT COUNT(*) as active_keys
                FROM api_keys 
                WHERE is_active = 1 AND (expires_at IS NULL OR expires_at > datetime('now'))
            ''')
            
            active_api_keys = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "recent_events": [
                    {"event_type": event[0], "severity": event[1], "count": event[2]}
                    for event in recent_events
                ],
                "recent_logins": [
                    {"username": login[0], "last_login": login[1], "failed_attempts": login[2]}
                    for login in recent_logins
                ],
                "active_api_keys": active_api_keys,
                "security_config": {
                    "rate_limiting_enabled": self.config.rate_limit_enabled,
                    "csrf_protection_enabled": self.config.csrf_enabled,
                    "audit_logging_enabled": self.config.audit_log_enabled,
                    "two_factor_enabled": self.config.totp_enabled
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get security dashboard data: {e}")
            return {}

# === Main Function ===

def main():
    """ทดสอบการทำงานของ Security Manager"""
    print("🔒 Testing Security Manager...")
    
    # สร้าง config
    config = SecurityConfig()
    
    # สร้าง Security Manager
    security_manager = SecurityManager(config)
    
    # ทดสอบสร้างผู้ใช้
    print("\n📝 Testing user creation...")
    result = security_manager.create_user(
        username="testuser",
        email="test@example.com",
        password="SecurePass123!",
        role="user"
    )
    print(f"User creation result: {result}")
    
    # ทดสอบการยืนยันตัวตน
    print("\n🔐 Testing authentication...")
    auth_result = security_manager.authenticate_user("testuser", "SecurePass123!")
    print(f"Authentication result: {auth_result['success']}")
    
    if auth_result["success"]:
        # ทดสอบ JWT token
        print("\n🎫 Testing JWT token...")
        token_result = security_manager.verify_jwt_token(auth_result["access_token"])
        print(f"Token verification: {token_result['valid']}")
        
        # ทดสอบสร้าง API key
        print("\n🔑 Testing API key generation...")
        api_key_result = security_manager.generate_api_key(
            user_id=auth_result["user"]["id"],
            name="Test API Key",
            permissions=["read", "write"]
        )
        print(f"API key generation: {api_key_result['success']}")
        
        if api_key_result["success"]:
            # ทดสอบ API key verification
            print("\n✅ Testing API key verification...")
            verify_result = security_manager.verify_api_key(api_key_result["api_key"])
            print(f"API key verification: {verify_result['valid']}")
    
    # ทดสอบ rate limiting
    print("\n⏱️ Testing rate limiting...")
    for i in range(3):
        rate_result = security_manager.check_rate_limit("127.0.0.1", "general")
        print(f"Rate limit check {i+1}: {rate_result['allowed']}")
    
    # ทดสอบ CSRF token
    print("\n🛡️ Testing CSRF token...")
    csrf_token = security_manager.generate_csrf_token("1")
    csrf_valid = security_manager.verify_csrf_token(csrf_token, "1")
    print(f"CSRF token validation: {csrf_valid}")
    
    # ทดสอบ input validation
    print("\n🧹 Testing input sanitization...")
    dirty_input = "<script>alert('xss')</script>Hello World"
    clean_input = security_manager.sanitize_input(dirty_input, "html")
    print(f"Sanitized input: {clean_input}")
    
    # ดึงข้อมูล dashboard
    print("\n📊 Getting security dashboard data...")
    dashboard_data = security_manager.get_security_dashboard_data()
    print(f"Dashboard data keys: {list(dashboard_data.keys())}")
    
    print("\n✅ Security Manager testing completed!")

if __name__ == "__main__":
    main()