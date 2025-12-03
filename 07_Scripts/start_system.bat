@echo off
echo ========================================
echo  YOLO Arduino Firebase Bridge v2.0
echo  P2P Detection System Launcher
echo ========================================
echo.

REM ตรวจสอบว่ามี Python หรือไม่
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ไม่พบในระบบ!
    echo 💡 กรุณาติดตั้ง Python จาก https://python.org
    pause
    exit /b 1
)

echo ✅ Python พบแล้ว
echo.

REM ตรวจสอบว่ามี dependencies หรือไม่
echo 🔍 ตรวจสอบ dependencies...
python -c "import cv2, numpy, serial, requests" >nul 2>&1
if errorlevel 1 (
    echo ❌ Dependencies ไม่ครบ!
    echo 📦 กำลังติดตั้ง dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ ติดตั้ง dependencies ไม่สำเร็จ!
        pause
        exit /b 1
    )
)

echo ✅ Dependencies พร้อมแล้ว
echo.

REM ตรวจสอบไฟล์ YOLO
echo 🔍 ตรวจสอบไฟล์ YOLO...
if not exist "yolo\yolov3.weights" (
    echo ❌ ไม่พบไฟล์ yolov3.weights!
    echo 📥 กรุณาดาวน์โหลดจาก:
    echo    https://pjreddie.com/media/files/yolov3.weights
    echo 📁 วางไฟล์ใน: yolo\yolov3.weights
    echo.
    echo 🤔 ต้องการเปิด URL ดาวน์โหลดหรือไม่? (y/n)
    set /p choice=
    if /i "%choice%"=="y" (
        start https://pjreddie.com/media/files/yolov3.weights
    )
    pause
    exit /b 1
)

echo ✅ ไฟล์ YOLO พร้อมแล้ว
echo.

REM เริ่มระบบ
echo 🚀 เริ่มระบบตรวจจับขวด...
echo 💡 กด Ctrl+C เพื่อหยุดระบบ
echo ========================================
echo.

python yolo_arduino_firebase_bridge.py

echo.
echo ========================================
echo 🛑 ระบบหยุดทำงานแล้ว
echo ========================================
pause