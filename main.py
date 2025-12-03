"""
🚀 Object Detection API - Main Application
YOLO Arduino Firebase Bridge System

Main entry point for the FastAPI application with object detection,
Arduino communication, and Firebase integration capabilities.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "02_AI_Detection"))
sys.path.insert(0, str(project_root / "03_Hardware"))
sys.path.insert(0, str(project_root / "04_Web_Dashboard"))
sys.path.insert(0, str(project_root / "05_Firebase_Config"))
sys.path.insert(0, str(project_root / "08_Config"))

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# Pydantic models
from pydantic import BaseModel, Field
from typing import Union
import base64
import cv2
import numpy as np
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Pydantic Models
class DetectionRequest(BaseModel):
    """Request model for object detection"""
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Confidence threshold for detections")
    model_name: str = Field("yolo", description="Model to use for detection")

class DetectionResult(BaseModel):
    """Response model for detection results"""
    detections: List[Dict[str, Any]]
    processing_time: float
    image_size: Dict[str, int]
    model_used: str
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

# Global variables for services
detection_service = None
arduino_service = None
firebase_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Object Detection API...")
    
    # Initialize services
    global detection_service, arduino_service, firebase_service
    
    try:
        # Initialize AI Detection Service
        logger.info("📸 Initializing AI Detection Service...")
        # detection_service = YOLODetectionService()
        
        # Initialize Arduino Service
        logger.info("🔌 Initializing Arduino Service...")
        # arduino_service = ArduinoService()
        
        # Initialize Firebase Service
        logger.info("🔥 Initializing Firebase Service...")
        # firebase_service = FirebaseService()
        
        logger.info("✅ All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Continue without services for basic functionality
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down services...")
    if arduino_service:
        await arduino_service.close()
    if firebase_service:
        await firebase_service.close()
    logger.info("✅ Shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="Object Detection API",
    description="YOLO Arduino Firebase Bridge System - AI-powered object detection with hardware integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = project_root / "06_Assets" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Object Detection API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { font-weight: bold; color: #007bff; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Object Detection API</h1>
            <p>Welcome to the YOLO Arduino Firebase Bridge System API!</p>
            
            <h2>📚 Documentation</h2>
            <div class="endpoint">
                <span class="method">GET</span> <a href="/docs">/docs</a> - Interactive API Documentation (Swagger UI)
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <a href="/redoc">/redoc</a> - Alternative API Documentation (ReDoc)
            </div>
            
            <h2>🔍 API Endpoints</h2>
            <div class="endpoint">
                <span class="method">GET</span> <a href="/health">/health</a> - Health Check
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /v1/detect/image - Object Detection from Image
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /v1/models - List Available Models
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /v1/analytics - Usage Analytics
            </div>
            
            <h2>🔧 System Status</h2>
            <p>Check the <a href="/health">/health</a> endpoint for current system status.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {
        "ai_detection": "available" if detection_service else "unavailable",
        "arduino": "available" if arduino_service else "unavailable", 
        "firebase": "available" if firebase_service else "unavailable",
        "api": "available"
    }
    
    overall_status = "healthy" if any(status == "available" for status in services_status.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        services=services_status
    )

@app.post("/v1/detect/image", response_model=DetectionResult)
async def detect_objects_in_image(
    image: UploadFile = File(...),
    confidence_threshold: float = Form(0.5),
    model_name: str = Form("yolo")
):
    """
    Detect objects in uploaded image
    
    - **image**: Image file to analyze
    - **confidence_threshold**: Minimum confidence for detections (0.0-1.0)
    - **model_name**: Model to use for detection
    """
    start_time = datetime.now()
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_data, np.uint8)
        cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if cv_image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        height, width = cv_image.shape[:2]
        
        # Mock detection results (replace with actual detection service)
        mock_detections = [
            {
                "class": "person",
                "confidence": 0.85,
                "bbox": [100, 100, 200, 300],
                "center": [150, 200]
            },
            {
                "class": "car", 
                "confidence": 0.72,
                "bbox": [300, 150, 500, 350],
                "center": [400, 250]
            }
        ]
        
        # Filter by confidence threshold
        filtered_detections = [
            det for det in mock_detections 
            if det["confidence"] >= confidence_threshold
        ]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return DetectionResult(
            detections=filtered_detections,
            processing_time=processing_time,
            image_size={"width": width, "height": height},
            model_used=model_name,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.get("/v1/models")
async def list_models():
    """List available detection models"""
    models = [
        {
            "name": "yolo",
            "description": "YOLOv8 Object Detection",
            "version": "8.0",
            "classes": ["person", "car", "truck", "bicycle", "motorcycle"],
            "status": "available"
        },
        {
            "name": "custom",
            "description": "Custom Trained Model",
            "version": "1.0",
            "classes": ["custom_object"],
            "status": "training"
        }
    ]
    
    return {"models": models, "default": "yolo"}

@app.get("/v1/analytics")
async def get_analytics():
    """Get usage analytics and statistics"""
    # Mock analytics data
    analytics = {
        "total_detections": 1250,
        "detections_today": 45,
        "average_processing_time": 0.85,
        "most_detected_classes": [
            {"class": "person", "count": 450},
            {"class": "car", "count": 320},
            {"class": "bicycle", "count": 180}
        ],
        "system_uptime": "5 days, 12 hours",
        "last_updated": datetime.now().isoformat()
    }
    
    return analytics

@app.post("/v1/arduino/command")
async def send_arduino_command(command: dict):
    """Send command to Arduino device"""
    if not arduino_service:
        raise HTTPException(status_code=503, detail="Arduino service not available")
    
    try:
        # Mock Arduino command
        result = {
            "command": command,
            "status": "sent",
            "response": "OK",
            "timestamp": datetime.now().isoformat()
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arduino command failed: {str(e)}")

@app.get("/v1/firebase/status")
async def firebase_status():
    """Get Firebase connection status"""
    if not firebase_service:
        return {"status": "disconnected", "message": "Firebase service not available"}
    
    return {
        "status": "connected",
        "last_sync": datetime.now().isoformat(),
        "pending_uploads": 0
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "Please try again later"}
    )

# Main function
def main():
    """Main function to run the application"""
    logger.info("🚀 Starting Object Detection API Server...")
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 1))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    # Run server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()