# 🔧 Scripts

โฟลเดอร์นี้เก็บสคริปต์และไฟล์ Batch ทั้งหมดสำหรับการจัดการและรันระบบ

## 📋 ไฟล์ในโฟลเดอร์

### 🐍 Python Scripts
- `firebase_debug_test.py` - สคริปต์ทดสอบการเชื่อมต่อ Firebase
- `test_firebase_connection.py` - ทดสอบการเชื่อมต่อ Firebase Database

### 🌐 JavaScript Scripts
- `server.js` - เซิร์ฟเวอร์ Node.js สำหรับ Web Dashboard
- `firebase-to-sheets.js` - สคริปต์ส่งข้อมูลจาก Firebase ไป Google Sheets
- `google-apps-script.gs` - Google Apps Script สำหรับ Google Workspace

### 🔨 Batch Files (.bat)
- `fix_netlify_firebase.bat` - แก้ไขปัญหา Netlify และ Firebase
- `setup_git_lfs.bat` - ติดตั้งและตั้งค่า Git LFS
- `start_system.bat` - เริ่มต้นระบบทั้งหมด
- `start_yolo_v11.bat` - เริ่มต้นระบบ YOLO v11
- `start_yolo_v11_servo.bat` - เริ่มต้นระบบ YOLO v11 พร้อม Servo
- `test_firebase.bat` - ทดสอบการเชื่อมต่อ Firebase

## 🚀 การใช้งาน Scripts

### 🐍 Python Scripts

#### Firebase Debug Test
```bash
python firebase_debug_test.py
```
- ทดสอบการเชื่อมต่อ Firebase
- ตรวจสอบ Authentication
- ทดสอบการอ่าน/เขียนข้อมูล

#### Firebase Connection Test
```bash
python test_firebase_connection.py
```
- ทดสอบความเสถียรของการเชื่อมต่อ
- ตรวจสอบ Latency
- รายงานสถานะการเชื่อมต่อ

### 🌐 JavaScript Scripts

#### Node.js Server
```bash
node server.js
```
- เริ่มต้น Web Server
- รองรับ API Endpoints
- จัดการ Static Files

#### Firebase to Sheets
```bash
node firebase-to-sheets.js
```
- ส่งออกข้อมูลจาก Firebase
- อัปเดต Google Sheets อัตโนมัติ
- สร้างรายงานประจำวัน

### 🔨 Batch Files

#### System Startup
```cmd
start_system.bat
```
- เริ่มต้นระบบทั้งหมด
- ตรวจสอบ Dependencies
- เปิดใช้งาน Services ทั้งหมด

#### YOLO System
```cmd
start_yolo_v11.bat
```
- เริ่มต้นระบบ AI Detection
- โหลด YOLO Model
- เริ่มการตรวจจับขวด

#### YOLO with Servo
```cmd
start_yolo_v11_servo.bat
```
- เริ่มต้นระบบ AI Detection
- เปิดใช้งาน Servo Control
- เริ่มการคัดแยกอัตโนมัติ

## ⚙️ Configuration

### 🔧 Environment Variables
```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-domain

# Google Sheets Configuration
GOOGLE_SHEETS_ID=your-sheet-id
GOOGLE_SERVICE_ACCOUNT=path/to/service-account.json

# System Configuration
YOLO_MODEL_PATH=path/to/model.pt
ARDUINO_PORT=COM3
```

### 📊 Logging
```python
# Python Logging Configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system.log'),
        logging.StreamHandler()
    ]
)
```

## 🔍 Troubleshooting Scripts

### ❌ Common Issues

#### Firebase Connection Error
```bash
# รัน Firebase Debug Test
python firebase_debug_test.py

# ตรวจสอบ Network
ping firebase.google.com

# ตรวจสอบ API Key
echo $FIREBASE_API_KEY
```

#### YOLO Model Loading Error
```bash
# ตรวจสอบ Model File
dir models\yolo_v11.pt

# ตรวจสอบ Dependencies
pip list | findstr ultralytics

# รัน Test Script
python test_yolo_model.py
```

#### Arduino Connection Error
```bash
# ตรวจสอบ COM Port
mode

# ทดสอบ Serial Connection
python test_arduino_connection.py

# รีเซ็ต Arduino
# กด Reset Button บน Arduino Board
```

## 📈 Performance Monitoring

### 📊 System Metrics
```python
# CPU และ Memory Usage
import psutil
print(f"CPU: {psutil.cpu_percent()}%")
print(f"Memory: {psutil.virtual_memory().percent}%")

# Firebase Response Time
import time
start_time = time.time()
# Firebase operation
response_time = time.time() - start_time
print(f"Firebase Response: {response_time:.2f}s")
```

### 📝 Log Analysis
```bash
# ดู Log ล่าสุด
tail -f system.log

# ค้นหา Error
grep "ERROR" system.log

# นับจำนวน Detection
grep "bottle_detected" system.log | wc -l
```

## 🔄 Automation

### ⏰ Scheduled Tasks
```bash
# Windows Task Scheduler
schtasks /create /tn "P2P_Daily_Report" /tr "python firebase-to-sheets.js" /sc daily /st 23:59

# Cron Job (Linux/Mac)
0 23 * * * /usr/bin/python3 /path/to/firebase-to-sheets.js
```

### 🔄 Auto-restart
```bash
# Auto-restart on failure
while true; do
    python yolo_v11_servo_system.py
    echo "System crashed. Restarting in 5 seconds..."
    sleep 5
done
```

## 🛡️ Security

### 🔐 API Key Management
- ใช้ Environment Variables
- ไม่ commit API Keys ใน Git
- ใช้ Service Account สำหรับ Production

### 🔒 Access Control
- จำกัดสิทธิ์การเข้าถึง Scripts
- ใช้ HTTPS สำหรับ API calls
- ตรวจสอบ Input validation