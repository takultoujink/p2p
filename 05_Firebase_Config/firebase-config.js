// Firebase Configuration - Unified Config
// Project: barcode-me (ระบบเก็บขวดอัตโนมัติ)
// Updated: 2025-12-16
// Version: 4.0

// ⚠️ สำคัญ: ใช้ Config นี้ในทุกไฟล์ของโปรเจค
// - dashboard.html (แสดงผลคะแนน)
// - kiosk.html (สแกนบาร์โค้ด + กล้อง YOLO)
// - admin.html (จัดการระบบ)
// - ไฟล์อื่นๆ ที่ต้องเชื่อมต่อ Firebase

// Import Firebase SDK
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getFirestore, collection, addDoc, query, where, orderBy, getDocs, onSnapshot, serverTimestamp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

// Firebase Configuration
export const firebaseConfig = {
    apiKey: "AIzaSyCcdAiBzbos42JyfueswYOdt1RfUo07igE",
    authDomain: "barcode-me.firebaseapp.com",
    projectId: "barcode-me",
    storageBucket: "barcode-me.firebasestorage.app",
    messagingSenderId: "690530427838",
    appId: "1:690530427838:web:4cf6e8c7b33d7ec3bb35f3"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);

// =====================================================
// 🎯 ฟังก์ชันสำหรับระบบ Kiosk (เครื่องรับขวด)
// =====================================================

/**
 * บันทึกข้อมูลขวดที่ตรวจจับได้
 * @param {string} studentId - รหัสนักเรียนจากบาร์โค้ด
 * @param {number} bottleCount - จำนวนขวดที่ YOLO ตรวจจับได้
 * @param {number} confidence - ความมั่นใจของ AI (0-1)
 * @returns {Promise<string>} - Document ID ที่สร้างใหม่
 */
export async function recordBottles(studentId, bottleCount, confidence = 0.95) {
    try {
        const docRef = await addDoc(collection(db, "bottles"), {
            studentId: studentId,
            count: bottleCount,
            confidence: confidence,
            timestamp: serverTimestamp(),
            source: "kiosk" // ระบุว่ามาจากเครื่อง Kiosk
        });
        
        console.log("✅ บันทึกสำเร็จ:", docRef.id);
        return docRef.id;
    } catch (error) {
        console.error("❌ Error recording bottles:", error);
        throw error;
    }
}

// =====================================================
// 📊 ฟังก์ชันสำหรับ Dashboard
// =====================================================

/**
 * ดึงประวัติการทิ้งขวดของนักเรียน
 * @param {string} studentId - รหัสนักเรียน
 * @param {number} limitCount - จำนวนรายการที่ต้องการ
 * @returns {Promise<Array>} - Array ของข้อมูลขวด
 */
export async function getStudentBottles(studentId, limitCount = 50) {
    try {
        const q = query(
            collection(db, "bottles"),
            where("studentId", "==", studentId),
            orderBy("timestamp", "desc"),
            limit(limitCount)
        );
        
        const querySnapshot = await getDocs(q);
        const bottles = [];
        
        querySnapshot.forEach((doc) => {
            bottles.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        return bottles;
    } catch (error) {
        console.error("❌ Error getting bottles:", error);
        return [];
    }
}

/**
 * ฟังการเปลี่ยนแปลงข้อมูลแบบ Real-time
 * @param {string} studentId - รหัสนักเรียน
 * @param {Function} callback - ฟังก์ชันที่จะถูกเรียกเมื่อมีข้อมูลใหม่
 * @returns {Function} - Unsubscribe function
 */
export function listenToBottles(studentId, callback) {
    const q = query(
        collection(db, "bottles"),
        where("studentId", "==", studentId),
        orderBy("timestamp", "desc")
    );
    
    return onSnapshot(q, (snapshot) => {
        const bottles = [];
        snapshot.forEach((doc) => {
            bottles.push({
                id: doc.id,
                ...doc.data()
            });
        });
        callback(bottles);
    });
}

// =====================================================
// 🔐 ฟังก์ชัน Authentication
// =====================================================

/**
 * Sign in แบบ Anonymous (สำหรับผู้ใช้ทั่วไป)
 */
export async function signInUser() {
    try {
        await signInAnonymously(auth);
        console.log("✅ Signed in successfully");
    } catch (error) {
        console.error("❌ Sign in error:", error);
    }
}

// =====================================================
// 📝 ตัวอย่างการใช้งาน
// =====================================================

/*
// ในหน้า Kiosk
import { recordBottles } from './firebase-config.js';

// เมื่อ YOLO ตรวจจับขวดเสร็จ
async function onBottlesDetected(studentId, bottles) {
    const bottleCount = bottles.length;
    const avgConfidence = bottles.reduce((sum, b) => sum + b.confidence, 0) / bottles.length;
    
    await recordBottles(studentId, bottleCount, avgConfidence);
    alert(`บันทึกสำเร็จ! +${bottleCount} ขวด`);
}

// ในหน้า Dashboard
import { listenToBottles } from './firebase-config.js';

const studentId = localStorage.getItem('studentId');
const unsubscribe = listenToBottles(studentId, (bottles) => {
    console.log('Updated bottles:', bottles);
    updateUI(bottles);
});

// เมื่อออกจากหน้า
// unsubscribe();
*/
