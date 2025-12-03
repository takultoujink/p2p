@echo off
chcp 65001 >nul
color 0A
title YOLOv11 Arduino Firebase Bridge v3.1 (Servo Edition)

echo.
echo ████████████████████████████████████████████████████████████████████████████████
echo ██                                                                            ██
echo ██    🎯 YOLOv11 Arduino Firebase Bridge v3.1 (Servo Edition)                ██
echo ██    🤖 P2P Detection System with Servo Control                             ██
echo ██    🔧 Powered by YOLOv11 + Arduino Servo Motor                           ██
echo ██                                                                            ██
echo ████████████████████████████████████████████████████████████████████████████████
echo.

echo 🔍 Checking system requirements...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo 📦 Please install Python 3.8+ from https://python.org
    echo 💡 Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python found:
for /f "tokens=*" %%i in ('python --version') do echo    %%i
echo.

REM Check if required files exist
echo 🔍 Checking required files...

if not exist "yolo_v11_servo_system.py" (
    echo ❌ Main Python file not found: yolo_v11_servo_system.py
    echo 💡 Please make sure all files are in the same directory
    pause
    exit /b 1
)
echo ✅ Main Python file found

if not exist "config_yolo_v11.py" (
    echo ❌ Config file not found: config_yolo_v11.py
    echo 💡 Please make sure all files are in the same directory
    pause
    exit /b 1
)
echo ✅ Config file found

if not exist "arduino_yolo_v11_servo.ino" (
    echo ⚠️  Arduino file not found: arduino_yolo_v11_servo.ino
    echo 💡 Please upload this file to your Arduino first
)
echo ✅ Arduino file found

if not exist "requirements_yolo_v11.txt" (
    echo ⚠️  Requirements file not found: requirements_yolo_v11.txt
    echo 💡 You may need to install dependencies manually
) else (
    echo ✅ Requirements file found
)

if not exist "best.pt" (
    echo ⚠️  YOLOv11 model not found: best.pt
    echo 💡 Please download or train a YOLOv11 model and place it here
    echo 📥 You can download from: https://github.com/ultralytics/ultralytics
) else (
    echo ✅ YOLOv11 model found
)

echo.
echo 📦 Checking Python dependencies...
echo.

REM Check critical dependencies
python -c "import cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ OpenCV not found
    echo 📦 Installing: pip install opencv-python
    pip install opencv-python
)

python -c "import serial" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PySerial not found
    echo 📦 Installing: pip install pyserial
    pip install pyserial
)

python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Requests not found
    echo 📦 Installing: pip install requests
    pip install requests
)

python -c "import ultralytics" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ultralytics not found
    echo 📦 Installing: pip install ultralytics
    pip install ultralytics
)

echo ✅ Dependencies check completed
echo.

echo ⚙️  System Configuration:
echo    📁 Working Directory: %CD%
echo    🐍 Python: Ready
echo    🤖 Arduino: Please ensure it's connected
echo    🔧 Servo: Please ensure it's connected to pin 9
echo    📹 Camera: Will auto-detect
echo    🔥 Firebase: Configure in config_yolo_v11.py
echo.

echo 📋 Pre-flight Checklist:
echo    ✓ Arduino uploaded with arduino_yolo_v11_servo.ino
echo    ✓ Servo motor connected to pin 9
echo    ✓ LED connected to pin 13
echo    ✓ Buzzer connected to pin 12
echo    ✓ Arduino connected via USB
echo    ✓ Camera connected and working
echo    ✓ WiFi credentials set in Arduino code
echo    ✓ Firebase URL configured
echo    ✓ YOLOv11 model (best.pt) available
echo.

echo 🎮 Controls (when running):
echo    ESC     - Quit system
echo    r       - Reset counter and servo
echo    s       - Show system status
echo    t       - Test servo motor
echo    w       - Manual bottle sweep
echo    h       - Move servo to rest position
echo    1-9     - Move servo to preset positions
echo.

echo 🚀 Starting YOLOv11 Servo Detection System...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.

REM Start the main Python script
python yolo_v11_servo_system.py

echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo 🏁 YOLOv11 Servo Detection System has stopped
echo.

if %errorlevel% neq 0 (
    echo ❌ System exited with error code: %errorlevel%
    echo.
    echo 🔧 Troubleshooting Tips:
    echo    1. Check Arduino connection and COM port
    echo    2. Ensure servo is properly connected
    echo    3. Verify camera is working
    echo    4. Check YOLOv11 model file
    echo    5. Verify Firebase configuration
    echo    6. Check Python dependencies
    echo.
) else (
    echo ✅ System exited normally
)

echo Press any key to exit...
pause >nul