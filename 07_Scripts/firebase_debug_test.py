#!/usr/bin/env python3
"""
Firebase Debug Test Script
สำหรับทดสอบการเชื่อมต่อ Firebase และการส่งข้อมูล

Author: P2P Team
Version: Debug 1.0
"""

import requests
import json
from datetime import datetime
import time

class FirebaseDebugTester:
    """ทดสอบการเชื่อมต่อ Firebase"""
    
    def __init__(self):
        # Firebase Settings (เหมือนกับในระบบหลัก)
        self.FIREBASE_URL = "https://takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app"
        self.USER_ID = "yolo_v11_servo_user"
        
        print("🔥 Firebase Debug Tester initialized")
        print(f"📡 Firebase URL: {self.FIREBASE_URL}")
        print(f"👤 User ID: {self.USER_ID}")
        print("="*70)
    
    def test_connection(self):
        """ทดสอบการเชื่อมต่อ Firebase"""
        print("🔍 Testing Firebase connection...")
        
        try:
            # ทดสอบ GET request ก่อน
            test_url = f"{self.FIREBASE_URL}/.json"
            print(f"📡 Testing URL: {test_url}")
            
            response = requests.get(test_url, timeout=10)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Firebase connection successful!")
                try:
                    data = response.json()
                    print(f"📄 Current data structure: {json.dumps(data, indent=2) if data else 'Empty database'}")
                except:
                    print("📄 Response is not valid JSON")
                return True
            else:
                print(f"❌ Firebase connection failed: {response.status_code}")
                print(f"📄 Response text: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def test_write_data(self):
        """ทดสอบการเขียนข้อมูล"""
        print("\n📝 Testing data write...")
        
        # ข้อมูลทดสอบ
        test_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_unix_timestamp": int(time.time()),
            "test_message": "Firebase debug test",
            "bottle_count": 999,
            "total_points": 9990,
            "device": "debug_tester",
            "status": "testing"
        }
        
        try:
            # ทดสอบเขียนข้อมูล
            url = f"{self.FIREBASE_URL}/debug_test/{self.USER_ID}.json"
            print(f"📡 Write URL: {url}")
            print(f"📄 Data to send: {json.dumps(test_data, indent=2)}")
            
            response = requests.put(url, json=test_data, timeout=10)
            
            print(f"📊 Write Response Status: {response.status_code}")
            print(f"📊 Write Response Text: {response.text}")
            
            if response.status_code == 200:
                print("✅ Data write successful!")
                return True
            else:
                print(f"❌ Data write failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Write error: {e}")
            return False
    
    def test_read_data(self):
        """ทดสอบการอ่านข้อมูล"""
        print("\n📖 Testing data read...")
        
        try:
            # อ่านข้อมูลที่เพิ่งเขียน
            url = f"{self.FIREBASE_URL}/debug_test/{self.USER_ID}.json"
            print(f"📡 Read URL: {url}")
            
            response = requests.get(url, timeout=10)
            
            print(f"📊 Read Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Data read successful!")
                print(f"📄 Retrieved data: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ Data read failed: {response.status_code}")
                print(f"📄 Response text: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Read error: {e}")
            return False
    
    def test_bottle_data_structure(self):
        """ทดสอบโครงสร้างข้อมูลขวด"""
        print("\n🍼 Testing bottle data structure...")
        
        # ข้อมูลขวดจำลอง (เหมือนกับในระบบจริง)
        bottle_data = {
            "bottle_count": 5,
            "total_points": 50,
            "last_detection": 1,
            "servo_actions": 5,
            "servo_position": 90,
            "auto_sweep_enabled": True,
            "device": "yolo_v11_servo_python",
            "confidence_threshold": 0.80,
            "model_path": "best.pt",
            "timestamp": datetime.now().isoformat(),
            "unix_timestamp": int(time.time()),
            "model_version": "YOLOv11",
            "has_servo": True
        }
        
        try:
            # เขียนข้อมูลขวด
            url = f"{self.FIREBASE_URL}/bottle_servo_data/{self.USER_ID}.json"
            print(f"📡 Bottle data URL: {url}")
            print(f"📄 Bottle data: {json.dumps(bottle_data, indent=2)}")
            
            response = requests.put(url, json=bottle_data, timeout=10)
            
            print(f"📊 Bottle data Response Status: {response.status_code}")
            print(f"📊 Bottle data Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Bottle data write successful!")
                return True
            else:
                print(f"❌ Bottle data write failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Bottle data error: {e}")
            return False
    
    def check_database_rules(self):
        """ตรวจสอบ Database Rules"""
        print("\n🔒 Checking database rules...")
        
        try:
            # ทดสอบการเข้าถึงโดยไม่มี auth
            test_url = f"{self.FIREBASE_URL}/.json"
            response = requests.get(test_url, timeout=5)
            
            if response.status_code == 200:
                print("✅ Database rules allow public read/write")
                return True
            elif response.status_code == 401:
                print("❌ Database rules require authentication")
                print("💡 Please set Firebase rules to allow public access:")
                print('   {"rules": {".read": true, ".write": true}}')
                return False
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Rules check error: {e}")
            return False
    
    def run_full_test(self):
        """รันการทดสอบทั้งหมด"""
        print("🚀 Starting Firebase Full Test...")
        print("="*70)
        
        tests = [
            ("Connection Test", self.test_connection),
            ("Database Rules Check", self.check_database_rules),
            ("Write Data Test", self.test_write_data),
            ("Read Data Test", self.test_read_data),
            ("Bottle Data Structure Test", self.test_bottle_data_structure)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 50)
            
            try:
                result = test_func()
                results.append((test_name, result))
                
                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                print(f"💥 {test_name}: ERROR - {e}")
                results.append((test_name, False))
        
        # สรุปผลการทดสอบ
        print("\n" + "="*70)
        print("📊 TEST RESULTS SUMMARY")
        print("="*70)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:30} : {status}")
            if result:
                passed += 1
        
        print("-" * 70)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Firebase is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the errors above.")
            print("\n💡 Common solutions:")
            print("   1. Check internet connection")
            print("   2. Verify Firebase URL is correct")
            print("   3. Set Firebase rules to allow public access")
            print("   4. Check if Firebase project is active")
        
        return passed == total

def main():
    """ฟังก์ชันหลัก"""
    print("🔥 Firebase Debug Test Tool")
    print("🎯 Testing Firebase connection and data operations")
    print("="*70)
    
    tester = FirebaseDebugTester()
    
    # รันการทดสอบทั้งหมด
    success = tester.run_full_test()
    
    print("\n" + "="*70)
    if success:
        print("🎉 Firebase is working correctly!")
        print("💡 Your YOLOv11 system should be able to save data to Firebase.")
    else:
        print("❌ Firebase has issues that need to be fixed.")
        print("💡 Please resolve the errors above before running YOLOv11 system.")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()