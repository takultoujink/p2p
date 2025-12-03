"""
Advanced Mobile AI System
รองรับ Offline detection, Camera filters, AR overlays และ Voice commands
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
import uuid

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image, ImageFilter, ImageEnhance
import speech_recognition as sr
import pyttsx3
import mediapipe as mp
from scipy.spatial.distance import euclidean
import tensorflow as tf
from tensorflow.lite.python import interpreter as tflite_interpreter

# Configuration Classes
@dataclass
class MobileConfig:
    """การกำหนดค่าสำหรับระบบ Mobile AI"""
    device_id: str
    platform: str  # 'android', 'ios', 'web'
    offline_mode: bool = True
    camera_enabled: bool = True
    ar_enabled: bool = True
    voice_enabled: bool = True
    model_path: str = "models/"
    cache_size: int = 100
    max_fps: int = 30
    resolution: Tuple[int, int] = (1280, 720)

@dataclass
class CameraConfig:
    """การกำหนดค่ากล้อง"""
    camera_id: int = 0
    resolution: Tuple[int, int] = (1280, 720)
    fps: int = 30
    auto_focus: bool = True
    flash_enabled: bool = False
    stabilization: bool = True
    exposure_compensation: int = 0

@dataclass
class ARConfig:
    """การกำหนดค่า AR"""
    tracking_enabled: bool = True
    occlusion_enabled: bool = True
    lighting_estimation: bool = True
    plane_detection: bool = True
    face_tracking: bool = True
    hand_tracking: bool = True
    object_tracking: bool = True

@dataclass
class VoiceConfig:
    """การกำหนดค่า Voice"""
    language: str = "th-TH"
    voice_rate: int = 150
    voice_volume: float = 0.9
    wake_word: str = "hey ai"
    continuous_listening: bool = False
    noise_reduction: bool = True

@dataclass
class FilterConfig:
    """การกำหนดค่า Camera Filter"""
    filter_type: str
    intensity: float = 1.0
    parameters: Dict[str, Any] = None

class DetectionResult:
    """ผลลัพธ์การตรวจจับ"""
    def __init__(self, class_name: str, confidence: float, bbox: Tuple[int, int, int, int], 
                 timestamp: datetime = None):
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox  # (x, y, width, height)
        self.timestamp = timestamp or datetime.now()
        self.id = str(uuid.uuid4())

class ARObject:
    """วัตถุ AR"""
    def __init__(self, object_id: str, position: Tuple[float, float, float], 
                 rotation: Tuple[float, float, float], scale: Tuple[float, float, float]):
        self.object_id = object_id
        self.position = position  # (x, y, z)
        self.rotation = rotation  # (rx, ry, rz)
        self.scale = scale       # (sx, sy, sz)
        self.visible = True
        self.created_at = datetime.now()

# Offline Model Manager
class OfflineModelManager:
    """จัดการโมเดล AI สำหรับการทำงานแบบ Offline"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.models = {}
        self.tflite_models = {}
        self.model_cache = {}
        self.logger = logging.getLogger(__name__)
        
    def load_tflite_model(self, model_name: str, model_file: str) -> bool:
        """โหลดโมเดล TensorFlow Lite"""
        try:
            model_path = self.model_path / model_file
            if not model_path.exists():
                self.logger.error(f"Model file not found: {model_path}")
                return False
                
            interpreter = tflite_interpreter.Interpreter(model_path=str(model_path))
            interpreter.allocate_tensors()
            
            self.tflite_models[model_name] = {
                'interpreter': interpreter,
                'input_details': interpreter.get_input_details(),
                'output_details': interpreter.get_output_details()
            }
            
            self.logger.info(f"TFLite model loaded: {model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading TFLite model {model_name}: {e}")
            return False
    
    def load_pytorch_model(self, model_name: str, model_class: nn.Module, 
                          model_file: str) -> bool:
        """โหลดโมเดล PyTorch"""
        try:
            model_path = self.model_path / model_file
            if not model_path.exists():
                self.logger.error(f"Model file not found: {model_path}")
                return False
                
            model = model_class()
            model.load_state_dict(torch.load(model_path, map_location='cpu'))
            model.eval()
            
            self.models[model_name] = model
            self.logger.info(f"PyTorch model loaded: {model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading PyTorch model {model_name}: {e}")
            return False
    
    def predict_tflite(self, model_name: str, input_data: np.ndarray) -> np.ndarray:
        """ทำนายด้วยโมเดล TFLite"""
        if model_name not in self.tflite_models:
            raise ValueError(f"Model {model_name} not loaded")
            
        model_info = self.tflite_models[model_name]
        interpreter = model_info['interpreter']
        input_details = model_info['input_details']
        output_details = model_info['output_details']
        
        # Set input tensor
        interpreter.set_tensor(input_details[0]['index'], input_data)
        
        # Run inference
        interpreter.invoke()
        
        # Get output
        output_data = interpreter.get_tensor(output_details[0]['index'])
        return output_data
    
    def predict_pytorch(self, model_name: str, input_data: torch.Tensor) -> torch.Tensor:
        """ทำนายด้วยโมเดล PyTorch"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
            
        model = self.models[model_name]
        with torch.no_grad():
            output = model(input_data)
        return output

# Camera Filter System
class CameraFilter:
    """ระบบ Filter กล้อง"""
    
    @staticmethod
    def apply_beauty_filter(image: np.ndarray, intensity: float = 0.5) -> np.ndarray:
        """ใช้ Beauty Filter"""
        # Skin smoothing
        bilateral = cv2.bilateralFilter(image, 15, 80, 80)
        
        # Blend with original
        result = cv2.addWeighted(image, 1 - intensity, bilateral, intensity, 0)
        
        # Enhance brightness slightly
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = cv2.add(hsv[:, :, 2], int(10 * intensity))
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return result
    
    @staticmethod
    def apply_vintage_filter(image: np.ndarray, intensity: float = 0.7) -> np.ndarray:
        """ใช้ Vintage Filter"""
        # Convert to float
        img_float = image.astype(np.float32) / 255.0
        
        # Apply sepia tone
        sepia_kernel = np.array([[0.272, 0.534, 0.131],
                                [0.349, 0.686, 0.168],
                                [0.393, 0.769, 0.189]])
        
        sepia_img = cv2.transform(img_float, sepia_kernel)
        sepia_img = np.clip(sepia_img, 0, 1)
        
        # Add vignette effect
        rows, cols = image.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, cols/3)
        kernel_y = cv2.getGaussianKernel(rows, rows/3)
        kernel = kernel_y * kernel_x.T
        mask = kernel / kernel.max()
        
        for i in range(3):
            sepia_img[:, :, i] = sepia_img[:, :, i] * mask
        
        # Blend with original
        result = cv2.addWeighted(image.astype(np.float32)/255.0, 1-intensity, 
                               sepia_img, intensity, 0)
        
        return (result * 255).astype(np.uint8)
    
    @staticmethod
    def apply_cartoon_filter(image: np.ndarray) -> np.ndarray:
        """ใช้ Cartoon Filter"""
        # Edge detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                     cv2.THRESH_BINARY, 9, 9)
        
        # Color quantization
        data = np.float32(image).reshape((-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, 8, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()].reshape(image.shape)
        
        # Combine edges and quantized image
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        cartoon = cv2.bitwise_and(quantized, edges)
        
        return cartoon

class FilterManager:
    """จัดการ Camera Filters"""
    
    def __init__(self):
        self.filters = {
            'beauty': CameraFilter.apply_beauty_filter,
            'vintage': CameraFilter.apply_vintage_filter,
            'cartoon': CameraFilter.apply_cartoon_filter
        }
        self.active_filters = []
    
    def add_filter(self, filter_config: FilterConfig):
        """เพิ่ม Filter"""
        self.active_filters.append(filter_config)
    
    def remove_filter(self, filter_type: str):
        """ลบ Filter"""
        self.active_filters = [f for f in self.active_filters if f.filter_type != filter_type]
    
    def apply_filters(self, image: np.ndarray) -> np.ndarray:
        """ใช้ Filters ทั้งหมด"""
        result = image.copy()
        
        for filter_config in self.active_filters:
            if filter_config.filter_type in self.filters:
                filter_func = self.filters[filter_config.filter_type]
                
                # Apply filter with intensity
                if filter_config.filter_type == 'beauty':
                    result = filter_func(result, filter_config.intensity)
                elif filter_config.filter_type == 'vintage':
                    result = filter_func(result, filter_config.intensity)
                else:
                    result = filter_func(result)
        
        return result

# AR System
class ARTracker:
    """ระบบติดตาม AR"""
    
    def __init__(self, ar_config: ARConfig):
        self.config = ar_config
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        
        # Initialize MediaPipe
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        ) if ar_config.face_tracking else None
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5
        ) if ar_config.hand_tracking else None
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5
        ) if ar_config.object_tracking else None
        
        self.tracked_objects = {}
        self.ar_objects = {}
    
    def track_face(self, image: np.ndarray) -> Optional[Dict]:
        """ติดตามใบหน้า"""
        if not self.face_mesh:
            return None
            
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extract key points
            landmarks = []
            for landmark in face_landmarks.landmark:
                x = int(landmark.x * image.shape[1])
                y = int(landmark.y * image.shape[0])
                landmarks.append((x, y))
            
            return {
                'landmarks': landmarks,
                'bbox': self._get_face_bbox(landmarks),
                'confidence': 0.9  # MediaPipe doesn't provide confidence
            }
        
        return None
    
    def track_hands(self, image: np.ndarray) -> List[Dict]:
        """ติดตามมือ"""
        if not self.hands:
            return []
            
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_image)
        
        hands_data = []
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, 
                                                 results.multi_handedness):
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * image.shape[1])
                    y = int(landmark.y * image.shape[0])
                    landmarks.append((x, y))
                
                hands_data.append({
                    'landmarks': landmarks,
                    'handedness': handedness.classification[0].label,
                    'bbox': self._get_hand_bbox(landmarks),
                    'confidence': handedness.classification[0].score
                })
        
        return hands_data
    
    def _get_face_bbox(self, landmarks: List[Tuple[int, int]]) -> Tuple[int, int, int, int]:
        """คำนวณ Bounding Box ของใบหน้า"""
        x_coords = [point[0] for point in landmarks]
        y_coords = [point[1] for point in landmarks]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        return (x_min, y_min, x_max - x_min, y_max - y_min)
    
    def _get_hand_bbox(self, landmarks: List[Tuple[int, int]]) -> Tuple[int, int, int, int]:
        """คำนวณ Bounding Box ของมือ"""
        x_coords = [point[0] for point in landmarks]
        y_coords = [point[1] for point in landmarks]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add padding
        padding = 20
        return (x_min - padding, y_min - padding, 
                x_max - x_min + 2*padding, y_max - y_min + 2*padding)

class ARRenderer:
    """เรนเดอร์วัตถุ AR"""
    
    def __init__(self):
        self.ar_objects = {}
        self.effects = {}
    
    def add_ar_object(self, object_id: str, ar_object: ARObject):
        """เพิ่มวัตถุ AR"""
        self.ar_objects[object_id] = ar_object
    
    def remove_ar_object(self, object_id: str):
        """ลบวัตถุ AR"""
        if object_id in self.ar_objects:
            del self.ar_objects[object_id]
    
    def render_face_effects(self, image: np.ndarray, face_data: Dict) -> np.ndarray:
        """เรนเดอร์เอฟเฟกต์บนใบหน้า"""
        result = image.copy()
        
        if face_data:
            landmarks = face_data['landmarks']
            
            # Draw face mesh
            for point in landmarks[::10]:  # Draw every 10th point
                cv2.circle(result, point, 2, (0, 255, 0), -1)
            
            # Add virtual glasses effect
            if len(landmarks) > 70:
                left_eye = landmarks[33]
                right_eye = landmarks[263]
                
                # Calculate glasses position and size
                eye_distance = euclidean(left_eye, right_eye)
                glasses_width = int(eye_distance * 2.5)
                glasses_height = int(glasses_width * 0.4)
                
                center_x = (left_eye[0] + right_eye[0]) // 2
                center_y = (left_eye[1] + right_eye[1]) // 2
                
                # Draw simple glasses
                cv2.rectangle(result, 
                            (center_x - glasses_width//2, center_y - glasses_height//2),
                            (center_x + glasses_width//2, center_y + glasses_height//2),
                            (0, 0, 255), 3)
                
                # Draw nose bridge
                cv2.line(result, 
                        (center_x - 10, center_y),
                        (center_x + 10, center_y),
                        (0, 0, 255), 3)
        
        return result
    
    def render_hand_effects(self, image: np.ndarray, hands_data: List[Dict]) -> np.ndarray:
        """เรนเดอร์เอฟเฟกต์บนมือ"""
        result = image.copy()
        
        for hand_data in hands_data:
            landmarks = hand_data['landmarks']
            
            # Draw hand skeleton
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                (0, 5), (5, 6), (6, 7), (7, 8),  # Index
                (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
                (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
                (0, 17), (17, 18), (18, 19), (19, 20)   # Pinky
            ]
            
            # Draw connections
            for connection in connections:
                if connection[0] < len(landmarks) and connection[1] < len(landmarks):
                    pt1 = landmarks[connection[0]]
                    pt2 = landmarks[connection[1]]
                    cv2.line(result, pt1, pt2, (255, 0, 0), 2)
            
            # Draw landmarks
            for point in landmarks:
                cv2.circle(result, point, 3, (0, 255, 255), -1)
        
        return result

# Voice Command System
class VoiceCommandProcessor:
    """ประมวลผลคำสั่งเสียง"""
    
    def __init__(self, voice_config: VoiceConfig):
        self.config = voice_config
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Configure TTS
        self.tts_engine.setProperty('rate', voice_config.voice_rate)
        self.tts_engine.setProperty('volume', voice_config.voice_volume)
        
        self.commands = {
            'take photo': self._take_photo,
            'start recording': self._start_recording,
            'stop recording': self._stop_recording,
            'apply filter': self._apply_filter,
            'remove filter': self._remove_filter,
            'switch camera': self._switch_camera,
            'enable ar': self._enable_ar,
            'disable ar': self._disable_ar
        }
        
        self.listening = False
        self.command_callbacks = {}
    
    def register_command_callback(self, command: str, callback: Callable):
        """ลงทะเบียน Callback สำหรับคำสั่ง"""
        self.command_callbacks[command] = callback
    
    def start_listening(self):
        """เริ่มฟังคำสั่งเสียง"""
        self.listening = True
        
        def listen_loop():
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            
            while self.listening:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    # Recognize speech
                    text = self.recognizer.recognize_google(audio, language=self.config.language)
                    text = text.lower()
                    
                    # Check for wake word
                    if self.config.wake_word in text:
                        self._process_command(text)
                        
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    logging.error(f"Voice recognition error: {e}")
        
        # Start listening in background thread
        listen_thread = threading.Thread(target=listen_loop)
        listen_thread.daemon = True
        listen_thread.start()
    
    def stop_listening(self):
        """หยุดฟังคำสั่งเสียง"""
        self.listening = False
    
    def speak(self, text: str):
        """พูดข้อความ"""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def _process_command(self, text: str):
        """ประมวลผลคำสั่ง"""
        for command, action in self.commands.items():
            if command in text:
                action()
                break
        else:
            # Check custom callbacks
            for command, callback in self.command_callbacks.items():
                if command in text:
                    callback()
                    break
    
    def _take_photo(self):
        """ถ่ายภาพ"""
        if 'take_photo' in self.command_callbacks:
            self.command_callbacks['take_photo']()
        self.speak("ถ่ายภาพแล้ว")
    
    def _start_recording(self):
        """เริ่มบันทึกวิดีโอ"""
        if 'start_recording' in self.command_callbacks:
            self.command_callbacks['start_recording']()
        self.speak("เริ่มบันทึกวิดีโอ")
    
    def _stop_recording(self):
        """หยุดบันทึกวิดีโอ"""
        if 'stop_recording' in self.command_callbacks:
            self.command_callbacks['stop_recording']()
        self.speak("หยุดบันทึกวิดีโอ")
    
    def _apply_filter(self):
        """ใช้ Filter"""
        if 'apply_filter' in self.command_callbacks:
            self.command_callbacks['apply_filter']()
        self.speak("ใช้ฟิลเตอร์แล้ว")
    
    def _remove_filter(self):
        """ลบ Filter"""
        if 'remove_filter' in self.command_callbacks:
            self.command_callbacks['remove_filter']()
        self.speak("ลบฟิลเตอร์แล้ว")
    
    def _switch_camera(self):
        """เปลี่ยนกล้อง"""
        if 'switch_camera' in self.command_callbacks:
            self.command_callbacks['switch_camera']()
        self.speak("เปลี่ยนกล้องแล้ว")
    
    def _enable_ar(self):
        """เปิด AR"""
        if 'enable_ar' in self.command_callbacks:
            self.command_callbacks['enable_ar']()
        self.speak("เปิด AR แล้ว")
    
    def _disable_ar(self):
        """ปิด AR"""
        if 'disable_ar' in self.command_callbacks:
            self.command_callbacks['disable_ar']()
        self.speak("ปิด AR แล้ว")

# Main Mobile AI System
class MobileAISystem:
    """ระบบ Mobile AI หลัก"""
    
    def __init__(self, config: MobileConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.model_manager = OfflineModelManager(config.model_path)
        self.filter_manager = FilterManager()
        self.ar_tracker = ARTracker(ARConfig()) if config.ar_enabled else None
        self.ar_renderer = ARRenderer() if config.ar_enabled else None
        self.voice_processor = VoiceCommandProcessor(VoiceConfig()) if config.voice_enabled else None
        
        # Camera setup
        self.camera = None
        self.camera_config = CameraConfig()
        self.recording = False
        self.video_writer = None
        
        # State
        self.running = False
        self.current_frame = None
        self.detection_results = []
        self.performance_metrics = {}
        
        # Database
        self.db_path = "mobile_ai_data.db"
        self._init_database()
        
        # Setup voice commands
        if self.voice_processor:
            self._setup_voice_commands()
    
    def _init_database(self):
        """เริ่มต้นฐานข้อมูล"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id TEXT PRIMARY KEY,
                class_name TEXT,
                confidence REAL,
                bbox TEXT,
                timestamp DATETIME,
                device_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fps REAL,
                processing_time REAL,
                memory_usage REAL,
                timestamp DATETIME,
                device_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_voice_commands(self):
        """ตั้งค่าคำสั่งเสียง"""
        self.voice_processor.register_command_callback('take_photo', self.take_photo)
        self.voice_processor.register_command_callback('start_recording', self.start_recording)
        self.voice_processor.register_command_callback('stop_recording', self.stop_recording)
        self.voice_processor.register_command_callback('apply_filter', self.apply_beauty_filter)
        self.voice_processor.register_command_callback('remove_filter', self.remove_all_filters)
        self.voice_processor.register_command_callback('switch_camera', self.switch_camera)
        self.voice_processor.register_command_callback('enable_ar', self.enable_ar)
        self.voice_processor.register_command_callback('disable_ar', self.disable_ar)
    
    def initialize_camera(self) -> bool:
        """เริ่มต้นกล้อง"""
        try:
            self.camera = cv2.VideoCapture(self.camera_config.camera_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config.resolution[1])
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_config.fps)
            
            if not self.camera.isOpened():
                self.logger.error("Failed to open camera")
                return False
            
            self.logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing camera: {e}")
            return False
    
    def load_models(self) -> bool:
        """โหลดโมเดล AI"""
        try:
            # Load object detection model (TFLite)
            success = self.model_manager.load_tflite_model(
                'object_detection', 
                'mobilenet_ssd_v2.tflite'
            )
            
            if not success:
                self.logger.warning("Object detection model not loaded")
            
            self.logger.info("Models loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False
    
    def start_system(self):
        """เริ่มระบบ"""
        if not self.initialize_camera():
            return False
        
        if not self.load_models():
            self.logger.warning("Some models failed to load")
        
        self.running = True
        
        # Start voice commands
        if self.voice_processor:
            self.voice_processor.start_listening()
        
        self.logger.info("Mobile AI System started")
        return True
    
    def stop_system(self):
        """หยุดระบบ"""
        self.running = False
        
        if self.camera:
            self.camera.release()
        
        if self.video_writer:
            self.video_writer.release()
        
        if self.voice_processor:
            self.voice_processor.stop_listening()
        
        cv2.destroyAllWindows()
        self.logger.info("Mobile AI System stopped")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """ประมวลผลเฟรม"""
        start_time = time.time()
        result = frame.copy()
        
        try:
            # Object detection (if model available)
            if 'object_detection' in self.model_manager.tflite_models:
                detections = self._detect_objects(frame)
                result = self._draw_detections(result, detections)
                self.detection_results = detections
            
            # Apply camera filters
            result = self.filter_manager.apply_filters(result)
            
            # AR processing
            if self.ar_tracker and self.ar_renderer:
                # Track face and hands
                face_data = self.ar_tracker.track_face(frame)
                hands_data = self.ar_tracker.track_hands(frame)
                
                # Render AR effects
                if face_data:
                    result = self.ar_renderer.render_face_effects(result, face_data)
                
                if hands_data:
                    result = self.ar_renderer.render_hand_effects(result, hands_data)
            
            # Calculate performance metrics
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time)
            
            self.current_frame = result
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return frame
    
    def _detect_objects(self, frame: np.ndarray) -> List[DetectionResult]:
        """ตรวจจับวัตถุ"""
        try:
            # Preprocess image
            input_size = (300, 300)  # MobileNet SSD input size
            resized = cv2.resize(frame, input_size)
            input_data = np.expand_dims(resized, axis=0).astype(np.float32)
            input_data = (input_data - 127.5) / 127.5  # Normalize to [-1, 1]
            
            # Run inference
            output = self.model_manager.predict_tflite('object_detection', input_data)
            
            # Parse results (assuming SSD MobileNet format)
            detections = []
            boxes = output[0][0]  # Bounding boxes
            classes = output[1][0]  # Class IDs
            scores = output[2][0]  # Confidence scores
            
            h, w = frame.shape[:2]
            
            for i in range(len(scores)):
                if scores[i] > 0.5:  # Confidence threshold
                    # Convert normalized coordinates to pixel coordinates
                    y1, x1, y2, x2 = boxes[i]
                    x1, y1, x2, y2 = int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)
                    
                    detection = DetectionResult(
                        class_name=f"class_{int(classes[i])}",
                        confidence=float(scores[i]),
                        bbox=(x1, y1, x2 - x1, y2 - y1)
                    )
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Error in object detection: {e}")
            return []
    
    def _draw_detections(self, frame: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """วาดผลลัพธ์การตรวจจับ"""
        for detection in detections:
            x, y, w, h = detection.bbox
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label
            label = f"{detection.class_name}: {detection.confidence:.2f}"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 255, 0), 2)
        
        return frame
    
    def _update_performance_metrics(self, processing_time: float):
        """อัปเดตเมตริกประสิทธิภาพ"""
        fps = 1.0 / processing_time if processing_time > 0 else 0
        
        self.performance_metrics = {
            'fps': fps,
            'processing_time': processing_time,
            'timestamp': datetime.now()
        }
    
    def take_photo(self):
        """ถ่ายภาพ"""
        if self.current_frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
            cv2.imwrite(filename, self.current_frame)
            self.logger.info(f"Photo saved: {filename}")
    
    def start_recording(self):
        """เริ่มบันทึกวิดีโอ"""
        if not self.recording and self.current_frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            h, w = self.current_frame.shape[:2]
            self.video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (w, h))
            
            self.recording = True
            self.logger.info(f"Recording started: {filename}")
    
    def stop_recording(self):
        """หยุดบันทึกวิดีโอ"""
        if self.recording and self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            self.recording = False
            self.logger.info("Recording stopped")
    
    def apply_beauty_filter(self):
        """ใช้ Beauty Filter"""
        filter_config = FilterConfig(filter_type='beauty', intensity=0.7)
        self.filter_manager.add_filter(filter_config)
        self.logger.info("Beauty filter applied")
    
    def remove_all_filters(self):
        """ลบ Filter ทั้งหมด"""
        self.filter_manager.active_filters.clear()
        self.logger.info("All filters removed")
    
    def switch_camera(self):
        """เปลี่ยนกล้อง"""
        if self.camera:
            self.camera.release()
            self.camera_config.camera_id = 1 - self.camera_config.camera_id  # Toggle between 0 and 1
            self.initialize_camera()
            self.logger.info(f"Switched to camera {self.camera_config.camera_id}")
    
    def enable_ar(self):
        """เปิด AR"""
        if not self.ar_tracker:
            self.ar_tracker = ARTracker(ARConfig())
            self.ar_renderer = ARRenderer()
            self.logger.info("AR enabled")
    
    def disable_ar(self):
        """ปิด AR"""
        self.ar_tracker = None
        self.ar_renderer = None
        self.logger.info("AR disabled")
    
    def run_camera_loop(self):
        """รันลูปกล้อง"""
        while self.running:
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    # Process frame
                    processed_frame = self.process_frame(frame)
                    
                    # Record if recording
                    if self.recording and self.video_writer:
                        self.video_writer.write(processed_frame)
                    
                    # Display frame
                    cv2.imshow('Mobile AI System', processed_frame)
                    
                    # Check for quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    self.logger.error("Failed to read frame from camera")
                    break
            else:
                time.sleep(0.1)

def main():
    """ฟังก์ชันหลักสำหรับทดสอบระบบ"""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create configuration
    config = MobileConfig(
        device_id="mobile_device_001",
        platform="android",
        offline_mode=True,
        camera_enabled=True,
        ar_enabled=True,
        voice_enabled=True
    )
    
    # Create and start system
    mobile_system = MobileAISystem(config)
    
    try:
        if mobile_system.start_system():
            print("Mobile AI System started successfully!")
            print("Press 'q' to quit")
            
            # Run camera loop
            mobile_system.run_camera_loop()
        else:
            print("Failed to start Mobile AI System")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    finally:
        mobile_system.stop_system()
        print("Mobile AI System stopped")

if __name__ == "__main__":
    main()