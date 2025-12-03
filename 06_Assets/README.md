# 🎨 Assets

โฟลเดอร์นี้เก็บไฟล์สื่อและทรัพยากรทั้งหมดสำหรับโปรเจกต์

## 📁 โครงสร้างโฟลเดอร์

### 🖼️ Images (`images/`)
- `S__9551875.jpg` - รูปภาพตัวอย่าง
- `back ground.jpg` - รูปพื้นหลัง
- `p2p.jpg` - โลโก้ P2P Detection System
- `ขวด.jpg` - รูปตัวอย่างขวดพลาสติก
- `ขวดโรงเรียน.jpg` - รูปขวดในโรงเรียน
- `อิ่มถ่าย.jpg` - รูปภาพเพิ่มเติม
- `พรีเซ้น qr.png` - QR Code สำหรับการนำเสนอ
- `รูป/` - โฟลเดอร์รูปภาพเพิ่มเติม

### 🔤 Fonts (`fonts/`)
- `Bai_Jamjuree.zip` - ฟอนต์ Bai Jamjuree (ไฟล์บีบอัด)

### 🎵 Audio (`audio/`)
- `relaxing-ambient.mp3` - เสียงบรรยากาศผ่อนคลาย
- `ssvid.net--Fallout-TV-Show-All-Songs.mp3` - เพลงจาก Fallout TV Show
- `ssvid.net--Playlist-아무-생각하기-싫을-때-가만히-듣기-좋은-잔잔한-재즈.mp3` - เพลงแจ๊สเงียบๆ

## 🎯 การใช้งาน

### 🖼️ Images
- **UI Elements** - ใช้ในการออกแบบ User Interface
- **Documentation** - ประกอบเอกสารและการนำเสนอ
- **Training Data** - ข้อมูลสำหรับฝึก AI Model
- **Marketing** - สื่อการตลาดและประชาสัมพันธ์

### 🔤 Fonts
- **Web Typography** - ใช้ในเว็บไซต์และแอปพลิเคชัน
- **Branding** - สร้างเอกลักษณ์ของแบรนด์
- **Documentation** - ใช้ในเอกสารและรายงาน

### 🎵 Audio
- **UI Feedback** - เสียงตอบสนองในระบบ
- **Ambient Sound** - เสียงบรรยากาศ
- **Notifications** - เสียงแจ้งเตือน

## 📏 ข้อมูลไฟล์

### 🖼️ Image Specifications
- **Format**: JPG, PNG
- **Resolution**: Various (optimized for web)
- **Color Space**: sRGB
- **Compression**: Optimized for web delivery

### 🔤 Font Specifications
- **Family**: Bai Jamjuree
- **Weights**: Light, Regular, Medium, Bold
- **Styles**: Normal, Italic
- **Format**: TTF (TrueType Font)
- **Language Support**: Thai, Latin

### 🎵 Audio Specifications
- **Format**: MP3
- **Quality**: 128-320 kbps
- **Sample Rate**: 44.1 kHz
- **Channels**: Stereo

## 🔧 การจัดการไฟล์

### 📦 Optimization
```bash
# บีบอัดรูปภาพ
imagemin images/*.jpg --out-dir=images/optimized

# แปลงฟอร์แมตเสียง
ffmpeg -i audio.mp3 -b:a 128k audio_compressed.mp3
```

### 📁 Organization
- จัดเรียงตามประเภทไฟล์
- ใช้ชื่อไฟล์ที่สื่อความหมาย
- เก็บไฟล์ต้นฉบับแยกจากไฟล์ที่ปรับแต่งแล้ว

## 🎨 Design Guidelines

### 🌈 Color Palette
- **Primary**: #2E7D32 (Green)
- **Secondary**: #1976D2 (Blue)
- **Accent**: #FF6F00 (Orange)
- **Neutral**: #757575 (Gray)

### 📐 Layout
- **Grid System**: 12-column grid
- **Spacing**: 8px base unit
- **Typography**: Bai Jamjuree font family
- **Icons**: Material Design icons

## 📱 Responsive Assets

### 📱 Mobile
- **Images**: 320px - 768px width
- **Touch Targets**: Minimum 44px
- **Font Size**: 16px minimum

### 💻 Desktop
- **Images**: 1024px+ width
- **Font Size**: 14px minimum
- **Line Height**: 1.5

## 🔒 License และ Copyright

### 📄 Font License
- **Bai Jamjuree**: SIL Open Font License 1.1
- **Commercial Use**: Allowed
- **Modification**: Allowed with attribution

### 🖼️ Image Rights
- **Project Images**: Internal use only
- **Stock Photos**: Check individual licenses
- **Generated Content**: Project ownership

### 🎵 Audio Rights
- **Background Music**: Check copyright status
- **Sound Effects**: Royalty-free preferred
- **Voice Recordings**: Project ownership