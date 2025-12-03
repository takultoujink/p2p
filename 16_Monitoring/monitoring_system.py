"""
Advanced Monitoring and Alerting System for Object Detection
รองรับ Health checks, Performance metrics, Error tracking, Real-time dashboards
"""

import os
import time
import json
import asyncio
import threading
import sqlite3
import redis
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import psutil
import socket
import subprocess
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import websockets
import aiohttp
from aiohttp import web
import plotly.graph_objs as go
import plotly.utils
from jinja2 import Template
import yaml
import schedule
from collections import defaultdict, deque
import statistics
import traceback
import sys
from contextlib import contextmanager
import uuid
import hashlib

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """ระดับความรุนแรงของ alert"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class HealthStatus(Enum):
    """สถานะสุขภาพของระบบ"""
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

class MetricType(Enum):
    """ประเภทของ metric"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    """ข้อมูล alert"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    timestamp: datetime
    source: str
    metric_name: str
    current_value: float
    threshold_value: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """การตรวจสอบสุขภาพ"""
    name: str
    description: str
    check_function: Callable
    interval_seconds: int
    timeout_seconds: int
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_status: HealthStatus = HealthStatus.HEALTHY
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    max_failures: int = 3

@dataclass
class Metric:
    """ข้อมูล metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""

@dataclass
class MonitoringConfig:
    """การกำหนดค่า monitoring"""
    # Database
    database_path: str = "monitoring.db"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 2
    
    # Health Checks
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 10
    max_consecutive_failures: int = 3
    
    # Metrics Collection
    metrics_collection_interval: int = 15  # seconds
    metrics_retention_days: int = 30
    metrics_aggregation_interval: int = 300  # 5 minutes
    
    # Alerting
    alert_enabled: bool = True
    alert_cooldown_minutes: int = 15
    email_notifications: bool = True
    webhook_notifications: bool = True
    slack_notifications: bool = False
    
    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    
    # Webhook Configuration
    webhook_urls: List[str] = field(default_factory=list)
    
    # Slack Configuration
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Dashboard
    dashboard_enabled: bool = True
    dashboard_port: int = 8080
    dashboard_host: str = "0.0.0.0"
    websocket_port: int = 8081
    
    # Performance Thresholds
    cpu_threshold_percent: float = 80.0
    memory_threshold_percent: float = 85.0
    disk_threshold_percent: float = 90.0
    response_time_threshold_ms: float = 1000.0
    error_rate_threshold_percent: float = 5.0
    
    # System Monitoring
    monitor_system_resources: bool = True
    monitor_application_metrics: bool = True
    monitor_external_services: bool = True
    
    # Log Monitoring
    log_monitoring_enabled: bool = True
    log_error_patterns: List[str] = field(default_factory=lambda: [
        "ERROR", "CRITICAL", "FATAL", "Exception", "Traceback"
    ])

class MetricsCollector:
    """เก็บรวบรวม metrics"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics_buffer = deque(maxlen=10000)
        self.redis_client = None
        self.collection_active = False
        
        self.init_redis()
        self.init_database()
    
    def init_redis(self):
        """เริ่มต้น Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db
            )
            self.redis_client.ping()
            logger.info("Metrics Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available for metrics: {e}")
            self.redis_client = None
    
    def init_database(self):
        """เริ่มต้นฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    labels TEXT,
                    description TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp 
                ON metrics(name, timestamp)
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Metrics database initialization error: {e}")
    
    def collect_system_metrics(self) -> List[Metric]:
        """เก็บ system metrics"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(Metric(
                name="system.cpu.usage_percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="CPU usage percentage"
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append(Metric(
                name="system.memory.usage_percent",
                value=memory.percent,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Memory usage percentage"
            ))
            
            metrics.append(Metric(
                name="system.memory.available_gb",
                value=memory.available / (1024**3),
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Available memory in GB"
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics.append(Metric(
                name="system.disk.usage_percent",
                value=(disk.used / disk.total) * 100,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Disk usage percentage"
            ))
            
            # Network metrics
            network = psutil.net_io_counters()
            metrics.append(Metric(
                name="system.network.bytes_sent",
                value=network.bytes_sent,
                metric_type=MetricType.COUNTER,
                timestamp=timestamp,
                description="Network bytes sent"
            ))
            
            metrics.append(Metric(
                name="system.network.bytes_recv",
                value=network.bytes_recv,
                metric_type=MetricType.COUNTER,
                timestamp=timestamp,
                description="Network bytes received"
            ))
            
            # Process metrics
            process = psutil.Process()
            metrics.append(Metric(
                name="process.memory.rss_mb",
                value=process.memory_info().rss / (1024**2),
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Process RSS memory in MB"
            ))
            
            metrics.append(Metric(
                name="process.cpu.percent",
                value=process.cpu_percent(),
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Process CPU usage percentage"
            ))
            
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
        
        return metrics
    
    def collect_application_metrics(self) -> List[Metric]:
        """เก็บ application metrics"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # ตัวอย่าง application metrics
            # (ในการใช้งานจริงจะดึงจาก application)
            
            # Request metrics
            metrics.append(Metric(
                name="app.requests.total",
                value=1000,  # placeholder
                metric_type=MetricType.COUNTER,
                timestamp=timestamp,
                description="Total number of requests"
            ))
            
            metrics.append(Metric(
                name="app.requests.error_rate",
                value=2.5,  # placeholder
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Request error rate percentage"
            ))
            
            metrics.append(Metric(
                name="app.response_time.avg_ms",
                value=250.0,  # placeholder
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Average response time in milliseconds"
            ))
            
            # Detection metrics
            metrics.append(Metric(
                name="detection.objects.total",
                value=500,  # placeholder
                metric_type=MetricType.COUNTER,
                timestamp=timestamp,
                description="Total objects detected"
            ))
            
            metrics.append(Metric(
                name="detection.accuracy.percent",
                value=95.2,  # placeholder
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Detection accuracy percentage"
            ))
            
            metrics.append(Metric(
                name="detection.processing_time.avg_ms",
                value=150.0,  # placeholder
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Average detection processing time"
            ))
            
        except Exception as e:
            logger.error(f"Application metrics collection error: {e}")
        
        return metrics
    
    def store_metrics(self, metrics: List[Metric]):
        """เก็บ metrics ลงฐานข้อมูล"""
        try:
            # เก็บใน buffer
            self.metrics_buffer.extend(metrics)
            
            # เก็บใน Redis (real-time)
            if self.redis_client:
                for metric in metrics:
                    key = f"metric:{metric.name}"
                    value = {
                        "value": metric.value,
                        "timestamp": metric.timestamp.isoformat(),
                        "labels": metric.labels,
                        "description": metric.description
                    }
                    self.redis_client.setex(key, 300, json.dumps(value))  # 5 minutes TTL
            
            # เก็บใน SQLite (persistent)
            if len(self.metrics_buffer) >= 100:  # Batch insert
                self._flush_metrics_to_db()
                
        except Exception as e:
            logger.error(f"Metrics storage error: {e}")
    
    def _flush_metrics_to_db(self):
        """เก็บ metrics จาก buffer ลงฐานข้อมูล"""
        try:
            if not self.metrics_buffer:
                return
            
            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()
            
            metrics_data = []
            while self.metrics_buffer:
                metric = self.metrics_buffer.popleft()
                metrics_data.append((
                    metric.name,
                    metric.value,
                    metric.metric_type.value,
                    metric.timestamp,
                    json.dumps(metric.labels),
                    metric.description
                ))
            
            cursor.executemany('''
                INSERT INTO metrics (name, value, metric_type, timestamp, labels, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', metrics_data)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Metrics database flush error: {e}")
    
    def get_metrics(self, metric_name: str, start_time: datetime, 
                   end_time: datetime) -> List[Metric]:
        """ดึง metrics จากฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, value, metric_type, timestamp, labels, description
                FROM metrics
                WHERE name = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (metric_name, start_time, end_time))
            
            metrics = []
            for row in cursor.fetchall():
                metrics.append(Metric(
                    name=row[0],
                    value=row[1],
                    metric_type=MetricType(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    labels=json.loads(row[4]) if row[4] else {},
                    description=row[5] or ""
                ))
            
            conn.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics retrieval error: {e}")
            return []

class HealthChecker:
    """ตรวจสอบสุขภาพของระบบ"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.health_checks = {}
        self.check_results = {}
        self.checking_active = False
        
        self.register_default_checks()
    
    def register_default_checks(self):
        """ลงทะเบียน health checks เริ่มต้น"""
        
        # Database connectivity check
        self.register_check(HealthCheck(
            name="database_connectivity",
            description="Check database connectivity",
            check_function=self._check_database_connectivity,
            interval_seconds=60,
            timeout_seconds=10
        ))
        
        # Redis connectivity check
        self.register_check(HealthCheck(
            name="redis_connectivity",
            description="Check Redis connectivity",
            check_function=self._check_redis_connectivity,
            interval_seconds=60,
            timeout_seconds=5
        ))
        
        # Disk space check
        self.register_check(HealthCheck(
            name="disk_space",
            description="Check available disk space",
            check_function=self._check_disk_space,
            interval_seconds=300,  # 5 minutes
            timeout_seconds=5
        ))
        
        # Memory usage check
        self.register_check(HealthCheck(
            name="memory_usage",
            description="Check memory usage",
            check_function=self._check_memory_usage,
            interval_seconds=60,
            timeout_seconds=5
        ))
        
        # CPU usage check
        self.register_check(HealthCheck(
            name="cpu_usage",
            description="Check CPU usage",
            check_function=self._check_cpu_usage,
            interval_seconds=60,
            timeout_seconds=10
        ))
        
        # Application endpoint check
        self.register_check(HealthCheck(
            name="app_endpoint",
            description="Check application endpoint",
            check_function=self._check_app_endpoint,
            interval_seconds=30,
            timeout_seconds=10
        ))
    
    def register_check(self, health_check: HealthCheck):
        """ลงทะเบียน health check"""
        self.health_checks[health_check.name] = health_check
        self.check_results[health_check.name] = {
            "status": HealthStatus.HEALTHY,
            "last_check": None,
            "error": None
        }
    
    def _check_database_connectivity(self) -> Tuple[HealthStatus, Optional[str]]:
        """ตรวจสอบการเชื่อมต่อฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.config.database_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return HealthStatus.HEALTHY, None
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
    
    def _check_redis_connectivity(self) -> Tuple[HealthStatus, Optional[str]]:
        """ตรวจสอบการเชื่อมต่อ Redis"""
        try:
            redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                socket_timeout=5
            )
            redis_client.ping()
            return HealthStatus.HEALTHY, None
        except Exception as e:
            return HealthStatus.WARNING, str(e)  # Redis ไม่จำเป็นต้องมี
    
    def _check_disk_space(self) -> Tuple[HealthStatus, Optional[str]]:
        """ตรวจสอบพื้นที่ disk"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent >= self.config.disk_threshold_percent:
                return HealthStatus.CRITICAL, f"Disk usage: {usage_percent:.1f}%"
            elif usage_percent >= self.config.disk_threshold_percent - 10:
                return HealthStatus.WARNING, f"Disk usage: {usage_percent:.1f}%"
            else:
                return HealthStatus.HEALTHY, None
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
    
    def _check_memory_usage(self) -> Tuple[HealthStatus, Optional[str]]:
        """ตรวจสอบการใช้ memory"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent >= self.config.memory_threshold_percent:
                return HealthStatus.CRITICAL, f"Memory usage: {memory.percent:.1f}%"
            elif memory.percent >= self.config.memory_threshold_percent - 10:
                return HealthStatus.WARNING, f"Memory usage: {memory.percent:.1f}%"
            else:
                return HealthStatus.HEALTHY, None
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
    
    def _check_cpu_usage(self) -> Tuple[HealthStatus, Optional[str]]:
        """ตรวจสอบการใช้ CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent >= self.config.cpu_threshold_percent:
                return HealthStatus.CRITICAL, f"CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent >= self.config.cpu_threshold_percent - 10:
                return HealthStatus.WARNING, f"CPU usage: {cpu_percent:.1f}%"
            else:
                return HealthStatus.HEALTHY, None
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
    
    def _check_app_endpoint(self) -> Tuple[HealthStatus, Optional[str]]:
        """ตรวจสอบ application endpoint"""
        try:
            # ตัวอย่างการตรวจสอบ endpoint
            # (ในการใช้งานจริงจะเป็น URL ของ application)
            
            start_time = time.time()
            response = requests.get("http://localhost:8000/health", timeout=5)
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                if response_time > self.config.response_time_threshold_ms:
                    return HealthStatus.WARNING, f"Slow response: {response_time:.0f}ms"
                else:
                    return HealthStatus.HEALTHY, None
            else:
                return HealthStatus.UNHEALTHY, f"HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return HealthStatus.CRITICAL, "Connection refused"
        except requests.exceptions.Timeout:
            return HealthStatus.UNHEALTHY, "Request timeout"
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
    
    def run_check(self, check_name: str) -> Dict[str, Any]:
        """รัน health check เดียว"""
        if check_name not in self.health_checks:
            return {"error": f"Health check '{check_name}' not found"}
        
        health_check = self.health_checks[check_name]
        
        try:
            start_time = time.time()
            status, error = health_check.check_function()
            check_time = time.time() - start_time
            
            # อัปเดตผลลัพธ์
            health_check.last_check = datetime.now()
            health_check.last_status = status
            health_check.last_error = error
            
            if status != HealthStatus.HEALTHY:
                health_check.consecutive_failures += 1
            else:
                health_check.consecutive_failures = 0
            
            self.check_results[check_name] = {
                "status": status,
                "last_check": health_check.last_check,
                "error": error,
                "check_time_ms": check_time * 1000,
                "consecutive_failures": health_check.consecutive_failures
            }
            
            return self.check_results[check_name]
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            health_check.consecutive_failures += 1
            health_check.last_error = error_msg
            
            self.check_results[check_name] = {
                "status": HealthStatus.UNHEALTHY,
                "last_check": datetime.now(),
                "error": error_msg,
                "consecutive_failures": health_check.consecutive_failures
            }
            
            return self.check_results[check_name]
    
    def run_all_checks(self) -> Dict[str, Any]:
        """รัน health checks ทั้งหมด"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for check_name in self.health_checks:
            if self.health_checks[check_name].enabled:
                result = self.run_check(check_name)
                results[check_name] = result
                
                # อัปเดต overall status
                if result["status"] == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif result["status"] == HealthStatus.UNHEALTHY and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.UNHEALTHY
                elif result["status"] == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now(),
            "checks": results
        }

class AlertManager:
    """จัดการ alerts และ notifications"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_cooldowns = {}
        
        self.init_database()
    
    def init_database(self):
        """เริ่มต้นฐานข้อมูล alerts"""
        try:
            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    metric_name TEXT,
                    current_value REAL,
                    threshold_value REAL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    tags TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Alert database initialization error: {e}")
    
    def create_alert(self, title: str, description: str, severity: AlertSeverity,
                    source: str, metric_name: str = "", current_value: float = 0,
                    threshold_value: float = 0, tags: Dict[str, str] = None) -> Alert:
        """สร้าง alert ใหม่"""
        
        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            timestamp=datetime.now(),
            source=source,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            tags=tags or {}
        )
        
        # ตรวจสอบ cooldown
        cooldown_key = f"{source}:{metric_name}"
        if cooldown_key in self.alert_cooldowns:
            last_alert_time = self.alert_cooldowns[cooldown_key]
            if datetime.now() - last_alert_time < timedelta(minutes=self.config.alert_cooldown_minutes):
                logger.info(f"Alert suppressed due to cooldown: {title}")
                return alert
        
        # เก็บ alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.alert_cooldowns[cooldown_key] = datetime.now()
        
        # เก็บลงฐานข้อมูล
        self._store_alert(alert)
        
        # ส่ง notifications
        if self.config.alert_enabled:
            self._send_notifications(alert)
        
        logger.warning(f"Alert created: {title} ({severity.value})")
        return alert
    
    def _store_alert(self, alert: Alert):
        """เก็บ alert ลงฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts 
                (id, title, description, severity, timestamp, source, metric_name,
                 current_value, threshold_value, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id, alert.title, alert.description, alert.severity.value,
                alert.timestamp, alert.source, alert.metric_name,
                alert.current_value, alert.threshold_value, json.dumps(alert.tags)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Alert storage error: {e}")
    
    def _send_notifications(self, alert: Alert):
        """ส่ง notifications"""
        try:
            # Email notification
            if self.config.email_notifications and self.config.email_to:
                self._send_email_notification(alert)
            
            # Webhook notification
            if self.config.webhook_notifications and self.config.webhook_urls:
                self._send_webhook_notification(alert)
            
            # Slack notification
            if self.config.slack_notifications and self.config.slack_webhook_url:
                self._send_slack_notification(alert)
                
        except Exception as e:
            logger.error(f"Notification sending error: {e}")
    
    def _send_email_notification(self, alert: Alert):
        """ส่ง email notification"""
        try:
            if not all([self.config.smtp_username, self.config.smtp_password, 
                       self.config.email_from]):
                return
            
            msg = MimeMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_to)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
Alert Details:
- Title: {alert.title}
- Description: {alert.description}
- Severity: {alert.severity.value}
- Source: {alert.source}
- Timestamp: {alert.timestamp}
- Metric: {alert.metric_name}
- Current Value: {alert.current_value}
- Threshold: {alert.threshold_value}

Please investigate this issue.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for alert: {alert.title}")
            
        except Exception as e:
            logger.error(f"Email notification error: {e}")
    
    def _send_webhook_notification(self, alert: Alert):
        """ส่ง webhook notification"""
        try:
            payload = {
                "alert_id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp.isoformat(),
                "source": alert.source,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "tags": alert.tags
            }
            
            for webhook_url in self.config.webhook_urls:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook notification sent to: {webhook_url}")
                else:
                    logger.error(f"Webhook notification failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Webhook notification error: {e}")
    
    def _send_slack_notification(self, alert: Alert):
        """ส่ง Slack notification"""
        try:
            color_map = {
                AlertSeverity.LOW: "good",
                AlertSeverity.MEDIUM: "warning",
                AlertSeverity.HIGH: "danger",
                AlertSeverity.CRITICAL: "danger"
            }
            
            payload = {
                "channel": self.config.slack_channel,
                "username": "Monitoring Bot",
                "icon_emoji": ":warning:",
                "attachments": [{
                    "color": color_map.get(alert.severity, "danger"),
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Metric", "value": alert.metric_name, "short": True},
                        {"title": "Value", "value": str(alert.current_value), "short": True}
                    ],
                    "timestamp": int(alert.timestamp.timestamp())
                }]
            }
            
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack notification sent")
            else:
                logger.error(f"Slack notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """แก้ไข alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                
                # อัปเดตฐานข้อมูล
                conn = sqlite3.connect(self.config.database_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE alerts 
                    SET resolved = TRUE, resolved_at = ?
                    WHERE id = ?
                ''', (alert.resolved_at, alert_id))
                conn.commit()
                conn.close()
                
                # ลบจาก active alerts
                del self.active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {alert.title}")
                return True
                
        except Exception as e:
            logger.error(f"Alert resolution error: {e}")
        
        return False
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """รับทราบ alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.now()
                
                # อัปเดตฐานข้อมูล
                conn = sqlite3.connect(self.config.database_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE alerts 
                    SET acknowledged = TRUE, acknowledged_by = ?, acknowledged_at = ?
                    WHERE id = ?
                ''', (acknowledged_by, alert.acknowledged_at, alert_id))
                conn.commit()
                conn.close()
                
                logger.info(f"Alert acknowledged by {acknowledged_by}: {alert.title}")
                return True
                
        except Exception as e:
            logger.error(f"Alert acknowledgment error: {e}")
        
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """ดึง active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """ดึงประวัติ alerts"""
        return list(self.alert_history)[-limit:]

class DashboardServer:
    """Web dashboard สำหรับ monitoring"""
    
    def __init__(self, config: MonitoringConfig, metrics_collector: MetricsCollector,
                 health_checker: HealthChecker, alert_manager: AlertManager):
        self.config = config
        self.metrics_collector = metrics_collector
        self.health_checker = health_checker
        self.alert_manager = alert_manager
        self.app = web.Application()
        self.websocket_clients = set()
        
        self.setup_routes()
    
    def setup_routes(self):
        """ตั้งค่า routes"""
        self.app.router.add_get('/', self.dashboard_handler)
        self.app.router.add_get('/api/health', self.health_api_handler)
        self.app.router.add_get('/api/metrics', self.metrics_api_handler)
        self.app.router.add_get('/api/alerts', self.alerts_api_handler)
        self.app.router.add_post('/api/alerts/{alert_id}/acknowledge', self.acknowledge_alert_handler)
        self.app.router.add_post('/api/alerts/{alert_id}/resolve', self.resolve_alert_handler)
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # Static files
        self.app.router.add_static('/', path='static', name='static')
    
    async def dashboard_handler(self, request):
        """หน้า dashboard หลัก"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Object Detection Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .status-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-healthy { border-left: 5px solid #27ae60; }
        .status-warning { border-left: 5px solid #f39c12; }
        .status-unhealthy { border-left: 5px solid #e74c3c; }
        .status-critical { border-left: 5px solid #c0392b; }
        .metrics-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .alerts-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert-item { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-critical { background: #ffebee; border-left: 4px solid #f44336; }
        .alert-high { background: #fff3e0; border-left: 4px solid #ff9800; }
        .alert-medium { background: #fff8e1; border-left: 4px solid #ffc107; }
        .alert-low { background: #e8f5e8; border-left: 4px solid #4caf50; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Object Detection Monitoring Dashboard</h1>
        <p>Real-time system monitoring and alerting</p>
    </div>
    
    <div class="status-grid" id="healthStatus">
        <!-- Health status cards will be populated here -->
    </div>
    
    <div class="metrics-container">
        <h2>📊 System Metrics</h2>
        <button class="refresh-btn" onclick="refreshMetrics()">Refresh Metrics</button>
        <div id="metricsCharts"></div>
    </div>
    
    <div class="alerts-container">
        <h2>🚨 Active Alerts</h2>
        <div id="alertsList">
            <!-- Alerts will be populated here -->
        </div>
    </div>

    <script>
        let ws;
        
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8081/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'health_update') {
                    updateHealthStatus(data.data);
                } else if (data.type === 'metrics_update') {
                    updateMetrics(data.data);
                } else if (data.type === 'alert_update') {
                    updateAlerts(data.data);
                }
            };
            
            ws.onclose = function() {
                setTimeout(connectWebSocket, 5000); // Reconnect after 5 seconds
            };
        }
        
        function updateHealthStatus(healthData) {
            const container = document.getElementById('healthStatus');
            container.innerHTML = '';
            
            for (const [checkName, result] of Object.entries(healthData.checks)) {
                const card = document.createElement('div');
                card.className = `status-card status-${result.status}`;
                card.innerHTML = `
                    <h3>${checkName.replace('_', ' ').toUpperCase()}</h3>
                    <p><strong>Status:</strong> ${result.status}</p>
                    <p><strong>Last Check:</strong> ${new Date(result.last_check).toLocaleString()}</p>
                    ${result.error ? `<p><strong>Error:</strong> ${result.error}</p>` : ''}
                    <p><strong>Check Time:</strong> ${result.check_time_ms?.toFixed(1)}ms</p>
                `;
                container.appendChild(card);
            }
        }
        
        function updateMetrics(metricsData) {
            // Update metrics charts
            // This would contain Plotly.js chart updates
        }
        
        function updateAlerts(alertsData) {
            const container = document.getElementById('alertsList');
            container.innerHTML = '';
            
            if (alertsData.length === 0) {
                container.innerHTML = '<p>No active alerts</p>';
                return;
            }
            
            alertsData.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert-item alert-${alert.severity}`;
                alertDiv.innerHTML = `
                    <h4>${alert.title}</h4>
                    <p>${alert.description}</p>
                    <p><strong>Source:</strong> ${alert.source} | <strong>Time:</strong> ${new Date(alert.timestamp).toLocaleString()}</p>
                    <button onclick="acknowledgeAlert('${alert.id}')">Acknowledge</button>
                    <button onclick="resolveAlert('${alert.id}')">Resolve</button>
                `;
                container.appendChild(alertDiv);
            });
        }
        
        function acknowledgeAlert(alertId) {
            fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' })
                .then(() => refreshAlerts());
        }
        
        function resolveAlert(alertId) {
            fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' })
                .then(() => refreshAlerts());
        }
        
        function refreshMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => updateMetrics(data));
        }
        
        function refreshAlerts() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => updateAlerts(data));
        }
        
        // Initialize
        connectWebSocket();
        
        // Initial data load
        fetch('/api/health')
            .then(response => response.json())
            .then(data => updateHealthStatus(data));
            
        refreshAlerts();
        refreshMetrics();
        
        // Auto refresh every 30 seconds
        setInterval(() => {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => updateHealthStatus(data));
        }, 30000);
    </script>
</body>
</html>
        """
        return web.Response(text=html_template, content_type='text/html')
    
    async def health_api_handler(self, request):
        """API endpoint สำหรับ health status"""
        health_data = self.health_checker.run_all_checks()
        return web.json_response(health_data, default=str)
    
    async def metrics_api_handler(self, request):
        """API endpoint สำหรับ metrics"""
        # ดึง metrics ล่าสุด
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        metrics_data = {}
        metric_names = [
            "system.cpu.usage_percent",
            "system.memory.usage_percent",
            "system.disk.usage_percent",
            "app.response_time.avg_ms"
        ]
        
        for metric_name in metric_names:
            metrics = self.metrics_collector.get_metrics(metric_name, start_time, end_time)
            metrics_data[metric_name] = [
                {"timestamp": m.timestamp.isoformat(), "value": m.value}
                for m in metrics
            ]
        
        return web.json_response(metrics_data)
    
    async def alerts_api_handler(self, request):
        """API endpoint สำหรับ alerts"""
        alerts = self.alert_manager.get_active_alerts()
        alerts_data = [asdict(alert) for alert in alerts]
        return web.json_response(alerts_data, default=str)
    
    async def acknowledge_alert_handler(self, request):
        """API endpoint สำหรับ acknowledge alert"""
        alert_id = request.match_info['alert_id']
        success = self.alert_manager.acknowledge_alert(alert_id, "dashboard_user")
        return web.json_response({"success": success})
    
    async def resolve_alert_handler(self, request):
        """API endpoint สำหรับ resolve alert"""
        alert_id = request.match_info['alert_id']
        success = self.alert_manager.resolve_alert(alert_id, "dashboard_user")
        return web.json_response({"success": success})
    
    async def websocket_handler(self, request):
        """WebSocket handler สำหรับ real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_clients.add(ws)
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Handle incoming messages if needed
                    pass
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        finally:
            self.websocket_clients.discard(ws)
        
        return ws
    
    async def broadcast_update(self, update_type: str, data: Any):
        """ส่งข้อมูลอัปเดตไปยัง WebSocket clients"""
        if not self.websocket_clients:
            return
        
        message = json.dumps({
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }, default=str)
        
        # ส่งไปยัง clients ทั้งหมด
        disconnected_clients = set()
        for ws in self.websocket_clients:
            try:
                await ws.send_str(message)
            except Exception:
                disconnected_clients.add(ws)
        
        # ลบ clients ที่ disconnect
        self.websocket_clients -= disconnected_clients

class MonitoringSystem:
    """ระบบ monitoring หลัก"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics_collector = MetricsCollector(config)
        self.health_checker = HealthChecker(config)
        self.alert_manager = AlertManager(config)
        self.dashboard_server = DashboardServer(
            config, self.metrics_collector, self.health_checker, self.alert_manager
        )
        
        self.monitoring_active = False
        self.monitoring_threads = []
    
    def start(self):
        """เริ่มต้นระบบ monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring system already running")
            return
        
        self.monitoring_active = True
        logger.info("Starting monitoring system...")
        
        # เริ่มต้น metrics collection
        metrics_thread = threading.Thread(target=self._metrics_collection_worker, daemon=True)
        metrics_thread.start()
        self.monitoring_threads.append(metrics_thread)
        
        # เริ่มต้น health checking
        health_thread = threading.Thread(target=self._health_checking_worker, daemon=True)
        health_thread.start()
        self.monitoring_threads.append(health_thread)
        
        # เริ่มต้น alert monitoring
        alert_thread = threading.Thread(target=self._alert_monitoring_worker, daemon=True)
        alert_thread.start()
        self.monitoring_threads.append(alert_thread)
        
        # เริ่มต้น dashboard server
        if self.config.dashboard_enabled:
            dashboard_thread = threading.Thread(target=self._start_dashboard_server, daemon=True)
            dashboard_thread.start()
            self.monitoring_threads.append(dashboard_thread)
        
        logger.info("Monitoring system started successfully")
    
    def _metrics_collection_worker(self):
        """Worker สำหรับเก็บ metrics"""
        while self.monitoring_active:
            try:
                # เก็บ system metrics
                if self.config.monitor_system_resources:
                    system_metrics = self.metrics_collector.collect_system_metrics()
                    self.metrics_collector.store_metrics(system_metrics)
                
                # เก็บ application metrics
                if self.config.monitor_application_metrics:
                    app_metrics = self.metrics_collector.collect_application_metrics()
                    self.metrics_collector.store_metrics(app_metrics)
                
                # ตรวจสอบ thresholds และสร้าง alerts
                self._check_metric_thresholds()
                
                time.sleep(self.config.metrics_collection_interval)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(60)
    
    def _health_checking_worker(self):
        """Worker สำหรับ health checking"""
        while self.monitoring_active:
            try:
                health_results = self.health_checker.run_all_checks()
                
                # ส่งข้อมูลไปยัง dashboard
                if self.config.dashboard_enabled:
                    asyncio.run_coroutine_threadsafe(
                        self.dashboard_server.broadcast_update("health_update", health_results),
                        asyncio.new_event_loop()
                    )
                
                # ตรวจสอบและสร้าง alerts สำหรับ health checks
                self._check_health_alerts(health_results)
                
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health checking error: {e}")
                time.sleep(60)
    
    def _alert_monitoring_worker(self):
        """Worker สำหรับ monitor alerts"""
        while self.monitoring_active:
            try:
                # ส่งข้อมูล alerts ไปยัง dashboard
                if self.config.dashboard_enabled:
                    active_alerts = self.alert_manager.get_active_alerts()
                    asyncio.run_coroutine_threadsafe(
                        self.dashboard_server.broadcast_update("alert_update", active_alerts),
                        asyncio.new_event_loop()
                    )
                
                time.sleep(30)  # ตรวจสอบทุก 30 วินาที
                
            except Exception as e:
                logger.error(f"Alert monitoring error: {e}")
                time.sleep(60)
    
    def _start_dashboard_server(self):
        """เริ่มต้น dashboard server"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            web.run_app(
                self.dashboard_server.app,
                host=self.config.dashboard_host,
                port=self.config.dashboard_port,
                loop=loop
            )
        except Exception as e:
            logger.error(f"Dashboard server error: {e}")
    
    def _check_metric_thresholds(self):
        """ตรวจสอบ metric thresholds และสร้าง alerts"""
        try:
            # ตรวจสอบ CPU usage
            cpu_metrics = self.metrics_collector.get_metrics(
                "system.cpu.usage_percent",
                datetime.now() - timedelta(minutes=5),
                datetime.now()
            )
            
            if cpu_metrics:
                latest_cpu = cpu_metrics[-1].value
                if latest_cpu > self.config.cpu_threshold_percent:
                    self.alert_manager.create_alert(
                        title="High CPU Usage",
                        description=f"CPU usage is {latest_cpu:.1f}%",
                        severity=AlertSeverity.HIGH if latest_cpu > 90 else AlertSeverity.MEDIUM,
                        source="system_monitor",
                        metric_name="system.cpu.usage_percent",
                        current_value=latest_cpu,
                        threshold_value=self.config.cpu_threshold_percent
                    )
            
            # ตรวจสอบ Memory usage
            memory_metrics = self.metrics_collector.get_metrics(
                "system.memory.usage_percent",
                datetime.now() - timedelta(minutes=5),
                datetime.now()
            )
            
            if memory_metrics:
                latest_memory = memory_metrics[-1].value
                if latest_memory > self.config.memory_threshold_percent:
                    self.alert_manager.create_alert(
                        title="High Memory Usage",
                        description=f"Memory usage is {latest_memory:.1f}%",
                        severity=AlertSeverity.HIGH if latest_memory > 95 else AlertSeverity.MEDIUM,
                        source="system_monitor",
                        metric_name="system.memory.usage_percent",
                        current_value=latest_memory,
                        threshold_value=self.config.memory_threshold_percent
                    )
            
            # ตรวจสอบ Response time
            response_time_metrics = self.metrics_collector.get_metrics(
                "app.response_time.avg_ms",
                datetime.now() - timedelta(minutes=5),
                datetime.now()
            )
            
            if response_time_metrics:
                latest_response_time = response_time_metrics[-1].value
                if latest_response_time > self.config.response_time_threshold_ms:
                    self.alert_manager.create_alert(
                        title="Slow Response Time",
                        description=f"Average response time is {latest_response_time:.0f}ms",
                        severity=AlertSeverity.MEDIUM,
                        source="application_monitor",
                        metric_name="app.response_time.avg_ms",
                        current_value=latest_response_time,
                        threshold_value=self.config.response_time_threshold_ms
                    )
            
        except Exception as e:
            logger.error(f"Metric threshold checking error: {e}")
    
    def _check_health_alerts(self, health_results: Dict[str, Any]):
        """ตรวจสอบ health check results และสร้าง alerts"""
        try:
            for check_name, result in health_results["checks"].items():
                if result["status"] in [HealthStatus.UNHEALTHY.value, HealthStatus.CRITICAL.value]:
                    severity = AlertSeverity.CRITICAL if result["status"] == HealthStatus.CRITICAL.value else AlertSeverity.HIGH
                    
                    self.alert_manager.create_alert(
                        title=f"Health Check Failed: {check_name}",
                        description=f"Health check '{check_name}' failed: {result.get('error', 'Unknown error')}",
                        severity=severity,
                        source="health_checker",
                        metric_name=f"health.{check_name}",
                        current_value=0,  # 0 = failed
                        threshold_value=1  # 1 = healthy
                    )
                    
        except Exception as e:
            logger.error(f"Health alert checking error: {e}")
    
    def stop(self):
        """หยุดระบบ monitoring"""
        logger.info("Stopping monitoring system...")
        self.monitoring_active = False
        
        # รอให้ threads หยุด
        for thread in self.monitoring_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        # Flush metrics ที่เหลือ
        self.metrics_collector._flush_metrics_to_db()
        
        logger.info("Monitoring system stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """ดึงสถานะระบบโดยรวม"""
        try:
            health_results = self.health_checker.run_all_checks()
            active_alerts = self.alert_manager.get_active_alerts()
            
            # คำนวณ metrics สรุป
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            cpu_metrics = self.metrics_collector.get_metrics(
                "system.cpu.usage_percent", start_time, end_time
            )
            memory_metrics = self.metrics_collector.get_metrics(
                "system.memory.usage_percent", start_time, end_time
            )
            
            avg_cpu = statistics.mean([m.value for m in cpu_metrics]) if cpu_metrics else 0
            avg_memory = statistics.mean([m.value for m in memory_metrics]) if memory_metrics else 0
            
            return {
                "timestamp": datetime.now(),
                "overall_health": health_results["overall_status"],
                "active_alerts_count": len(active_alerts),
                "critical_alerts_count": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "metrics_summary": {
                    "avg_cpu_usage": round(avg_cpu, 1),
                    "avg_memory_usage": round(avg_memory, 1),
                    "metrics_collected": len(cpu_metrics) + len(memory_metrics)
                },
                "health_checks": {
                    "total": len(health_results["checks"]),
                    "healthy": len([c for c in health_results["checks"].values() if c["status"] == "healthy"]),
                    "unhealthy": len([c for c in health_results["checks"].values() if c["status"] != "healthy"])
                },
                "monitoring_active": self.monitoring_active
            }
            
        except Exception as e:
            logger.error(f"System status error: {e}")
            return {"error": str(e)}

# === Main Function ===

def main():
    """ทดสอบการทำงานของ Monitoring System"""
    print("📊 Testing Monitoring System...")
    
    # สร้าง config
    config = MonitoringConfig()
    
    # สร้าง Monitoring System
    monitoring = MonitoringSystem(config)
    
    try:
        # เริ่มต้นระบบ monitoring
        monitoring.start()
        
        print("✅ Monitoring system started successfully!")
        print(f"📊 Dashboard available at: http://localhost:{config.dashboard_port}")
        print(f"🔍 WebSocket available at: ws://localhost:{config.websocket_port}/ws")
        
        # ทดสอบการสร้าง alert
        print("\n🚨 Testing alert creation...")
        monitoring.alert_manager.create_alert(
            title="Test Alert",
            description="This is a test alert for monitoring system",
            severity=AlertSeverity.MEDIUM,
            source="test_system",
            metric_name="test.metric",
            current_value=85.0,
            threshold_value=80.0
        )
        
        # แสดงสถานะระบบ
        print("\n📈 System Status:")
        status = monitoring.get_system_status()
        for key, value in status.items():
            if key != "timestamp":
                print(f"  {key}: {value}")
        
        # รอให้ระบบทำงาน
        print("\n⏳ Monitoring system is running...")
        print("Press Ctrl+C to stop")
        
        while True:
            time.sleep(10)
            
            # แสดงสถานะทุก 10 วินาที
            status = monitoring.get_system_status()
            print(f"🔄 Health: {status.get('overall_health', 'unknown')} | "
                  f"Alerts: {status.get('active_alerts_count', 0)} | "
                  f"CPU: {status.get('metrics_summary', {}).get('avg_cpu_usage', 0)}%")
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring system...")
        monitoring.stop()
        print("✅ Monitoring system stopped successfully!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        monitoring.stop()

if __name__ == "__main__":
    main()