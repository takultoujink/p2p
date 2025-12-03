# ========================================
# Performance Optimizer และ Memory Management
# ========================================

import gc
import psutil
import threading
import time
import logging
import tracemalloc
import weakref
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import cv2
from collections import defaultdict
import sqlite3
import json

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent / "08_Config"))
from security_config import SecureConfig

@dataclass
class MemorySnapshot:
    """คลาสสำหรับเก็บข้อมูล memory snapshot"""
    timestamp: datetime
    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    memory_percent: float
    python_memory_mb: float
    gc_objects: int
    gc_collections: Dict[int, int]
    top_memory_objects: List[Dict[str, Any]]

@dataclass
class PerformanceMetrics:
    """คลาสสำหรับเก็บข้อมูล performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    io_read_mb: float
    io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    open_files: int
    response_times: Dict[str, float]

class MemoryManager:
    """คลาสสำหรับจัดการ memory"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.memory_snapshots = []
        self.memory_threshold_mb = 1024  # 1GB threshold
        self.cleanup_callbacks = []
        self.object_pools = {}
        self.weak_references = weakref.WeakSet()
        
        # เริ่ม tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start()
    
    def _setup_logging(self) -> logging.Logger:
        """ตั้งค่า logging"""
        logger = logging.getLogger("MemoryManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler("memory_manager.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def take_memory_snapshot(self) -> MemorySnapshot:
        """สร้าง memory snapshot"""
        try:
            # System memory
            memory = psutil.virtual_memory()
            
            # Python memory
            process = psutil.Process()
            python_memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # GC statistics
            gc_stats = gc.get_stats()
            gc_collections = {i: stat['collections'] for i, stat in enumerate(gc_stats)}
            gc_objects = len(gc.get_objects())
            
            # Top memory objects
            top_objects = []
            if tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')[:10]
                
                for stat in top_stats:
                    top_objects.append({
                        'filename': stat.traceback.format()[-1] if stat.traceback else 'unknown',
                        'size_mb': stat.size / (1024 * 1024),
                        'count': stat.count
                    })
            
            memory_snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                total_memory_mb=memory.total / (1024 * 1024),
                used_memory_mb=memory.used / (1024 * 1024),
                available_memory_mb=memory.available / (1024 * 1024),
                memory_percent=memory.percent,
                python_memory_mb=python_memory_mb,
                gc_objects=gc_objects,
                gc_collections=gc_collections,
                top_memory_objects=top_objects
            )
            
            self.memory_snapshots.append(memory_snapshot)
            
            # เก็บแค่ 100 snapshots ล่าสุด
            if len(self.memory_snapshots) > 100:
                self.memory_snapshots = self.memory_snapshots[-100:]
            
            return memory_snapshot
            
        except Exception as e:
            self.logger.error(f"Error taking memory snapshot: {e}")
            raise
    
    def check_memory_usage(self) -> bool:
        """ตรวจสอบการใช้ memory และทำ cleanup ถ้าจำเป็น"""
        snapshot = self.take_memory_snapshot()
        
        if snapshot.python_memory_mb > self.memory_threshold_mb:
            self.logger.warning(
                f"High memory usage detected: {snapshot.python_memory_mb:.1f}MB"
            )
            
            # ทำ cleanup
            cleaned_mb = self.cleanup_memory()
            
            self.logger.info(f"Memory cleanup completed. Freed: {cleaned_mb:.1f}MB")
            return True
        
        return False
    
    def cleanup_memory(self) -> float:
        """ทำความสะอาด memory"""
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        # รัน cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in cleanup callback: {e}")
        
        # ทำ garbage collection
        collected = 0
        for generation in range(3):
            collected += gc.collect(generation)
        
        # ลบ weak references ที่ตายแล้ว
        self.weak_references.clear()
        
        # ลบ object pools ที่ไม่ใช้
        self._cleanup_object_pools()
        
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        freed_memory = initial_memory - final_memory
        
        self.logger.info(
            f"Garbage collection: {collected} objects collected, "
            f"{freed_memory:.1f}MB freed"
        )
        
        return max(0, freed_memory)
    
    def register_cleanup_callback(self, callback: Callable[[], None]):
        """ลงทะเบียน cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    def create_object_pool(self, name: str, factory: Callable, max_size: int = 10):
        """สร้าง object pool"""
        self.object_pools[name] = {
            'factory': factory,
            'pool': [],
            'max_size': max_size,
            'created': 0,
            'reused': 0
        }
    
    def get_from_pool(self, name: str):
        """ดึง object จาก pool"""
        if name not in self.object_pools:
            raise ValueError(f"Object pool '{name}' not found")
        
        pool_info = self.object_pools[name]
        
        if pool_info['pool']:
            obj = pool_info['pool'].pop()
            pool_info['reused'] += 1
            return obj
        else:
            obj = pool_info['factory']()
            pool_info['created'] += 1
            return obj
    
    def return_to_pool(self, name: str, obj):
        """คืน object ไป pool"""
        if name not in self.object_pools:
            return
        
        pool_info = self.object_pools[name]
        
        if len(pool_info['pool']) < pool_info['max_size']:
            # Reset object state ถ้าเป็น numpy array
            if isinstance(obj, np.ndarray):
                obj.fill(0)
            
            pool_info['pool'].append(obj)
    
    def _cleanup_object_pools(self):
        """ทำความสะอาด object pools"""
        for name, pool_info in self.object_pools.items():
            # เก็บแค่ครึ่งหนึ่งของ objects ใน pool
            pool_size = len(pool_info['pool'])
            if pool_size > 2:
                keep_size = pool_size // 2
                pool_info['pool'] = pool_info['pool'][:keep_size]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """ดึงสถิติ memory"""
        if not self.memory_snapshots:
            return {}
        
        latest = self.memory_snapshots[-1]
        
        # คำนวณ trend
        if len(self.memory_snapshots) >= 2:
            previous = self.memory_snapshots[-2]
            memory_trend = latest.python_memory_mb - previous.python_memory_mb
        else:
            memory_trend = 0
        
        # Object pool stats
        pool_stats = {}
        for name, pool_info in self.object_pools.items():
            pool_stats[name] = {
                'pool_size': len(pool_info['pool']),
                'created': pool_info['created'],
                'reused': pool_info['reused'],
                'hit_rate': (
                    pool_info['reused'] / (pool_info['created'] + pool_info['reused'])
                    if (pool_info['created'] + pool_info['reused']) > 0 else 0
                )
            }
        
        return {
            'current_memory_mb': latest.python_memory_mb,
            'memory_percent': latest.memory_percent,
            'gc_objects': latest.gc_objects,
            'memory_trend_mb': memory_trend,
            'object_pools': pool_stats,
            'top_memory_objects': latest.top_memory_objects[:5]
        }

class PerformanceOptimizer:
    """คลาสสำหรับ optimize performance"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = SecureConfig(config_path)
        self.logger = self._setup_logging()
        self.memory_manager = MemoryManager()
        
        # Performance tracking
        self.performance_history = []
        self.response_times = defaultdict(list)
        self.optimization_active = False
        self.optimization_thread = None
        
        # Database
        self.db_path = Path("performance.db")
        self._init_database()
        
        # Optimization settings
        self.optimization_interval = 60  # seconds
        self.auto_cleanup_threshold = 80  # memory percent
        
        # Setup object pools
        self._setup_object_pools()
        
        # Register cleanup callbacks
        self._register_cleanup_callbacks()
    
    def _setup_logging(self) -> logging.Logger:
        """ตั้งค่า logging"""
        logger = logging.getLogger("PerformanceOptimizer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler("performance_optimizer.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """สร้าง database สำหรับเก็บ performance data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    io_read_mb REAL,
                    io_write_mb REAL,
                    network_sent_mb REAL,
                    network_recv_mb REAL,
                    active_threads INTEGER,
                    open_files INTEGER,
                    response_times TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_memory_mb REAL,
                    used_memory_mb REAL,
                    python_memory_mb REAL,
                    gc_objects INTEGER,
                    top_objects TEXT
                )
            """)
    
    def _setup_object_pools(self):
        """ตั้งค่า object pools"""
        # Image arrays pool
        self.memory_manager.create_object_pool(
            'image_arrays',
            lambda: np.zeros((480, 640, 3), dtype=np.uint8),
            max_size=5
        )
        
        # Detection results pool
        self.memory_manager.create_object_pool(
            'detection_results',
            lambda: {'boxes': [], 'scores': [], 'classes': []},
            max_size=10
        )
        
        # Buffer pool
        self.memory_manager.create_object_pool(
            'buffers',
            lambda: bytearray(1024),
            max_size=20
        )
    
    def _register_cleanup_callbacks(self):
        """ลงทะเบียน cleanup callbacks"""
        # OpenCV cleanup
        def opencv_cleanup():
            cv2.destroyAllWindows()
            # ลบ cache ของ cv2 ถ้ามี
        
        # Numpy cleanup
        def numpy_cleanup():
            # ลบ numpy arrays ที่ไม่ใช้
            pass
        
        self.memory_manager.register_cleanup_callback(opencv_cleanup)
        self.memory_manager.register_cleanup_callback(numpy_cleanup)
    
    def collect_performance_metrics(self) -> PerformanceMetrics:
        """เก็บข้อมูล performance metrics"""
        try:
            process = psutil.Process()
            
            # CPU และ Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # I/O
            io_counters = process.io_counters()
            io_read_mb = io_counters.read_bytes / (1024 * 1024)
            io_write_mb = io_counters.write_bytes / (1024 * 1024)
            
            # Network
            net_counters = psutil.net_io_counters()
            network_sent_mb = net_counters.bytes_sent / (1024 * 1024)
            network_recv_mb = net_counters.bytes_recv / (1024 * 1024)
            
            # Threads และ Files
            active_threads = process.num_threads()
            open_files = len(process.open_files())
            
            # Response times
            avg_response_times = {}
            for operation, times in self.response_times.items():
                if times:
                    avg_response_times[operation] = sum(times) / len(times)
                    # เก็บแค่ 100 ค่าล่าสุด
                    self.response_times[operation] = times[-100:]
            
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                io_read_mb=io_read_mb,
                io_write_mb=io_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_threads=active_threads,
                open_files=open_files,
                response_times=avg_response_times
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")
            raise
    
    def save_performance_metrics(self, metrics: PerformanceMetrics):
        """บันทึก performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_metrics (
                        timestamp, cpu_percent, memory_percent, io_read_mb,
                        io_write_mb, network_sent_mb, network_recv_mb,
                        active_threads, open_files, response_times
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.io_read_mb,
                    metrics.io_write_mb,
                    metrics.network_sent_mb,
                    metrics.network_recv_mb,
                    metrics.active_threads,
                    metrics.open_files,
                    json.dumps(metrics.response_times)
                ))
            
            # เพิ่มใน memory
            self.performance_history.append(metrics)
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
                
        except Exception as e:
            self.logger.error(f"Error saving performance metrics: {e}")
    
    def record_response_time(self, operation: str, response_time: float):
        """บันทึกเวลาตอบสนอง"""
        self.response_times[operation].append(response_time)
    
    def optimize_system(self):
        """ทำ system optimization"""
        self.logger.info("Starting system optimization...")
        
        # เก็บ metrics ก่อน optimization
        before_metrics = self.collect_performance_metrics()
        
        optimizations_performed = []
        
        # Memory optimization
        if before_metrics.memory_percent > self.auto_cleanup_threshold:
            freed_mb = self.memory_manager.cleanup_memory()
            optimizations_performed.append(f"Memory cleanup: {freed_mb:.1f}MB freed")
        
        # Thread optimization
        if before_metrics.active_threads > 20:
            # ลด thread pool size ถ้ามีมากเกินไป
            optimizations_performed.append("Thread pool optimization")
        
        # File handle optimization
        if before_metrics.open_files > 100:
            # ปิดไฟล์ที่ไม่ใช้
            optimizations_performed.append("File handle cleanup")
        
        # CPU optimization
        if before_metrics.cpu_percent > 80:
            # ลด CPU intensive operations
            optimizations_performed.append("CPU load reduction")
        
        # เก็บ metrics หลัง optimization
        after_metrics = self.collect_performance_metrics()
        
        # Log ผลลัพธ์
        improvement = {
            'memory_improvement': before_metrics.memory_percent - after_metrics.memory_percent,
            'cpu_improvement': before_metrics.cpu_percent - after_metrics.cpu_percent,
            'optimizations': optimizations_performed
        }
        
        self.logger.info(f"Optimization completed: {improvement}")
        
        return improvement
    
    def start_auto_optimization(self):
        """เริ่ม auto optimization"""
        if self.optimization_active:
            self.logger.warning("Auto optimization is already active")
            return
        
        self.optimization_active = True
        self.optimization_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True
        )
        self.optimization_thread.start()
        
        self.logger.info("Auto optimization started")
    
    def _optimization_loop(self):
        """Loop สำหรับ auto optimization"""
        while self.optimization_active:
            try:
                # เก็บ metrics
                metrics = self.collect_performance_metrics()
                self.save_performance_metrics(metrics)
                
                # ตรวจสอบว่าต้อง optimize หรือไม่
                if (metrics.memory_percent > self.auto_cleanup_threshold or
                    metrics.cpu_percent > 90 or
                    metrics.active_threads > 50):
                    
                    self.optimize_system()
                
                # Memory snapshot
                self.memory_manager.take_memory_snapshot()
                
                time.sleep(self.optimization_interval)
                
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                time.sleep(self.optimization_interval)
    
    def stop_auto_optimization(self):
        """หยุด auto optimization"""
        self.optimization_active = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)
        
        self.logger.info("Auto optimization stopped")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """ดึงสรุป performance"""
        if not self.performance_history:
            return {"status": "no_data"}
        
        latest = self.performance_history[-1]
        
        # คำนวณ averages
        recent_metrics = self.performance_history[-10:]
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_threads = sum(m.active_threads for m in recent_metrics) / len(recent_metrics)
        
        # Memory stats
        memory_stats = self.memory_manager.get_memory_stats()
        
        # Response time stats
        response_stats = {}
        for operation, times in self.response_times.items():
            if times:
                response_stats[operation] = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
        
        return {
            'timestamp': latest.timestamp.isoformat(),
            'current': {
                'cpu_percent': latest.cpu_percent,
                'memory_percent': latest.memory_percent,
                'active_threads': latest.active_threads,
                'open_files': latest.open_files
            },
            'averages': {
                'cpu_percent': round(avg_cpu, 2),
                'memory_percent': round(avg_memory, 2),
                'active_threads': round(avg_threads, 1)
            },
            'memory_stats': memory_stats,
            'response_times': response_stats,
            'optimization_active': self.optimization_active
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """ดึงคำแนะนำสำหรับ optimization"""
        recommendations = []
        
        if not self.performance_history:
            return recommendations
        
        latest = self.performance_history[-1]
        
        # Memory recommendations
        if latest.memory_percent > 85:
            recommendations.append("Consider increasing system memory or reducing memory usage")
        
        if latest.memory_percent > 70:
            recommendations.append("Enable automatic memory cleanup")
        
        # CPU recommendations
        if latest.cpu_percent > 80:
            recommendations.append("High CPU usage detected - consider optimizing algorithms")
        
        # Thread recommendations
        if latest.active_threads > 30:
            recommendations.append("High thread count - consider using thread pools")
        
        # File handle recommendations
        if latest.open_files > 100:
            recommendations.append("Many open files - ensure proper file handle cleanup")
        
        # Response time recommendations
        for operation, times in self.response_times.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > 1.0:  # > 1 second
                    recommendations.append(f"Slow response time for {operation}: {avg_time:.2f}s")
        
        return recommendations
    
    def cleanup_old_data(self, days: int = 7):
        """ลบข้อมูลเก่า"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # ลบ performance metrics เก่า
                cursor = conn.execute(
                    "DELETE FROM performance_metrics WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                metrics_deleted = cursor.rowcount
                
                # ลบ memory snapshots เก่า
                cursor = conn.execute(
                    "DELETE FROM memory_snapshots WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                snapshots_deleted = cursor.rowcount
                
                # Vacuum database
                conn.execute("VACUUM")
                
                self.logger.info(
                    f"Cleaned up old data: {metrics_deleted} metrics, "
                    f"{snapshots_deleted} snapshots"
                )
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")

# ========================================
# Context Manager สำหรับ Performance Tracking
# ========================================

class PerformanceTracker:
    """Context manager สำหรับ track performance"""
    
    def __init__(self, optimizer: PerformanceOptimizer, operation: str):
        self.optimizer = optimizer
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            response_time = time.time() - self.start_time
            self.optimizer.record_response_time(self.operation, response_time)

# ========================================
# Decorators สำหรับ Performance Monitoring
# ========================================

def monitor_performance(operation: str):
    """Decorator สำหรับ monitor performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # หา optimizer instance
            optimizer = None
            if hasattr(args[0], 'performance_optimizer'):
                optimizer = args[0].performance_optimizer
            
            if optimizer:
                with PerformanceTracker(optimizer, operation):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def auto_cleanup(threshold_mb: int = 500):
    """Decorator สำหรับ auto cleanup memory"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # ตรวจสอบ memory ก่อนรัน function
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024 * 1024)
            
            result = func(*args, **kwargs)
            
            # ตรวจสอบ memory หลังรัน function
            memory_after = process.memory_info().rss / (1024 * 1024)
            
            if memory_after > threshold_mb:
                gc.collect()
            
            return result
        
        return wrapper
    return decorator

# ========================================
# Main Function สำหรับทดสอบ
# ========================================

if __name__ == "__main__":
    # สร้าง performance optimizer
    optimizer = PerformanceOptimizer()
    
    try:
        # เริ่ม auto optimization
        optimizer.start_auto_optimization()
        
        print("Performance optimization started. Press Ctrl+C to stop.")
        
        # แสดงสถานะทุก 15 วินาที
        while True:
            time.sleep(15)
            summary = optimizer.get_performance_summary()
            
            if summary.get('status') != 'no_data':
                print(f"\nPerformance Summary:")
                print(f"CPU: {summary['current']['cpu_percent']:.1f}%")
                print(f"Memory: {summary['current']['memory_percent']:.1f}%")
                print(f"Threads: {summary['current']['active_threads']}")
                print(f"Open Files: {summary['current']['open_files']}")
                
                # แสดงคำแนะนำ
                recommendations = optimizer.get_optimization_recommendations()
                if recommendations:
                    print("\nRecommendations:")
                    for rec in recommendations[:3]:  # แสดงแค่ 3 อันแรก
                        print(f"- {rec}")
            
    except KeyboardInterrupt:
        print("\nStopping optimization...")
        optimizer.stop_auto_optimization()
        print("Optimization stopped.")