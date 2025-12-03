@echo off
chcp 65001 >nul
color 0A

echo ========================================
echo 🧪 Firebase Connection Test
echo ========================================
echo.

echo 🔍 Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

echo.
echo 🔍 Checking required packages...
python -c "import requests; print('✅ requests package found')"
if errorlevel 1 (
    echo ❌ requests package not found!
    echo 💡 Installing requests...
    pip install requests
)

echo.
echo 🔍 Checking config file...
if not exist "config_yolo_v11_servo.py" (
    echo ❌ Config file not found!
    echo 💡 Please make sure config_yolo_v11_servo.py exists in this directory.
    pause
    exit /b 1
)

echo ✅ Config file found
echo.
echo 🚀 Starting Firebase connection test...
echo ========================================
echo.

python test_firebase_connection.py

echo.
echo ========================================
echo 🏁 Test completed!
echo ========================================
echo.
echo 💡 If the test failed, please check:
echo    - Your internet connection
echo    - Firebase URL in config file
echo    - Firebase database rules
echo.
echo Press any key to exit...
pause >nul