# 🌐 Web Dashboard

โฟลเดอร์นี้เก็บไฟล์ HTML และ Web Interface ทั้งหมดสำหรับระบบ Dashboard

## 📋 ไฟล์ในโฟลเดอร์

### 🏠 Main Pages
- `index.html` - หน้าแรกของเว็บไซต์
- `dashboard.html` - หน้า Dashboard หลัก
- `login.html` - หน้าเข้าสู่ระบบ
- `register.html` - หน้าสมัครสมาชิก
- `reset-password.html` - หน้ารีเซ็ตรหัสผ่าน

### 🧪 Test Pages
- `check_firebase_domains.html` - ทดสอบการเชื่อมต่อ Firebase Domains
- `loader-test.html` - ทดสอบ Loading Animation
- `test-team-color.html` - ทดสอบสีของทีม

## 🎨 Features

### 📊 Dashboard Features
- **Real-time Data Visualization** - แสดงข้อมูลแบบเรียลไทม์
- **Bottle Detection Statistics** - สถิติการตรวจจับขวด
- **System Status Monitoring** - ติดตามสถานะระบบ
- **Historical Data Charts** - กราฟข้อมูลย้อนหลัง

### 🔐 Authentication
- **User Login/Register** - ระบบเข้าสู่ระบบ
- **Password Reset** - รีเซ็ตรหัสผ่าน
- **Session Management** - จัดการ Session ผู้ใช้
- **Role-based Access** - การเข้าถึงตามสิทธิ์

### 📱 Responsive Design
- **Mobile Friendly** - รองรับมือถือ
- **Tablet Optimized** - เหมาะสำหรับแท็บเล็ต
- **Desktop Experience** - ประสบการณ์บนเดสก์ท็อป

## 🛠️ Technology Stack

### 🎨 Frontend
- **HTML5** - โครงสร้างหน้าเว็บ
- **CSS3** - การจัดรูปแบบ
- **JavaScript** - การทำงานแบบ Interactive
- **Bootstrap** - Framework สำหรับ Responsive Design

### 🔥 Backend Integration
- **Firebase Authentication** - ระบบ Authentication
- **Firestore Database** - ฐานข้อมูล
- **Firebase Hosting** - การ Host เว็บไซต์
- **Real-time Database** - ข้อมูลแบบเรียลไทม์

## 📊 Dashboard Sections

### 📈 Analytics
- จำนวนขวดที่ตรวจจับได้
- อัตราความแม่นยำ
- สถิติรายวัน/รายเดือน
- กราฟแนวโน้ม

### ⚙️ System Control
- เปิด/ปิดระบบตรวจจับ
- ปรับตั้งค่าความไว
- ควบคุม Servo Motors
- ตั้งค่าการแจ้งเตือน

### 👥 User Management
- จัดการผู้ใช้งาน
- กำหนดสิทธิ์การเข้าถึง
- ประวัติการใช้งาน
- การตั้งค่าโปรไฟล์

## 🚀 การติดตั้งและใช้งาน

### 1. Local Development
```bash
# เปิดไฟล์ HTML ในเบราว์เซอร์
open index.html
```

### 2. Firebase Hosting
```bash
# Deploy ไปยัง Firebase
firebase deploy --only hosting
```

### 3. Live Server (VS Code)
```bash
# ใช้ Live Server Extension
Right-click on index.html -> Open with Live Server
```

## 🔧 Configuration

### 🔥 Firebase Config
```javascript
// firebase-config.js
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  databaseURL: "your-database-url",
  projectId: "your-project-id"
};
```

### 🎨 Styling
- **Primary Color**: #2E7D32 (Green)
- **Secondary Color**: #1976D2 (Blue)
- **Accent Color**: #FF6F00 (Orange)
- **Background**: #F5F5F5 (Light Gray)

## 📱 Browser Support

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+
- ✅ Mobile Browsers