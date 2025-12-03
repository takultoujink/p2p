# ========================================
# Unit Tests for Arduino Communication
# ========================================

import pytest
import serial
import time
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# เพิ่ม path สำหรับ import modules
sys.path.append(str(Path(__file__).parent.parent / "03_Arduino_Control"))
sys.path.append(str(Path(__file__).parent.parent / "08_Config"))

class TestArduinoCommunication:
    """Test cases สำหรับ Arduino Communication System"""
    
    @pytest.fixture
    def mock_serial(self):
        """Mock serial connection สำหรับ testing"""
        mock_ser = Mock(spec=serial.Serial)
        mock_ser.is_open = True
        mock_ser.in_waiting = 0
        mock_ser.write.return_value = 10
        mock_ser.read.return_value = b'OK\n'
        mock_ser.readline.return_value = b'OK\n'
        return mock_ser
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration สำหรับ testing"""
        config = Mock()
        config.ARDUINO_PORT = "COM3"
        config.ARDUINO_BAUDRATE = 9600
        config.ARDUINO_TIMEOUT = 1.0
        return config
    
    def test_serial_connection_success(self, mock_config):
        """ทดสอบการเชื่อมต่อ Arduino สำเร็จ"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_class.return_value = mock_serial_instance
            
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ตรวจสอบว่า Serial ถูกเรียกด้วยพารามิเตอร์ที่ถูกต้อง
                mock_serial_class.assert_called_once_with(
                    port=mock_config.ARDUINO_PORT,
                    baudrate=mock_config.ARDUINO_BAUDRATE,
                    timeout=mock_config.ARDUINO_TIMEOUT
                )
                assert controller.is_connected()
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_serial_connection_failure(self, mock_config):
        """ทดสอบการเชื่อมต่อ Arduino ล้มเหลว"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_class.side_effect = serial.SerialException("Port not found")
            
            try:
                from arduino_servo_control import ArduinoController
                
                # ควร raise exception หรือ handle error อย่างเหมาะสม
                with pytest.raises((serial.SerialException, ConnectionError)):
                    controller = ArduinoController(mock_config)
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_send_command_success(self, mock_serial, mock_config):
        """ทดสอบการส่งคำสั่งไป Arduino สำเร็จ"""
        with patch('serial.Serial', return_value=mock_serial):
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ทดสอบการส่งคำสั่ง
                command = "SERVO:90"
                result = controller.send_command(command)
                
                # ตรวจสอบว่าคำสั่งถูกส่ง
                mock_serial.write.assert_called()
                assert result is not None
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_send_command_timeout(self, mock_config):
        """ทดสอบการส่งคำสั่งที่ timeout"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_instance.write.return_value = 10
            mock_serial_instance.readline.side_effect = serial.SerialTimeoutException("Timeout")
            mock_serial_class.return_value = mock_serial_instance
            
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ทดสอบการส่งคำสั่งที่ timeout
                command = "SERVO:90"
                result = controller.send_command(command)
                
                # ควรได้ None หรือ error response
                assert result is None or "timeout" in str(result).lower()
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    @pytest.mark.parametrize("angle", [0, 45, 90, 135, 180])
    def test_servo_control_angles(self, mock_serial, mock_config, angle):
        """ทดสอบการควบคุม servo ด้วยมุมต่างๆ"""
        with patch('serial.Serial', return_value=mock_serial):
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ทดสอบการส่งคำสั่งควบคุม servo
                result = controller.move_servo(angle)
                
                # ตรวจสอบว่าคำสั่งถูกส่ง
                mock_serial.write.assert_called()
                expected_command = f"SERVO:{angle}\n".encode()
                
                # ตรวจสอบว่าคำสั่งที่ส่งถูกต้อง
                call_args = mock_serial.write.call_args[0][0]
                assert expected_command in call_args or str(angle) in call_args.decode()
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_servo_angle_validation(self, mock_serial, mock_config):
        """ทดสอบการตรวจสอบมุม servo ที่ถูกต้อง"""
        with patch('serial.Serial', return_value=mock_serial):
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ทดสอบมุมที่ไม่ถูกต้อง
                invalid_angles = [-10, 200, 360, -90]
                
                for angle in invalid_angles:
                    with pytest.raises((ValueError, AssertionError)):
                        controller.move_servo(angle)
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_multiple_commands_sequence(self, mock_serial, mock_config):
        """ทดสอบการส่งคำสั่งหลายคำสั่งติดต่อกัน"""
        with patch('serial.Serial', return_value=mock_serial):
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ส่งคำสั่งหลายคำสั่ง
                commands = ["SERVO:0", "SERVO:90", "SERVO:180"]
                results = []
                
                for command in commands:
                    result = controller.send_command(command)
                    results.append(result)
                    time.sleep(0.1)  # รอระหว่างคำสั่ง
                
                # ตรวจสอบว่าทุกคำสั่งถูกส่ง
                assert len(results) == len(commands)
                assert mock_serial.write.call_count == len(commands)
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_connection_status_check(self, mock_serial, mock_config):
        """ทดสอบการตรวจสอบสถานะการเชื่อมต่อ"""
        with patch('serial.Serial', return_value=mock_serial):
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ทดสอบเมื่อเชื่อมต่อสำเร็จ
                assert controller.is_connected()
                
                # ทดสอบเมื่อการเชื่อมต่อขาด
                mock_serial.is_open = False
                assert not controller.is_connected()
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_reconnection_mechanism(self, mock_config):
        """ทดสอบกลไกการเชื่อมต่อใหม่"""
        with patch('serial.Serial') as mock_serial_class:
            # จำลองการเชื่อมต่อล้มเหลวครั้งแรก แล้วสำเร็จครั้งที่สอง
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            
            mock_serial_class.side_effect = [
                serial.SerialException("Connection failed"),
                mock_serial_instance
            ]
            
            try:
                from arduino_servo_control import ArduinoController
                
                # ทดสอบการ reconnect
                controller = None
                for attempt in range(2):
                    try:
                        controller = ArduinoController(mock_config)
                        break
                    except serial.SerialException:
                        if attempt == 0:
                            continue
                        raise
                
                assert controller is not None
                assert controller.is_connected()
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_command_response_parsing(self, mock_config):
        """ทดสอบการแปลง response จาก Arduino"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_instance.write.return_value = 10
            
            # ทดสอบ response ต่างๆ
            responses = [
                b'OK\n',
                b'ERROR\n',
                b'SERVO_MOVED:90\n',
                b'READY\n'
            ]
            
            mock_serial_instance.readline.side_effect = responses
            mock_serial_class.return_value = mock_serial_instance
            
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ทดสอบการแปลง response แต่ละแบบ
                for expected_response in responses:
                    result = controller.send_command("TEST")
                    
                    # ตรวจสอบว่า response ถูกแปลงถูกต้อง
                    if result:
                        assert isinstance(result, str)
                        assert expected_response.decode().strip() in result
                
            except ImportError:
                pytest.skip("Arduino control module not available")

class TestArduinoProtocol:
    """Test cases สำหรับ Arduino Communication Protocol"""
    
    def test_command_format_validation(self):
        """ทดสอบการตรวจสอบรูปแบบคำสั่ง"""
        valid_commands = [
            "SERVO:90",
            "LED:ON",
            "LED:OFF",
            "STATUS",
            "RESET"
        ]
        
        invalid_commands = [
            "",
            "SERVO",
            "SERVO:",
            "SERVO:ABC",
            "INVALID_COMMAND"
        ]
        
        for command in valid_commands:
            assert self._is_valid_command(command)
        
        for command in invalid_commands:
            assert not self._is_valid_command(command)
    
    def test_response_parsing(self):
        """ทดสอบการแปลง response"""
        test_responses = [
            (b'OK\n', 'OK'),
            (b'ERROR:Invalid command\n', 'ERROR:Invalid command'),
            (b'SERVO_MOVED:90\n', 'SERVO_MOVED:90'),
            (b'', ''),
            (b'READY\r\n', 'READY')
        ]
        
        for raw_response, expected in test_responses:
            parsed = self._parse_response(raw_response)
            assert parsed == expected
    
    def test_checksum_calculation(self):
        """ทดสอบการคำนวณ checksum (ถ้ามี)"""
        commands = [
            "SERVO:90",
            "LED:ON",
            "STATUS"
        ]
        
        for command in commands:
            checksum = self._calculate_checksum(command)
            assert isinstance(checksum, int)
            assert 0 <= checksum <= 255
    
    def _is_valid_command(self, command):
        """ตรวจสอบความถูกต้องของคำสั่ง"""
        if not command or not isinstance(command, str):
            return False
        
        valid_prefixes = ["SERVO:", "LED:", "STATUS", "RESET"]
        
        for prefix in valid_prefixes:
            if command.startswith(prefix):
                if prefix.endswith(":"):
                    # ตรวจสอบว่ามีค่าหลัง :
                    parts = command.split(":")
                    if len(parts) != 2 or not parts[1]:
                        return False
                    
                    # ตรวจสอบค่าเฉพาะสำหรับ SERVO
                    if prefix == "SERVO:":
                        try:
                            angle = int(parts[1])
                            return 0 <= angle <= 180
                        except ValueError:
                            return False
                    
                    # ตรวจสอบค่าเฉพาะสำหรับ LED
                    if prefix == "LED:":
                        return parts[1] in ["ON", "OFF"]
                
                return True
        
        return False
    
    def _parse_response(self, raw_response):
        """แปลง response จาก Arduino"""
        if not raw_response:
            return ""
        
        try:
            decoded = raw_response.decode('utf-8').strip()
            return decoded
        except UnicodeDecodeError:
            return ""
    
    def _calculate_checksum(self, command):
        """คำนวณ checksum ของคำสั่ง"""
        return sum(ord(c) for c in command) % 256

# ========================================
# Performance Tests
# ========================================

@pytest.mark.performance
class TestArduinoPerformance:
    """Performance tests สำหรับ Arduino Communication"""
    
    def test_command_response_time(self, mock_config):
        """ทดสอบเวลาตอบสนองของคำสั่ง"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_instance.write.return_value = 10
            mock_serial_instance.readline.return_value = b'OK\n'
            mock_serial_class.return_value = mock_serial_instance
            
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # วัดเวลาการส่งคำสั่งหลายครั้ง
                times = []
                for _ in range(10):
                    start_time = time.time()
                    controller.send_command("SERVO:90")
                    times.append(time.time() - start_time)
                
                # คำนวณสถิติ
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                print(f"Command response time - Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
                
                # ตรวจสอบว่าเวลาเฉลี่ยไม่เกิน 0.1 วินาที (สำหรับ mock)
                assert avg_time < 0.1
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_throughput_measurement(self, mock_config):
        """ทดสอบ throughput ของการส่งคำสั่ง"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_instance.write.return_value = 10
            mock_serial_instance.readline.return_value = b'OK\n'
            mock_serial_class.return_value = mock_serial_instance
            
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ส่งคำสั่งจำนวนมากในเวลาที่กำหนด
                start_time = time.time()
                command_count = 0
                duration = 1.0  # 1 วินาที
                
                while time.time() - start_time < duration:
                    controller.send_command("STATUS")
                    command_count += 1
                
                throughput = command_count / duration
                print(f"Command throughput: {throughput:.1f} commands/second")
                
                # ตรวจสอบว่า throughput ไม่ต่ำเกินไป
                assert throughput > 10  # อย่างน้อย 10 commands/second
                
            except ImportError:
                pytest.skip("Arduino control module not available")

# ========================================
# Integration Tests
# ========================================

@pytest.mark.integration
class TestArduinoIntegration:
    """Integration tests สำหรับ Arduino Communication"""
    
    def test_full_servo_control_sequence(self, mock_config):
        """ทดสอบลำดับการควบคุม servo แบบเต็ม"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_instance.write.return_value = 10
            mock_serial_instance.readline.return_value = b'OK\n'
            mock_serial_class.return_value = mock_serial_instance
            
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ทดสอบลำดับการควบคุม servo
                sequence = [0, 45, 90, 135, 180, 90, 0]
                
                for angle in sequence:
                    result = controller.move_servo(angle)
                    assert result is not None
                    time.sleep(0.1)  # รอให้ servo เคลื่อนที่
                
                # ตรวจสอบว่าทุกคำสั่งถูกส่ง
                assert mock_serial_instance.write.call_count == len(sequence)
                
            except ImportError:
                pytest.skip("Arduino control module not available")
    
    def test_error_recovery(self, mock_config):
        """ทดสอบการกู้คืนจากข้อผิดพลาด"""
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_instance = Mock()
            mock_serial_instance.is_open = True
            mock_serial_instance.write.return_value = 10
            
            # จำลองการตอบสนองที่มี error แล้วกลับมาปกติ
            responses = [
                b'ERROR\n',
                b'ERROR\n',
                b'OK\n',
                b'OK\n'
            ]
            mock_serial_instance.readline.side_effect = responses
            mock_serial_class.return_value = mock_serial_instance
            
            try:
                from arduino_servo_control import ArduinoController
                controller = ArduinoController(mock_config)
                
                # ส่งคำสั่งหลายครั้ง
                results = []
                for _ in range(4):
                    result = controller.send_command("SERVO:90")
                    results.append(result)
                
                # ตรวจสอบว่าได้รับ response ทั้ง error และ success
                error_count = sum(1 for r in results if r and 'ERROR' in r)
                success_count = sum(1 for r in results if r and 'OK' in r)
                
                assert error_count > 0
                assert success_count > 0
                
            except ImportError:
                pytest.skip("Arduino control module not available")

if __name__ == "__main__":
    # รัน tests
    pytest.main([__file__, "-v", "--tb=short"])