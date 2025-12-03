@echo off
chcp 65001 >nul
color 0A

echo.
echo ████████████████████████████████████████████████████████████████
echo ██                                                            ██
echo ██    🚀 YOLOv11 Arduino Firebase Bridge v3.0                ██
echo ██    🎯 P2P (Plastic to Point) Detection System             ██
echo ██    🤖 Powered by YOLOv11                                  ██
echo ██                                                            ██
echo ████████████████████████████████████████████████████████████████
echo.

echo 🔍 Checking system requirements...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo 📦 Please install Python 3.8 or higher
    echo 🌐 Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found

REM Check if required files exist
if not exist "yolo_v11_arduino_firebase.py" (
    echo ❌ Main Python file not found!
    echo 📁 Please ensure yolo_v11_arduino_firebase.py is in this directory
    pause
    exit /b 1
)

echo ✅ Main Python file found

if not exist "requirements_yolo_v11.txt" (
    echo ⚠️  Requirements file not found
    echo 📦 Will try to run without checking dependencies
) else (
    echo ✅ Requirements file found
    echo 📦 Installing/updating dependencies...
    pip install -r requirements_yolo_v11.txt
    if errorlevel 1 (
        echo ⚠️  Some dependencies might not be installed correctly
        echo 🔄 Continuing anyway...
    )
)

echo.
echo 🎯 Pre-flight checklist:
echo ✓ Ensure your Arduino is connected via USB
echo ✓ Ensure your webcam is connected and working
echo ✓ Ensure you have a YOLOv11 model file (.pt)
echo ✓ Ensure your WiFi is working for Firebase connection
echo.

echo 📋 Configuration tips:
echo 💡 Edit the Config class in yolo_v11_arduino_firebase.py to:
echo    - Set correct COM port (check Device Manager)
echo    - Set correct camera ID (usually 0 or 1)
echo    - Set correct model path
echo    - Set Firebase URL
echo.

echo 🚀 Starting YOLOv11 Detection System...
echo ⏱️  This may take a moment to load the AI model...
echo.
echo 🎮 Controls:
echo    ESC - Quit system
echo    'r' - Reset counter
echo    's' - Show status
echo.
echo 📊 Watch the console for detection results!
echo ════════════════════════════════════════════════════════════════
echo.

REM Start the Python script
python yolo_v11_arduino_firebase.py

echo.
echo ════════════════════════════════════════════════════════════════
echo 🏁 YOLOv11 Detection System has stopped
echo.

if errorlevel 1 (
    echo ❌ System exited with error
    echo 🔧 Check the error messages above
    echo 📖 Refer to README_YOLOv11.md for troubleshooting
) else (
    echo ✅ System exited normally
)

echo.
echo 💡 Tips for next run:
echo    - Check COM port if Arduino connection failed
echo    - Try different camera ID if camera not found
echo    - Ensure model file exists and is correct format
echo    - Check internet connection for Firebase
echo.
echo Press any key to exit...
pause >nul