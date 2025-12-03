# 📊 Analytics Dashboard

ระบบ Analytics Dashboard ที่ครอบคลุมสำหรับ AI Detection System พร้อมการวิเคราะห์แบบ Real-time, Business Intelligence และ User Behavior Analytics

## 🌟 คุณสมบัติหลัก

### 📈 Usage Statistics
- **Request Analytics**: ติดตามจำนวน requests, response time, error rate
- **User Analytics**: วิเคราะห์ unique users, session duration, user patterns
- **Endpoint Analytics**: สถิติการใช้งาน API endpoints ต่างๆ
- **Geographic Analytics**: การกระจายของผู้ใช้ตามภูมิศาสตร์

### 🎯 Detection Accuracy Metrics
- **Model Performance**: ประสิทธิภาพของ AI models แต่ละตัว
- **Accuracy Tracking**: ติดตาม accuracy, precision, recall
- **Confidence Analysis**: การวิเคราะห์ confidence scores
- **Error Analysis**: False positives/negatives tracking

### 👥 User Behavior Analysis
- **Session Analytics**: ระยะเวลาการใช้งาน, page views
- **Device Analytics**: การกระจายของ device types และ browsers
- **User Journey**: การติดตาม user flow และ conversion
- **Engagement Metrics**: การวัด user engagement

### 💰 Business Intelligence
- **Revenue Tracking**: ติดตามรายได้และต้นทุน
- **ROI Analysis**: การวิเคราะห์ Return on Investment
- **Cost Breakdown**: การแยกต้นทุนตามหมวดหมู่
- **Profit Analysis**: การวิเคราะห์กำไรและแนวโน้ม

### ⚡ Real-time Analytics
- **Live Data Streaming**: ข้อมูลแบบ real-time ผ่าน WebSocket
- **Real-time Alerts**: การแจ้งเตือนทันทีเมื่อมีปัญหา
- **Live Dashboards**: Dashboard ที่อัปเดตแบบ real-time
- **Event Streaming**: การประมวลผล events แบบ streaming

## 🏗️ โครงสร้างโปรเจกต์

```
21_Analytics_Dashboard/
├── analytics_dashboard.py      # Main dashboard application
├── dashboard_config.py         # Configuration management
├── real_time_analytics.py      # Real-time analytics engine
├── requirements.txt           # Dependencies
├── README.md                 # Documentation
├── config/                   # Configuration files
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── templates/               # Dashboard templates
│   ├── dashboard.html
│   ├── charts.html
│   └── alerts.html
├── static/                 # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── tests/                  # Test files
│   ├── test_dashboard.py
│   ├── test_analytics.py
│   └── test_config.py
└── docs/                   # Additional documentation
    ├── api.md
    ├── deployment.md
    └── troubleshooting.md
```

## 🚀 การติดตั้ง

### 1. Dependencies

```bash
# ติดตั้ง Python dependencies
pip install -r requirements.txt

# ติดตั้ง Redis (สำหรับ real-time analytics)
# Windows (ใช้ Docker)
docker run -d -p 6379:6379 redis:alpine

# หรือติดตั้งผ่าน Chocolatey
choco install redis-64
```

### 2. Database Setup

```bash
# สร้าง database (SQLite - default)
python analytics_dashboard.py --setup-db

# หรือใช้ PostgreSQL
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_USER=analytics_user
export DB_PASSWORD=your_password
export DB_NAME=analytics_db
```

### 3. Configuration

```bash
# สร้างไฟล์ configuration เริ่มต้น
python dashboard_config.py --create-defaults

# แก้ไขไฟล์ config/development.yaml ตามต้องการ
```

## 📊 การใช้งาน

### 1. การเริ่มต้น Dashboard

```python
from analytics_dashboard import DashboardApp, AnalyticsConfig

# สร้าง configuration
config = AnalyticsConfig(
    dashboard_port=8050,
    database_url="sqlite:///analytics.db",
    redis_url="redis://localhost:6379"
)

# เริ่มต้น dashboard
app = DashboardApp(config)
app.run(debug=True)
```

### 2. การเริ่มต้น Real-time Analytics

```python
from real_time_analytics import RealTimeAnalyticsEngine
import asyncio

async def main():
    engine = RealTimeAnalyticsEngine()
    await engine.start()
    
    # รัน server
    import uvicorn
    config = uvicorn.Config(app=engine.app, host="0.0.0.0", port=8051)
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
```

### 3. การส่งข้อมูล Metrics

```python
import requests
import json
from datetime import datetime

# ส่ง usage statistics
usage_data = {
    "user_id": "user_123",
    "endpoint": "/detect",
    "method": "POST",
    "response_time": 1.5,
    "status_code": 200,
    "user_agent": "Chrome/91.0",
    "ip_address": "192.168.1.100"
}

# ส่งผ่าน HTTP API
response = requests.post("http://localhost:8051/metrics", json={
    "metric_name": "api.response_time",
    "value": 1.5,
    "timestamp": datetime.now().isoformat(),
    "tags": {"endpoint": "/detect", "method": "POST"}
})
```

## 🎨 Dashboard Types

### 1. Dash Dashboard (Default)

```bash
# เริ่มต้น Dash dashboard
python analytics_dashboard.py

# เข้าถึงที่ http://localhost:8050
```

### 2. Streamlit Dashboard

```bash
# เริ่มต้น Streamlit dashboard
streamlit run analytics_dashboard.py

# เข้าถึงที่ http://localhost:8501
```

### 3. Custom Dashboard

```python
from analytics_dashboard import ChartGenerator, MetricsCalculator

# สร้าง custom charts
chart_generator = ChartGenerator()
metrics = {"total_requests": 1000, "avg_response_time": 1.2}
chart = chart_generator.create_usage_chart(metrics)

# แสดงผลใน Jupyter Notebook
chart.show()
```

## ⚙️ การกำหนดค่า

### 1. Environment Variables

```bash
# Database
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=analytics
export DB_USER=analytics_user
export DB_PASSWORD=secure_password

# Cache
export CACHE_TYPE=redis
export CACHE_HOST=localhost
export CACHE_PORT=6379

# Security
export SECRET_KEY=your-super-secret-key
export JWT_ALGORITHM=HS256

# Dashboard
export DASHBOARD_THEME=bootstrap
export DASHBOARD_TITLE="AI Analytics Dashboard"
```

### 2. Configuration File (YAML)

```yaml
# config/production.yaml
environment: production
debug: false
host: "0.0.0.0"
port: 8050

database:
  type: postgresql
  host: db.example.com
  port: 5432
  database: analytics_prod
  username: analytics_user
  password: ${DB_PASSWORD}
  pool_size: 20

cache:
  type: redis
  host: redis.example.com
  port: 6379
  password: ${REDIS_PASSWORD}
  ttl: 300

security:
  secret_key: ${SECRET_KEY}
  cors_origins:
    - "https://yourdomain.com"
  rate_limit: "1000/minute"
  enable_https: true

dashboard:
  theme: bootstrap
  title: "Production Analytics"
  auto_refresh: true
  refresh_interval: 30

alerting:
  enable_alerts: true
  email_alerts: true
  email_to:
    - "admin@yourdomain.com"
    - "ops@yourdomain.com"
```

## 📡 Real-time Features

### 1. WebSocket Connection

```javascript
// JavaScript client
const ws = new WebSocket('ws://localhost:8051/ws/client_123');

// Subscribe to metrics
ws.send(JSON.stringify({
    type: 'subscribe',
    metrics: ['api.response_time', 'detection.accuracy']
}));

// Handle incoming data
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'metric_update') {
        updateChart(data.data);
    } else if (data.type === 'alert') {
        showAlert(data.data);
    }
};
```

### 2. Alert Rules

```python
from real_time_analytics import AlertRule

# สร้าง alert rule
rule = AlertRule(
    name="high_error_rate",
    metric_name="api.error_rate",
    condition="gt",
    threshold=0.05,
    duration=300,  # 5 minutes
    severity="warning"
)

# เพิ่ม rule ผ่าน API
requests.post("http://localhost:8051/alerts/rules", json={
    "name": "high_error_rate",
    "metric_name": "api.error_rate",
    "condition": "gt",
    "threshold": 0.05,
    "duration": 300,
    "severity": "warning"
})
```

### 3. Data Aggregation

```python
# เพิ่ม aggregation rule
engine.data_processor.add_aggregation_rule(
    name="response_time_avg_5m",
    source_metric="api.response_time",
    aggregation="avg",
    window_seconds=300,
    output_metric="api.response_time_5m_avg"
)
```

## 📊 Chart Types

### 1. Usage Charts
- **Time Series**: Request volume over time
- **Gauge Charts**: Response time, error rate
- **Bar Charts**: Top endpoints, status codes
- **Heatmaps**: Request patterns by time

### 2. Detection Charts
- **Accuracy Trends**: Model accuracy over time
- **Confidence Distribution**: Histogram of confidence scores
- **Model Comparison**: Performance comparison charts
- **Error Analysis**: False positive/negative rates

### 3. User Behavior Charts
- **Pie Charts**: Device/browser distribution
- **Funnel Charts**: User conversion flow
- **Cohort Analysis**: User retention
- **Geographic Maps**: User distribution

### 4. Business Charts
- **Revenue Trends**: Revenue over time
- **Cost Breakdown**: Cost by category
- **ROI Analysis**: Return on investment
- **Profit/Loss**: Financial performance

## 🔧 API Endpoints

### Analytics API

```bash
# Submit metric
POST /metrics
{
    "metric_name": "api.response_time",
    "value": 1.5,
    "timestamp": "2024-01-01T12:00:00Z",
    "tags": {"endpoint": "/detect"},
    "metadata": {"user_id": "123"}
}

# Get latest metric value
GET /metrics/{metric_name}/latest

# Get metric history
GET /metrics/{metric_name}/history?minutes=60

# Health check
GET /health
```

### Alert API

```bash
# Add alert rule
POST /alerts/rules
{
    "name": "high_error_rate",
    "metric_name": "api.error_rate",
    "condition": "gt",
    "threshold": 0.05,
    "duration": 300,
    "severity": "warning"
}

# Remove alert rule
DELETE /alerts/rules/{rule_name}

# List alert rules
GET /alerts/rules
```

## 🚀 การ Deploy

### 1. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8050 8051

CMD ["python", "analytics_dashboard.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  analytics-dashboard:
    build: .
    ports:
      - "8050:8050"
      - "8051:8051"
    environment:
      - DB_TYPE=postgresql
      - DB_HOST=postgres
      - CACHE_TYPE=redis
      - CACHE_HOST=redis
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: analytics
      POSTGRES_USER: analytics_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 2. Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytics-dashboard
  template:
    metadata:
      labels:
        app: analytics-dashboard
    spec:
      containers:
      - name: dashboard
        image: analytics-dashboard:latest
        ports:
        - containerPort: 8050
        - containerPort: 8051
        env:
        - name: DB_TYPE
          value: "postgresql"
        - name: DB_HOST
          value: "postgres-service"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: analytics-dashboard-service
spec:
  selector:
    app: analytics-dashboard
  ports:
  - name: dashboard
    port: 8050
    targetPort: 8050
  - name: api
    port: 8051
    targetPort: 8051
  type: LoadBalancer
```

## 🔍 การตรวจสอบและปรับปรุงประสิทธิภาพ

### 1. Performance Monitoring

```python
# เปิดใช้งาน performance monitoring
config.performance.enable_caching = True
config.performance.enable_compression = True
config.performance.chart_data_limit = 1000

# ตรวจสอบ memory usage
import psutil
memory_usage = psutil.virtual_memory().percent
```

### 2. Database Optimization

```python
# Connection pooling
config.database.pool_size = 20
config.database.max_overflow = 30
config.database.pool_timeout = 30

# Query optimization
config.performance.enable_query_cache = True
config.performance.query_timeout = 30
```

### 3. Caching Strategy

```python
# Redis caching
config.cache.ttl = 300  # 5 minutes
config.performance.enable_chart_caching = True
config.performance.chart_cache_ttl = 60
```

## 🔐 Security

### 1. Authentication & Authorization

```python
# JWT authentication
config.security.jwt_algorithm = "HS256"
config.security.jwt_expiration = 3600

# CORS configuration
config.security.cors_origins = ["https://yourdomain.com"]
config.security.cors_methods = ["GET", "POST"]
```

### 2. Rate Limiting

```python
# API rate limiting
config.security.rate_limit = "100/minute"

# IP-based limiting
from slowapi import Limiter
limiter = Limiter(key_func=lambda: request.client.host)
```

### 3. Data Protection

```python
# Encrypt sensitive data
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)

# Hash user IDs
import hashlib
user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()
```

## 🧪 การทดสอบ

### 1. Unit Tests

```python
# test_dashboard.py
import pytest
from analytics_dashboard import MetricsCalculator, DataCollector

def test_metrics_calculation():
    collector = DataCollector(config)
    calculator = MetricsCalculator(collector)
    
    # Test usage metrics
    metrics = calculator.calculate_usage_metrics("24h")
    assert "total_requests" in metrics
    assert "avg_response_time" in metrics
```

### 2. Integration Tests

```python
# test_api.py
import requests

def test_metrics_api():
    response = requests.post("http://localhost:8051/metrics", json={
        "metric_name": "test.metric",
        "value": 100
    })
    assert response.status_code == 200
```

### 3. Load Testing

```python
# load_test.py
import asyncio
import aiohttp

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(1000):
            task = session.post("http://localhost:8051/metrics", json={
                "metric_name": "load.test",
                "value": i
            })
            tasks.append(task)
        
        await asyncio.gather(*tasks)

asyncio.run(load_test())
```

## 📈 การขยายระบบ

### 1. Horizontal Scaling

```yaml
# Load balancer configuration
upstream analytics_dashboard {
    server dashboard1:8050;
    server dashboard2:8050;
    server dashboard3:8050;
}

server {
    listen 80;
    location / {
        proxy_pass http://analytics_dashboard;
    }
}
```

### 2. Database Sharding

```python
# Database sharding by date
def get_database_shard(timestamp):
    month = timestamp.strftime("%Y_%m")
    return f"analytics_{month}"

# Route queries to appropriate shard
shard = get_database_shard(datetime.now())
engine = create_engine(f"postgresql://user:pass@host/{shard}")
```

### 3. Microservices Architecture

```python
# Separate services
services = {
    "metrics_collector": "http://metrics-service:8080",
    "alert_manager": "http://alerts-service:8081",
    "chart_generator": "http://charts-service:8082"
}
```

## 🔧 การแก้ไขปัญหา

### 1. ปัญหาที่พบบ่อย

**Dashboard ไม่แสดงข้อมูล**
```bash
# ตรวจสอบ database connection
python -c "from analytics_dashboard import DataCollector; DataCollector(config).engine.connect()"

# ตรวจสอบ Redis connection
redis-cli ping
```

**Real-time updates ไม่ทำงาน**
```bash
# ตรวจสอบ WebSocket connection
wscat -c ws://localhost:8051/ws/test_client

# ตรวจสอบ Redis pub/sub
redis-cli monitor
```

**Performance ช้า**
```python
# เปิดใช้งาน caching
config.performance.enable_caching = True

# ลด data points
config.performance.chart_data_limit = 500

# เพิ่ม database pool
config.database.pool_size = 30
```

### 2. Debugging

```python
# เปิดใช้งาน debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# ตรวจสอบ metrics buffer
print(f"Buffer size: {len(metric_buffer.buffer)}")
print(f"Latest metrics: {metric_buffer.get_metrics()[-5:]}")

# ตรวจสอบ WebSocket connections
print(f"Active connections: {len(connection_manager.active_connections)}")
```

## 📚 เอกสารเพิ่มเติม

- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Performance Tuning](docs/performance.md)
- [Security Best Practices](docs/security.md)

## 🤝 การมีส่วนร่วม

1. Fork repository
2. สร้าง feature branch (`git checkout -b feature/amazing-feature`)
3. Commit การเปลี่ยนแปลง (`git commit -m 'Add amazing feature'`)
4. Push ไปยัง branch (`git push origin feature/amazing-feature`)
5. เปิด Pull Request

## 📄 License

โปรเจกต์นี้ใช้ MIT License - ดูรายละเอียดใน [LICENSE](LICENSE) file

## 🆘 Support

- 📧 Email: support@analytics-dashboard.com
- 💬 Discord: [Analytics Dashboard Community](https://discord.gg/analytics)
- 📖 Documentation: [https://docs.analytics-dashboard.com](https://docs.analytics-dashboard.com)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/your-repo/analytics-dashboard/issues)

## 🙏 Acknowledgments

- [Plotly](https://plotly.com/) สำหรับ interactive charts
- [Dash](https://dash.plotly.com/) สำหรับ dashboard framework
- [FastAPI](https://fastapi.tiangolo.com/) สำหรับ API framework
- [Redis](https://redis.io/) สำหรับ real-time data streaming
- [SQLAlchemy](https://www.sqlalchemy.org/) สำหรับ database ORM