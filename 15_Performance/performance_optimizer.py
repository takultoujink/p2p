"""
Advanced Performance Optimizer for Object Detection System
รองรับ Model caching, Image preprocessing optimization, Batch processing, GPU acceleration
"""

import os
import time
import psutil
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio
import aiofiles
import numpy as np
import cv2
import torch
import tensorflow as tf
from PIL import Image, ImageOps
import pickle
import redis
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from functools import lru_cache, wraps
import hashlib
import gc
import tracemalloc
from memory_profiler import profile
import cProfile
import pstats
from contextlib import contextmanager
import queue
import weakref

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceConfig:
    """การกำหนดค่าประสิทธิภาพ"""
    # Model Caching
    model_cache_enabled: bool = True
    model_cache_size: int = 5  # จำนวน models ที่เก็บใน cache
    model_cache_ttl_hours: int = 24
    model_cache_storage: str = "memory"  # memory, redis, disk
    
    # Image Processing
    image_cache_enabled: bool = True
    image_cache_size_mb: int = 500
    image_preprocessing_workers: int = 4
    image_batch_size: int = 8
    image_resize_quality: str = "high"  # low, medium, high
    
    # GPU Configuration
    gpu_enabled: bool = True
    gpu_memory_fraction: float = 0.8
    gpu_allow_growth: bool = True
    mixed_precision_enabled: bool = True
    
    # Batch Processing
    batch_processing_enabled: bool = True
    max_batch_size: int = 16
    batch_timeout_seconds: float = 0.5
    dynamic_batching: bool = True
    
    # Memory Management
    memory_monitoring_enabled: bool = True
    max_memory_usage_percent: float = 85.0
    garbage_collection_threshold: int = 1000
    memory_cleanup_interval_minutes: int = 30
    
    # CPU Optimization
    cpu_workers: int = multiprocessing.cpu_count()
    thread_pool_size: int = 20
    process_pool_size: int = 4
    
    # Caching Strategy
    result_cache_enabled: bool = True
    result_cache_size: int = 1000
    result_cache_ttl_minutes: int = 60
    
    # Performance Monitoring
    performance_tracking_enabled: bool = True
    metrics_collection_interval_seconds: int = 30
    performance_history_days: int = 7
    
    # Optimization Features
    lazy_loading_enabled: bool = True
    preloading_enabled: bool = True
    compression_enabled: bool = True
    async_processing_enabled: bool = True

@dataclass
class PerformanceMetrics:
    """เมตริกประสิทธิภาพ"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_mb: float
    memory_usage_percent: float
    gpu_usage_percent: float
    gpu_memory_mb: float
    processing_time_ms: float
    throughput_requests_per_second: float
    cache_hit_rate: float
    error_rate: float
    active_connections: int
    queue_size: int

class ModelCache:
    """จัดการ cache สำหรับ models"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.cache = {}
        self.access_times = {}
        self.redis_client = None
        self.cache_dir = "model_cache"
        
        if config.model_cache_storage == "redis":
            self.init_redis()
        elif config.model_cache_storage == "disk":
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def init_redis(self):
        """เริ่มต้น Redis connection"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
            self.redis_client.ping()
            logger.info("Model cache Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available for model cache: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, model_name: str, model_version: str = "latest") -> str:
        """สร้าง cache key"""
        return f"model:{model_name}:{model_version}"
    
    def get_model(self, model_name: str, model_version: str = "latest"):
        """ดึง model จาก cache"""
        if not self.config.model_cache_enabled:
            return None
        
        cache_key = self._generate_cache_key(model_name, model_version)
        
        try:
            if self.config.model_cache_storage == "memory":
                return self._get_from_memory(cache_key)
            elif self.config.model_cache_storage == "redis":
                return self._get_from_redis(cache_key)
            elif self.config.model_cache_storage == "disk":
                return self._get_from_disk(cache_key)
        except Exception as e:
            logger.error(f"Error getting model from cache: {e}")
            return None
    
    def set_model(self, model_name: str, model, model_version: str = "latest"):
        """เก็บ model ใน cache"""
        if not self.config.model_cache_enabled:
            return
        
        cache_key = self._generate_cache_key(model_name, model_version)
        
        try:
            if self.config.model_cache_storage == "memory":
                self._set_to_memory(cache_key, model)
            elif self.config.model_cache_storage == "redis":
                self._set_to_redis(cache_key, model)
            elif self.config.model_cache_storage == "disk":
                self._set_to_disk(cache_key, model)
        except Exception as e:
            logger.error(f"Error setting model to cache: {e}")
    
    def _get_from_memory(self, cache_key: str):
        """ดึงจาก memory cache"""
        if cache_key in self.cache:
            self.access_times[cache_key] = time.time()
            return self.cache[cache_key]
        return None
    
    def _set_to_memory(self, cache_key: str, model):
        """เก็บใน memory cache"""
        # ตรวจสอบขนาด cache
        if len(self.cache) >= self.config.model_cache_size:
            self._evict_lru()
        
        self.cache[cache_key] = model
        self.access_times[cache_key] = time.time()
    
    def _evict_lru(self):
        """ลบ model ที่ใช้นานที่สุด"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
        
        # บังคับ garbage collection
        gc.collect()
    
    def _get_from_redis(self, cache_key: str):
        """ดึงจาก Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(cache_key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    def _set_to_redis(self, cache_key: str, model):
        """เก็บใน Redis cache"""
        if not self.redis_client:
            return
        
        try:
            data = pickle.dumps(model)
            ttl = self.config.model_cache_ttl_hours * 3600
            self.redis_client.setex(cache_key, ttl, data)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def _get_from_disk(self, cache_key: str):
        """ดึงจาก disk cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_file):
            # ตรวจสอบอายุไฟล์
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < self.config.model_cache_ttl_hours * 3600:
                try:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                except Exception as e:
                    logger.error(f"Disk cache read error: {e}")
        return None
    
    def _set_to_disk(self, cache_key: str, model):
        """เก็บใน disk cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(model, f)
        except Exception as e:
            logger.error(f"Disk cache write error: {e}")
    
    def clear_cache(self):
        """ล้าง cache ทั้งหมด"""
        self.cache.clear()
        self.access_times.clear()
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys("model:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis cache clear error: {e}")
        
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                if file.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, file))

class ImageProcessor:
    """ประมวลผลภาพอย่างมีประสิทธิภาพ"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.thread_pool = ThreadPoolExecutor(max_workers=config.image_preprocessing_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=config.process_pool_size)
        self.image_cache = {}
        self.batch_queue = queue.Queue()
        self.batch_processor_running = False
        
        if config.batch_processing_enabled:
            self.start_batch_processor()
    
    def start_batch_processor(self):
        """เริ่มต้น batch processor"""
        if not self.batch_processor_running:
            self.batch_processor_running = True
            threading.Thread(target=self._batch_processor_worker, daemon=True).start()
    
    def _batch_processor_worker(self):
        """Worker สำหรับ batch processing"""
        batch = []
        last_process_time = time.time()
        
        while self.batch_processor_running:
            try:
                # รอรับ item ใหม่
                try:
                    item = self.batch_queue.get(timeout=0.1)
                    batch.append(item)
                except queue.Empty:
                    pass
                
                current_time = time.time()
                
                # ประมวลผล batch เมื่อ:
                # 1. batch เต็ม
                # 2. timeout
                # 3. มี item ใน batch และเวลาผ่านไป
                should_process = (
                    len(batch) >= self.config.max_batch_size or
                    (batch and current_time - last_process_time >= self.config.batch_timeout_seconds)
                )
                
                if should_process and batch:
                    self._process_batch(batch)
                    batch = []
                    last_process_time = current_time
                
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                batch = []
    
    def _process_batch(self, batch: List[Dict]):
        """ประมวลผล batch ของภาพ"""
        try:
            # จัดกลุ่มตามประเภทการประมวลผล
            resize_batch = []
            normalize_batch = []
            augment_batch = []
            
            for item in batch:
                operation = item.get('operation')
                if operation == 'resize':
                    resize_batch.append(item)
                elif operation == 'normalize':
                    normalize_batch.append(item)
                elif operation == 'augment':
                    augment_batch.append(item)
            
            # ประมวลผลแต่ละกลุ่ม
            if resize_batch:
                self._batch_resize(resize_batch)
            if normalize_batch:
                self._batch_normalize(normalize_batch)
            if augment_batch:
                self._batch_augment(augment_batch)
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
    
    def _batch_resize(self, batch: List[Dict]):
        """Batch resize images"""
        try:
            for item in batch:
                image = item['image']
                target_size = item['target_size']
                callback = item['callback']
                
                # ใช้ OpenCV สำหรับ batch resize
                if isinstance(image, np.ndarray):
                    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
                else:
                    # PIL Image
                    resized = image.resize(target_size, Image.LANCZOS)
                
                # เรียก callback
                if callback:
                    callback(resized)
                    
        except Exception as e:
            logger.error(f"Batch resize error: {e}")
    
    def _batch_normalize(self, batch: List[Dict]):
        """Batch normalize images"""
        try:
            images = [item['image'] for item in batch]
            callbacks = [item['callback'] for item in batch]
            
            # Batch normalization
            if images and isinstance(images[0], np.ndarray):
                # NumPy batch processing
                batch_array = np.stack(images)
                normalized_batch = (batch_array.astype(np.float32) / 255.0)
                
                for i, callback in enumerate(callbacks):
                    if callback:
                        callback(normalized_batch[i])
                        
        except Exception as e:
            logger.error(f"Batch normalize error: {e}")
    
    def _batch_augment(self, batch: List[Dict]):
        """Batch augment images"""
        try:
            for item in batch:
                image = item['image']
                augmentations = item.get('augmentations', [])
                callback = item['callback']
                
                augmented = self._apply_augmentations(image, augmentations)
                
                if callback:
                    callback(augmented)
                    
        except Exception as e:
            logger.error(f"Batch augment error: {e}")
    
    def _apply_augmentations(self, image: np.ndarray, augmentations: List[str]) -> np.ndarray:
        """ใช้ augmentations กับภาพ"""
        result = image.copy()
        
        for aug in augmentations:
            if aug == 'flip_horizontal':
                result = cv2.flip(result, 1)
            elif aug == 'flip_vertical':
                result = cv2.flip(result, 0)
            elif aug == 'rotate_90':
                result = cv2.rotate(result, cv2.ROTATE_90_CLOCKWISE)
            elif aug == 'brightness':
                result = cv2.convertScaleAbs(result, alpha=1.2, beta=10)
            elif aug == 'contrast':
                result = cv2.convertScaleAbs(result, alpha=1.5, beta=0)
        
        return result
    
    @lru_cache(maxsize=1000)
    def get_image_hash(self, image_path: str) -> str:
        """สร้าง hash สำหรับภาพ"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return hashlib.md5(image_path.encode()).hexdigest()
    
    async def preprocess_image_async(self, image_path: str, target_size: Tuple[int, int], 
                                   normalize: bool = True) -> np.ndarray:
        """ประมวลผลภาพแบบ async"""
        try:
            # ตรวจสอบ cache
            cache_key = f"{self.get_image_hash(image_path)}_{target_size}_{normalize}"
            
            if self.config.image_cache_enabled and cache_key in self.image_cache:
                return self.image_cache[cache_key]
            
            # อ่านภาพ
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
            
            # ประมวลผลใน thread pool
            loop = asyncio.get_event_loop()
            processed_image = await loop.run_in_executor(
                self.thread_pool,
                self._process_image_sync,
                image_data, target_size, normalize
            )
            
            # เก็บใน cache
            if self.config.image_cache_enabled:
                self._manage_image_cache(cache_key, processed_image)
            
            return processed_image
            
        except Exception as e:
            logger.error(f"Async image preprocessing error: {e}")
            raise
    
    def _process_image_sync(self, image_data: bytes, target_size: Tuple[int, int], 
                           normalize: bool) -> np.ndarray:
        """ประมวลผลภาพแบบ sync"""
        try:
            # แปลง bytes เป็น image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image")
            
            # Resize
            if target_size:
                image = cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
            
            # Normalize
            if normalize:
                image = image.astype(np.float32) / 255.0
            
            return image
            
        except Exception as e:
            logger.error(f"Sync image processing error: {e}")
            raise
    
    def _manage_image_cache(self, cache_key: str, image: np.ndarray):
        """จัดการ image cache"""
        try:
            # ตรวจสอบขนาด cache
            current_size_mb = sum(
                img.nbytes / (1024 * 1024) 
                for img in self.image_cache.values()
            )
            
            # ลบ cache เก่าถ้าเกินขนาดที่กำหนด
            while current_size_mb > self.config.image_cache_size_mb and self.image_cache:
                oldest_key = next(iter(self.image_cache))
                oldest_image = self.image_cache.pop(oldest_key)
                current_size_mb -= oldest_image.nbytes / (1024 * 1024)
            
            # เพิ่ม image ใหม่
            self.image_cache[cache_key] = image
            
        except Exception as e:
            logger.error(f"Image cache management error: {e}")

class GPUManager:
    """จัดการ GPU อย่างมีประสิทธิภาพ"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.gpu_available = False
        self.device = None
        self.memory_pool = None
        
        self.init_gpu()
    
    def init_gpu(self):
        """เริ่มต้น GPU"""
        try:
            if self.config.gpu_enabled:
                # PyTorch GPU setup
                if torch.cuda.is_available():
                    self.device = torch.device('cuda')
                    self.gpu_available = True
                    
                    # ตั้งค่า memory management
                    if self.config.gpu_allow_growth:
                        torch.cuda.empty_cache()
                    
                    logger.info(f"GPU initialized: {torch.cuda.get_device_name()}")
                
                # TensorFlow GPU setup
                if tf.config.list_physical_devices('GPU'):
                    gpus = tf.config.experimental.list_physical_devices('GPU')
                    if gpus:
                        try:
                            for gpu in gpus:
                                if self.config.gpu_allow_growth:
                                    tf.config.experimental.set_memory_growth(gpu, True)
                                else:
                                    tf.config.experimental.set_memory_limit(
                                        gpu, 
                                        int(self.config.gpu_memory_fraction * 1024)
                                    )
                        except RuntimeError as e:
                            logger.error(f"GPU setup error: {e}")
                
                # Mixed precision
                if self.config.mixed_precision_enabled:
                    self.enable_mixed_precision()
                    
        except Exception as e:
            logger.error(f"GPU initialization failed: {e}")
            self.gpu_available = False
    
    def enable_mixed_precision(self):
        """เปิดใช้ mixed precision"""
        try:
            # TensorFlow mixed precision
            policy = tf.keras.mixed_precision.Policy('mixed_float16')
            tf.keras.mixed_precision.set_global_policy(policy)
            
            # PyTorch mixed precision (ใช้ใน training loop)
            logger.info("Mixed precision enabled")
            
        except Exception as e:
            logger.error(f"Mixed precision setup error: {e}")
    
    def get_gpu_memory_info(self) -> Dict[str, float]:
        """ดึงข้อมูลการใช้ memory ของ GPU"""
        try:
            if not self.gpu_available:
                return {"total": 0, "used": 0, "free": 0, "usage_percent": 0}
            
            if torch.cuda.is_available():
                total = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                allocated = torch.cuda.memory_allocated(0) / (1024**3)  # GB
                cached = torch.cuda.memory_reserved(0) / (1024**3)  # GB
                free = total - cached
                
                return {
                    "total": total,
                    "allocated": allocated,
                    "cached": cached,
                    "free": free,
                    "usage_percent": (cached / total) * 100
                }
            
        except Exception as e:
            logger.error(f"GPU memory info error: {e}")
        
        return {"total": 0, "used": 0, "free": 0, "usage_percent": 0}
    
    def optimize_model_for_gpu(self, model):
        """ปรับแต่ง model สำหรับ GPU"""
        try:
            if not self.gpu_available:
                return model
            
            # PyTorch model
            if hasattr(model, 'to'):
                model = model.to(self.device)
                
                # Enable optimizations
                if hasattr(model, 'eval'):
                    model.eval()
                
                # Compile model (PyTorch 2.0+)
                if hasattr(torch, 'compile'):
                    model = torch.compile(model)
            
            # TensorFlow model
            elif hasattr(model, 'compile'):
                # Use mixed precision
                if self.config.mixed_precision_enabled:
                    model.compile(
                        optimizer=model.optimizer,
                        loss=model.loss,
                        metrics=model.metrics,
                        jit_compile=True  # XLA compilation
                    )
            
            return model
            
        except Exception as e:
            logger.error(f"GPU model optimization error: {e}")
            return model
    
    def clear_gpu_memory(self):
        """ล้าง GPU memory"""
        try:
            if self.gpu_available:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                
                # TensorFlow memory cleanup
                tf.keras.backend.clear_session()
                
                logger.info("GPU memory cleared")
                
        except Exception as e:
            logger.error(f"GPU memory clear error: {e}")

class MemoryManager:
    """จัดการ memory อย่างมีประสิทธิภาพ"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.monitoring_active = False
        self.cleanup_thread = None
        self.memory_alerts = []
        
        if config.memory_monitoring_enabled:
            self.start_monitoring()
    
    def start_monitoring(self):
        """เริ่มต้น memory monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.cleanup_thread = threading.Thread(target=self._memory_monitor_worker, daemon=True)
            self.cleanup_thread.start()
    
    def _memory_monitor_worker(self):
        """Worker สำหรับ monitor memory"""
        while self.monitoring_active:
            try:
                memory_info = self.get_memory_info()
                
                # ตรวจสอบการใช้ memory
                if memory_info['usage_percent'] > self.config.max_memory_usage_percent:
                    self._handle_high_memory_usage(memory_info)
                
                # Cleanup ตามกำหนด
                time.sleep(self.config.memory_cleanup_interval_minutes * 60)
                self.cleanup_memory()
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(60)  # รอ 1 นาทีก่อนลองใหม่
    
    def get_memory_info(self) -> Dict[str, float]:
        """ดึงข้อมูลการใช้ memory"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "usage_percent": memory.percent,
                "process_rss_mb": process_memory.rss / (1024**2),
                "process_vms_mb": process_memory.vms / (1024**2)
            }
            
        except Exception as e:
            logger.error(f"Memory info error: {e}")
            return {}
    
    def _handle_high_memory_usage(self, memory_info: Dict[str, float]):
        """จัดการเมื่อ memory ใช้งานสูง"""
        try:
            logger.warning(f"High memory usage detected: {memory_info['usage_percent']:.1f}%")
            
            # บังคับ garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
            
            # ล้าง cache ต่างๆ
            self.cleanup_memory()
            
            # บันทึก alert
            alert = {
                "timestamp": datetime.now(),
                "memory_usage_percent": memory_info['usage_percent'],
                "action_taken": "cleanup_performed"
            }
            self.memory_alerts.append(alert)
            
            # เก็บเฉพาะ alert ล่าสุด 100 รายการ
            if len(self.memory_alerts) > 100:
                self.memory_alerts = self.memory_alerts[-100:]
                
        except Exception as e:
            logger.error(f"High memory usage handling error: {e}")
    
    def cleanup_memory(self):
        """ทำความสะอาด memory"""
        try:
            # Python garbage collection
            collected = gc.collect()
            
            # ล้าง weak references
            import weakref
            weakref.finalize_all()
            
            logger.info(f"Memory cleanup completed, freed {collected} objects")
            
        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")
    
    @contextmanager
    def memory_profiler(self, description: str = ""):
        """Context manager สำหรับ profile memory"""
        try:
            tracemalloc.start()
            start_memory = self.get_memory_info()
            start_time = time.time()
            
            yield
            
            end_time = time.time()
            end_memory = self.get_memory_info()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            memory_diff = end_memory.get('process_rss_mb', 0) - start_memory.get('process_rss_mb', 0)
            
            logger.info(f"Memory Profile [{description}]: "
                       f"Time: {end_time - start_time:.2f}s, "
                       f"Memory diff: {memory_diff:.1f}MB, "
                       f"Peak: {peak / (1024**2):.1f}MB")
            
        except Exception as e:
            logger.error(f"Memory profiling error: {e}")
            yield

class PerformanceOptimizer:
    """ระบบปรับปรุงประสิทธิภาพหลัก"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.model_cache = ModelCache(config)
        self.image_processor = ImageProcessor(config)
        self.gpu_manager = GPUManager(config)
        self.memory_manager = MemoryManager(config)
        
        self.metrics_history = []
        self.performance_db = "performance.db"
        self.result_cache = {}
        
        self.init_database()
        
        if config.performance_tracking_enabled:
            self.start_metrics_collection()
    
    def init_database(self):
        """เริ่มต้นฐานข้อมูลประสิทธิภาพ"""
        try:
            conn = sqlite3.connect(self.performance_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage_percent REAL,
                    memory_usage_mb REAL,
                    memory_usage_percent REAL,
                    gpu_usage_percent REAL,
                    gpu_memory_mb REAL,
                    processing_time_ms REAL,
                    throughput_rps REAL,
                    cache_hit_rate REAL,
                    error_rate REAL,
                    active_connections INTEGER,
                    queue_size INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Performance database initialization error: {e}")
    
    def start_metrics_collection(self):
        """เริ่มต้นการเก็บ metrics"""
        def metrics_worker():
            while True:
                try:
                    metrics = self.collect_metrics()
                    self.store_metrics(metrics)
                    time.sleep(self.config.metrics_collection_interval_seconds)
                except Exception as e:
                    logger.error(f"Metrics collection error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=metrics_worker, daemon=True).start()
    
    def collect_metrics(self) -> PerformanceMetrics:
        """เก็บ metrics ปัจจุบัน"""
        try:
            # CPU และ Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = self.memory_manager.get_memory_info()
            
            # GPU
            gpu_info = self.gpu_manager.get_gpu_memory_info()
            
            # Cache hit rate
            cache_hit_rate = self._calculate_cache_hit_rate()
            
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                memory_usage_mb=memory_info.get('process_rss_mb', 0),
                memory_usage_percent=memory_info.get('usage_percent', 0),
                gpu_usage_percent=gpu_info.get('usage_percent', 0),
                gpu_memory_mb=gpu_info.get('used', 0) * 1024,  # GB to MB
                processing_time_ms=0,  # จะอัปเดตจากการประมวลผลจริง
                throughput_requests_per_second=0,  # จะอัปเดตจากการประมวลผลจริง
                cache_hit_rate=cache_hit_rate,
                error_rate=0,  # จะอัปเดตจากการติดตาม error
                active_connections=0,  # จะอัปเดตจาก web server
                queue_size=self.image_processor.batch_queue.qsize()
            )
            
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=0, memory_usage_mb=0, memory_usage_percent=0,
                gpu_usage_percent=0, gpu_memory_mb=0, processing_time_ms=0,
                throughput_requests_per_second=0, cache_hit_rate=0, error_rate=0,
                active_connections=0, queue_size=0
            )
    
    def _calculate_cache_hit_rate(self) -> float:
        """คำนวณ cache hit rate"""
        try:
            # ใช้ข้อมูลจาก metrics history
            if len(self.metrics_history) < 2:
                return 0.0
            
            # คำนวณจากการใช้งาน cache ในช่วงเวลาที่ผ่านมา
            # (ตัวอย่างการคำนวณ - ต้องปรับตามการใช้งานจริง)
            return 85.0  # placeholder
            
        except Exception as e:
            logger.error(f"Cache hit rate calculation error: {e}")
            return 0.0
    
    def store_metrics(self, metrics: PerformanceMetrics):
        """เก็บ metrics ลงฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.performance_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics 
                (cpu_usage_percent, memory_usage_mb, memory_usage_percent,
                 gpu_usage_percent, gpu_memory_mb, processing_time_ms,
                 throughput_rps, cache_hit_rate, error_rate,
                 active_connections, queue_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.cpu_usage_percent, metrics.memory_usage_mb, metrics.memory_usage_percent,
                metrics.gpu_usage_percent, metrics.gpu_memory_mb, metrics.processing_time_ms,
                metrics.throughput_requests_per_second, metrics.cache_hit_rate, metrics.error_rate,
                metrics.active_connections, metrics.queue_size
            ))
            
            conn.commit()
            conn.close()
            
            # เก็บใน memory สำหรับการวิเคราะห์
            self.metrics_history.append(metrics)
            
            # เก็บเฉพาะข้อมูลล่าสุด
            max_history = 1000
            if len(self.metrics_history) > max_history:
                self.metrics_history = self.metrics_history[-max_history:]
            
        except Exception as e:
            logger.error(f"Metrics storage error: {e}")
    
    @contextmanager
    def performance_timer(self, operation_name: str = ""):
        """Context manager สำหรับวัดเวลาการทำงาน"""
        start_time = time.time()
        start_memory = self.memory_manager.get_memory_info()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.memory_manager.get_memory_info()
            
            processing_time = (end_time - start_time) * 1000  # ms
            memory_diff = end_memory.get('process_rss_mb', 0) - start_memory.get('process_rss_mb', 0)
            
            logger.info(f"Performance [{operation_name}]: "
                       f"Time: {processing_time:.2f}ms, "
                       f"Memory: {memory_diff:+.1f}MB")
    
    def optimize_for_inference(self, model):
        """ปรับแต่ง model สำหรับ inference"""
        try:
            # GPU optimization
            optimized_model = self.gpu_manager.optimize_model_for_gpu(model)
            
            # Model-specific optimizations
            if hasattr(optimized_model, 'eval'):
                optimized_model.eval()
            
            # Disable gradient computation
            if hasattr(optimized_model, 'requires_grad_'):
                for param in optimized_model.parameters():
                    param.requires_grad_(False)
            
            return optimized_model
            
        except Exception as e:
            logger.error(f"Model optimization error: {e}")
            return model
    
    def get_performance_report(self) -> Dict[str, Any]:
        """สร้างรายงานประสิทธิภาพ"""
        try:
            if not self.metrics_history:
                return {"error": "No metrics data available"}
            
            recent_metrics = self.metrics_history[-100:]  # ข้อมูล 100 รายการล่าสุด
            
            # คำนวณสถิติ
            avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
            avg_gpu = sum(m.gpu_usage_percent for m in recent_metrics) / len(recent_metrics)
            avg_processing_time = sum(m.processing_time_ms for m in recent_metrics) / len(recent_metrics)
            
            # ข้อมูล cache
            cache_stats = {
                "model_cache_size": len(self.model_cache.cache),
                "image_cache_size": len(self.image_processor.image_cache),
                "result_cache_size": len(self.result_cache)
            }
            
            # ข้อมูล GPU
            gpu_info = self.gpu_manager.get_gpu_memory_info()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "averages": {
                    "cpu_usage_percent": round(avg_cpu, 2),
                    "memory_usage_mb": round(avg_memory, 2),
                    "gpu_usage_percent": round(avg_gpu, 2),
                    "processing_time_ms": round(avg_processing_time, 2)
                },
                "current": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_info": self.memory_manager.get_memory_info(),
                    "gpu_info": gpu_info
                },
                "cache_stats": cache_stats,
                "configuration": {
                    "gpu_enabled": self.config.gpu_enabled,
                    "batch_processing": self.config.batch_processing_enabled,
                    "model_caching": self.config.model_cache_enabled,
                    "image_caching": self.config.image_cache_enabled
                },
                "recommendations": self._generate_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Performance report error: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """สร้างคำแนะนำสำหรับปรับปรุงประสิทธิภาพ"""
        recommendations = []
        
        try:
            if not self.metrics_history:
                return recommendations
            
            recent_metrics = self.metrics_history[-10:]
            avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage_percent for m in recent_metrics) / len(recent_metrics)
            avg_gpu = sum(m.gpu_usage_percent for m in recent_metrics) / len(recent_metrics)
            
            # CPU recommendations
            if avg_cpu > 80:
                recommendations.append("High CPU usage detected. Consider increasing CPU workers or optimizing algorithms.")
            elif avg_cpu < 20:
                recommendations.append("Low CPU usage. You might be able to reduce CPU workers to save resources.")
            
            # Memory recommendations
            if avg_memory > 85:
                recommendations.append("High memory usage. Consider reducing cache sizes or implementing memory cleanup.")
            
            # GPU recommendations
            if self.config.gpu_enabled and avg_gpu < 30:
                recommendations.append("Low GPU utilization. Consider increasing batch sizes or using GPU acceleration more effectively.")
            elif not self.config.gpu_enabled and avg_cpu > 70:
                recommendations.append("Consider enabling GPU acceleration to reduce CPU load.")
            
            # Cache recommendations
            if len(self.model_cache.cache) == 0:
                recommendations.append("Model cache is empty. Enable model caching to improve performance.")
            
            if not recommendations:
                recommendations.append("Performance looks good! No specific recommendations at this time.")
            
        except Exception as e:
            logger.error(f"Recommendations generation error: {e}")
            recommendations.append("Unable to generate recommendations due to an error.")
        
        return recommendations
    
    def cleanup_all(self):
        """ทำความสะอาดทุกอย่าง"""
        try:
            # ล้าง caches
            self.model_cache.clear_cache()
            self.image_processor.image_cache.clear()
            self.result_cache.clear()
            
            # ล้าง GPU memory
            self.gpu_manager.clear_gpu_memory()
            
            # ล้าง system memory
            self.memory_manager.cleanup_memory()
            
            logger.info("All caches and memory cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# === Main Function ===

def main():
    """ทดสอบการทำงานของ Performance Optimizer"""
    print("⚡ Testing Performance Optimizer...")
    
    # สร้าง config
    config = PerformanceConfig()
    
    # สร้าง Performance Optimizer
    optimizer = PerformanceOptimizer(config)
    
    # ทดสอบ memory profiling
    print("\n🧠 Testing memory profiling...")
    with optimizer.memory_manager.memory_profiler("test_operation"):
        # จำลองการทำงานที่ใช้ memory
        test_data = [i for i in range(100000)]
        del test_data
    
    # ทดสอบ performance timer
    print("\n⏱️ Testing performance timer...")
    with optimizer.performance_timer("test_processing"):
        time.sleep(0.1)  # จำลองการประมวลผล
    
    # ทดสอบ GPU manager
    print("\n🎮 Testing GPU manager...")
    gpu_info = optimizer.gpu_manager.get_gpu_memory_info()
    print(f"GPU Info: {gpu_info}")
    
    # ทดสอบ metrics collection
    print("\n📊 Testing metrics collection...")
    metrics = optimizer.collect_metrics()
    print(f"CPU: {metrics.cpu_usage_percent:.1f}%, Memory: {metrics.memory_usage_mb:.1f}MB")
    
    # สร้างรายงานประสิทธิภาพ
    print("\n📈 Generating performance report...")
    report = optimizer.get_performance_report()
    print(f"Report keys: {list(report.keys())}")
    
    if "recommendations" in report:
        print("\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")
    
    # ทดสอบ cleanup
    print("\n🧹 Testing cleanup...")
    optimizer.cleanup_all()
    
    print("\n✅ Performance Optimizer testing completed!")

if __name__ == "__main__":
    main()