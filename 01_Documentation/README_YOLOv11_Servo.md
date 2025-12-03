# YOLOv11 Arduino Firebase Bridge v3.1 (Servo Edition)

🎯 **P2P (Plastic to Point) Detection System with Servo Control**  
🤖 **Powered by YOLOv11 + Arduino Servo Motor**

## 📋 ภาพรวมระบบ

ระบบตรวจจับขวดพลาสติกด้วย YOLOv11 ที่เชื่อมต่อกับ Arduino R4 WiFi พร้อม Servo Motor สำหรับการปัดขวดอัตโนมัติ และบันทึกข้อมูลลง Firebase Realtime Database

### ✨ ฟีเจอร์หลัก
- 🔍 **YOLOv11 Detection**: ตรวจจับขวดพลาสติกด้วยความแม่นยำสูง
- 🤖 **Servo Control**: ปัดขวดอัตโนมัติเมื่อตรวจพบ
- 📡 **Arduino Integration**: เชื่อมต่อ Serial กับ Arduino R4 WiFi
- 🔥 **Firebase Sync**: บันทึกข้อมูลแบบ Real-time
- 💡 **LED & Buzzer**: แสดงสถานะการตรวจจับ
- 📊 **Live Dashboard**: แสดงสถิติการทำงาน
- 🎮 **Manual Control**: ควบคุม Servo ด้วยตนเอง

## 🛠️ ความต้องการของระบบ

### Hardware
- **Arduino R4 WiFi** (หรือ Arduino ที่รองรับ WiFi)
- **Servo Motor** (SG90 หรือเทียบเท่า)
- **LED** (สำหรับแสดงสถานะ)
- **Buzzer** (สำหรับเสียงแจ้งเตือน)
- **Webcam** (USB Camera)
- **Computer** (Windows/Linux/Mac)

### Software
- Python 3.8+
- Arduino IDE
- YOLOv11 Model (.pt file)
- Firebase Account

### Python Dependencies
```bash
pip install -r requirements_yolo_v11.txt
```

## 📦 การติดตั้ง

### 1. เตรียม Python Environment
```bash
# Clone หรือ download โปรเจค
cd "c:\app na ka"

# ติดตั้ง dependencies
pip install -r requirements_yolo_v11.txt

# ดาวน์โหลด YOLOv11 model
# วางไฟล์ best.pt ในโฟลเดอร์โปรเจค
```

### 2. ตั้งค่า Arduino
```cpp
// อัปโหลดไฟล์ arduino_yolo_v11_servo.ino ไป Arduino
// ตั้งค่า WiFi และ Firebase ใน code
// เชื่อมต่อ hardware ตามแผนภาพ
```

### 3. การเชื่อมต่อ Hardware
```
Arduino R4 WiFi:
├── Pin 9  → Servo Motor (Signal)
├── Pin 13 → LED (Anode)
├── Pin 12 → Buzzer (+)
├── 5V     → Servo Motor (VCC)
├── GND    → Servo Motor (GND), LED (Cathode), Buzzer (-)
└── USB    → Computer
```

## ⚙️ การตั้งค่า

### 1. แก้ไข config_yolo_v11.py
```python
class ServoConfig:
    # Arduino Settings
    ARDUINO_PORT = "COM5"  # แก้ตามพอร์ต Arduino ของคุณ
    
    # YOLOv11 Settings
    MODEL_PATH = "best.pt"  # path ไปยัง model ของคุณ
    TARGET_CLASS_ID = 0     # ID ของ plastic bottle
    
    # Firebase Settings
    FIREBASE_URL = "https://your-project.firebasedatabase.app"
    
    # Servo Settings
    AUTO_SERVO_SWEEP = True  # เปิด/ปิดการปัดขวดอัตโนมัติ
```

### 2. ตั้งค่า Firebase
1. สร้าง Firebase Project
2. เปิดใช้ Realtime Database
3. ตั้งค่า Rules:
```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

### 3. ตั้งค่า Arduino
```cpp
// ใน arduino_yolo_v11_servo.ino
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* firebase_host = "your-project-default-rtdb.asia-southeast1.firebasedatabase.app";
```

## 🚀 การใช้งาน

### วิธีที่ 1: ใช้ Batch Script
```bash
# Double-click ไฟล์
start_yolo_v11.bat
```

### วิธีที่ 2: รัน Python โดยตรง
```bash
python yolo_v11_servo_system.py
```

### 🎮 การควบคุม

#### Keyboard Controls
- **ESC**: ออกจากโปรแกรม
- **r**: รีเซ็ตตัวนับและ Servo
- **s**: แสดงสถานะระบบ
- **t**: ทดสอบ Servo Motor
- **w**: ปัดขวดด้วยตนเอง
- **h**: เคลื่อนไหว Servo ไปตำแหน่งพัก
- **1-9**: เคลื่อนไหว Servo ไปตำแหน่งที่กำหนด (0°-160°)

#### Arduino Commands (Serial)
- `90`: ตรวจพบขวด (เปิด LED + Buzzer)
- `0`: ไม่พบขวด (ปิด LED + Buzzer)
- `SERVO:angle`: เคลื่อนไหว Servo ไปมุมที่กำหนด (0-180°)
- `SWEEP`: ทำการปัดขวดอัตโนมัติ
- `reset`: รีเซ็ตตัวนับ Arduino

## 📁 ไฟล์ในระบบ

### Python Files
- `yolo_v11_servo_system.py` - ไฟล์หลักของระบบ
- `config_yolo_v11.py` - การตั้งค่าระบบ
- `requirements_yolo_v11.txt` - Python dependencies

### Arduino Files
- `arduino_yolo_v11_servo.ino` - โค้ด Arduino พร้อม Servo

### Documentation & Tools
- `README_YOLOv11_Servo.md` - คู่มือนี้
- `start_yolo_v11.bat` - Script เริ่มระบบ

### Model Files (ต้องเตรียมเอง)
- `best.pt` - YOLOv11 trained model

## 🔧 การทำงานของระบบ

### 1. กระบวนการตรวจจับ
```
1. Camera capture frame
2. YOLOv11 analyze frame
3. Detect plastic bottles
4. Send signal to Arduino
5. Arduino control LED/Buzzer/Servo
6. Update Firebase database
7. Display results on screen
```

### 2. Servo Control Flow
```
1. Bottle detected → Send "SWEEP" command
2. Arduino moves servo to sweep position (45°)
3. Wait 500ms
4. Move to return position (135°)
5. Wait 500ms
6. Return to rest position (90°)
7. Update servo action counter
```

### 3. ข้อมูลที่เก็บใน Firebase
```json
{
  "bottle_servo_data": {
    "yolo_v11_servo_user": {
      "bottle_count": 15,
      "total_points": 150,
      "servo_actions": 15,
      "servo_position": 90,
      "last_detection": 1,
      "auto_sweep_enabled": true,
      "timestamp": "2024-01-15T10:30:45",
      "device": "yolo_v11_servo_python",
      "model_version": "YOLOv11",
      "has_servo": true
    }
  },
  "servo_data": {
    "yolo_v11_servo_user": {
      "servo_angle": 45,
      "action": "bottle_sweep",
      "timestamp": "2024-01-15T10:30:45"
    }
  }
}
```

## 🔍 การแก้ไขปัญหา

### ปัญหา Arduino
```
❌ Arduino not connected
💡 Solutions:
   - ตรวจสอบ USB cable
   - เปลี่ยน COM port ใน config
   - ปิด Arduino IDE/Serial Monitor
   - ตรวจสอบ Driver
```

### ปัญหา Servo
```
❌ Servo not moving
💡 Solutions:
   - ตรวจสอบการเชื่อมต่อ pin 9
   - ตรวจสอบ power supply (5V)
   - ทดสอบด้วยคำสั่ง 't'
   - ตรวจสอบ servo motor
```

### ปัญหา YOLOv11
```
❌ Model not found
💡 Solutions:
   - ดาวน์โหลด YOLOv11 model
   - ตรวจสอบ MODEL_PATH
   - ตรวจสอบไฟล์ .pt
```

### ปัญหา Camera
```
❌ Camera not detected
💡 Solutions:
   - เปลี่ยน CAM_ID (0, 1, 2...)
   - ตรวจสอบ USB camera
   - ปิดแอปอื่นที่ใช้ camera
```

### ปัญหา Firebase
```
❌ Firebase connection failed
💡 Solutions:
   - ตรวจสอบ internet connection
   - ตรวจสอบ FIREBASE_URL
   - ตรวจสอบ Database Rules
```

## ⚡ การปรับแต่งประสิทธิภาพ

### 1. YOLOv11 Settings
```python
# สำหรับความเร็ว
CONF_THRESHOLD = 0.5  # ลดความแม่นยำ เพิ่มความเร็ว
IMG_SIZE = 320        # ลดขนาดภาพ

# สำหรับความแม่นยำ
CONF_THRESHOLD = 0.8  # เพิ่มความแม่นยำ
IMG_SIZE = 640        # เพิ่มขนาดภาพ
```

### 2. Servo Settings
```python
# ปรับความเร็ว Servo
SERVO_DELAY = 0.3     # เร็วขึ้น
SERVO_DELAY = 1.0     # ช้าลง แต่เสถียร

# ปรับตำแหน่งการปัด
SERVO_SWEEP_POSITION = 30   # ปัดน้อยลง
SERVO_RETURN_POSITION = 150 # ปัดมากขึ้น
```

### 3. Detection Settings
```python
# ปรับความถี่การตรวจจับ
DETECTION_COOLDOWN = 1.0  # ตรวจจับบ่อยขึ้น
SEND_DELAY = 0.5          # ส่งข้อมูลบ่อยขึ้น
```

## 📊 การติดตาม Performance

### System Status
- กด `s` เพื่อดูสถานะระบบ
- ตรวจสอบ FPS ใน OpenCV window
- ดู Arduino Serial Monitor
- ตรวจสอบ Firebase Console

### Metrics ที่สำคัญ
- **Detection Rate**: จำนวนขวดที่ตรวจพบต่อนาที
- **Servo Actions**: จำนวนครั้งที่ Servo ทำงาน
- **Arduino Response**: เวลาตอบสนองของ Arduino
- **Firebase Sync**: ความถี่การอัปเดตข้อมูล

## 🔄 การอัปเดต

### Version History
- **v3.1**: เพิ่ม Servo Motor Control
- **v3.0**: YOLOv11 Integration
- **v2.0**: Firebase Integration
- **v1.0**: Basic Arduino Communication

### การอัปเดตระบบ
1. สำรองข้อมูล config
2. ดาวน์โหลดเวอร์ชันใหม่
3. อัปเดต dependencies
4. ทดสอบระบบ

## 🆘 การขอความช่วยเหลือ

### ข้อมูลที่ต้องเตรียมเมื่อขอความช่วยเหลือ
1. เวอร์ชัน Python
2. เวอร์ชัน Arduino IDE
3. รุ่น Arduino board
4. ข้อความ error ที่แสดง
5. ไฟล์ config ที่ใช้

### Logs ที่สำคัญ
- Python console output
- Arduino Serial Monitor
- Firebase Console logs
- System performance metrics

---

## 📝 หมายเหตุ

- ระบบนี้ออกแบบสำหรับการใช้งานในสภาพแวดล้อมที่ควบคุมได้
- ควรทดสอบ Servo Motor ก่อนใช้งานจริง
- ตรวจสอบการเชื่อมต่อ Hardware เป็นประจำ
- สำรองข้อมูล Firebase เป็นระยะ

**🎯 Happy Detecting with Servo Control! 🤖**

---
*YOLOv11 Arduino Firebase Bridge v3.1 (Servo Edition)*  
*Developed by P2P Team*  
*Last Updated: 2024*