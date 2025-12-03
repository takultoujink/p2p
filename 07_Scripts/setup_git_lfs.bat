@echo off
chcp 65001 >nul
color 0A
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                🔧 Git LFS Setup Tool 🔧                     ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 📁 แก้ไขปัญหาไฟล์ขนาดใหญ่ใน GitHub
echo.
echo ⚠️  ปัญหาที่พบ:
echo    - ssvid.net--Playlist-아무-생각하기-싫을-때-가만히-듣기-좋은-잔잔한-재즈.mp3 (55.40 MB)
echo    - ssvid.net--Fallout-TV-Show-All-Songs.mp3 (101.59 MB)
echo.
echo 🔧 กำลังติดตั้ง Git LFS...
echo.

REM Check if Git LFS is installed
git lfs version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git LFS ยังไม่ได้ติดตั้ง
    echo 📥 กำลังติดตั้ง Git LFS...
    
    REM Try to install Git LFS using winget
    winget install Git.LFS >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️  ไม่สามารถติดตั้ง Git LFS อัตโนมัติได้
        echo 📋 กรุณาติดตั้งด้วยตนเอง:
        echo    1. ไปที่ https://git-lfs.github.com/
        echo    2. ดาวน์โหลดและติดตั้ง Git LFS
        echo    3. รันสคริปต์นี้อีกครั้ง
        echo.
        echo กด Enter เพื่อเปิดหน้าเว็บ Git LFS...
        pause >nul
        start "" "https://git-lfs.github.com/"
        exit /b 1
    )
) else (
    echo ✅ Git LFS ติดตั้งแล้ว
)

echo.
echo 🔧 กำลังตั้งค่า Git LFS...

REM Initialize Git LFS
git lfs install
if %errorlevel% neq 0 (
    echo ❌ ไม่สามารถตั้งค่า Git LFS ได้
    pause
    exit /b 1
)

echo ✅ ตั้งค่า Git LFS เรียบร้อย
echo.
echo 📁 กำลังเพิ่มไฟล์เสียงเข้า Git LFS...

REM Track audio files with Git LFS
git lfs track "*.mp3"
git lfs track "*.wav"
git lfs track "*.flac"
git lfs track "*.m4a"
git lfs track "*.aac"

REM Track other large file types
git lfs track "*.zip"
git lfs track "*.rar"
git lfs track "*.7z"
git lfs track "*.tar.gz"
git lfs track "*.mp4"
git lfs track "*.avi"
git lfs track "*.mov"
git lfs track "*.mkv"
git lfs track "*.jpg" 
git lfs track "*.jpeg"
git lfs track "*.png"
git lfs track "*.gif"
git lfs track "*.bmp"
git lfs track "*.tiff"
git lfs track "*.psd"
git lfs track "*.ai"

echo ✅ เพิ่มไฟล์ประเภทต่างๆ เข้า Git LFS แล้ว
echo.
echo 📋 กำลังเพิ่ม .gitattributes...

REM Add .gitattributes to git
git add .gitattributes
if %errorlevel% neq 0 (
    echo ❌ ไม่สามารถเพิ่ม .gitattributes ได้
    pause
    exit /b 1
)

echo ✅ เพิ่ม .gitattributes เรียบร้อย
echo.
echo 🔄 กำลัง migrate ไฟล์เสียงที่มีอยู่...

REM Migrate existing large files to LFS
git lfs migrate import --include="*.mp3" --everything
if %errorlevel% neq 0 (
    echo ⚠️  การ migrate อาจมีปัญหา แต่จะดำเนินการต่อ
)

echo.
echo 📤 กำลัง commit และ push...

REM Commit the changes
git add .
git commit -m "🔧 Setup Git LFS for large files (audio, video, images)"

REM Push to remote
echo 📤 กำลัง push ไปยัง GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ การ push ล้มเหลว
    echo.
    echo 🔧 วิธีแก้ไขเพิ่มเติม:
    echo    1. ตรวจสอบ internet connection
    echo    2. ตรวจสอบ GitHub credentials
    echo    3. ลองใช้คำสั่ง: git push origin main --force
    echo.
    echo กด Enter เพื่อลอง force push...
    pause >nul
    
    git push origin main --force
    if %errorlevel% neq 0 (
        echo ❌ Force push ยังล้มเหลว
        echo 📞 กรุณาตรวจสอบ:
        echo    - GitHub repository permissions
        echo    - Network connection
        echo    - Git credentials
    ) else (
        echo ✅ Force push สำเร็จ!
    )
) else (
    echo ✅ Push สำเร็จ!
)

echo.
echo 🎉 การตั้งค่า Git LFS เสร็จสิ้น!
echo.
echo 📋 สิ่งที่ทำไปแล้ว:
echo    ✅ ติดตั้งและตั้งค่า Git LFS
echo    ✅ เพิ่มไฟล์เสียงเข้า LFS tracking
echo    ✅ Migrate ไฟล์ที่มีอยู่เข้า LFS
echo    ✅ Commit และ push การเปลี่ยนแปลง
echo.
echo 💡 ตอนนี้คุณสามารถ:
echo    - เพิ่มไฟล์ขนาดใหญ่ได้โดยไม่มีปัญหา
    - Git LFS จะจัดการไฟล์ขนาดใหญ่อัตโนมัติ
echo    - Repository จะมีขนาดเล็กลง
echo.
echo 🔍 ตรวจสอบสถานะ Git LFS:
git lfs ls-files
echo.
echo กด Enter เพื่อปิดหน้าต่าง...
pause >nul