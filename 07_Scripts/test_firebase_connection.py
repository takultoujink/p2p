#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase Connection Test Script
ทดสอบการเชื่อมต่อ Firebase และการบันทึกข้อมูล

Author: YOLOv11 Servo System
Version: 1.0
Date: 2024
"""

import requests
import json
import time
from datetime import datetime
from config_yolo_v11_servo import YOLOv11ServoConfig

def test_firebase_connection():
    """ทดสอบการเชื่อมต่อ Firebase"""
    print("🔥 Firebase Connection Test")
    print("=" * 50)
    
    # โหลด config
    try:
        config = YOLOv11ServoConfig()
        print(f"✅ Config loaded successfully")
        print(f"📍 Firebase URL: {config.firebase_url}")
        print(f"👤 User ID: {config.firebase_user_id}")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # ทดสอบการเชื่อมต่อพื้นฐาน
    print("\n🌐 Testing basic connection...")
    try:
        test_url = f"{config.firebase_url}/.json"
        response = requests.get(test_url, timeout=10)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Basic connection successful")
        else:
            print(f"❌ Basic connection failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # ทดสอบการเขียนข้อมูล
    print("\n📝 Testing data write...")
    try:
        test_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_unix_time": int(time.time()),
            "test_message": "Firebase connection test",
            "bottle_count": 0,
            "servo_position": 90,
            "system_status": "testing"
        }
        
        write_url = f"{config.firebase_url}/connection_test/{config.firebase_user_id}.json"
        print(f"📡 Writing to: {write_url}")
        print(f"📄 Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.put(write_url, json=test_data, timeout=10)
        print(f"📊 Write Response Status: {response.status_code}")
        print(f"📊 Write Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Data write successful")
        else:
            print(f"❌ Data write failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Write error: {e}")
        return False
    
    # ทดสอบการอ่านข้อมูล
    print("\n📖 Testing data read...")
    try:
        read_url = f"{config.firebase_url}/connection_test/{config.firebase_user_id}.json"
        response = requests.get(read_url, timeout=10)
        print(f"📊 Read Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data read successful")
            print(f"📄 Retrieved data: {json.dumps(data, indent=2)}")
            
            # ตรวจสอบว่าข้อมูลที่อ่านตรงกับที่เขียน
            if data and data.get('test_message') == 'Firebase connection test':
                print(f"✅ Data integrity verified")
            else:
                print(f"⚠️ Data integrity issue")
        else:
            print(f"❌ Data read failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Read error: {e}")
        return False
    
    # ทดสอบการเขียนข้อมูลขวด
    print("\n🍼 Testing bottle data write...")
    try:
        bottle_data = {
            "bottle_count": 5,
            "confidence": 0.85,
            "servo_action": "sweep",
            "servo_position": 45,
            "auto_sweep_enabled": True,
            "timestamp": datetime.now().isoformat(),
            "unix_timestamp": int(time.time()),
            "model_version": "YOLOv11",
            "has_servo": True
        }
        
        bottle_url = f"{config.firebase_url}/bottle_servo_data/{config.firebase_user_id}.json"
        print(f"📡 Writing bottle data to: {bottle_url}")
        
        response = requests.put(bottle_url, json=bottle_data, timeout=10)
        print(f"📊 Bottle Data Response Status: {response.status_code}")
        print(f"📊 Bottle Data Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Bottle data write successful")
        else:
            print(f"❌ Bottle data write failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Bottle data write error: {e}")
        return False
    
    print("\n🎉 All Firebase tests passed!")
    return True

def test_network_connectivity():
    """ทดสอบการเชื่อมต่อเครือข่าย"""
    print("\n🌐 Network Connectivity Test")
    print("=" * 50)
    
    test_urls = [
        "https://www.google.com",
        "https://firebase.google.com",
        "https://httpbin.org/get"
    ]
    
    for url in test_urls:
        try:
            print(f"🔗 Testing: {url}")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - OK")
            else:
                print(f"⚠️ {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")

def main():
    """ฟังก์ชันหลัก"""
    print("🧪 Firebase & Network Test Suite")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ทดสอบเครือข่าย
    test_network_connectivity()
    
    # ทดสอบ Firebase
    firebase_success = test_firebase_connection()
    
    print("\n📋 Test Summary")
    print("=" * 50)
    if firebase_success:
        print("✅ Firebase connection: PASSED")
        print("💡 Your Firebase setup is working correctly!")
        print("💡 If the main system still can't save data, check:")
        print("   - YOLOv11 model file exists")
        print("   - Camera is connected")
        print("   - Arduino is connected (if using servo)")
    else:
        print("❌ Firebase connection: FAILED")
        print("💡 Please check:")
        print("   - Internet connection")
        print("   - Firebase URL in config")
        print("   - Firebase database rules")
        print("   - Firewall settings")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()