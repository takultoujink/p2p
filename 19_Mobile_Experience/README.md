# Mobile AI Experience System

ระบบ AI ขั้นสูงสำหรับอุปกรณ์มือถือ รองรับการตรวจจับวัตถุแบบ Offline, Camera Filters, AR Overlays และ Voice Commands

## 🌟 คุณสมบัติหลัก

### 📱 Mobile-First Design
- **Cross-Platform Support**: Android, iOS, Web และ Desktop
- **Offline Detection**: ทำงานได้โดยไม่ต้องเชื่อมต่ออินเทอร์เน็ต
- **Optimized Performance**: ปรับให้เหมาะสมกับอุปกรณ์มือถือ
- **Battery Efficient**: ประหยัดแบตเตอรี่

### 📸 Camera Features
- **Real-time Object Detection**: ตรวจจับวัตถุแบบเรียลไทม์
- **Multiple Camera Support**: รองรับกล้องหน้า-หลัง
- **Advanced Filters**: Beauty, Vintage, Cartoon และอื่นๆ
- **Photo & Video Recording**: บันทึกภาพและวิดีโอ

### 🔮 AR Capabilities
- **Face Tracking**: ติดตามใบหน้าแบบเรียลไทม์
- **Hand Tracking**: ติดตามการเคลื่อนไหวของมือ
- **Object Tracking**: ติดตามวัตถุต่างๆ
- **Virtual Overlays**: วางวัตถุเสมือนบนภาพจริง

### 🎤 Voice Commands
- **Thai Language Support**: รองรับภาษาไทย
- **Wake Word Detection**: เรียกใช้ด้วยคำสั่งเสียง
- **Voice Feedback**: ตอบกลับด้วยเสียง
- **Noise Reduction**: ลดเสียงรบกวน

## 🏗️ โครงสร้างโปรเจกต์

```
19_Mobile_Experience/
├── mobile_ai_system.py      # ระบบหลัก Mobile AI
├── mobile_config.py         # การจัดการการกำหนดค่า
├── requirements.txt         # Dependencies
├── README.md               # เอกสารนี้
├── models/                 # โฟลเดอร์โมเดล AI
│   ├── mobilenet_ssd_v2.tflite
│   ├── face_detection.tflite
│   └── hand_tracking.tflite
├── assets/                 # ไฟล์ทรัพยากร
│   ├── icons/
│   ├── sounds/
│   └── filters/
├── config/                 # ไฟล์การกำหนดค่า
│   ├── android_config.json
│   ├── ios_config.json
│   └── web_config.json
└── tests/                  # ไฟล์ทดสอบ
    ├── test_mobile_ai.py
    ├── test_camera.py
    ├── test_ar.py
    └── test_voice.py
```

## 🚀 การติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 2. ติดตั้ง Platform-Specific Dependencies

#### Android
```bash
pip install buildozer python-for-android
```

#### iOS (macOS เท่านั้น)
```bash
pip install kivy-ios
```

#### Web
```bash
pip install flask socketio
```

### 3. ดาวน์โหลดโมเดล AI

```bash
# สร้างโฟลเดอร์โมเดล
mkdir models

# ดาวน์โหลดโมเดลตัวอย่าง (ต้องมีโมเดลจริง)
# wget -O models/mobilenet_ssd_v2.tflite [URL]
# wget -O models/face_detection.tflite [URL]
# wget -O models/hand_tracking.tflite [URL]
```

## 📖 การใช้งาน

### การใช้งานพื้นฐาน

```python
from mobile_ai_system import MobileAISystem, MobileConfig
from mobile_config import Platform, create_default_config

# สร้างการกำหนดค่า
config = create_default_config(Platform.ANDROID)
config.device_id = "my_device_001"
config.offline.offline_mode_enabled = True
config.camera.resolution = (1280, 720)
config.ar.face_tracking_enabled = True
config.voice.voice_commands_enabled = True

# สร้างและเริ่มระบบ
mobile_system = MobileAISystem(config)

if mobile_system.start_system():
    print("Mobile AI System เริ่มทำงานแล้ว!")
    
    # รันลูปกล้อง
    mobile_system.run_camera_loop()
else:
    print("ไม่สามารถเริ่มระบบได้")

# หยุดระบบ
mobile_system.stop_system()
```

### การใช้งาน Camera Filters

```python
from mobile_ai_system import FilterManager, FilterConfig, FilterType

# สร้าง Filter Manager
filter_manager = FilterManager()

# เพิ่ม Beauty Filter
beauty_filter = FilterConfig(
    filter_type=FilterType.BEAUTY,
    intensity=0.7
)
filter_manager.add_filter(beauty_filter)

# เพิ่ม Vintage Filter
vintage_filter = FilterConfig(
    filter_type=FilterType.VINTAGE,
    intensity=0.5
)
filter_manager.add_filter(vintage_filter)

# ใช้ Filters กับภาพ
import cv2
image = cv2.imread("input.jpg")
filtered_image = filter_manager.apply_filters(image)
cv2.imwrite("output.jpg", filtered_image)
```

### การใช้งาน AR Tracking

```python
from mobile_ai_system import ARTracker, ARRenderer, ARConfig

# สร้าง AR Tracker
ar_config = ARConfig(
    face_tracking=True,
    hand_tracking=True,
    object_tracking=False
)
ar_tracker = ARTracker(ar_config)
ar_renderer = ARRenderer()

# ประมวลผลเฟรม
import cv2
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # ติดตามใบหน้า
    face_data = ar_tracker.track_face(frame)
    
    # ติดตามมือ
    hands_data = ar_tracker.track_hands(frame)
    
    # เรนเดอร์เอฟเฟกต์ AR
    if face_data:
        frame = ar_renderer.render_face_effects(frame, face_data)
    
    if hands_data:
        frame = ar_renderer.render_hand_effects(frame, hands_data)
    
    cv2.imshow('AR Demo', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### การใช้งาน Voice Commands

```python
from mobile_ai_system import VoiceCommandProcessor, VoiceConfig

# สร้าง Voice Processor
voice_config = VoiceConfig(
    language="th-TH",
    wake_word="hey ai",
    voice_commands_enabled=True
)
voice_processor = VoiceCommandProcessor(voice_config)

# ลงทะเบียนคำสั่งเสียง
def take_photo_callback():
    print("ถ่ายภาพ!")

def apply_filter_callback():
    print("ใช้ฟิลเตอร์!")

voice_processor.register_command_callback('take_photo', take_photo_callback)
voice_processor.register_command_callback('apply_filter', apply_filter_callback)

# เริ่มฟังคำสั่งเสียง
voice_processor.start_listening()

# พูดข้อความ
voice_processor.speak("ระบบพร้อมใช้งาน")

# หยุดฟัง
voice_processor.stop_listening()
```

## ⚙️ การกำหนดค่า

### การกำหนดค่าพื้นฐาน

```python
from mobile_config import MobileAIConfig, Platform

# สร้างการกำหนดค่าใหม่
config = MobileAIConfig()

# ตั้งค่าแพลตฟอร์ม
config.platform = Platform.ANDROID
config.device_id = "my_device_001"

# ตั้งค่าประสิทธิภาพ
config.performance.target_fps = 30
config.performance.enable_gpu_acceleration = True
config.performance.memory_limit_mb = 512

# ตั้งค่ากล้อง
config.camera.resolution = (1920, 1080)
config.camera.fps = 30
config.camera.auto_focus = True

# ตั้งค่า AR
config.ar.face_tracking_enabled = True
config.ar.hand_tracking_enabled = True
config.ar.max_tracked_faces = 2

# ตั้งค่าเสียง
config.voice.language = "th-TH"
config.voice.wake_word = "hey ai"
config.voice.tts_enabled = True

# บันทึกการกำหนดค่า
config.save_to_file("my_config.json")
```

### การโหลดการกำหนดค่า

```python
# โหลดจากไฟล์
config = MobileAIConfig("my_config.json")

# โหลดจากตัวแปรสภาพแวดล้อม
config = load_config_from_environment()

# ตรวจสอบความถูกต้อง
errors = config.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")
```

### การปรับให้เหมาะสมกับอุปกรณ์

```python
# ข้อมูลอุปกรณ์
device_info = {
    'ram_mb': 4096,
    'cpu_cores': 8,
    'gpu_available': True
}

# ปรับการกำหนดค่าอัตโนมัติ
config.optimize_for_device(device_info)
```

## 🎯 คำสั่งเสียงที่รองรับ

### คำสั่งภาษาไทย
- **"ถ่ายภาพ"** - ถ่ายภาพ
- **"เริ่มบันทึก"** - เริ่มบันทึกวิดีโอ
- **"หยุดบันทึก"** - หยุดบันทึกวิดีโอ
- **"ใช้ฟิลเตอร์"** - ใช้ฟิลเตอร์ความงาม
- **"ลบฟิลเตอร์"** - ลบฟิลเตอร์ทั้งหมด
- **"เปลี่ยนกล้อง"** - สลับกล้องหน้า-หลัง
- **"เปิด AR"** - เปิดโหมด AR
- **"ปิด AR"** - ปิดโหมด AR

### คำสั่งภาษาอังกฤษ
- **"take photo"** - Take a photo
- **"start recording"** - Start video recording
- **"stop recording"** - Stop video recording
- **"apply filter"** - Apply beauty filter
- **"remove filter"** - Remove all filters
- **"switch camera"** - Switch front/back camera
- **"enable ar"** - Enable AR mode
- **"disable ar"** - Disable AR mode

## 🔧 การปรับแต่งขั้นสูง

### การเพิ่ม Filter ใหม่

```python
from mobile_ai_system import CameraFilter
import cv2
import numpy as np

class CustomFilter(CameraFilter):
    @staticmethod
    def apply_neon_filter(image: np.ndarray, intensity: float = 0.8) -> np.ndarray:
        """ใช้ Neon Filter"""
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Increase saturation
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.5)
        
        # Add glow effect
        blur = cv2.GaussianBlur(image, (15, 15), 0)
        result = cv2.addWeighted(image, 1 - intensity, blur, intensity, 0)
        
        return result

# ลงทะเบียน Filter ใหม่
filter_manager.filters['neon'] = CustomFilter.apply_neon_filter
```

### การเพิ่ม AR Effect ใหม่

```python
from mobile_ai_system import ARRenderer
import cv2

class CustomARRenderer(ARRenderer):
    def render_crown_effect(self, image: np.ndarray, face_data: dict) -> np.ndarray:
        """เรนเดอร์มงกุฎบนหัว"""
        if not face_data:
            return image
        
        landmarks = face_data['landmarks']
        
        # หาจุดบนหัว
        forehead_points = landmarks[10:15]  # จุดหน้าผาก
        top_point = min(forehead_points, key=lambda p: p[1])
        
        # วาดมงกุฎ
        crown_points = [
            (top_point[0] - 50, top_point[1] - 30),
            (top_point[0] - 25, top_point[1] - 60),
            (top_point[0], top_point[1] - 80),
            (top_point[0] + 25, top_point[1] - 60),
            (top_point[0] + 50, top_point[1] - 30)
        ]
        
        # วาดมงกุฎ
        cv2.polylines(image, [np.array(crown_points)], True, (0, 215, 255), 3)
        
        return image
```

### การเพิ่มคำสั่งเสียงใหม่

```python
# เพิ่มคำสั่งใหม่
voice_processor.commands['เปิดไฟแฟลช'] = lambda: mobile_system.toggle_flash()
voice_processor.commands['ซูมเข้า'] = lambda: mobile_system.zoom_in()
voice_processor.commands['ซูมออก'] = lambda: mobile_system.zoom_out()

# ลงทะเบียน Callback
def toggle_flash_callback():
    mobile_system.camera_config.flash_enabled = not mobile_system.camera_config.flash_enabled
    status = "เปิด" if mobile_system.camera_config.flash_enabled else "ปิด"
    voice_processor.speak(f"{status}ไฟแฟลชแล้ว")

voice_processor.register_command_callback('toggle_flash', toggle_flash_callback)
```

## 📊 การตรวจสอบประสิทธิภาพ

### การวัดประสิทธิภาพ

```python
# ดูเมตริกประสิทธิภาพ
metrics = mobile_system.performance_metrics
print(f"FPS: {metrics['fps']:.2f}")
print(f"Processing Time: {metrics['processing_time']:.3f}s")

# ดูการใช้หน่วยความจำ
import psutil
memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
print(f"Memory Usage: {memory_usage:.2f} MB")
```

### การปรับปรุงประสิทธิภาพ

```python
# ลด FPS เมื่อแบตเตอรี่ต่ำ
if battery_level < 20:
    config.performance.target_fps = 15
    config.camera.resolution = (640, 480)

# เปิด GPU Acceleration
config.performance.enable_gpu_acceleration = True
config.performance.enable_model_quantization = True

# ปรับ Thread Count
import multiprocessing
config.performance.thread_count = multiprocessing.cpu_count()
```

## 🧪 การทดสอบ

### รันการทดสอบ

```bash
# ทดสอบทั้งหมด
python -m pytest tests/

# ทดสอบเฉพาะส่วน
python -m pytest tests/test_camera.py
python -m pytest tests/test_ar.py
python -m pytest tests/test_voice.py

# ทดสอบประสิทธิภาพ
python -m pytest tests/test_performance.py -v
```

### การทดสอบด้วยตนเอง

```python
# ทดสอบกล้อง
python mobile_ai_system.py --test-camera

# ทดสอบ AR
python mobile_ai_system.py --test-ar

# ทดสอบเสียง
python mobile_ai_system.py --test-voice

# ทดสอบ Offline Mode
python mobile_ai_system.py --offline
```

## 🚀 การ Deploy

### Android (APK)

```bash
# ติดตั้ง Buildozer
pip install buildozer

# สร้าง APK
buildozer android debug

# สร้าง APK สำหรับ Release
buildozer android release
```

### iOS (IPA)

```bash
# ติดตั้ง kivy-ios (macOS เท่านั้น)
pip install kivy-ios

# Build สำหรับ iOS
kivy-ios build python3 kivy
kivy-ios create <YourApp> <path/to/your/app>
```

### Web Application

```bash
# รัน Web Server
python web_server.py

# หรือใช้ Flask
export FLASK_APP=mobile_web_app.py
flask run --host=0.0.0.0 --port=5000
```

## 🔒 ความปลอดภัย

### การเข้ารหัสข้อมูล

```python
# เปิดการเข้ารหัสข้อมูลท้องถิ่น
config.security.encrypt_local_data = True

# ใช้การยืนยันตัวตน
config.security.require_authentication = True
config.security.biometric_auth = True

# เปิด Privacy Mode
config.security.privacy_mode = True
config.security.data_anonymization = True
```

### การจัดการสิทธิ์

```python
# ตรวจสอบสิทธิ์กล้อง
if not check_camera_permission():
    request_camera_permission()

# ตรวจสอบสิทธิ์ไมโครโฟน
if not check_microphone_permission():
    request_microphone_permission()

# ตรวจสอบสิทธิ์จัดเก็บไฟล์
if not check_storage_permission():
    request_storage_permission()
```

## 🐛 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

#### กล้องไม่ทำงาน
```python
# ตรวจสอบกล้อง
if not mobile_system.camera or not mobile_system.camera.isOpened():
    print("ไม่สามารถเปิดกล้องได้")
    # ลองเปลี่ยน camera_id
    mobile_system.camera_config.camera_id = 1
    mobile_system.initialize_camera()
```

#### AR ไม่ทำงาน
```python
# ตรวจสอบ MediaPipe
try:
    import mediapipe as mp
    print("MediaPipe พร้อมใช้งาน")
except ImportError:
    print("ติดตั้ง MediaPipe: pip install mediapipe")
```

#### เสียงไม่ทำงาน
```python
# ตรวจสอบไมโครโฟน
try:
    import speech_recognition as sr
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("ไมโครโฟนพร้อมใช้งาน")
except:
    print("ปัญหาไมโครโฟน - ตรวจสอบการเชื่อมต่อ")
```

#### ประสิทธิภาพต่ำ
```python
# ลด FPS และความละเอียด
config.performance.target_fps = 15
config.camera.resolution = (640, 480)

# ปิดฟีเจอร์ที่ไม่จำเป็น
config.ar.hand_tracking_enabled = False
config.voice.voice_commands_enabled = False
```

### การ Debug

```python
# เปิด Debug Mode
import logging
logging.basicConfig(level=logging.DEBUG)

# ดู Log ประสิทธิภาพ
mobile_system.logger.setLevel(logging.DEBUG)

# บันทึก Debug Info
config.analytics.detailed_logging = True
config.analytics.log_level = "DEBUG"
```

## 📈 การพัฒนาต่อ

### Roadmap
- [ ] รองรับ 3D Object Tracking
- [ ] เพิ่ม Machine Learning บนอุปกรณ์
- [ ] รองรับ Multi-language Voice Commands
- [ ] เพิ่ม Social Media Integration
- [ ] พัฒนา Cloud Sync
- [ ] เพิ่ม Advanced Analytics

### การมีส่วนร่วม
1. Fork โปรเจกต์
2. สร้าง Feature Branch
3. Commit การเปลี่ยนแปลง
4. Push ไปยัง Branch
5. สร้าง Pull Request

## 📄 License

MIT License - ดูไฟล์ LICENSE สำหรับรายละเอียด

## 🤝 Support

- **Email**: support@mobileai.com
- **Discord**: [Mobile AI Community](https://discord.gg/mobileai)
- **GitHub Issues**: [Report Issues](https://github.com/mobileai/issues)
- **Documentation**: [Full Documentation](https://docs.mobileai.com)

## 🙏 Acknowledgments

- MediaPipe team สำหรับ AR tracking
- OpenCV community สำหรับ computer vision
- TensorFlow team สำหรับ mobile ML
- Kivy team สำหรับ mobile framework

---

**Mobile AI Experience System** - Bringing AI to your fingertips! 📱✨