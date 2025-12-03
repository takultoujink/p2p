"""
Real-time Analytics System
WebSocket-based real-time data streaming and analytics
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import websockets
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RealTimeMetric:
    """Real-time metric data structure"""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "value": self.value,
            "tags": self.tags,
            "metadata": self.metadata
        }

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "ne"
    threshold: float
    duration: int  # seconds
    severity: str = "warning"  # "info", "warning", "error", "critical"
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """Evaluate if alert condition is met"""
        if not self.enabled:
            return False
            
        if self.condition == "gt":
            return value > self.threshold
        elif self.condition == "lt":
            return value < self.threshold
        elif self.condition == "eq":
            return value == self.threshold
        elif self.condition == "ne":
            return value != self.threshold
        else:
            return False

class MetricBuffer:
    """Thread-safe metric buffer with time-based windowing"""
    
    def __init__(self, max_size: int = 1000, window_size: int = 300):
        self.max_size = max_size
        self.window_size = window_size  # seconds
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add_metric(self, metric: RealTimeMetric):
        """Add metric to buffer"""
        with self.lock:
            self.buffer.append(metric)
            self._cleanup_old_metrics()
    
    def get_metrics(self, metric_name: Optional[str] = None, 
                   since: Optional[datetime] = None) -> List[RealTimeMetric]:
        """Get metrics from buffer"""
        with self.lock:
            metrics = list(self.buffer)
            
            if metric_name:
                metrics = [m for m in metrics if m.metric_name == metric_name]
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return metrics
    
    def get_latest_value(self, metric_name: str) -> Optional[float]:
        """Get latest value for metric"""
        with self.lock:
            for metric in reversed(self.buffer):
                if metric.metric_name == metric_name:
                    return metric.value
            return None
    
    def get_aggregated_value(self, metric_name: str, 
                           aggregation: str = "avg",
                           window_seconds: int = 60) -> Optional[float]:
        """Get aggregated value over time window"""
        since = datetime.now() - timedelta(seconds=window_seconds)
        metrics = self.get_metrics(metric_name, since)
        
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        if aggregation == "avg":
            return np.mean(values)
        elif aggregation == "sum":
            return np.sum(values)
        elif aggregation == "min":
            return np.min(values)
        elif aggregation == "max":
            return np.max(values)
        elif aggregation == "count":
            return len(values)
        else:
            return None
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than window size"""
        cutoff_time = datetime.now() - timedelta(seconds=self.window_size)
        while self.buffer and self.buffer[0].timestamp < cutoff_time:
            self.buffer.popleft()

class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # client_id -> metric_names
        self.lock = threading.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        with self.lock:
            self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        with self.lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.subscriptions:
                del self.subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    def subscribe(self, client_id: str, metric_names: List[str]):
        """Subscribe client to specific metrics"""
        with self.lock:
            self.subscriptions[client_id].update(metric_names)
        logger.info(f"Client {client_id} subscribed to {metric_names}")
    
    def unsubscribe(self, client_id: str, metric_names: List[str]):
        """Unsubscribe client from specific metrics"""
        with self.lock:
            self.subscriptions[client_id].difference_update(metric_names)
        logger.info(f"Client {client_id} unsubscribed from {metric_names}")
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        with self.lock:
            websocket = self.active_connections.get(client_id)
        
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_metric(self, metric: RealTimeMetric):
        """Broadcast metric to subscribed clients"""
        message = {
            "type": "metric_update",
            "data": metric.to_dict()
        }
        
        with self.lock:
            clients_to_notify = [
                client_id for client_id, metrics in self.subscriptions.items()
                if metric.metric_name in metrics
            ]
        
        # Send to subscribed clients
        for client_id in clients_to_notify:
            await self.send_to_client(client_id, message)
    
    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast alert to all connected clients"""
        message = {
            "type": "alert",
            "data": alert
        }
        
        with self.lock:
            client_ids = list(self.active_connections.keys())
        
        for client_id in client_ids:
            await self.send_to_client(client_id, message)

class AlertManager:
    """Real-time alert management system"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_states: Dict[str, Dict[str, Any]] = {}  # rule_name -> state
        self.lock = threading.Lock()
    
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        with self.lock:
            self.alert_rules[rule.name] = rule
            self.alert_states[rule.name] = {
                "triggered": False,
                "trigger_time": None,
                "last_value": None
            }
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule"""
        with self.lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
            if rule_name in self.alert_states:
                del self.alert_states[rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
    
    async def evaluate_metric(self, metric: RealTimeMetric):
        """Evaluate metric against alert rules"""
        with self.lock:
            rules_to_check = [
                rule for rule in self.alert_rules.values()
                if rule.metric_name == metric.metric_name
            ]
        
        for rule in rules_to_check:
            await self._evaluate_rule(rule, metric)
    
    async def _evaluate_rule(self, rule: AlertRule, metric: RealTimeMetric):
        """Evaluate single alert rule"""
        current_time = datetime.now()
        condition_met = rule.evaluate(metric.value)
        
        with self.lock:
            state = self.alert_states[rule.name]
            state["last_value"] = metric.value
        
        if condition_met and not state["triggered"]:
            # Condition just became true
            state["trigger_time"] = current_time
            state["triggered"] = True
            
            # Check if duration threshold is met
            if rule.duration == 0:
                await self._fire_alert(rule, metric, "triggered")
        
        elif condition_met and state["triggered"]:
            # Condition still true, check duration
            if state["trigger_time"]:
                duration = (current_time - state["trigger_time"]).total_seconds()
                if duration >= rule.duration:
                    await self._fire_alert(rule, metric, "ongoing")
        
        elif not condition_met and state["triggered"]:
            # Condition became false
            state["triggered"] = False
            state["trigger_time"] = None
            await self._fire_alert(rule, metric, "resolved")
    
    async def _fire_alert(self, rule: AlertRule, metric: RealTimeMetric, status: str):
        """Fire alert"""
        alert = {
            "rule_name": rule.name,
            "metric_name": rule.metric_name,
            "status": status,
            "severity": rule.severity,
            "threshold": rule.threshold,
            "current_value": metric.value,
            "timestamp": datetime.now().isoformat(),
            "message": f"Alert {status}: {rule.name} - {rule.metric_name} is {metric.value} (threshold: {rule.threshold})"
        }
        
        logger.warning(f"Alert fired: {alert}")
        await self.connection_manager.broadcast_alert(alert)

class DataProcessor:
    """Real-time data processing and aggregation"""
    
    def __init__(self, metric_buffer: MetricBuffer):
        self.metric_buffer = metric_buffer
        self.aggregation_rules: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def add_aggregation_rule(self, name: str, source_metric: str, 
                           aggregation: str, window_seconds: int, 
                           output_metric: str):
        """Add aggregation rule"""
        self.aggregation_rules[name] = {
            "source_metric": source_metric,
            "aggregation": aggregation,
            "window_seconds": window_seconds,
            "output_metric": output_metric,
            "last_calculated": datetime.now()
        }
        logger.info(f"Added aggregation rule: {name}")
    
    async def process_metric(self, metric: RealTimeMetric) -> List[RealTimeMetric]:
        """Process incoming metric and generate derived metrics"""
        derived_metrics = []
        
        # Add to buffer
        self.metric_buffer.add_metric(metric)
        
        # Calculate aggregations
        for rule_name, rule in self.aggregation_rules.items():
            if rule["source_metric"] == metric.metric_name:
                # Check if it's time to calculate
                now = datetime.now()
                time_since_last = (now - rule["last_calculated"]).total_seconds()
                
                if time_since_last >= 10:  # Calculate every 10 seconds
                    aggregated_value = self.metric_buffer.get_aggregated_value(
                        rule["source_metric"],
                        rule["aggregation"],
                        rule["window_seconds"]
                    )
                    
                    if aggregated_value is not None:
                        derived_metric = RealTimeMetric(
                            timestamp=now,
                            metric_name=rule["output_metric"],
                            value=aggregated_value,
                            tags={"aggregation": rule["aggregation"], "window": str(rule["window_seconds"])},
                            metadata={"source_metric": rule["source_metric"], "rule": rule_name}
                        )
                        derived_metrics.append(derived_metric)
                        rule["last_calculated"] = now
        
        return derived_metrics

class RealTimeAnalyticsEngine:
    """Main real-time analytics engine"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.metric_buffer = MetricBuffer()
        self.connection_manager = ConnectionManager()
        self.alert_manager = AlertManager(self.connection_manager)
        self.data_processor = DataProcessor(self.metric_buffer)
        self.running = False
        self.background_tasks = []
        
        # Setup FastAPI app
        self.app = FastAPI(title="Real-time Analytics API")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    async def start(self):
        """Start the analytics engine"""
        self.running = True
        
        # Connect to Redis
        self.redis_client = redis.from_url(self.redis_url)
        
        # Setup default alert rules
        self._setup_default_alerts()
        
        # Setup default aggregation rules
        self._setup_default_aggregations()
        
        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._redis_subscriber()),
            asyncio.create_task(self._health_monitor()),
            asyncio.create_task(self._cleanup_task())
        ]
        
        logger.info("Real-time analytics engine started")
    
    async def stop(self):
        """Stop the analytics engine"""
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Real-time analytics engine stopped")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await self.connection_manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self._handle_websocket_message(client_id, message)
            except WebSocketDisconnect:
                self.connection_manager.disconnect(client_id)
        
        @self.app.post("/metrics")
        async def submit_metric(metric_data: Dict[str, Any]):
            """Submit metric via HTTP"""
            metric = RealTimeMetric(
                timestamp=datetime.fromisoformat(metric_data.get("timestamp", datetime.now().isoformat())),
                metric_name=metric_data["metric_name"],
                value=float(metric_data["value"]),
                tags=metric_data.get("tags", {}),
                metadata=metric_data.get("metadata", {})
            )
            
            await self._process_metric(metric)
            return {"status": "success"}
        
        @self.app.get("/metrics/{metric_name}/latest")
        async def get_latest_metric(metric_name: str):
            """Get latest value for metric"""
            value = self.metric_buffer.get_latest_value(metric_name)
            return {"metric_name": metric_name, "value": value}
        
        @self.app.get("/metrics/{metric_name}/history")
        async def get_metric_history(metric_name: str, minutes: int = 60):
            """Get metric history"""
            since = datetime.now() - timedelta(minutes=minutes)
            metrics = self.metric_buffer.get_metrics(metric_name, since)
            return {
                "metric_name": metric_name,
                "data": [m.to_dict() for m in metrics]
            }
        
        @self.app.post("/alerts/rules")
        async def add_alert_rule(rule_data: Dict[str, Any]):
            """Add alert rule"""
            rule = AlertRule(**rule_data)
            self.alert_manager.add_alert_rule(rule)
            return {"status": "success", "rule_name": rule.name}
        
        @self.app.delete("/alerts/rules/{rule_name}")
        async def remove_alert_rule(rule_name: str):
            """Remove alert rule"""
            self.alert_manager.remove_alert_rule(rule_name)
            return {"status": "success"}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_connections": len(self.connection_manager.active_connections),
                "metrics_in_buffer": len(self.metric_buffer.buffer),
                "alert_rules": len(self.alert_manager.alert_rules)
            }
    
    async def _handle_websocket_message(self, client_id: str, message: Dict[str, Any]):
        """Handle WebSocket message from client"""
        message_type = message.get("type")
        
        if message_type == "subscribe":
            metric_names = message.get("metrics", [])
            self.connection_manager.subscribe(client_id, metric_names)
        
        elif message_type == "unsubscribe":
            metric_names = message.get("metrics", [])
            self.connection_manager.unsubscribe(client_id, metric_names)
        
        elif message_type == "get_latest":
            metric_name = message.get("metric_name")
            if metric_name:
                value = self.metric_buffer.get_latest_value(metric_name)
                await self.connection_manager.send_to_client(client_id, {
                    "type": "latest_value",
                    "metric_name": metric_name,
                    "value": value
                })
    
    async def _redis_subscriber(self):
        """Subscribe to Redis for incoming metrics"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("analytics:metrics")
        
        try:
            while self.running:
                message = await pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        metric = RealTimeMetric(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            metric_name=data["metric_name"],
                            value=data["value"],
                            tags=data.get("tags", {}),
                            metadata=data.get("metadata", {})
                        )
                        await self._process_metric(metric)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        finally:
            await pubsub.unsubscribe("analytics:metrics")
    
    async def _process_metric(self, metric: RealTimeMetric):
        """Process incoming metric"""
        # Process metric and get derived metrics
        derived_metrics = await self.data_processor.process_metric(metric)
        
        # Evaluate alerts for original metric
        await self.alert_manager.evaluate_metric(metric)
        
        # Broadcast original metric
        await self.connection_manager.broadcast_metric(metric)
        
        # Process derived metrics
        for derived_metric in derived_metrics:
            await self.alert_manager.evaluate_metric(derived_metric)
            await self.connection_manager.broadcast_metric(derived_metric)
    
    async def _health_monitor(self):
        """Monitor system health"""
        while self.running:
            try:
                # Generate system health metrics
                health_metrics = [
                    RealTimeMetric(
                        timestamp=datetime.now(),
                        metric_name="system.connections",
                        value=len(self.connection_manager.active_connections),
                        tags={"component": "websocket"}
                    ),
                    RealTimeMetric(
                        timestamp=datetime.now(),
                        metric_name="system.buffer_size",
                        value=len(self.metric_buffer.buffer),
                        tags={"component": "buffer"}
                    ),
                    RealTimeMetric(
                        timestamp=datetime.now(),
                        metric_name="system.alert_rules",
                        value=len(self.alert_manager.alert_rules),
                        tags={"component": "alerts"}
                    )
                ]
                
                for metric in health_metrics:
                    await self._process_metric(metric)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_task(self):
        """Cleanup old data periodically"""
        while self.running:
            try:
                # Cleanup is handled by MetricBuffer automatically
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                metric_name="api.error_rate",
                condition="gt",
                threshold=0.05,
                duration=300,
                severity="warning"
            ),
            AlertRule(
                name="slow_response_time",
                metric_name="api.response_time_avg",
                condition="gt",
                threshold=2.0,
                duration=300,
                severity="warning"
            ),
            AlertRule(
                name="low_detection_accuracy",
                metric_name="detection.accuracy_avg",
                condition="lt",
                threshold=0.9,
                duration=600,
                severity="error"
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="system.memory_usage",
                condition="gt",
                threshold=0.9,
                duration=300,
                severity="critical"
            )
        ]
        
        for rule in default_rules:
            self.alert_manager.add_alert_rule(rule)
    
    def _setup_default_aggregations(self):
        """Setup default aggregation rules"""
        aggregations = [
            ("response_time_avg", "api.response_time", "avg", 300, "api.response_time_avg"),
            ("error_rate_avg", "api.error_rate", "avg", 300, "api.error_rate_avg"),
            ("detection_accuracy_avg", "detection.accuracy", "avg", 600, "detection.accuracy_avg"),
            ("requests_per_minute", "api.requests", "count", 60, "api.requests_per_minute")
        ]
        
        for name, source, agg, window, output in aggregations:
            self.data_processor.add_aggregation_rule(name, source, agg, window, output)

async def main():
    """Main function"""
    # Create analytics engine
    engine = RealTimeAnalyticsEngine()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(engine.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start engine
        await engine.start()
        
        # Run FastAPI server
        config = uvicorn.Config(
            app=engine.app,
            host="0.0.0.0",
            port=8051,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info("Starting real-time analytics server on http://0.0.0.0:8051")
        await server.serve()
        
    except Exception as e:
        logger.error(f"Error running analytics engine: {e}")
    finally:
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())