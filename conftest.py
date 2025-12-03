"""Global pytest configuration and fixtures."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import main application
try:
    from main import app
except ImportError:
    # Create a mock app if main.py is not available
    from fastapi import FastAPI
    app = FastAPI()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[TestClient, None]:
    """Create an async test client for the FastAPI application."""
    async with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_arduino():
    """Mock Arduino serial connection."""
    mock = MagicMock()
    mock.is_open = True
    mock.write.return_value = None
    mock.read.return_value = b"OK"
    mock.readline.return_value = b"Arduino Ready\n"
    return mock


@pytest.fixture
def mock_firebase():
    """Mock Firebase connection."""
    mock = AsyncMock()
    mock.put.return_value = {"status": "success"}
    mock.get.return_value = {"data": "test"}
    mock.delete.return_value = {"status": "deleted"}
    return mock


@pytest.fixture
def mock_yolo_model():
    """Mock YOLO model for object detection."""
    mock = MagicMock()
    mock.predict.return_value = [
        MagicMock(
            boxes=MagicMock(
                xyxy=[[100, 100, 200, 200]],
                conf=[0.95],
                cls=[0]
            ),
            names={0: "person"}
        )
    ]
    return mock


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image file for testing."""
    import numpy as np
    from PIL import Image
    
    # Create a simple test image
    image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    image = Image.fromarray(image_array)
    
    image_path = tmp_path / "test_image.jpg"
    image.save(image_path)
    
    return str(image_path)


@pytest.fixture
def sample_video_path(tmp_path):
    """Create a sample video file path for testing."""
    video_path = tmp_path / "test_video.mp4"
    # Create an empty file to simulate video
    video_path.touch()
    return str(video_path)


@pytest.fixture
def test_config():
    """Test configuration dictionary."""
    return {
        "arduino": {
            "port": "/dev/ttyUSB0",
            "baudrate": 9600,
            "timeout": 1.0
        },
        "firebase": {
            "url": "https://test-firebase.firebaseio.com",
            "auth_token": "test_token"
        },
        "yolo": {
            "model_path": "yolov8n.pt",
            "confidence_threshold": 0.5,
            "device": "cpu"
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True
        }
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "ARDUINO_PORT": "/dev/ttyUSB0",
        "ARDUINO_BAUDRATE": "9600",
        "FIREBASE_URL": "https://test-firebase.firebaseio.com",
        "FIREBASE_AUTH_TOKEN": "test_token",
        "YOLO_MODEL_PATH": "yolov8n.pt",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_database():
    """Mock database connection."""
    mock = AsyncMock()
    mock.execute.return_value = None
    mock.fetch.return_value = []
    mock.fetchone.return_value = None
    mock.commit.return_value = None
    mock.rollback.return_value = None
    return mock


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Set up test environment with temporary directories and paths."""
    # Create temporary directories
    test_data_dir = tmp_path / "test_data"
    test_logs_dir = tmp_path / "test_logs"
    test_models_dir = tmp_path / "test_models"
    
    test_data_dir.mkdir()
    test_logs_dir.mkdir()
    test_models_dir.mkdir()
    
    # Set environment variables for test paths
    monkeypatch.setenv("TEST_DATA_DIR", str(test_data_dir))
    monkeypatch.setenv("TEST_LOGS_DIR", str(test_logs_dir))
    monkeypatch.setenv("TEST_MODELS_DIR", str(test_models_dir))
    
    # Change to test directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield {
        "data_dir": test_data_dir,
        "logs_dir": test_logs_dir,
        "models_dir": test_models_dir,
        "tmp_path": tmp_path
    }
    
    # Restore original directory
    os.chdir(original_cwd)


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    mock = MagicMock()
    mock.info.return_value = None
    mock.error.return_value = None
    mock.warning.return_value = None
    mock.debug.return_value = None
    return mock


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "arduino: marks tests that require Arduino hardware"
    )
    config.addinivalue_line(
        "markers", "firebase: marks tests that require Firebase connection"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "arduino" in item.nodeid:
            item.add_marker(pytest.mark.arduino)
        elif "firebase" in item.nodeid:
            item.add_marker(pytest.mark.firebase)
        
        # Add slow marker for tests that might take longer
        if any(keyword in item.nodeid.lower() for keyword in ["slow", "performance", "load"]):
            item.add_marker(pytest.mark.slow)


# Async test support
@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"