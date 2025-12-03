// Firebase Configuration for P2P System
// Updated: 2025-01-03
// Version: 3.0

// Import Firebase SDK
import { initializeApp } from 'firebase/app';
import { getDatabase, ref, onValue, set, push, serverTimestamp } from 'firebase/database';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';

// Firebase configuration
// คุณต้องไปที่ Firebase Console เพื่อรับข้อมูลเหล่านี้
// ไปที่: https://console.firebase.google.com/
// เลือกโปรเจคของคุณ > Project Settings > General > Your apps > Firebase SDK snippet

export const firebaseConfig = {
    apiKey: "AIzaSyAmw1lDRZIxYKDblO8nhS3SR5aTVCVPJbg",
    authDomain: "takultoujink.firebaseapp.com",
    projectId: "takultoujink",
    storageBucket: "takultoujink.firebasestorage.app",
    messagingSenderId: "865462073491",
    appId: "1:865462073491:web:5985dfd8a0e91b71fa3566",
    measurementId: "G-ZVXD02VSWF"
};

// วิธีการหาข้อมูล Firebase Config:
// 1. เข้าไปที่ https://console.firebase.google.com/
// 2. เลือกโปรเจคของคุณ
// 3. คลิก Settings (เฟือง) > Project settings
// 4. ไปที่แท็บ General
// 5. เลื่อนลงมาหาส่วน "Your apps"
// 6. คลิก "Config" หรือ "Firebase SDK snippet"
// 7. เลือก "Config"
// 8. คัดลอกข้อมูลมาใส่ที่นี่

// ตัวอย่างการใช้งาน:
/*
const firebaseConfig = {
    apiKey: "AIzaSyBa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    authDomain: "my-project.firebaseapp.com",
    projectId: "my-project",
    storageBucket: "my-project.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:a1b2c3d4e5f6g7h8i9j0k1"
};
*/
