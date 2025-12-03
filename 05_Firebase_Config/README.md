# 🔥 Firebase Configuration

โฟลเดอร์นี้เก็บไฟล์การตั้งค่า Firebase ทั้งหมดสำหรับโปรเจกต์

## 📋 ไฟล์ในโฟลเดอร์

### ⚙️ Configuration Files
- `firebase-config.js` - การตั้งค่า Firebase สำหรับ Web
- `firebase.json` - การตั้งค่า Firebase CLI
- `firestore.indexes.json` - การตั้งค่า Firestore Indexes
- `firestore.rules` - กฎการเข้าถึง Firestore Database

## 🔧 Firebase Services

### 🔐 Authentication
- **Email/Password** - เข้าสู่ระบบด้วยอีเมล
- **Google Sign-in** - เข้าสู่ระบบด้วย Google
- **Anonymous Auth** - เข้าสู่ระบบแบบไม่ระบุตัวตน

### 📊 Firestore Database
- **Real-time Updates** - อัปเดตข้อมูลแบบเรียลไทม์
- **Offline Support** - รองรับการทำงานออฟไลน์
- **Security Rules** - กฎความปลอดภัย

### 🌐 Hosting
- **Static Website** - โฮสต์เว็บไซต์
- **Custom Domain** - โดเมนที่กำหนดเอง
- **SSL Certificate** - ใบรับรอง SSL อัตโนมัติ

## 📁 Database Structure

### 📊 Collections
```
bottles/
├── {bottleId}/
│   ├── timestamp: Date
│   ├── confidence: Number
│   ├── location: GeoPoint
│   ├── processed: Boolean
│   └── image_url: String

users/
├── {userId}/
│   ├── email: String
│   ├── displayName: String
│   ├── role: String
│   └── created_at: Date

statistics/
├── daily/
│   ├── date: String
│   ├── total_bottles: Number
│   └── accuracy: Number
```

## 🔒 Security Rules

### 📝 Firestore Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Bottles data - read for authenticated users
    match /bottles/{bottleId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
        request.auth.token.role == 'admin';
    }
  }
}
```

## ⚙️ Configuration Setup

### 1. Firebase Project Setup
```bash
# ติดตั้ง Firebase CLI
npm install -g firebase-tools

# เข้าสู่ระบบ
firebase login

# เริ่มต้นโปรเจกต์
firebase init
```

### 2. Web App Configuration
```javascript
// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);
```

### 3. Environment Variables
```bash
# .env file
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=your-app-id
```

## 🚀 Deployment

### 📤 Deploy Commands
```bash
# Deploy ทั้งหมด
firebase deploy

# Deploy เฉพาะ Hosting
firebase deploy --only hosting

# Deploy เฉพาะ Firestore Rules
firebase deploy --only firestore:rules

# Deploy เฉพาะ Indexes
firebase deploy --only firestore:indexes
```

## 📊 Monitoring

### 📈 Analytics
- **User Engagement** - การมีส่วนร่วมของผู้ใช้
- **Performance** - ประสิทธิภาพของแอป
- **Crash Reporting** - รายงานข้อผิดพลาด

### 🔍 Debugging
- **Firebase Console** - หน้าจัดการ Firebase
- **Firestore Emulator** - ทดสอบ Firestore ในเครื่อง
- **Auth Emulator** - ทดสอบ Authentication ในเครื่อง

## 🛡️ Best Practices

### 🔐 Security
- ใช้ Security Rules ที่เข้มงวด
- ตรวจสอบสิทธิ์การเข้าถึงข้อมูล
- ไม่เก็บข้อมูลสำคัญใน Client

### ⚡ Performance
- ใช้ Indexes ที่เหมาะสม
- จำกัดขนาดของ Query
- ใช้ Pagination สำหรับข้อมูลจำนวนมาก