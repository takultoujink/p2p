# ========================================
# System Monitoring และ Health Check System
# ========================================

import psutil
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import deque
import sqlite3
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import cv2
import serial

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent / "08_Config"))
from security_config import SecureConfig

@dataclass
class SystemMetrics:
    """คลาสสำหรับเก็บข้อมูล system metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    temperature: Optional[float] = None
    gpu_percent: Optional[float] = None
    gpu_memory_percent: Optional[float] = None

@dataclass
class HealthStatus:
    """คลาสสำหรับเก็บสถานะ health check"""
    component: str
    status: str  # "healthy", "warning", "critical", "unknown"
    message: str
    timestamp: datetime
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class SystemMonitor:
    """คลาสสำหรับมอนิเตอร์ระบบ"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = SecureConfig(config_path)
        self.logger = self._setup_logging()
        
        # Database สำหรับเก็บ metrics
        self.db_path = Path("monitoring.db")
        self._init_database()
        
        # Memory สำหรับเก็บ metrics ล่าสุด
        self.metrics_history = deque(maxlen=1000)
        self.health_status = {}
        
        # Threading
        self.monitoring_active = False
        self.monitor_thread = None
        self.health_check_thread = None
        
        # Thresholds
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "temperature_warning": 70.0,
            "temperature_critical": 85.0
        }
        
        # Alert settings
        self.alert_cooldown = {}
        self.alert_cooldown_period = 300  # 5 minutes
        
    def _setup_logging(self) -> logging.Logger:
        """ตั้งค่า logging"""
        logger = logging.getLogger("SystemMonitor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler("system_monitor.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """สร้าง database สำหรับเก็บ metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    memory_available_mb REAL,
                    disk_percent REAL,
                    disk_used_gb REAL,
                    disk_free_gb REAL,
                    network_sent_mb REAL,
                    network_recv_mb REAL,
                    temperature REAL,
                    gpu_percent REAL,
                    gpu_memory_percent REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    response_time REAL,
                    details TEXT
                )
            """)
            
            # สร้าง index สำหรับ performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_health_timestamp ON health_checks(timestamp)")
    
    def collect_system_metrics(self) -> SystemMetrics:
        """เก็บข้อมูล system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Network
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            # Temperature (ถ้ามี)
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # ใช้ temperature แรกที่หาได้
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except Exception:
                pass
            
            # GPU (ถ้ามี)
            gpu_percent = None
            gpu_memory_percent = None
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_percent = gpu.load * 100
                    gpu_memory_percent = gpu.memoryUtil * 100
            except Exception:
                pass
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                temperature=temperature,
                gpu_percent=gpu_percent,
                gpu_memory_percent=gpu_memory_percent
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            raise
    
    def save_metrics(self, metrics: SystemMetrics):
        """บันทึก metrics ลง database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, memory_used_mb,
                        memory_available_mb, disk_percent, disk_used_gb, disk_free_gb,
                        network_sent_mb, network_recv_mb, temperature,
                        gpu_percent, gpu_memory_percent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.memory_used_mb,
                    metrics.memory_available_mb,
                    metrics.disk_percent,
                    metrics.disk_used_gb,
                    metrics.disk_free_gb,
                    metrics.network_sent_mb,
                    metrics.network_recv_mb,
                    metrics.temperature,
                    metrics.gpu_percent,
                    metrics.gpu_memory_percent
                ))
            
            # เพิ่มใน memory
            self.metrics_history.append(metrics)
            
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
    
    def check_thresholds(self, metrics: SystemMetrics):
        """ตรวจสอบ thresholds และส่ง alerts"""
        alerts = []
        
        # CPU
        if metrics.cpu_percent >= self.thresholds["cpu_critical"]:
            alerts.append(("CPU", "critical", f"CPU usage: {metrics.cpu_percent:.1f}%"))
        elif metrics.cpu_percent >= self.thresholds["cpu_warning"]:
            alerts.append(("CPU", "warning", f"CPU usage: {metrics.cpu_percent:.1f}%"))
        
        # Memory
        if metrics.memory_percent >= self.thresholds["memory_critical"]:
            alerts.append(("Memory", "critical", f"Memory usage: {metrics.memory_percent:.1f}%"))
        elif metrics.memory_percent >= self.thresholds["memory_warning"]:
            alerts.append(("Memory", "warning", f"Memory usage: {metrics.memory_percent:.1f}%"))
        
        # Disk
        if metrics.disk_percent >= self.thresholds["disk_critical"]:
            alerts.append(("Disk", "critical", f"Disk usage: {metrics.disk_percent:.1f}%"))
        elif metrics.disk_percent >= self.thresholds["disk_warning"]:
            alerts.append(("Disk", "warning", f"Disk usage: {metrics.disk_percent:.1f}%"))
        
        # Temperature
        if metrics.temperature and metrics.temperature >= self.thresholds["temperature_critical"]:
            alerts.append(("Temperature", "critical", f"Temperature: {metrics.temperature:.1f}°C"))
        elif metrics.temperature and metrics.temperature >= self.thresholds["temperature_warning"]:
            alerts.append(("Temperature", "warning", f"Temperature: {metrics.temperature:.1f}°C"))
        
        # ส่ง alerts
        for component, level, message in alerts:
            self._send_alert(component, level, message)
    
    def _send_alert(self, component: str, level: str, message: str):
        """ส่ง alert"""
        alert_key = f"{component}_{level}"
        current_time = time.time()
        
        # ตรวจสอบ cooldown
        if alert_key in self.alert_cooldown:
            if current_time - self.alert_cooldown[alert_key] < self.alert_cooldown_period:
                return
        
        self.alert_cooldown[alert_key] = current_time
        
        # Log alert
        self.logger.warning(f"ALERT [{level.upper()}] {component}: {message}")
        
        # ส่ง email (ถ้าตั้งค่าไว้)
        try:
            self._send_email_alert(component, level, message)
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
        
        # ส่ง webhook (ถ้าตั้งค่าไว้)
        try:
            self._send_webhook_alert(component, level, message)
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_email_alert(self, component: str, level: str, message: str):
        """ส่ง email alert"""
        email_config = self.config.get_dict("EMAIL_CONFIG", {})
        if not email_config:
            return
        
        smtp_server = email_config.get("smtp_server")
        smtp_port = email_config.get("smtp_port", 587)
        username = email_config.get("username")
        password = email_config.get("password")
        to_emails = email_config.get("to_emails", [])
        
        if not all([smtp_server, username, password, to_emails]):
            return
        
        msg = MimeMultipart()
        msg['From'] = username
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = f"System Alert [{level.upper()}] - {component}"
        
        body = f"""
System Alert Notification

Component: {component}
Level: {level.upper()}
Message: {message}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from the system monitoring service.
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
    
    def _send_webhook_alert(self, component: str, level: str, message: str):
        """ส่ง webhook alert"""
        webhook_url = self.config.get_string("WEBHOOK_URL")
        if not webhook_url:
            return
        
        payload = {
            "component": component,
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "hostname": psutil.os.uname().nodename if hasattr(psutil.os, 'uname') else "unknown"
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
    
    def start_monitoring(self, interval: int = 60):
        """เริ่ม monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info(f"System monitoring started with {interval}s interval")
    
    def _monitoring_loop(self, interval: int):
        """Loop สำหรับ monitoring"""
        while self.monitoring_active:
            try:
                metrics = self.collect_system_metrics()
                self.save_metrics(metrics)
                self.check_thresholds(metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def stop_monitoring(self):
        """หยุด monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("System monitoring stopped")
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """ดึง metrics ปัจจุบัน"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, hours: int = 24) -> List[SystemMetrics]:
        """ดึง metrics history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM system_metrics 
                    WHERE timestamp > ? 
                    ORDER BY timestamp DESC
                """, (cutoff_time.isoformat(),))
                
                metrics_list = []
                for row in cursor.fetchall():
                    metrics = SystemMetrics(
                        timestamp=datetime.fromisoformat(row[1]),
                        cpu_percent=row[2],
                        memory_percent=row[3],
                        memory_used_mb=row[4],
                        memory_available_mb=row[5],
                        disk_percent=row[6],
                        disk_used_gb=row[7],
                        disk_free_gb=row[8],
                        network_sent_mb=row[9],
                        network_recv_mb=row[10],
                        temperature=row[11],
                        gpu_percent=row[12],
                        gpu_memory_percent=row[13]
                    )
                    metrics_list.append(metrics)
                
                return metrics_list
                
        except Exception as e:
            self.logger.error(f"Error getting metrics history: {e}")
            return []
    
    def get_system_summary(self) -> Dict[str, Any]:
        """ดึงสรุปสถานะระบบ"""
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return {"status": "no_data"}
        
        # คำนวณ average จาก history
        recent_metrics = list(self.metrics_history)[-10:]  # 10 ล่าสุด
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_percent for m in recent_metrics) / len(recent_metrics)
        
        # ประเมินสถานะรวม
        status = "healthy"
        if (avg_cpu >= self.thresholds["cpu_critical"] or 
            avg_memory >= self.thresholds["memory_critical"] or 
            avg_disk >= self.thresholds["disk_critical"]):
            status = "critical"
        elif (avg_cpu >= self.thresholds["cpu_warning"] or 
              avg_memory >= self.thresholds["memory_warning"] or 
              avg_disk >= self.thresholds["disk_warning"]):
            status = "warning"
        
        return {
            "status": status,
            "timestamp": current_metrics.timestamp.isoformat(),
            "current": asdict(current_metrics),
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_percent": round(avg_memory, 2),
                "disk_percent": round(avg_disk, 2)
            },
            "uptime": self._get_system_uptime(),
            "health_checks": {k: v.status for k, v in self.health_status.items()}
        }
    
    def _get_system_uptime(self) -> str:
        """ดึงเวลา uptime ของระบบ"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_delta = timedelta(seconds=uptime_seconds)
            
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            return f"{days}d {hours}h {minutes}m"
        except Exception:
            return "unknown"
    
    def cleanup_old_data(self, days: int = 30):
        """ลบข้อมูลเก่า"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # ลบ metrics เก่า
                cursor = conn.execute(
                    "DELETE FROM system_metrics WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                metrics_deleted = cursor.rowcount
                
                # ลบ health checks เก่า
                cursor = conn.execute(
                    "DELETE FROM health_checks WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                health_deleted = cursor.rowcount
                
                # Vacuum database
                conn.execute("VACUUM")
                
                self.logger.info(
                    f"Cleaned up old data: {metrics_deleted} metrics, "
                    f"{health_deleted} health checks"
                )
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")

class HealthChecker:
    """คลาสสำหรับ health checks"""
    
    def __init__(self, system_monitor: SystemMonitor):
        self.system_monitor = system_monitor
        self.logger = system_monitor.logger
        self.health_checks = {}
        self.check_active = False
        self.check_thread = None
    
    def register_health_check(self, name: str, check_func: Callable[[], HealthStatus]):
        """ลงทะเบียน health check function"""
        self.health_checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")
    
    def check_camera_health(self) -> HealthStatus:
        """ตรวจสอบสถานะกล้อง"""
        start_time = time.time()
        
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return HealthStatus(
                    component="camera",
                    status="critical",
                    message="Camera not accessible",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return HealthStatus(
                    component="camera",
                    status="critical",
                    message="Camera not capturing frames",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
            
            return HealthStatus(
                component="camera",
                status="healthy",
                message="Camera working normally",
                timestamp=datetime.now(),
                response_time=time.time() - start_time,
                details={"frame_shape": frame.shape}
            )
            
        except Exception as e:
            return HealthStatus(
                component="camera",
                status="critical",
                message=f"Camera error: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    def check_arduino_health(self) -> HealthStatus:
        """ตรวจสอบสถานะ Arduino"""
        start_time = time.time()
        
        try:
            arduino_port = self.system_monitor.config.get_string("ARDUINO_PORT", "COM3")
            
            ser = serial.Serial(arduino_port, 9600, timeout=2)
            time.sleep(1)  # รอ Arduino reset
            
            # ส่งคำสั่งทดสอบ
            ser.write(b"STATUS\n")
            response = ser.readline().decode().strip()
            ser.close()
            
            if "OK" in response:
                return HealthStatus(
                    component="arduino",
                    status="healthy",
                    message="Arduino responding normally",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time,
                    details={"response": response}
                )
            else:
                return HealthStatus(
                    component="arduino",
                    status="warning",
                    message=f"Arduino unexpected response: {response}",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
                
        except Exception as e:
            return HealthStatus(
                component="arduino",
                status="critical",
                message=f"Arduino connection error: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    def check_firebase_health(self) -> HealthStatus:
        """ตรวจสอบสถานะ Firebase"""
        start_time = time.time()
        
        try:
            # ทดสอบการเชื่อมต่อ Firebase
            import firebase_admin
            from firebase_admin import firestore
            
            db = firestore.client()
            
            # ทดสอบ write/read
            test_doc = db.collection('health_check').document('test')
            test_data = {
                'timestamp': datetime.now(),
                'test': True
            }
            
            test_doc.set(test_data)
            read_data = test_doc.get()
            
            if read_data.exists:
                # ลบ test document
                test_doc.delete()
                
                return HealthStatus(
                    component="firebase",
                    status="healthy",
                    message="Firebase connection working",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
            else:
                return HealthStatus(
                    component="firebase",
                    status="warning",
                    message="Firebase read/write test failed",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
                
        except Exception as e:
            return HealthStatus(
                component="firebase",
                status="critical",
                message=f"Firebase error: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    def check_disk_space(self) -> HealthStatus:
        """ตรวจสอบพื้นที่ disk"""
        start_time = time.time()
        
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 * 1024 * 1024)
            percent_used = disk.percent
            
            if percent_used >= 95:
                status = "critical"
                message = f"Disk space critically low: {percent_used:.1f}% used"
            elif percent_used >= 85:
                status = "warning"
                message = f"Disk space low: {percent_used:.1f}% used"
            else:
                status = "healthy"
                message = f"Disk space OK: {percent_used:.1f}% used"
            
            return HealthStatus(
                component="disk_space",
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time=time.time() - start_time,
                details={
                    "percent_used": percent_used,
                    "free_gb": round(free_gb, 2),
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 2)
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="disk_space",
                status="unknown",
                message=f"Disk check error: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    def run_all_checks(self) -> Dict[str, HealthStatus]:
        """รัน health checks ทั้งหมด"""
        results = {}
        
        # รัน default checks
        default_checks = {
            "camera": self.check_camera_health,
            "arduino": self.check_arduino_health,
            "firebase": self.check_firebase_health,
            "disk_space": self.check_disk_space
        }
        
        all_checks = {**default_checks, **self.health_checks}
        
        for name, check_func in all_checks.items():
            try:
                result = check_func()
                results[name] = result
                
                # บันทึกลง database
                self._save_health_check(result)
                
                # อัปเดต status ใน system monitor
                self.system_monitor.health_status[name] = result
                
            except Exception as e:
                self.logger.error(f"Error running health check {name}: {e}")
                results[name] = HealthStatus(
                    component=name,
                    status="unknown",
                    message=f"Check failed: {str(e)}",
                    timestamp=datetime.now()
                )
        
        return results
    
    def _save_health_check(self, health_status: HealthStatus):
        """บันทึก health check result"""
        try:
            with sqlite3.connect(self.system_monitor.db_path) as conn:
                conn.execute("""
                    INSERT INTO health_checks (
                        timestamp, component, status, message, response_time, details
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    health_status.timestamp.isoformat(),
                    health_status.component,
                    health_status.status,
                    health_status.message,
                    health_status.response_time,
                    json.dumps(health_status.details) if health_status.details else None
                ))
                
        except Exception as e:
            self.logger.error(f"Error saving health check: {e}")
    
    def start_periodic_checks(self, interval: int = 300):
        """เริ่ม periodic health checks"""
        if self.check_active:
            self.logger.warning("Health checks are already active")
            return
        
        self.check_active = True
        self.check_thread = threading.Thread(
            target=self._check_loop,
            args=(interval,),
            daemon=True
        )
        self.check_thread.start()
        
        self.logger.info(f"Health checks started with {interval}s interval")
    
    def _check_loop(self, interval: int):
        """Loop สำหรับ health checks"""
        while self.check_active:
            try:
                self.run_all_checks()
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                time.sleep(interval)
    
    def stop_periodic_checks(self):
        """หยุด periodic health checks"""
        self.check_active = False
        if self.check_thread:
            self.check_thread.join(timeout=5)
        
        self.logger.info("Health checks stopped")

# ========================================
# Main Function สำหรับทดสอบ
# ========================================

if __name__ == "__main__":
    # สร้าง system monitor
    monitor = SystemMonitor()
    health_checker = HealthChecker(monitor)
    
    try:
        # เริ่ม monitoring
        monitor.start_monitoring(interval=30)
        health_checker.start_periodic_checks(interval=60)
        
        print("System monitoring started. Press Ctrl+C to stop.")
        
        # แสดงสถานะทุก 10 วินาที
        while True:
            time.sleep(10)
            summary = monitor.get_system_summary()
            print(f"\nSystem Status: {summary['status']}")
            print(f"CPU: {summary['current']['cpu_percent']:.1f}%")
            print(f"Memory: {summary['current']['memory_percent']:.1f}%")
            print(f"Disk: {summary['current']['disk_percent']:.1f}%")
            print(f"Uptime: {summary['uptime']}")
            
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        monitor.stop_monitoring()
        health_checker.stop_periodic_checks()
        print("Monitoring stopped.")