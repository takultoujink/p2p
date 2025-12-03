# 🧪 Testing Framework

โฟลเดอร์นี้เก็บ Testing Scripts และ Automated Testing Framework ทั้งหมดสำหรับโปรเจกต์

## 📋 ไฟล์ในโฟลเดอร์

### 🐍 Unit Tests
- `test_yolo_detection.py` - ทดสอบระบบ YOLO Detection
- `test_arduino_communication.py` - ทดสอบการสื่อสาร Arduino
- `test_firebase_connection.py` - ทดสอบการเชื่อมต่อ Firebase
- `test_config_validation.py` - ทดสอบการตรวจสอบ Configuration

### 🔧 Integration Tests
- `test_full_system.py` - ทดสอบระบบทั้งหมด
- `test_error_handling.py` - ทดสอบการจัดการ Error
- `test_performance.py` - ทดสอบ Performance

### 📊 Test Utilities
- `test_utils.py` - Utilities สำหรับ Testing
- `mock_data.py` - Mock Data สำหรับ Testing
- `test_fixtures.py` - Test Fixtures

### 🤖 Automated Testing
- `run_all_tests.py` - รันทดสอบทั้งหมด
- `continuous_testing.py` - Continuous Testing
- `test_report_generator.py` - สร้างรายงานผลการทดสอบ

## 🚀 การใช้งาน Testing Framework

### 📦 ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 🧪 รันทดสอบแต่ละส่วน
```bash
# ทดสอบ YOLO Detection
python -m pytest test_yolo_detection.py -v

# ทดสอบ Arduino Communication
python -m pytest test_arduino_communication.py -v

# ทดสอบ Firebase Connection
python -m pytest test_firebase_connection.py -v
```

### 🔄 รันทดสอบทั้งหมด
```bash
# รันทดสอบทั้งหมด
python run_all_tests.py

# รันทดสอบพร้อม Coverage Report
python -m pytest --cov=../02_AI_Detection --cov-report=html
```

### 📊 สร้างรายงานผลการทดสอบ
```bash
python test_report_generator.py
```

## 🎯 Test Categories

### ✅ Unit Tests
- **YOLO Detection**: ทดสอบการ detect objects
- **Arduino Communication**: ทดสอบการส่งข้อมูลไป Arduino
- **Firebase Operations**: ทดสอบการอ่าน/เขียน Firebase
- **Configuration**: ทดสอบการโหลดและตรวจสอบ config

### 🔗 Integration Tests
- **End-to-End Flow**: ทดสอบการทำงานจากต้นจนจบ
- **Error Recovery**: ทดสอบการกู้คืนเมื่อเกิด error
- **Performance**: ทดสอบความเร็วและ memory usage

### 🚨 Stress Tests
- **High Load**: ทดสอบภายใต้ load สูง
- **Memory Leak**: ทดสอบ memory leaks
- **Long Running**: ทดสอบการทำงานต่อเนื่องนาน

## 📈 Test Metrics

### 🎯 Coverage Goals
- **Unit Tests**: > 80% code coverage
- **Integration Tests**: > 70% feature coverage
- **Critical Paths**: 100% coverage

### ⏱️ Performance Benchmarks
- **YOLO Detection**: < 200ms per frame
- **Arduino Response**: < 100ms
- **Firebase Upload**: < 500ms
- **Memory Usage**: < 500MB

## 🔧 Test Configuration

### 🛠️ pytest.ini
```ini
[tool:pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
```

### 📋 Test Data
- **Mock Images**: ตัวอย่างภาพสำหรับทดสอบ YOLO
- **Mock Arduino Responses**: ข้อมูลตอบกลับจาก Arduino
- **Mock Firebase Data**: ข้อมูลตัวอย่างใน Firebase

## 🚀 Continuous Integration

### 🔄 Automated Testing Pipeline
1. **Pre-commit Hooks**: รันทดสอบก่อน commit
2. **Pull Request Tests**: ทดสอบเมื่อมี PR
3. **Nightly Tests**: ทดสอบทุกคืน
4. **Performance Regression**: ตรวจสอบ performance

### 📊 Test Reports
- **HTML Coverage Report**: รายงาน code coverage
- **Performance Report**: รายงานความเร็ว
- **Error Summary**: สรุป errors ที่พบ

## 🛠️ Test Development Guidelines

### ✅ Best Practices
- เขียน test ก่อนเขียน code (TDD)
- ใช้ descriptive test names
- แยก unit tests และ integration tests
- ใช้ mock objects สำหรับ external dependencies

### 🚫 Common Pitfalls
- อย่าทดสอบ implementation details
- อย่าให้ tests depend กัน
- อย่าใช้ real external services ใน unit tests
- อย่าเขียน tests ที่ flaky

## 📞 การแก้ไขปัญหา Testing

### 🔍 Common Issues
1. **Tests ล้มเหลว**: ตรวจสอบ dependencies และ environment
2. **Slow tests**: ใช้ mock objects และ optimize test data
3. **Flaky tests**: ตรวจสอบ timing issues และ external dependencies

### 💡 Solutions
- ใช้ `pytest-xdist` สำหรับ parallel testing
- ใช้ `pytest-mock` สำหรับ mocking
- ใช้ `pytest-benchmark` สำหรับ performance testing

---

**📝 หมายเหตุ**: Testing Framework นี้ช่วยให้มั่นใจในคุณภาพของโค้ดและป้องกัน regression bugs