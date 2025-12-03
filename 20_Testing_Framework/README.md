# Testing Framework

ระบบทดสอบที่ครอบคลุมสำหรับ AI Detection System รองรับการทดสอบแบบ Unit, Integration, Performance และ End-to-End

## 🎯 คุณสมบัติหลัก

### 📋 ประเภทการทดสอบ
- **Unit Tests**: ทดสอบส่วนประกอบแต่ละตัวแยกกัน
- **Integration Tests**: ทดสอบการทำงานร่วมกันของส่วนประกอบ
- **Performance Tests**: ทดสอบประสิทธิภาพและความเร็ว
- **End-to-End Tests**: ทดสอบระบบทั้งหมดผ่าน Browser

### 🔧 เครื่องมือทดสอบ
- **pytest**: Framework หลักสำหรับการทดสอบ
- **Selenium**: Browser automation สำหรับ E2E testing
- **Locust**: Load testing และ Performance testing
- **Memory Profiler**: ตรวจสอบการใช้หน่วยความจำ
- **Coverage**: วัดความครอบคลุมของการทดสอบ

### 📊 การรายงานผล
- **HTML Reports**: รายงานแบบ Interactive
- **JSON Reports**: ข้อมูลสำหรับการวิเคราะห์
- **XML Reports**: รองรับ CI/CD systems
- **Performance Metrics**: กราฟและสถิติประสิทธิภาพ

## 📁 โครงสร้างโปรเจกต์

```
20_Testing_Framework/
├── test_framework.py          # Framework หลัก
├── test_config.py            # การจัดการ Configuration
├── requirements.txt          # Dependencies
├── README.md                # เอกสารนี้
├── test_data/               # ข้อมูลทดสอบ
│   ├── images/             # รูปภาพสำหรับทดสอบ
│   ├── videos/             # วิดีโอสำหรับทดสอบ
│   ├── fixtures/           # ข้อมูล Mock
│   └── mocks/              # Mock responses
├── test_results/           # ผลการทดสอบ
│   ├── reports/           # รายงาน HTML/JSON
│   ├── screenshots/       # ภาพหน้าจอจาก E2E tests
│   └── logs/              # Log files
└── configs/               # ไฟล์ Configuration
    ├── test_config.yaml   # Configuration หลัก
    ├── ci_config.yaml     # Configuration สำหรับ CI
    └── perf_config.yaml   # Configuration สำหรับ Performance
```

## 🚀 การติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 2. ติดตั้ง Browser Drivers

```bash
# Chrome Driver (จัดการอัตโนมัติโดย webdriver-manager)
# หรือติดตั้งด้วยตนเอง
pip install webdriver-manager
```

### 3. ตั้งค่า Environment Variables

```bash
# API Configuration
export API_BASE_URL="http://localhost:8000"
export DATABASE_URL="sqlite:///test.db"

# Browser Configuration
export BROWSER_HEADLESS="true"
export BROWSER_TYPE="chrome"

# Performance Configuration
export CONCURRENT_USERS="10"
export TEST_DURATION="300"

# CI Configuration
export CI="true"  # สำหรับ CI environments
```

## 📖 การใช้งาน

### การทดสอบพื้นฐาน

```python
from test_framework import TestFramework
from test_config import TestConfig, create_default_config

# สร้าง Configuration
config = create_default_config()

# สร้าง Testing Framework
framework = TestFramework(config)

# รันการทดสอบทั้งหมด
results = framework.run_all_tests()

# แสดงผลสรุป
print(f"Total Tests: {results['total_tests']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Success Rate: {results['success_rate']:.2%}")
```

### การทดสอบแต่ละประเภท

```python
# Unit Tests เท่านั้น
unit_results = framework.run_unit_tests()

# Integration Tests เท่านั้น
integration_results = framework.run_integration_tests()

# Performance Tests เท่านั้น
performance_results = framework.run_performance_tests()

# E2E Tests เท่านั้น
e2e_results = framework.run_e2e_tests()
```

### การใช้งานผ่าน Command Line

```bash
# รันการทดสอบทั้งหมด
python test_framework.py

# รันการทดสอบเฉพาะประเภท
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m performance
pytest tests/ -m e2e

# รันการทดสอบแบบ Parallel
pytest tests/ -n auto

# สร้างรายงาน Coverage
pytest tests/ --cov=src --cov-report=html
```

## ⚙️ การกำหนดค่า

### การสร้าง Configuration

```python
from test_config import TestConfig, TestEnvironment, TestType

# Configuration พื้นฐาน
config = TestConfig(
    environment=TestEnvironment.DEVELOPMENT,
    enabled_test_types=[TestType.UNIT, TestType.INTEGRATION]
)

# กำหนดค่า API
config.api.base_url = "http://localhost:8000"
config.api.timeout = 30

# กำหนดค่า Performance Thresholds
config.performance.response_time_ms = 2000
config.performance.memory_usage_mb = 500
config.performance.accuracy_threshold = 0.95

# กำหนดค่า Load Testing
config.load_test.concurrent_users = 50
config.load_test.test_duration = 600

# บันทึก Configuration
config.save_to_yaml_file("my_test_config.yaml")
```

### การโหลด Configuration จากไฟล์

```python
# จาก YAML
config = TestConfig.from_yaml_file("test_config.yaml")

# จาก JSON
config = TestConfig.from_json_file("test_config.json")

# จาก Environment Variables
config = load_config_from_environment()
```

### ตัวอย่าง Configuration File (YAML)

```yaml
environment: development
enabled_test_types:
  - unit
  - integration
  - performance

api:
  base_url: "http://localhost:8000"
  timeout: 30
  retry_attempts: 3

performance:
  response_time_ms: 2000.0
  memory_usage_mb: 500.0
  cpu_usage_percent: 80.0
  accuracy_threshold: 0.95

load_test:
  concurrent_users: 10
  test_duration: 300
  requests_per_user: 100

browser:
  browser_type: chrome
  headless: true
  window_width: 1920
  window_height: 1080

reporting:
  output_path: "test_results"
  report_format: ["json", "html", "xml"]
  include_screenshots: true
```

## 🧪 การเขียน Tests

### Unit Test Example

```python
import pytest
from test_framework import UnitTestSuite
from test_config import create_default_config

class TestImageProcessing:
    def setup_method(self):
        self.config = create_default_config()
        self.unit_suite = UnitTestSuite(self.config)
    
    def test_image_resize(self):
        result = self.unit_suite.test_image_preprocessing()
        assert result.status == "passed"
        assert result.metrics["operations_tested"] == 3
    
    def test_model_inference(self):
        result = self.unit_suite.test_model_inference()
        assert result.status == "passed"
        assert "inference_time" in result.metrics
```

### Integration Test Example

```python
import pytest
import requests
from test_framework import IntegrationTestSuite

class TestAPIIntegration:
    def setup_method(self):
        self.config = create_default_config()
        self.integration_suite = IntegrationTestSuite(self.config)
    
    def test_detection_endpoint(self):
        # Test data
        test_data = {
            "image": "base64_encoded_image",
            "confidence_threshold": 0.8
        }
        
        # Make request
        response = requests.post(
            f"{self.config.api.base_url}/detect",
            json=test_data
        )
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert "detections" in result
        assert "confidence" in result
```

### Performance Test Example

```python
import time
import pytest
from test_framework import PerformanceTestSuite

class TestPerformance:
    def setup_method(self):
        self.config = create_default_config()
        self.perf_suite = PerformanceTestSuite(self.config)
    
    def test_response_time_benchmark(self):
        result = self.perf_suite.test_response_time()
        
        # Check if response time meets threshold
        avg_time = result.metrics["avg_response_time"]
        threshold = self.config.performance.response_time_ms / 1000
        
        assert avg_time <= threshold, f"Response time {avg_time}s exceeds threshold {threshold}s"
    
    @pytest.mark.slow
    def test_load_capacity(self):
        result = self.perf_suite.test_concurrent_load()
        
        # Check success rate
        success_rate = result.metrics["success_rate"]
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
```

### E2E Test Example

```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from test_framework import E2ETestSuite

class TestWebInterface:
    def setup_method(self):
        self.config = create_default_config()
        self.e2e_suite = E2ETestSuite(self.config)
    
    def test_image_upload_workflow(self):
        # Setup browser
        self.e2e_suite.setup_browser()
        driver = self.e2e_suite.driver
        
        try:
            # Navigate to app
            driver.get(self.config.api.base_url)
            
            # Upload image
            upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            upload_input.send_keys("/path/to/test/image.jpg")
            
            # Click detect button
            detect_button = driver.find_element(By.CSS_SELECTOR, ".detect-button")
            detect_button.click()
            
            # Wait for results
            results = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".results"))
            )
            
            # Verify results
            assert results.is_displayed()
            
        finally:
            self.e2e_suite.teardown_browser()
```

## 📊 Performance Testing

### Load Testing with Locust

```python
from locust import HttpUser, task, between

class DetectionUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup user session"""
        self.test_image = "base64_encoded_test_image"
    
    @task(3)
    def test_health_check(self):
        """Test health endpoint"""
        self.client.get("/health")
    
    @task(1)
    def test_detection(self):
        """Test detection endpoint"""
        self.client.post("/detect", json={
            "image": self.test_image,
            "confidence_threshold": 0.8
        })

# รันด้วย: locust -f locust_tests.py --host=http://localhost:8000
```

### Memory Profiling

```python
import memory_profiler

@memory_profiler.profile
def test_memory_intensive_operation():
    """Test memory usage during heavy operations"""
    # Simulate heavy image processing
    large_images = []
    for i in range(100):
        image = np.random.rand(1000, 1000, 3)
        processed = process_image(image)
        large_images.append(processed)
    
    return large_images

# รันด้วย: python -m memory_profiler test_memory.py
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        pytest tests/ -m unit --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/ -m integration
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

### Docker Testing Environment

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy test files
COPY . .

# Set environment variables
ENV BROWSER_HEADLESS=true
ENV CI=true

# Run tests
CMD ["python", "test_framework.py"]
```

## 📈 การตรวจสอบและปรับปรุงประสิทธิภาพ

### Performance Monitoring

```python
import psutil
import time
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    cpu_percent: float
    memory_mb: float
    response_time_ms: float
    throughput_rps: float

def monitor_performance(func):
    """Decorator สำหรับตรวจสอบประสิทธิภาพ"""
    def wrapper(*args, **kwargs):
        # เริ่มตรวจสอบ
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        start_memory = psutil.virtual_memory().used / 1024 / 1024
        
        # รันฟังก์ชัน
        result = func(*args, **kwargs)
        
        # คำนวณ metrics
        end_time = time.time()
        end_cpu = psutil.cpu_percent()
        end_memory = psutil.virtual_memory().used / 1024 / 1024
        
        metrics = PerformanceMetrics(
            cpu_percent=(start_cpu + end_cpu) / 2,
            memory_mb=end_memory - start_memory,
            response_time_ms=(end_time - start_time) * 1000,
            throughput_rps=1 / (end_time - start_time) if end_time > start_time else 0
        )
        
        print(f"Performance Metrics: {metrics}")
        return result
    
    return wrapper

# การใช้งาน
@monitor_performance
def test_detection_api():
    # ทดสอบ API
    pass
```

### Benchmarking

```python
import pytest
import time

class TestBenchmarks:
    def test_image_processing_benchmark(self, benchmark):
        """Benchmark image processing performance"""
        test_image = create_test_image()
        
        # Benchmark the function
        result = benchmark(process_image, test_image)
        
        # Assertions
        assert result is not None
        assert benchmark.stats.mean < 0.1  # Less than 100ms
    
    def test_model_inference_benchmark(self, benchmark):
        """Benchmark model inference performance"""
        test_input = create_test_input()
        
        result = benchmark(model_inference, test_input)
        
        assert result is not None
        assert benchmark.stats.mean < 0.05  # Less than 50ms
```

## 🛡️ Security Testing

### Security Test Examples

```python
import pytest
import requests
from test_framework import SecurityTestSuite

class TestSecurity:
    def test_sql_injection(self):
        """Test SQL injection vulnerabilities"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
        ]
        
        for payload in malicious_inputs:
            response = requests.post("/api/search", json={
                "query": payload
            })
            
            # Should not return sensitive data
            assert response.status_code != 200 or "error" in response.json()
    
    def test_xss_protection(self):
        """Test XSS protection"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        
        for payload in xss_payloads:
            response = requests.post("/api/comment", json={
                "content": payload
            })
            
            # Should sanitize input
            if response.status_code == 200:
                assert "<script>" not in response.text
                assert "javascript:" not in response.text
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        # Make rapid requests
        responses = []
        for i in range(100):
            response = requests.get("/api/health")
            responses.append(response.status_code)
        
        # Should have some rate limited responses
        rate_limited = [r for r in responses if r == 429]
        assert len(rate_limited) > 0, "Rate limiting not working"
```

## 📋 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

1. **Browser Driver Issues**
   ```bash
   # ติดตั้ง webdriver-manager
   pip install webdriver-manager
   
   # หรือดาวน์โหลด driver ด้วยตนเอง
   from webdriver_manager.chrome import ChromeDriverManager
   driver = webdriver.Chrome(ChromeDriverManager().install())
   ```

2. **Memory Issues**
   ```python
   # เพิ่ม memory limit สำหรับ tests
   pytest tests/ --maxfail=1 --tb=short
   
   # ใช้ garbage collection
   import gc
   gc.collect()
   ```

3. **Timeout Issues**
   ```python
   # เพิ่ม timeout สำหรับ slow tests
   @pytest.mark.timeout(300)
   def test_slow_operation():
       pass
   ```

4. **Database Connection Issues**
   ```python
   # ใช้ test database แยกต่างหาก
   TEST_DATABASE_URL = "sqlite:///test.db"
   
   # Cleanup หลังการทดสอบ
   def teardown_method(self):
       db.session.remove()
       db.drop_all()
   ```

### การ Debug Tests

```python
import pytest
import logging

# เปิด debug logging
logging.basicConfig(level=logging.DEBUG)

# ใช้ pytest debugging
pytest tests/ -v -s --tb=long

# ใช้ pdb สำหรับ interactive debugging
pytest tests/ --pdb

# ใช้ pytest-xvs สำหรับ verbose output
pytest tests/ -xvs
```

## 📊 การรายงานผล

### HTML Report Generation

```python
# สร้างรายงาน HTML
pytest tests/ --html=reports/report.html --self-contained-html

# รายงานพร้อม screenshots
pytest tests/ --html=reports/report.html --capture=sys
```

### Custom Report Generation

```python
import json
from datetime import datetime

def generate_custom_report(test_results):
    """สร้างรายงานแบบกำหนดเอง"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(test_results),
            "passed": len([r for r in test_results if r.status == "passed"]),
            "failed": len([r for r in test_results if r.status == "failed"]),
        },
        "details": [
            {
                "name": r.test_name,
                "status": r.status,
                "duration": r.duration,
                "error": r.error_message
            }
            for r in test_results
        ]
    }
    
    # บันทึกเป็น JSON
    with open("custom_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report
```

## 🚀 การ Deploy และ Scaling

### Distributed Testing

```python
# รัน tests แบบ parallel
pytest tests/ -n auto  # ใช้ CPU cores ทั้งหมด
pytest tests/ -n 4     # ใช้ 4 processes

# รัน tests บน multiple machines
pytest tests/ --dist=loadscope --tx=ssh://user@host1//python
```

### Cloud Testing

```yaml
# AWS CodeBuild example
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.9
    commands:
      - pip install -r requirements.txt
  
  pre_build:
    commands:
      - echo Starting tests...
  
  build:
    commands:
      - python test_framework.py
      - pytest tests/ --junitxml=test-results.xml
  
  post_build:
    commands:
      - echo Tests completed

reports:
  test-reports:
    files:
      - test-results.xml
    base-directory: .
```

## 📚 เอกสารเพิ่มเติม

- [pytest Documentation](https://docs.pytest.org/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## 🤝 การมีส่วนร่วม

1. Fork repository
2. สร้าง feature branch
3. เขียน tests สำหรับ features ใหม่
4. รัน test suite ให้ผ่านทั้งหมด
5. Submit pull request

## 📄 License

MIT License - ดูรายละเอียดในไฟล์ LICENSE

## 📞 Support

- Email: support@example.com
- Issues: GitHub Issues
- Documentation: Wiki pages

---

**หมายเหตุ**: Testing Framework นี้ออกแบบมาเพื่อให้ครอบคลุมการทดสอบทุกระดับ ตั้งแต่ Unit tests ไปจนถึง End-to-End tests เพื่อให้มั่นใจในคุณภาพของระบบ AI Detection