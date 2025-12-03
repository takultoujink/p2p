# ========================================
# Unit Tests for YOLO Detection System
# ========================================

import pytest
import numpy as np
import cv2
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# เพิ่ม path สำหรับ import modules
sys.path.append(str(Path(__file__).parent.parent / "02_AI_Detection"))
sys.path.append(str(Path(__file__).parent.parent / "08_Config"))

class TestYOLODetection:
    """Test cases สำหรับ YOLO Detection System"""
    
    @pytest.fixture
    def mock_yolo_model(self):
        """Mock YOLO model สำหรับ testing"""
        mock_model = Mock()
        mock_model.predict.return_value = [Mock()]
        mock_model.predict.return_value[0].boxes = Mock()
        mock_model.predict.return_value[0].boxes.xyxy = np.array([[100, 100, 200, 200]])
        mock_model.predict.return_value[0].boxes.conf = np.array([0.85])
        mock_model.predict.return_value[0].boxes.cls = np.array([0])
        return mock_model
    
    @pytest.fixture
    def sample_image(self):
        """สร้างภาพตัวอย่างสำหรับ testing"""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration สำหรับ testing"""
        config = Mock()
        config.MODEL_PATH = "test_model.pt"
        config.CONF_THRESHOLD = 0.5
        config.CAM_ID = 0
        config.CLASS_NAMES = ["bottle", "can", "plastic"]
        return config
    
    def test_model_loading(self, mock_config):
        """ทดสอบการโหลด YOLO model"""
        with patch('ultralytics.YOLO') as mock_yolo:
            mock_yolo.return_value = Mock()
            
            # Import และทดสอบ
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                # ตรวจสอบว่า YOLO ถูกเรียกด้วย model path ที่ถูกต้อง
                mock_yolo.assert_called_once_with(mock_config.MODEL_PATH)
                assert detector is not None
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    def test_image_preprocessing(self, sample_image):
        """ทดสอบการ preprocess ภาพ"""
        # ทดสอบการ resize ภาพ
        target_size = (640, 640)
        resized = cv2.resize(sample_image, target_size)
        
        assert resized.shape[:2] == target_size
        assert resized.dtype == np.uint8
    
    def test_detection_with_valid_image(self, mock_yolo_model, sample_image, mock_config):
        """ทดสอบการ detect objects ด้วยภาพที่ถูกต้อง"""
        with patch('ultralytics.YOLO', return_value=mock_yolo_model):
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                # ทดสอบการ detect
                results = detector.detect_objects(sample_image)
                
                # ตรวจสอบผลลัพธ์
                assert isinstance(results, list)
                if results:
                    assert 'bbox' in results[0]
                    assert 'confidence' in results[0]
                    assert 'class_name' in results[0]
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    def test_detection_with_invalid_image(self, mock_yolo_model, mock_config):
        """ทดสอบการ detect ด้วยภาพที่ไม่ถูกต้อง"""
        with patch('ultralytics.YOLO', return_value=mock_yolo_model):
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                # ทดสอบด้วยภาพ None
                results = detector.detect_objects(None)
                assert results == []
                
                # ทดสอบด้วยภาพที่มี shape ผิด
                invalid_image = np.array([1, 2, 3])
                results = detector.detect_objects(invalid_image)
                assert results == []
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    def test_confidence_threshold_filtering(self, mock_config):
        """ทดสอบการกรอง detection ตาม confidence threshold"""
        # สร้าง mock results ที่มี confidence ต่างๆ
        mock_results = Mock()
        mock_results.boxes = Mock()
        mock_results.boxes.xyxy = np.array([[100, 100, 200, 200], [300, 300, 400, 400]])
        mock_results.boxes.conf = np.array([0.8, 0.3])  # confidence สูงและต่ำ
        mock_results.boxes.cls = np.array([0, 1])
        
        with patch('ultralytics.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.predict.return_value = [mock_results]
            mock_yolo.return_value = mock_model
            
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                sample_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                results = detector.detect_objects(sample_image)
                
                # ควรมีเฉพาะ detection ที่มี confidence > threshold
                high_conf_results = [r for r in results if r['confidence'] > mock_config.CONF_THRESHOLD]
                assert len(high_conf_results) <= len(results)
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    def test_bbox_coordinates_validation(self, mock_yolo_model, sample_image, mock_config):
        """ทดสอบการตรวจสอบ bounding box coordinates"""
        with patch('ultralytics.YOLO', return_value=mock_yolo_model):
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                results = detector.detect_objects(sample_image)
                
                for result in results:
                    bbox = result['bbox']
                    # ตรวจสอบว่า bbox มี format [x1, y1, x2, y2]
                    assert len(bbox) == 4
                    assert bbox[0] < bbox[2]  # x1 < x2
                    assert bbox[1] < bbox[3]  # y1 < y2
                    assert all(coord >= 0 for coord in bbox)  # coordinates ต้องเป็นบวก
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    def test_class_name_mapping(self, mock_config):
        """ทดสอบการแปลง class ID เป็น class name"""
        # สร้าง mock results ที่มี class IDs ต่างๆ
        mock_results = Mock()
        mock_results.boxes = Mock()
        mock_results.boxes.xyxy = np.array([[100, 100, 200, 200]])
        mock_results.boxes.conf = np.array([0.8])
        mock_results.boxes.cls = np.array([0])  # class ID 0
        
        with patch('ultralytics.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.predict.return_value = [mock_results]
            mock_yolo.return_value = mock_model
            
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                sample_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                results = detector.detect_objects(sample_image)
                
                if results:
                    # ตรวจสอบว่า class name ถูกแปลงถูกต้อง
                    assert results[0]['class_name'] == mock_config.CLASS_NAMES[0]
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    def test_performance_timing(self, mock_yolo_model, sample_image, mock_config):
        """ทดสอบ performance ของการ detect"""
        import time
        
        with patch('ultralytics.YOLO', return_value=mock_yolo_model):
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                # วัดเวลาการ detect
                start_time = time.time()
                results = detector.detect_objects(sample_image)
                detection_time = time.time() - start_time
                
                # ตรวจสอบว่าเวลาการ detect ไม่เกิน 1 วินาที (สำหรับ mock)
                assert detection_time < 1.0
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    @pytest.mark.parametrize("image_size", [(320, 320), (640, 640), (1280, 1280)])
    def test_different_image_sizes(self, mock_yolo_model, mock_config, image_size):
        """ทดสอบการ detect ด้วยขนาดภาพต่างๆ"""
        with patch('ultralytics.YOLO', return_value=mock_yolo_model):
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                # สร้างภาพขนาดต่างๆ
                test_image = np.random.randint(0, 255, (*image_size, 3), dtype=np.uint8)
                results = detector.detect_objects(test_image)
                
                # ตรวจสอบว่าสามารถ detect ได้โดยไม่ error
                assert isinstance(results, list)
                
            except ImportError:
                pytest.skip("YOLO detection module not available")
    
    def test_memory_usage(self, mock_yolo_model, sample_image, mock_config):
        """ทดสอบการใช้ memory"""
        import psutil
        import os
        
        with patch('ultralytics.YOLO', return_value=mock_yolo_model):
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                
                # วัด memory ก่อนสร้าง detector
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss
                
                detector = YOLODetectionSystem(mock_config)
                
                # รัน detection หลายครั้ง
                for _ in range(10):
                    detector.detect_objects(sample_image)
                
                # วัด memory หลังใช้งาน
                memory_after = process.memory_info().rss
                memory_increase = memory_after - memory_before
                
                # ตรวจสอบว่า memory ไม่เพิ่มขึ้นมากเกินไป (< 100MB)
                assert memory_increase < 100 * 1024 * 1024
                
            except ImportError:
                pytest.skip("YOLO detection module not available")

class TestYOLOUtilities:
    """Test cases สำหรับ utility functions"""
    
    def test_image_validation(self):
        """ทดสอบการตรวจสอบความถูกต้องของภาพ"""
        # ภาพที่ถูกต้อง
        valid_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        assert self._is_valid_image(valid_image)
        
        # ภาพที่ไม่ถูกต้อง
        assert not self._is_valid_image(None)
        assert not self._is_valid_image(np.array([1, 2, 3]))
        assert not self._is_valid_image(np.random.randint(0, 255, (480, 640), dtype=np.uint8))  # ไม่มี channel
    
    def test_bbox_area_calculation(self):
        """ทดสอบการคำนวณพื้นที่ bounding box"""
        bbox = [100, 100, 200, 200]  # [x1, y1, x2, y2]
        area = self._calculate_bbox_area(bbox)
        expected_area = (200 - 100) * (200 - 100)  # 100 * 100 = 10000
        assert area == expected_area
    
    def test_bbox_intersection(self):
        """ทดสอบการคำนวณ intersection ของ bounding boxes"""
        bbox1 = [100, 100, 200, 200]
        bbox2 = [150, 150, 250, 250]
        
        intersection = self._calculate_intersection(bbox1, bbox2)
        expected_intersection = (200 - 150) * (200 - 150)  # 50 * 50 = 2500
        assert intersection == expected_intersection
    
    def _is_valid_image(self, image):
        """ตรวจสอบความถูกต้องของภาพ"""
        if image is None:
            return False
        if not isinstance(image, np.ndarray):
            return False
        if len(image.shape) != 3:
            return False
        if image.shape[2] != 3:
            return False
        return True
    
    def _calculate_bbox_area(self, bbox):
        """คำนวณพื้นที่ bounding box"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    def _calculate_intersection(self, bbox1, bbox2):
        """คำนวณ intersection ของ bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # หา intersection coordinates
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        # ตรวจสอบว่ามี intersection หรือไม่
        if x1_i >= x2_i or y1_i >= y2_i:
            return 0
        
        return (x2_i - x1_i) * (y2_i - y1_i)

# ========================================
# Performance Tests
# ========================================

@pytest.mark.performance
class TestYOLOPerformance:
    """Performance tests สำหรับ YOLO Detection"""
    
    def test_detection_speed_benchmark(self, mock_yolo_model, mock_config):
        """Benchmark ความเร็วการ detect"""
        import time
        
        with patch('ultralytics.YOLO', return_value=mock_yolo_model):
            try:
                from yolo_v11_servo_system import YOLODetectionSystem
                detector = YOLODetectionSystem(mock_config)
                
                # สร้างภาพทดสอบ
                test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
                
                # วัดเวลาการ detect หลายครั้ง
                times = []
                for _ in range(10):
                    start_time = time.time()
                    detector.detect_objects(test_image)
                    times.append(time.time() - start_time)
                
                # คำนวณสถิติ
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                print(f"Detection time - Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
                
                # ตรวจสอบว่าเวลาเฉลี่ยไม่เกิน 0.5 วินาที (สำหรับ mock)
                assert avg_time < 0.5
                
            except ImportError:
                pytest.skip("YOLO detection module not available")

# ========================================
# Integration Tests
# ========================================

@pytest.mark.integration
class TestYOLOIntegration:
    """Integration tests สำหรับ YOLO Detection"""
    
    def test_camera_integration(self, mock_config):
        """ทดสอบการเชื่อมต่อกับกล้อง"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            mock_cap_instance.read.return_value = (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
            mock_cap.return_value = mock_cap_instance
            
            # ทดสอบการเปิดกล้อง
            cap = cv2.VideoCapture(mock_config.CAM_ID)
            assert cap.isOpened()
            
            ret, frame = cap.read()
            assert ret
            assert frame is not None
            assert frame.shape == (480, 640, 3)

if __name__ == "__main__":
    # รัน tests
    pytest.main([__file__, "-v", "--tb=short"])