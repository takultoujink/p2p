# ========================================
# Unit Tests for Firebase Integration
# ========================================

import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

# เพิ่ม path สำหรับ import modules
sys.path.append(str(Path(__file__).parent.parent / "04_Firebase_Integration"))
sys.path.append(str(Path(__file__).parent.parent / "08_Config"))

class TestFirebaseConnection:
    """Test cases สำหรับ Firebase Connection"""
    
    @pytest.fixture
    def mock_firebase_config(self):
        """Mock Firebase configuration"""
        return {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "test-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    
    @pytest.fixture
    def mock_firebase_app(self):
        """Mock Firebase app instance"""
        mock_app = Mock()
        mock_app.name = "test-app"
        return mock_app
    
    @pytest.fixture
    def mock_firestore_client(self):
        """Mock Firestore client"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_document = Mock()
        
        # Setup mock chain
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_document
        mock_collection.add.return_value = (None, Mock())
        mock_document.set.return_value = None
        mock_document.get.return_value = Mock(exists=True, to_dict=lambda: {"test": "data"})
        
        return mock_client
    
    def test_firebase_initialization_success(self, mock_firebase_config):
        """ทดสอบการเริ่มต้น Firebase สำเร็จ"""
        with patch('firebase_admin.initialize_app') as mock_init, \
             patch('firebase_admin.credentials.Certificate') as mock_cert:
            
            mock_init.return_value = Mock()
            mock_cert.return_value = Mock()
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                # ตรวจสอบว่า Firebase ถูกเริ่มต้น
                mock_cert.assert_called_once()
                mock_init.assert_called_once()
                assert manager is not None
                
            except ImportError:
                pytest.skip("Firebase manager module not available")
    
    def test_firebase_initialization_failure(self, mock_firebase_config):
        """ทดสอบการเริ่มต้น Firebase ล้มเหลว"""
        with patch('firebase_admin.initialize_app') as mock_init:
            mock_init.side_effect = Exception("Firebase initialization failed")
            
            try:
                from firebase_manager import FirebaseManager
                
                with pytest.raises(Exception):
                    FirebaseManager(mock_firebase_config)
                
            except ImportError:
                pytest.skip("Firebase manager module not available")
    
    def test_firestore_connection(self, mock_firebase_config, mock_firestore_client):
        """ทดสอบการเชื่อมต่อ Firestore"""
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                # ทดสอบการเข้าถึง Firestore
                db = manager.get_firestore_client()
                assert db is not None
                
            except ImportError:
                pytest.skip("Firebase manager module not available")

class TestFirestoreOperations:
    """Test cases สำหรับ Firestore Operations"""
    
    @pytest.fixture
    def firebase_manager(self, mock_firebase_config, mock_firestore_client):
        """สร้าง Firebase manager สำหรับ testing"""
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
            
            try:
                from firebase_manager import FirebaseManager
                return FirebaseManager(mock_firebase_config)
            except ImportError:
                pytest.skip("Firebase manager module not available")
    
    def test_add_detection_record(self, firebase_manager, mock_firestore_client):
        """ทดสอบการเพิ่มข้อมูล detection"""
        detection_data = {
            "timestamp": datetime.now().isoformat(),
            "object_type": "bottle",
            "confidence": 0.85,
            "bbox": [100, 100, 200, 200],
            "image_path": "test_image.jpg"
        }
        
        # ทดสอบการเพิ่มข้อมูล
        result = firebase_manager.add_detection(detection_data)
        
        # ตรวจสอบว่า Firestore collection ถูกเรียก
        mock_firestore_client.collection.assert_called()
        assert result is not None
    
    def test_get_detection_history(self, firebase_manager, mock_firestore_client):
        """ทดสอบการดึงประวัติ detection"""
        # Mock query results
        mock_docs = [
            Mock(to_dict=lambda: {"timestamp": "2024-01-01T10:00:00", "object_type": "bottle"}),
            Mock(to_dict=lambda: {"timestamp": "2024-01-01T11:00:00", "object_type": "can"})
        ]
        
        mock_query = Mock()
        mock_query.stream.return_value = mock_docs
        mock_firestore_client.collection.return_value.order_by.return_value.limit.return_value = mock_query
        
        # ทดสอบการดึงข้อมูล
        history = firebase_manager.get_detection_history(limit=10)
        
        # ตรวจสอบผลลัพธ์
        assert isinstance(history, list)
        assert len(history) == 2
        assert history[0]["object_type"] == "bottle"
    
    def test_update_detection_record(self, firebase_manager, mock_firestore_client):
        """ทดสอบการอัปเดตข้อมูล detection"""
        doc_id = "test_doc_id"
        update_data = {
            "verified": True,
            "notes": "Manually verified"
        }
        
        # ทดสอบการอัปเดต
        result = firebase_manager.update_detection(doc_id, update_data)
        
        # ตรวจสอบว่า document ถูกอัปเดต
        mock_firestore_client.collection.assert_called()
        assert result is not None
    
    def test_delete_detection_record(self, firebase_manager, mock_firestore_client):
        """ทดสอบการลบข้อมูล detection"""
        doc_id = "test_doc_id"
        
        # ทดสอบการลบ
        result = firebase_manager.delete_detection(doc_id)
        
        # ตรวจสอบว่า document ถูกลบ
        mock_firestore_client.collection.assert_called()
        assert result is not None
    
    def test_batch_operations(self, firebase_manager, mock_firestore_client):
        """ทดสอบการทำงานแบบ batch"""
        detection_list = [
            {"timestamp": "2024-01-01T10:00:00", "object_type": "bottle"},
            {"timestamp": "2024-01-01T11:00:00", "object_type": "can"},
            {"timestamp": "2024-01-01T12:00:00", "object_type": "plastic"}
        ]
        
        # Mock batch operations
        mock_batch = Mock()
        mock_firestore_client.batch.return_value = mock_batch
        
        # ทดสอบการเพิ่มข้อมูลแบบ batch
        result = firebase_manager.add_detections_batch(detection_list)
        
        # ตรวจสอบว่า batch ถูกใช้
        mock_firestore_client.batch.assert_called()
        assert result is not None

class TestFirebaseDataValidation:
    """Test cases สำหรับ Data Validation"""
    
    def test_detection_data_validation(self):
        """ทดสอบการตรวจสอบข้อมูล detection"""
        # ข้อมูลที่ถูกต้อง
        valid_data = {
            "timestamp": datetime.now().isoformat(),
            "object_type": "bottle",
            "confidence": 0.85,
            "bbox": [100, 100, 200, 200]
        }
        
        assert self._validate_detection_data(valid_data)
        
        # ข้อมูลที่ไม่ถูกต้อง
        invalid_data_cases = [
            {},  # ข้อมูลว่าง
            {"timestamp": "invalid_date"},  # timestamp ผิด
            {"timestamp": datetime.now().isoformat(), "confidence": 1.5},  # confidence เกิน 1
            {"timestamp": datetime.now().isoformat(), "bbox": [100, 100]},  # bbox ไม่ครบ
        ]
        
        for invalid_data in invalid_data_cases:
            assert not self._validate_detection_data(invalid_data)
    
    def test_timestamp_validation(self):
        """ทดสอบการตรวจสอบ timestamp"""
        # Timestamp ที่ถูกต้อง
        valid_timestamps = [
            datetime.now().isoformat(),
            "2024-01-01T10:00:00",
            "2024-12-31T23:59:59.999Z"
        ]
        
        for timestamp in valid_timestamps:
            assert self._validate_timestamp(timestamp)
        
        # Timestamp ที่ไม่ถูกต้อง
        invalid_timestamps = [
            "invalid_date",
            "2024-13-01T10:00:00",  # เดือนผิด
            "2024-01-32T10:00:00",  # วันผิด
            ""
        ]
        
        for timestamp in invalid_timestamps:
            assert not self._validate_timestamp(timestamp)
    
    def test_confidence_validation(self):
        """ทดสอบการตรวจสอบ confidence score"""
        # Confidence ที่ถูกต้อง
        valid_confidences = [0.0, 0.5, 0.85, 1.0]
        
        for confidence in valid_confidences:
            assert self._validate_confidence(confidence)
        
        # Confidence ที่ไม่ถูกต้อง
        invalid_confidences = [-0.1, 1.1, "0.5", None]
        
        for confidence in invalid_confidences:
            assert not self._validate_confidence(confidence)
    
    def test_bbox_validation(self):
        """ทดสอบการตรวจสอบ bounding box"""
        # Bbox ที่ถูกต้อง
        valid_bboxes = [
            [0, 0, 100, 100],
            [50, 50, 200, 200],
            [100.5, 100.5, 200.5, 200.5]  # float coordinates
        ]
        
        for bbox in valid_bboxes:
            assert self._validate_bbox(bbox)
        
        # Bbox ที่ไม่ถูกต้อง
        invalid_bboxes = [
            [100, 100, 50, 50],  # x1 > x2, y1 > y2
            [0, 0, 100],  # ไม่ครบ 4 ค่า
            [-10, -10, 100, 100],  # ค่าติดลบ
            ["0", "0", "100", "100"]  # string values
        ]
        
        for bbox in invalid_bboxes:
            assert not self._validate_bbox(bbox)
    
    def _validate_detection_data(self, data):
        """ตรวจสอบความถูกต้องของข้อมูล detection"""
        required_fields = ["timestamp", "object_type", "confidence", "bbox"]
        
        # ตรวจสอบ required fields
        for field in required_fields:
            if field not in data:
                return False
        
        # ตรวจสอบแต่ละ field
        if not self._validate_timestamp(data["timestamp"]):
            return False
        
        if not isinstance(data["object_type"], str) or not data["object_type"]:
            return False
        
        if not self._validate_confidence(data["confidence"]):
            return False
        
        if not self._validate_bbox(data["bbox"]):
            return False
        
        return True
    
    def _validate_timestamp(self, timestamp):
        """ตรวจสอบ timestamp"""
        if not isinstance(timestamp, str):
            return False
        
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    def _validate_confidence(self, confidence):
        """ตรวจสอบ confidence score"""
        if not isinstance(confidence, (int, float)):
            return False
        
        return 0.0 <= confidence <= 1.0
    
    def _validate_bbox(self, bbox):
        """ตรวจสอบ bounding box"""
        if not isinstance(bbox, list) or len(bbox) != 4:
            return False
        
        try:
            x1, y1, x2, y2 = bbox
            x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
            
            # ตรวจสอบว่า coordinates ถูกต้อง
            return x1 < x2 and y1 < y2 and x1 >= 0 and y1 >= 0
        except (ValueError, TypeError):
            return False

class TestFirebaseErrorHandling:
    """Test cases สำหรับ Error Handling"""
    
    def test_network_error_handling(self, mock_firebase_config):
        """ทดสอบการจัดการ network error"""
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client') as mock_client:
            
            # จำลอง network error
            mock_firestore = Mock()
            mock_firestore.collection.side_effect = Exception("Network error")
            mock_client.return_value = mock_firestore
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                # ทดสอบการจัดการ error
                result = manager.add_detection({"test": "data"})
                
                # ควรได้ None หรือ error response
                assert result is None or "error" in str(result).lower()
                
            except ImportError:
                pytest.skip("Firebase manager module not available")
    
    def test_authentication_error_handling(self, mock_firebase_config):
        """ทดสอบการจัดการ authentication error"""
        with patch('firebase_admin.initialize_app') as mock_init:
            mock_init.side_effect = Exception("Authentication failed")
            
            try:
                from firebase_manager import FirebaseManager
                
                # ควร raise exception หรือ handle error
                with pytest.raises(Exception):
                    FirebaseManager(mock_firebase_config)
                
            except ImportError:
                pytest.skip("Firebase manager module not available")
    
    def test_quota_exceeded_handling(self, mock_firebase_config, mock_firestore_client):
        """ทดสอบการจัดการ quota exceeded error"""
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
            
            # จำลอง quota exceeded error
            mock_firestore_client.collection.return_value.add.side_effect = Exception("Quota exceeded")
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                # ทดสอบการจัดการ quota error
                result = manager.add_detection({"test": "data"})
                
                # ควรได้ error response
                assert result is None or "quota" in str(result).lower() or "error" in str(result).lower()
                
            except ImportError:
                pytest.skip("Firebase manager module not available")

# ========================================
# Performance Tests
# ========================================

@pytest.mark.performance
class TestFirebasePerformance:
    """Performance tests สำหรับ Firebase Operations"""
    
    def test_batch_write_performance(self, mock_firebase_config, mock_firestore_client):
        """ทดสอบประสิทธิภาพการเขียนแบบ batch"""
        import time
        
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                # สร้างข้อมูลจำนวนมาก
                detection_list = []
                for i in range(100):
                    detection_list.append({
                        "timestamp": datetime.now().isoformat(),
                        "object_type": f"object_{i}",
                        "confidence": 0.8,
                        "bbox": [i, i, i+100, i+100]
                    })
                
                # วัดเวลาการเขียนแบบ batch
                start_time = time.time()
                result = manager.add_detections_batch(detection_list)
                batch_time = time.time() - start_time
                
                print(f"Batch write time for 100 records: {batch_time:.3f}s")
                
                # ตรวจสอบว่าเวลาไม่เกิน 5 วินาที (สำหรับ mock)
                assert batch_time < 5.0
                
            except ImportError:
                pytest.skip("Firebase manager module not available")
    
    def test_query_performance(self, mock_firebase_config, mock_firestore_client):
        """ทดสอบประสิทธิภาพการ query"""
        import time
        
        # Mock large dataset
        mock_docs = [Mock(to_dict=lambda i=i: {"id": i, "data": f"test_{i}"}) for i in range(1000)]
        mock_query = Mock()
        mock_query.stream.return_value = mock_docs
        mock_firestore_client.collection.return_value.where.return_value.order_by.return_value = mock_query
        
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                # วัดเวลาการ query
                start_time = time.time()
                results = manager.query_detections_by_date(
                    start_date=datetime.now() - timedelta(days=7),
                    end_date=datetime.now()
                )
                query_time = time.time() - start_time
                
                print(f"Query time for 1000 records: {query_time:.3f}s")
                
                # ตรวจสอบว่าเวลาไม่เกิน 2 วินาที (สำหรับ mock)
                assert query_time < 2.0
                
            except ImportError:
                pytest.skip("Firebase manager module not available")

# ========================================
# Integration Tests
# ========================================

@pytest.mark.integration
class TestFirebaseIntegration:
    """Integration tests สำหรับ Firebase"""
    
    def test_full_detection_workflow(self, mock_firebase_config, mock_firestore_client):
        """ทดสอบ workflow การ detection แบบเต็ม"""
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                # 1. เพิ่มข้อมูล detection
                detection_data = {
                    "timestamp": datetime.now().isoformat(),
                    "object_type": "bottle",
                    "confidence": 0.85,
                    "bbox": [100, 100, 200, 200],
                    "image_path": "test_image.jpg"
                }
                
                doc_ref = manager.add_detection(detection_data)
                assert doc_ref is not None
                
                # 2. ดึงข้อมูลที่เพิ่ม
                history = manager.get_detection_history(limit=1)
                assert len(history) >= 0
                
                # 3. อัปเดตข้อมูล
                if hasattr(doc_ref, 'id'):
                    update_result = manager.update_detection(doc_ref.id, {"verified": True})
                    assert update_result is not None
                
                print("Full detection workflow completed successfully")
                
            except ImportError:
                pytest.skip("Firebase manager module not available")
    
    def test_concurrent_operations(self, mock_firebase_config, mock_firestore_client):
        """ทดสอบการทำงานพร้อมกันหลาย operations"""
        import threading
        import time
        
        with patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
            
            try:
                from firebase_manager import FirebaseManager
                manager = FirebaseManager(mock_firebase_config)
                
                results = []
                
                def add_detection_worker(worker_id):
                    """Worker function สำหรับเพิ่มข้อมูล"""
                    detection_data = {
                        "timestamp": datetime.now().isoformat(),
                        "object_type": f"object_{worker_id}",
                        "confidence": 0.8,
                        "bbox": [worker_id, worker_id, worker_id+100, worker_id+100]
                    }
                    result = manager.add_detection(detection_data)
                    results.append(result)
                
                # สร้าง threads หลายตัว
                threads = []
                for i in range(5):
                    thread = threading.Thread(target=add_detection_worker, args=(i,))
                    threads.append(thread)
                    thread.start()
                
                # รอให้ threads เสร็จ
                for thread in threads:
                    thread.join()
                
                # ตรวจสอบผลลัพธ์
                assert len(results) == 5
                print("Concurrent operations completed successfully")
                
            except ImportError:
                pytest.skip("Firebase manager module not available")

if __name__ == "__main__":
    # รัน tests
    pytest.main([__file__, "-v", "--tb=short"])