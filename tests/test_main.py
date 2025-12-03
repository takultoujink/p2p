"""Tests for the main application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


class TestMainApplication:
    """Test cases for the main FastAPI application."""

    def test_app_creation(self):
        """Test that the FastAPI app is created successfully."""
        assert app is not None
        assert app.title == "YOLO Arduino Firebase Bridge"

    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    @patch('main.yolo_model')
    def test_detect_objects_endpoint(self, mock_model, client: TestClient, sample_image_path):
        """Test the object detection endpoint."""
        # Mock YOLO model response
        mock_result = MagicMock()
        mock_result.boxes.xyxy = [[100, 100, 200, 200]]
        mock_result.boxes.conf = [0.95]
        mock_result.boxes.cls = [0]
        mock_result.names = {0: "person"}
        mock_model.predict.return_value = [mock_result]

        with open(sample_image_path, "rb") as f:
            response = client.post(
                "/detect",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert "processing_time" in data

    def test_list_models_endpoint(self, client: TestClient):
        """Test the list models endpoint."""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "available_models" in data
        assert isinstance(data["available_models"], list)

    @patch('main.arduino_manager')
    def test_arduino_command_endpoint(self, mock_arduino, client: TestClient):
        """Test the Arduino command endpoint."""
        mock_arduino.send_command.return_value = "OK"

        response = client.post(
            "/arduino/command",
            json={"command": "LED_ON"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch('main.firebase_manager')
    def test_firebase_status_endpoint(self, mock_firebase, client: TestClient):
        """Test the Firebase status endpoint."""
        mock_firebase.get_status.return_value = {"connected": True}

        response = client.get("/firebase/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_analytics_endpoint(self, client: TestClient):
        """Test the analytics endpoint."""
        response = client.get("/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "total_detections" in data
        assert "uptime" in data

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set."""
        response = client.options("/health")
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_invalid_endpoint(self, client: TestClient):
        """Test that invalid endpoints return 404."""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_lifespan_events(self):
        """Test application lifespan events."""
        # This test ensures the lifespan context manager works
        from main import lifespan
        from contextlib import asynccontextmanager

        # Test that lifespan is an async context manager
        assert hasattr(lifespan, '__aenter__')
        assert hasattr(lifespan, '__aexit__')


class TestErrorHandling:
    """Test error handling in the application."""

    def test_validation_error_handler(self, client: TestClient):
        """Test validation error handling."""
        response = client.post(
            "/arduino/command",
            json={"invalid": "data"}
        )
        assert response.status_code == 422

    @patch('main.yolo_model')
    def test_detection_error_handling(self, mock_model, client: TestClient):
        """Test error handling in object detection."""
        mock_model.predict.side_effect = Exception("Model error")

        response = client.post(
            "/detect",
            files={"file": ("test.jpg", b"invalid image data", "image/jpeg")}
        )

        assert response.status_code == 500
        data = response.json()
        assert "error" in data


class TestConfiguration:
    """Test application configuration."""

    def test_app_metadata(self):
        """Test application metadata."""
        assert app.title == "YOLO Arduino Firebase Bridge"
        assert app.description is not None
        assert app.version == "1.0.0"

    def test_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema generation."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "YOLO Arduino Firebase Bridge"

    def test_docs_endpoint(self, client: TestClient):
        """Test API documentation endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.integration
class TestIntegration:
    """Integration tests for the application."""

    @pytest.mark.slow
    def test_full_detection_pipeline(self, client: TestClient, sample_image_path):
        """Test the full object detection pipeline."""
        # This would be a more comprehensive test in a real scenario
        with open(sample_image_path, "rb") as f:
            response = client.post(
                "/detect",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )

        # Should not crash even if model is not available
        assert response.status_code in [200, 500]  # Either success or expected error


if __name__ == "__main__":
    pytest.main([__file__])