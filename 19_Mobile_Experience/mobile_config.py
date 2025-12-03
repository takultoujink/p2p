"""
Mobile AI System Configuration Management
จัดการการกำหนดค่าสำหรับระบบ Mobile AI
"""

import json
import os
import yaml
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

class Platform(Enum):
    """แพลตฟอร์มที่รองรับ"""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    DESKTOP = "desktop"

class CameraType(Enum):
    """ประเภทกล้อง"""
    FRONT = "front"
    BACK = "back"
    EXTERNAL = "external"

class FilterType(Enum):
    """ประเภท Filter"""
    BEAUTY = "beauty"
    VINTAGE = "vintage"
    CARTOON = "cartoon"
    BLUR = "blur"
    SHARPEN = "sharpen"
    SEPIA = "sepia"
    GRAYSCALE = "grayscale"

class ARMode(Enum):
    """โหมด AR"""
    FACE_TRACKING = "face_tracking"
    HAND_TRACKING = "hand_tracking"
    OBJECT_TRACKING = "object_tracking"
    PLANE_DETECTION = "plane_detection"
    FULL_AR = "full_ar"

@dataclass
class DeviceCapabilities:
    """ความสามารถของอุปกรณ์"""
    has_camera: bool = True
    has_microphone: bool = True
    has_accelerometer: bool = True
    has_gyroscope: bool = True
    has_gps: bool = True
    has_nfc: bool = False
    has_bluetooth: bool = True
    has_wifi: bool = True
    supports_ar: bool = True
    supports_ml: bool = True
    max_camera_resolution: Tuple[int, int] = (1920, 1080)
    max_fps: int = 60
    available_cameras: List[str] = None
    
    def __post_init__(self):
        if self.available_cameras is None:
            self.available_cameras = ["front", "back"]

@dataclass
class PerformanceSettings:
    """การตั้งค่าประสิทธิภาพ"""
    target_fps: int = 30
    max_processing_time: float = 0.033  # 33ms for 30fps
    enable_gpu_acceleration: bool = True
    enable_model_quantization: bool = True
    enable_frame_skipping: bool = True
    memory_limit_mb: int = 512
    cache_size_mb: int = 100
    batch_size: int = 1
    thread_count: int = 4
    priority_mode: str = "balanced"  # "performance", "battery", "balanced"

@dataclass
class CameraSettings:
    """การตั้งค่ากล้อง"""
    camera_id: int = 0
    camera_type: CameraType = CameraType.BACK
    resolution: Tuple[int, int] = (1280, 720)
    fps: int = 30
    auto_focus: bool = True
    auto_exposure: bool = True
    auto_white_balance: bool = True
    flash_enabled: bool = False
    stabilization: bool = True
    zoom_level: float = 1.0
    exposure_compensation: int = 0
    iso_value: int = 0  # 0 for auto
    focus_distance: float = 0.0  # 0 for auto
    
@dataclass
class FilterSettings:
    """การตั้งค่า Filter"""
    enabled_filters: List[FilterType] = None
    default_filter: Optional[FilterType] = None
    filter_intensity: float = 0.7
    real_time_preview: bool = True
    save_original: bool = True
    custom_filters: Dict[str, Dict] = None
    
    def __post_init__(self):
        if self.enabled_filters is None:
            self.enabled_filters = [FilterType.BEAUTY, FilterType.VINTAGE]
        if self.custom_filters is None:
            self.custom_filters = {}

@dataclass
class ARSettings:
    """การตั้งค่า AR"""
    ar_mode: ARMode = ARMode.FACE_TRACKING
    face_tracking_enabled: bool = True
    hand_tracking_enabled: bool = True
    object_tracking_enabled: bool = False
    plane_detection_enabled: bool = False
    occlusion_enabled: bool = True
    lighting_estimation: bool = True
    max_tracked_faces: int = 1
    max_tracked_hands: int = 2
    max_tracked_objects: int = 5
    tracking_confidence: float = 0.5
    detection_confidence: float = 0.7
    ar_effects_enabled: bool = True
    virtual_objects_enabled: bool = True

@dataclass
class VoiceSettings:
    """การตั้งค่าเสียง"""
    voice_commands_enabled: bool = True
    language: str = "th-TH"
    alternative_languages: List[str] = None
    wake_word: str = "hey ai"
    continuous_listening: bool = False
    voice_feedback: bool = True
    tts_enabled: bool = True
    tts_voice: str = "default"
    tts_rate: int = 150
    tts_volume: float = 0.8
    noise_reduction: bool = True
    echo_cancellation: bool = True
    microphone_sensitivity: float = 0.7
    
    def __post_init__(self):
        if self.alternative_languages is None:
            self.alternative_languages = ["en-US", "zh-CN"]

@dataclass
class OfflineSettings:
    """การตั้งค่าโหมด Offline"""
    offline_mode_enabled: bool = True
    auto_download_models: bool = True
    model_storage_path: str = "models/"
    max_storage_size_mb: int = 1024
    cache_detection_results: bool = True
    cache_duration_hours: int = 24
    sync_when_online: bool = True
    offline_analytics: bool = True
    local_database_enabled: bool = True

@dataclass
class SecuritySettings:
    """การตั้งค่าความปลอดภัย"""
    encrypt_local_data: bool = True
    require_authentication: bool = False
    biometric_auth: bool = False
    session_timeout_minutes: int = 30
    auto_lock_enabled: bool = True
    privacy_mode: bool = False
    data_anonymization: bool = True
    secure_communication: bool = True
    certificate_pinning: bool = True

@dataclass
class UISettings:
    """การตั้งค่า UI"""
    theme: str = "dark"  # "light", "dark", "auto"
    language: str = "th"
    show_fps_counter: bool = False
    show_detection_info: bool = True
    show_ar_debug: bool = False
    button_size: str = "medium"  # "small", "medium", "large"
    gesture_controls: bool = True
    haptic_feedback: bool = True
    sound_effects: bool = True
    animation_enabled: bool = True
    fullscreen_mode: bool = False

@dataclass
class NetworkSettings:
    """การตั้งค่าเครือข่าย"""
    cloud_sync_enabled: bool = True
    auto_upload: bool = False
    wifi_only_upload: bool = True
    max_upload_size_mb: int = 100
    compression_enabled: bool = True
    retry_attempts: int = 3
    timeout_seconds: int = 30
    api_endpoint: str = "https://api.example.com"
    api_key: str = ""
    use_cdn: bool = True

@dataclass
class AnalyticsSettings:
    """การตั้งค่า Analytics"""
    analytics_enabled: bool = True
    crash_reporting: bool = True
    performance_monitoring: bool = True
    usage_statistics: bool = True
    anonymous_data_collection: bool = True
    detailed_logging: bool = False
    log_level: str = "INFO"  # "DEBUG", "INFO", "WARNING", "ERROR"
    max_log_size_mb: int = 50

class MobileAIConfig:
    """คลาสหลักสำหรับการกำหนดค่า Mobile AI"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        
        # Default configurations
        self.platform = Platform.ANDROID
        self.device_id = "mobile_device_001"
        self.app_version = "1.0.0"
        
        # Component configurations
        self.device_capabilities = DeviceCapabilities()
        self.performance = PerformanceSettings()
        self.camera = CameraSettings()
        self.filters = FilterSettings()
        self.ar = ARSettings()
        self.voice = VoiceSettings()
        self.offline = OfflineSettings()
        self.security = SecuritySettings()
        self.ui = UISettings()
        self.network = NetworkSettings()
        self.analytics = AnalyticsSettings()
        
        # Load configuration if file provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงการกำหนดค่าเป็น Dictionary"""
        return {
            'platform': self.platform.value,
            'device_id': self.device_id,
            'app_version': self.app_version,
            'device_capabilities': asdict(self.device_capabilities),
            'performance': asdict(self.performance),
            'camera': asdict(self.camera),
            'filters': asdict(self.filters),
            'ar': asdict(self.ar),
            'voice': asdict(self.voice),
            'offline': asdict(self.offline),
            'security': asdict(self.security),
            'ui': asdict(self.ui),
            'network': asdict(self.network),
            'analytics': asdict(self.analytics)
        }
    
    def from_dict(self, config_dict: Dict[str, Any]):
        """โหลดการกำหนดค่าจาก Dictionary"""
        self.platform = Platform(config_dict.get('platform', 'android'))
        self.device_id = config_dict.get('device_id', 'mobile_device_001')
        self.app_version = config_dict.get('app_version', '1.0.0')
        
        # Load component configurations
        if 'device_capabilities' in config_dict:
            self.device_capabilities = DeviceCapabilities(**config_dict['device_capabilities'])
        
        if 'performance' in config_dict:
            self.performance = PerformanceSettings(**config_dict['performance'])
        
        if 'camera' in config_dict:
            camera_data = config_dict['camera'].copy()
            if 'camera_type' in camera_data:
                camera_data['camera_type'] = CameraType(camera_data['camera_type'])
            self.camera = CameraSettings(**camera_data)
        
        if 'filters' in config_dict:
            filters_data = config_dict['filters'].copy()
            if 'enabled_filters' in filters_data:
                filters_data['enabled_filters'] = [FilterType(f) for f in filters_data['enabled_filters']]
            if 'default_filter' in filters_data and filters_data['default_filter']:
                filters_data['default_filter'] = FilterType(filters_data['default_filter'])
            self.filters = FilterSettings(**filters_data)
        
        if 'ar' in config_dict:
            ar_data = config_dict['ar'].copy()
            if 'ar_mode' in ar_data:
                ar_data['ar_mode'] = ARMode(ar_data['ar_mode'])
            self.ar = ARSettings(**ar_data)
        
        if 'voice' in config_dict:
            self.voice = VoiceSettings(**config_dict['voice'])
        
        if 'offline' in config_dict:
            self.offline = OfflineSettings(**config_dict['offline'])
        
        if 'security' in config_dict:
            self.security = SecuritySettings(**config_dict['security'])
        
        if 'ui' in config_dict:
            self.ui = UISettings(**config_dict['ui'])
        
        if 'network' in config_dict:
            self.network = NetworkSettings(**config_dict['network'])
        
        if 'analytics' in config_dict:
            self.analytics = AnalyticsSettings(**config_dict['analytics'])
    
    def save_to_file(self, file_path: str, format: str = 'json'):
        """บันทึกการกำหนดค่าลงไฟล์"""
        config_dict = self.to_dict()
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'yaml':
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def load_from_file(self, file_path: str):
        """โหลดการกำหนดค่าจากไฟล์"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_ext == '.json':
                config_dict = json.load(f)
            elif file_ext in ['.yaml', '.yml']:
                config_dict = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        
        self.from_dict(config_dict)
    
    def validate(self) -> List[str]:
        """ตรวจสอบความถูกต้องของการกำหนดค่า"""
        errors = []
        
        # Validate performance settings
        if self.performance.target_fps <= 0:
            errors.append("Target FPS must be positive")
        
        if self.performance.max_processing_time <= 0:
            errors.append("Max processing time must be positive")
        
        # Validate camera settings
        if self.camera.resolution[0] <= 0 or self.camera.resolution[1] <= 0:
            errors.append("Camera resolution must be positive")
        
        if self.camera.fps <= 0:
            errors.append("Camera FPS must be positive")
        
        # Validate AR settings
        if self.ar.tracking_confidence < 0 or self.ar.tracking_confidence > 1:
            errors.append("AR tracking confidence must be between 0 and 1")
        
        if self.ar.detection_confidence < 0 or self.ar.detection_confidence > 1:
            errors.append("AR detection confidence must be between 0 and 1")
        
        # Validate voice settings
        if self.voice.tts_rate <= 0:
            errors.append("TTS rate must be positive")
        
        if self.voice.tts_volume < 0 or self.voice.tts_volume > 1:
            errors.append("TTS volume must be between 0 and 1")
        
        # Validate network settings
        if self.network.timeout_seconds <= 0:
            errors.append("Network timeout must be positive")
        
        if self.network.retry_attempts < 0:
            errors.append("Retry attempts must be non-negative")
        
        return errors
    
    def get_platform_specific_config(self) -> Dict[str, Any]:
        """ได้การกำหนดค่าเฉพาะแพลตฟอร์ม"""
        base_config = self.to_dict()
        
        if self.platform == Platform.ANDROID:
            # Android specific optimizations
            base_config['performance']['enable_gpu_acceleration'] = True
            base_config['camera']['stabilization'] = True
            base_config['ar']['occlusion_enabled'] = True
            
        elif self.platform == Platform.IOS:
            # iOS specific optimizations
            base_config['performance']['enable_model_quantization'] = True
            base_config['camera']['auto_focus'] = True
            base_config['ar']['lighting_estimation'] = True
            
        elif self.platform == Platform.WEB:
            # Web specific limitations
            base_config['performance']['enable_gpu_acceleration'] = False
            base_config['ar']['ar_mode'] = ARMode.FACE_TRACKING.value
            base_config['offline']['offline_mode_enabled'] = False
            
        return base_config
    
    def optimize_for_device(self, device_info: Dict[str, Any]):
        """ปรับการกำหนดค่าให้เหมาะสมกับอุปกรณ์"""
        # Get device specifications
        ram_mb = device_info.get('ram_mb', 4096)
        cpu_cores = device_info.get('cpu_cores', 4)
        gpu_available = device_info.get('gpu_available', True)
        
        # Adjust performance settings based on device capabilities
        if ram_mb < 2048:  # Low-end device
            self.performance.target_fps = 15
            self.performance.memory_limit_mb = 256
            self.performance.cache_size_mb = 50
            self.camera.resolution = (640, 480)
            self.ar.max_tracked_faces = 1
            self.ar.max_tracked_hands = 1
            
        elif ram_mb < 4096:  # Mid-range device
            self.performance.target_fps = 24
            self.performance.memory_limit_mb = 384
            self.performance.cache_size_mb = 75
            self.camera.resolution = (1280, 720)
            
        else:  # High-end device
            self.performance.target_fps = 30
            self.performance.memory_limit_mb = 512
            self.performance.cache_size_mb = 100
            self.camera.resolution = (1920, 1080)
        
        # Adjust thread count based on CPU cores
        self.performance.thread_count = min(cpu_cores, 8)
        
        # Disable GPU acceleration if not available
        if not gpu_available:
            self.performance.enable_gpu_acceleration = False

def create_default_config(platform: Platform = Platform.ANDROID) -> MobileAIConfig:
    """สร้างการกำหนดค่าเริ่มต้น"""
    config = MobileAIConfig()
    config.platform = platform
    
    # Platform-specific defaults
    if platform == Platform.ANDROID:
        config.camera.camera_type = CameraType.BACK
        config.ar.ar_mode = ARMode.FULL_AR
        config.voice.language = "th-TH"
        
    elif platform == Platform.IOS:
        config.camera.camera_type = CameraType.BACK
        config.ar.ar_mode = ARMode.FACE_TRACKING
        config.voice.language = "th-TH"
        
    elif platform == Platform.WEB:
        config.camera.camera_type = CameraType.FRONT
        config.ar.ar_mode = ARMode.FACE_TRACKING
        config.offline.offline_mode_enabled = False
        config.voice.voice_commands_enabled = False
    
    return config

def load_config_from_environment() -> MobileAIConfig:
    """โหลดการกำหนดค่าจากตัวแปรสภาพแวดล้อม"""
    config = create_default_config()
    
    # Override with environment variables
    if 'MOBILE_AI_PLATFORM' in os.environ:
        config.platform = Platform(os.environ['MOBILE_AI_PLATFORM'])
    
    if 'MOBILE_AI_DEVICE_ID' in os.environ:
        config.device_id = os.environ['MOBILE_AI_DEVICE_ID']
    
    if 'MOBILE_AI_TARGET_FPS' in os.environ:
        config.performance.target_fps = int(os.environ['MOBILE_AI_TARGET_FPS'])
    
    if 'MOBILE_AI_CAMERA_RESOLUTION' in os.environ:
        resolution = os.environ['MOBILE_AI_CAMERA_RESOLUTION'].split('x')
        config.camera.resolution = (int(resolution[0]), int(resolution[1]))
    
    if 'MOBILE_AI_OFFLINE_MODE' in os.environ:
        config.offline.offline_mode_enabled = os.environ['MOBILE_AI_OFFLINE_MODE'].lower() == 'true'
    
    if 'MOBILE_AI_API_ENDPOINT' in os.environ:
        config.network.api_endpoint = os.environ['MOBILE_AI_API_ENDPOINT']
    
    if 'MOBILE_AI_API_KEY' in os.environ:
        config.network.api_key = os.environ['MOBILE_AI_API_KEY']
    
    return config

def main():
    """ฟังก์ชันทดสอบการกำหนดค่า"""
    # Create default configuration
    config = create_default_config(Platform.ANDROID)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid")
    
    # Save configuration
    config.save_to_file("mobile_config.json", "json")
    config.save_to_file("mobile_config.yaml", "yaml")
    
    # Load and test configuration
    loaded_config = MobileAIConfig("mobile_config.json")
    print(f"Loaded configuration for platform: {loaded_config.platform.value}")
    
    # Test platform-specific configuration
    platform_config = loaded_config.get_platform_specific_config()
    print(f"Platform-specific config keys: {list(platform_config.keys())}")
    
    # Test device optimization
    device_info = {
        'ram_mb': 3072,
        'cpu_cores': 6,
        'gpu_available': True
    }
    loaded_config.optimize_for_device(device_info)
    print(f"Optimized target FPS: {loaded_config.performance.target_fps}")

if __name__ == "__main__":
    main()