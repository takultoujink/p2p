# ========================================
# Mobile App Support และ PWA Features
# ========================================

import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
from datetime import datetime, timedelta
import asyncio
import websockets
import qrcode
from PIL import Image
import io

# Import FastAPI components
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent / "08_Config"))
from security_config import SecureConfig

@dataclass
class PWAConfig:
    """คลาสสำหรับ PWA configuration"""
    name: str
    short_name: str
    description: str
    theme_color: str
    background_color: str
    display: str
    orientation: str
    start_url: str
    scope: str
    icons: List[Dict[str, str]]
    categories: List[str]

@dataclass
class MobileFeature:
    """คลาสสำหรับ Mobile feature"""
    name: str
    enabled: bool
    config: Dict[str, Any]
    permissions: List[str]

@dataclass
class NotificationConfig:
    """คลาสสำหรับ Push notification configuration"""
    vapid_public_key: str
    vapid_private_key: str
    vapid_email: str
    enabled: bool

class PWAManager:
    """คลาสสำหรับจัดการ Progressive Web App"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = SecureConfig(config_path)
        self.logger = self._setup_logging()
        
        # Paths
        self.project_root = Path.cwd()
        self.static_dir = self.project_root / "static"
        self.templates_dir = self.project_root / "templates"
        self.mobile_dir = self.project_root / "mobile"
        
        # Create directories
        self.static_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.mobile_dir.mkdir(exist_ok=True)
        
        # PWA Configuration
        self.pwa_config = PWAConfig(
            name="Object Detection App",
            short_name="ObjDetect",
            description="AI-powered object detection application",
            theme_color="#2196F3",
            background_color="#ffffff",
            display="standalone",
            orientation="portrait",
            start_url="/",
            scope="/",
            icons=[
                {
                    "src": "/static/icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png"
                },
                {
                    "src": "/static/icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            categories=["productivity", "utilities", "photo"]
        )
        
        # Mobile features
        self.mobile_features = {
            "camera": MobileFeature(
                name="Camera Access",
                enabled=True,
                config={"quality": 0.8, "max_width": 1920, "max_height": 1080},
                permissions=["camera"]
            ),
            "geolocation": MobileFeature(
                name="Geolocation",
                enabled=True,
                config={"accuracy": "high", "timeout": 10000},
                permissions=["geolocation"]
            ),
            "notifications": MobileFeature(
                name="Push Notifications",
                enabled=True,
                config={"badge": True, "sound": True, "vibrate": True},
                permissions=["notifications"]
            ),
            "offline": MobileFeature(
                name="Offline Support",
                enabled=True,
                config={"cache_size": "50MB", "strategy": "cache_first"},
                permissions=[]
            ),
            "file_access": MobileFeature(
                name="File Access",
                enabled=True,
                config={"accept": "image/*", "multiple": True},
                permissions=["file-system-access"]
            )
        }
    
    def _setup_logging(self) -> logging.Logger:
        """ตั้งค่า logging"""
        logger = logging.getLogger("PWAManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler("pwa_manager.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def generate_manifest(self) -> str:
        """สร้าง Web App Manifest"""
        manifest = {
            "name": self.pwa_config.name,
            "short_name": self.pwa_config.short_name,
            "description": self.pwa_config.description,
            "theme_color": self.pwa_config.theme_color,
            "background_color": self.pwa_config.background_color,
            "display": self.pwa_config.display,
            "orientation": self.pwa_config.orientation,
            "start_url": self.pwa_config.start_url,
            "scope": self.pwa_config.scope,
            "icons": self.pwa_config.icons,
            "categories": self.pwa_config.categories,
            "lang": "th",
            "dir": "ltr",
            "prefer_related_applications": False,
            "related_applications": [],
            "shortcuts": [
                {
                    "name": "Take Photo",
                    "short_name": "Camera",
                    "description": "Take a photo for object detection",
                    "url": "/camera",
                    "icons": [{"src": "/static/icons/camera-icon.png", "sizes": "96x96"}]
                },
                {
                    "name": "Upload Image",
                    "short_name": "Upload",
                    "description": "Upload an image for detection",
                    "url": "/upload",
                    "icons": [{"src": "/static/icons/upload-icon.png", "sizes": "96x96"}]
                },
                {
                    "name": "History",
                    "short_name": "History",
                    "description": "View detection history",
                    "url": "/history",
                    "icons": [{"src": "/static/icons/history-icon.png", "sizes": "96x96"}]
                }
            ],
            "screenshots": [
                {
                    "src": "/static/screenshots/mobile-screenshot-1.png",
                    "sizes": "540x720",
                    "type": "image/png",
                    "form_factor": "narrow"
                },
                {
                    "src": "/static/screenshots/desktop-screenshot-1.png",
                    "sizes": "1280x720",
                    "type": "image/png",
                    "form_factor": "wide"
                }
            ]
        }
        
        return json.dumps(manifest, indent=2)
    
    def generate_service_worker(self) -> str:
        """สร้าง Service Worker"""
        sw_content = f"""// ========================================
// Service Worker for Object Detection PWA
// ========================================

const CACHE_NAME = 'object-detection-v1.0.0';
const STATIC_CACHE = 'static-v1.0.0';
const DYNAMIC_CACHE = 'dynamic-v1.0.0';

// Files to cache
const STATIC_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/camera.js',
    '/static/js/detection.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/offline.html'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
    /\\/api\\/detect/,
    /\\/api\\/history/,
    /\\/api\\/models/
];

// Install event
self.addEventListener('install', event => {{
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {{
                console.log('Caching static files...');
                return cache.addAll(STATIC_FILES);
            }})
            .then(() => {{
                console.log('Static files cached successfully');
                return self.skipWaiting();
            }})
            .catch(error => {{
                console.error('Error caching static files:', error);
            }})
    );
}});

// Activate event
self.addEventListener('activate', event => {{
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {{
                return Promise.all(
                    cacheNames.map(cacheName => {{
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {{
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }}
                    }})
                );
            }})
            .then(() => {{
                console.log('Service Worker activated');
                return self.clients.claim();
            }})
    );
}});

// Fetch event
self.addEventListener('fetch', event => {{
    const {{ request }} = event;
    const url = new URL(request.url);
    
    // Handle different types of requests
    if (request.method === 'GET') {{
        if (STATIC_FILES.includes(url.pathname)) {{
            // Static files - cache first
            event.respondWith(cacheFirst(request));
        }} else if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {{
            // API requests - network first with cache fallback
            event.respondWith(networkFirst(request));
        }} else if (url.pathname.startsWith('/static/')) {{
            // Static assets - cache first
            event.respondWith(cacheFirst(request));
        }} else {{
            // Other requests - network first
            event.respondWith(networkFirst(request));
        }}
    }}
}});

// Cache first strategy
async function cacheFirst(request) {{
    try {{
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {{
            return cachedResponse;
        }}
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {{
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }}
        
        return networkResponse;
    }} catch (error) {{
        console.error('Cache first strategy failed:', error);
        
        // Return offline page for navigation requests
        if (request.destination === 'document') {{
            return caches.match('/offline.html');
        }}
        
        throw error;
    }}
}}

// Network first strategy
async function networkFirst(request) {{
    try {{
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {{
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }}
        
        return networkResponse;
    }} catch (error) {{
        console.log('Network failed, trying cache:', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {{
            return cachedResponse;
        }}
        
        // Return offline page for navigation requests
        if (request.destination === 'document') {{
            return caches.match('/offline.html');
        }}
        
        throw error;
    }}
}}

// Background sync
self.addEventListener('sync', event => {{
    if (event.tag === 'background-detection') {{
        event.waitUntil(processBackgroundDetections());
    }}
}});

// Process background detections
async function processBackgroundDetections() {{
    try {{
        // Get pending detections from IndexedDB
        const pendingDetections = await getPendingDetections();
        
        for (const detection of pendingDetections) {{
            try {{
                const response = await fetch('/api/detect', {{
                    method: 'POST',
                    body: detection.data
                }});
                
                if (response.ok) {{
                    await removePendingDetection(detection.id);
                    
                    // Notify user
                    self.registration.showNotification('Detection Complete', {{
                        body: 'Your background detection has been processed.',
                        icon: '/static/icons/icon-192x192.png',
                        badge: '/static/icons/badge-72x72.png',
                        tag: 'detection-complete'
                    }});
                }}
            }} catch (error) {{
                console.error('Background detection failed:', error);
            }}
        }}
    }} catch (error) {{
        console.error('Background sync failed:', error);
    }}
}}

// Push notification
self.addEventListener('push', event => {{
    console.log('Push notification received');
    
    const options = {{
        body: 'New detection results available',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {{
            url: '/results'
        }},
        actions: [
            {{
                action: 'view',
                title: 'View Results',
                icon: '/static/icons/view-icon.png'
            }},
            {{
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/dismiss-icon.png'
            }}
        ]
    }};
    
    if (event.data) {{
        const data = event.data.json();
        options.body = data.message || options.body;
        options.data = {{ ...options.data, ...data }};
    }}
    
    event.waitUntil(
        self.registration.showNotification('Object Detection', options)
    );
}});

// Notification click
self.addEventListener('notificationclick', event => {{
    console.log('Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'view') {{
        event.waitUntil(
            clients.openWindow(event.notification.data.url || '/')
        );
    }}
}});

// Message from main thread
self.addEventListener('message', event => {{
    if (event.data && event.data.type === 'SKIP_WAITING') {{
        self.skipWaiting();
    }}
}});

// Utility functions for IndexedDB
async function getPendingDetections() {{
    // Implementation for getting pending detections from IndexedDB
    return [];
}}

async function removePendingDetection(id) {{
    // Implementation for removing pending detection from IndexedDB
}}
"""
        
        return sw_content
    
    def generate_mobile_html(self) -> str:
        """สร้าง Mobile-optimized HTML"""
        html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="{self.pwa_config.theme_color}">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="{self.pwa_config.short_name}">
    
    <title>{self.pwa_config.name}</title>
    <meta name="description" content="{self.pwa_config.description}">
    
    <!-- PWA Manifest -->
    <link rel="manifest" href="/manifest.json">
    
    <!-- iOS Icons -->
    <link rel="apple-touch-icon" href="/static/icons/icon-152x152.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/icons/icon-180x180.png">
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" sizes="32x32" href="/static/icons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/icons/favicon-16x16.png">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/static/css/mobile.css">
    <link rel="stylesheet" href="/static/css/components.css">
    
    <!-- Preload critical resources -->
    <link rel="preload" href="/static/js/app.js" as="script">
    <link rel="preload" href="/static/js/camera.js" as="script">
</head>
<body>
    <!-- App Shell -->
    <div id="app" class="app-container">
        <!-- Header -->
        <header class="app-header">
            <div class="header-content">
                <h1 class="app-title">{self.pwa_config.short_name}</h1>
                <div class="header-actions">
                    <button id="install-btn" class="install-btn hidden">
                        <svg class="icon" viewBox="0 0 24 24">
                            <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                        </svg>
                        Install
                    </button>
                    <button id="menu-btn" class="menu-btn">
                        <svg class="icon" viewBox="0 0 24 24">
                            <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </header>
        
        <!-- Navigation -->
        <nav id="nav-menu" class="nav-menu hidden">
            <ul class="nav-list">
                <li><a href="#camera" class="nav-link active">Camera</a></li>
                <li><a href="#upload" class="nav-link">Upload</a></li>
                <li><a href="#history" class="nav-link">History</a></li>
                <li><a href="#settings" class="nav-link">Settings</a></li>
            </ul>
        </nav>
        
        <!-- Main Content -->
        <main class="main-content">
            <!-- Camera Section -->
            <section id="camera-section" class="section active">
                <div class="camera-container">
                    <video id="camera-video" class="camera-video" autoplay playsinline></video>
                    <canvas id="camera-canvas" class="camera-canvas hidden"></canvas>
                    
                    <div class="camera-overlay">
                        <div class="detection-frame"></div>
                        <div class="camera-info">
                            <span id="camera-status">Ready</span>
                        </div>
                    </div>
                    
                    <div class="camera-controls">
                        <button id="switch-camera" class="control-btn">
                            <svg class="icon" viewBox="0 0 24 24">
                                <path d="M20 4h-3.17L15 2H9L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-5 11.5V13H9v2.5L5.5 12 9 8.5V11h6V8.5l3.5 3.5-3.5 3.5z"/>
                            </svg>
                        </button>
                        
                        <button id="capture-btn" class="capture-btn">
                            <div class="capture-ring">
                                <div class="capture-dot"></div>
                            </div>
                        </button>
                        
                        <button id="flash-btn" class="control-btn">
                            <svg class="icon" viewBox="0 0 24 24">
                                <path d="M7 2v11h3v9l7-12h-4l4-8z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </section>
            
            <!-- Upload Section -->
            <section id="upload-section" class="section">
                <div class="upload-container">
                    <div id="drop-zone" class="drop-zone">
                        <svg class="upload-icon" viewBox="0 0 24 24">
                            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                        </svg>
                        <h3>Upload Image</h3>
                        <p>Drag and drop or click to select</p>
                        <input type="file" id="file-input" accept="image/*" multiple>
                    </div>
                    
                    <div id="preview-container" class="preview-container hidden">
                        <div class="preview-images"></div>
                        <button id="process-btn" class="process-btn">Process Images</button>
                    </div>
                </div>
            </section>
            
            <!-- History Section -->
            <section id="history-section" class="section">
                <div class="history-container">
                    <div class="history-header">
                        <h2>Detection History</h2>
                        <button id="clear-history" class="clear-btn">Clear All</button>
                    </div>
                    
                    <div id="history-list" class="history-list">
                        <!-- History items will be loaded here -->
                    </div>
                </div>
            </section>
            
            <!-- Settings Section -->
            <section id="settings-section" class="section">
                <div class="settings-container">
                    <h2>Settings</h2>
                    
                    <div class="settings-group">
                        <h3>Detection</h3>
                        <div class="setting-item">
                            <label for="confidence-threshold">Confidence Threshold</label>
                            <input type="range" id="confidence-threshold" min="0.1" max="1" step="0.1" value="0.5">
                            <span class="setting-value">0.5</span>
                        </div>
                        
                        <div class="setting-item">
                            <label for="max-detections">Max Detections</label>
                            <input type="number" id="max-detections" min="1" max="100" value="10">
                        </div>
                    </div>
                    
                    <div class="settings-group">
                        <h3>Camera</h3>
                        <div class="setting-item">
                            <label for="camera-resolution">Resolution</label>
                            <select id="camera-resolution">
                                <option value="640x480">640x480</option>
                                <option value="1280x720" selected>1280x720</option>
                                <option value="1920x1080">1920x1080</option>
                            </select>
                        </div>
                        
                        <div class="setting-item">
                            <label class="switch">
                                <input type="checkbox" id="auto-detect">
                                <span class="slider"></span>
                            </label>
                            <span>Auto Detection</span>
                        </div>
                    </div>
                    
                    <div class="settings-group">
                        <h3>Notifications</h3>
                        <div class="setting-item">
                            <label class="switch">
                                <input type="checkbox" id="push-notifications">
                                <span class="slider"></span>
                            </label>
                            <span>Push Notifications</span>
                        </div>
                        
                        <div class="setting-item">
                            <label class="switch">
                                <input type="checkbox" id="sound-notifications">
                                <span class="slider"></span>
                            </label>
                            <span>Sound</span>
                        </div>
                    </div>
                </div>
            </section>
        </main>
        
        <!-- Results Modal -->
        <div id="results-modal" class="modal hidden">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Detection Results</h3>
                    <button class="modal-close">&times;</button>
                </div>
                
                <div class="modal-body">
                    <div id="result-image" class="result-image"></div>
                    <div id="result-details" class="result-details"></div>
                </div>
                
                <div class="modal-footer">
                    <button id="save-result" class="btn btn-primary">Save</button>
                    <button id="share-result" class="btn btn-secondary">Share</button>
                </div>
            </div>
        </div>
        
        <!-- Loading Overlay -->
        <div id="loading-overlay" class="loading-overlay hidden">
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p id="loading-text">Processing...</p>
            </div>
        </div>
        
        <!-- Toast Notifications -->
        <div id="toast-container" class="toast-container"></div>
    </div>
    
    <!-- Scripts -->
    <script src="/static/js/app.js"></script>
    <script src="/static/js/camera.js"></script>
    <script src="/static/js/detection.js"></script>
    <script src="/static/js/pwa.js"></script>
    
    <!-- Service Worker Registration -->
    <script>
        if ('serviceWorker' in navigator) {{
            window.addEventListener('load', () => {{
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {{
                        console.log('SW registered: ', registration);
                    }})
                    .catch(registrationError => {{
                        console.log('SW registration failed: ', registrationError);
                    }});
            }});
        }}
    </script>
</body>
</html>
"""
        
        return html_content
    
    def generate_mobile_css(self) -> str:
        """สร้าง Mobile CSS"""
        css_content = f"""/* ========================================
   Mobile Styles for Object Detection PWA
   ======================================== */

:root {{
    --primary-color: {self.pwa_config.theme_color};
    --background-color: {self.pwa_config.background_color};
    --text-color: #333;
    --border-color: #ddd;
    --shadow-color: rgba(0, 0, 0, 0.1);
    --success-color: #4CAF50;
    --warning-color: #FF9800;
    --error-color: #F44336;
    --header-height: 60px;
    --nav-height: 50px;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow-x: hidden;
}}

/* App Container */
.app-container {{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}}

/* Header */
.app-header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--header-height);
    background: var(--primary-color);
    color: white;
    z-index: 1000;
    box-shadow: 0 2px 10px var(--shadow-color);
}}

.header-content {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;
    padding: 0 16px;
}}

.app-title {{
    font-size: 1.2rem;
    font-weight: 600;
}}

.header-actions {{
    display: flex;
    align-items: center;
    gap: 8px;
}}

.install-btn, .menu-btn {{
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    padding: 8px;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.9rem;
    transition: background-color 0.2s;
}}

.install-btn:hover, .menu-btn:hover {{
    background: rgba(255, 255, 255, 0.3);
}}

.icon {{
    width: 20px;
    height: 20px;
    fill: currentColor;
}}

/* Navigation */
.nav-menu {{
    position: fixed;
    top: var(--header-height);
    left: 0;
    right: 0;
    background: white;
    border-bottom: 1px solid var(--border-color);
    z-index: 999;
    transform: translateY(-100%);
    transition: transform 0.3s ease;
}}

.nav-menu.show {{
    transform: translateY(0);
}}

.nav-list {{
    display: flex;
    list-style: none;
    overflow-x: auto;
    padding: 0 16px;
}}

.nav-link {{
    display: block;
    padding: 16px 20px;
    text-decoration: none;
    color: var(--text-color);
    white-space: nowrap;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
}}

.nav-link.active {{
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
}}

/* Main Content */
.main-content {{
    flex: 1;
    margin-top: var(--header-height);
    padding-bottom: 20px;
}}

.section {{
    display: none;
    padding: 20px 16px;
}}

.section.active {{
    display: block;
}}

/* Camera Section */
.camera-container {{
    position: relative;
    width: 100%;
    height: calc(100vh - var(--header-height) - 40px);
    background: #000;
    border-radius: 12px;
    overflow: hidden;
}}

.camera-video {{
    width: 100%;
    height: 100%;
    object-fit: cover;
}}

.camera-canvas {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}}

.camera-overlay {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
}}

.detection-frame {{
    position: absolute;
    top: 50%;
    left: 50%;
    width: 200px;
    height: 200px;
    border: 2px solid var(--primary-color);
    border-radius: 12px;
    transform: translate(-50%, -50%);
    opacity: 0.7;
}}

.camera-info {{
    position: absolute;
    top: 16px;
    left: 16px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.9rem;
}}

.camera-controls {{
    position: absolute;
    bottom: 20px;
    left: 0;
    right: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    pointer-events: auto;
}}

.control-btn {{
    width: 50px;
    height: 50px;
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
}}

.control-btn:hover {{
    background: white;
    transform: scale(1.1);
}}

.capture-btn {{
    width: 80px;
    height: 80px;
    background: none;
    border: none;
    cursor: pointer;
}}

.capture-ring {{
    width: 100%;
    height: 100%;
    border: 4px solid white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}}

.capture-btn:active .capture-ring {{
    transform: scale(0.9);
}}

.capture-dot {{
    width: 60px;
    height: 60px;
    background: white;
    border-radius: 50%;
    transition: all 0.2s;
}}

.capture-btn:active .capture-dot {{
    background: var(--primary-color);
}}

/* Upload Section */
.upload-container {{
    max-width: 500px;
    margin: 0 auto;
}}

.drop-zone {{
    border: 2px dashed var(--border-color);
    border-radius: 12px;
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
}}

.drop-zone:hover,
.drop-zone.dragover {{
    border-color: var(--primary-color);
    background: rgba(33, 150, 243, 0.05);
}}

.upload-icon {{
    width: 64px;
    height: 64px;
    fill: var(--border-color);
    margin-bottom: 16px;
}}

.drop-zone h3 {{
    margin-bottom: 8px;
    color: var(--text-color);
}}

.drop-zone p {{
    color: #666;
    font-size: 0.9rem;
}}

#file-input {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
}}

.preview-container {{
    margin-top: 20px;
}}

.preview-images {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}}

.preview-item {{
    position: relative;
    aspect-ratio: 1;
    border-radius: 8px;
    overflow: hidden;
    background: #f5f5f5;
}}

.preview-item img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
}}

.preview-remove {{
    position: absolute;
    top: 4px;
    right: 4px;
    width: 24px;
    height: 24px;
    background: rgba(244, 67, 54, 0.9);
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    font-size: 12px;
}}

.process-btn {{
    width: 100%;
    padding: 16px;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s;
}}

.process-btn:hover {{
    background: #1976D2;
}}

.process-btn:disabled {{
    background: #ccc;
    cursor: not-allowed;
}}

/* History Section */
.history-container {{
    max-width: 600px;
    margin: 0 auto;
}}

.history-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}}

.history-header h2 {{
    font-size: 1.5rem;
    font-weight: 600;
}}

.clear-btn {{
    background: var(--error-color);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
}}

.history-list {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.history-item {{
    background: white;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 2px 8px var(--shadow-color);
    cursor: pointer;
    transition: transform 0.2s;
}}

.history-item:hover {{
    transform: translateY(-2px);
}}

.history-item-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}}

.history-date {{
    font-size: 0.9rem;
    color: #666;
}}

.history-count {{
    background: var(--primary-color);
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
}}

.history-preview {{
    display: flex;
    gap: 8px;
    overflow-x: auto;
}}

.history-thumbnail {{
    width: 60px;
    height: 60px;
    border-radius: 6px;
    object-fit: cover;
    flex-shrink: 0;
}}

/* Settings Section */
.settings-container {{
    max-width: 500px;
    margin: 0 auto;
}}

.settings-group {{
    margin-bottom: 32px;
}}

.settings-group h3 {{
    font-size: 1.2rem;
    margin-bottom: 16px;
    color: var(--text-color);
}}

.setting-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0;
    border-bottom: 1px solid #f0f0f0;
}}

.setting-item:last-child {{
    border-bottom: none;
}}

.setting-item label {{
    font-weight: 500;
    flex: 1;
}}

.setting-item input[type="range"] {{
    flex: 1;
    margin: 0 12px;
}}

.setting-item input[type="number"],
.setting-item select {{
    padding: 8px 12px;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 0.9rem;
}}

.setting-value {{
    min-width: 40px;
    text-align: center;
    font-weight: 600;
    color: var(--primary-color);
}}

/* Switch Toggle */
.switch {{
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
}}

.switch input {{
    opacity: 0;
    width: 0;
    height: 0;
}}

.slider {{
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: 0.4s;
    border-radius: 24px;
}}

.slider:before {{
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.4s;
    border-radius: 50%;
}}

input:checked + .slider {{
    background-color: var(--primary-color);
}}

input:checked + .slider:before {{
    transform: translateX(26px);
}}

/* Modal */
.modal {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    padding: 20px;
}}

.modal-content {{
    background: white;
    border-radius: 12px;
    width: 100%;
    max-width: 500px;
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}}

.modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
}}

.modal-header h3 {{
    font-size: 1.3rem;
    font-weight: 600;
}}

.modal-close {{
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #666;
    padding: 4px;
}}

.modal-body {{
    flex: 1;
    padding: 20px;
    overflow-y: auto;
}}

.modal-footer {{
    display: flex;
    gap: 12px;
    padding: 20px;
    border-top: 1px solid var(--border-color);
}}

.btn {{
    flex: 1;
    padding: 12px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}}

.btn-primary {{
    background: var(--primary-color);
    color: white;
}}

.btn-primary:hover {{
    background: #1976D2;
}}

.btn-secondary {{
    background: #f5f5f5;
    color: var(--text-color);
}}

.btn-secondary:hover {{
    background: #e0e0e0;
}}

/* Loading Overlay */
.loading-overlay {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 3000;
}}

.loading-spinner {{
    text-align: center;
}}

.spinner {{
    width: 50px;
    height: 50px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
}}

@keyframes spin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}

#loading-text {{
    font-size: 1rem;
    color: var(--text-color);
}}

/* Toast Notifications */
.toast-container {{
    position: fixed;
    top: calc(var(--header-height) + 20px);
    right: 20px;
    z-index: 2500;
    display: flex;
    flex-direction: column;
    gap: 8px;
}}

.toast {{
    background: white;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 4px 12px var(--shadow-color);
    border-left: 4px solid var(--primary-color);
    max-width: 300px;
    animation: slideIn 0.3s ease;
}}

.toast.success {{
    border-left-color: var(--success-color);
}}

.toast.warning {{
    border-left-color: var(--warning-color);
}}

.toast.error {{
    border-left-color: var(--error-color);
}}

@keyframes slideIn {{
    from {{
        transform: translateX(100%);
        opacity: 0;
    }}
    to {{
        transform: translateX(0);
        opacity: 1;
    }}
}}

/* Utility Classes */
.hidden {{
    display: none !important;
}}

.text-center {{
    text-align: center;
}}

.mt-20 {{
    margin-top: 20px;
}}

.mb-20 {{
    margin-bottom: 20px;
}}

/* Responsive Design */
@media (max-width: 480px) {{
    .header-content {{
        padding: 0 12px;
    }}
    
    .section {{
        padding: 16px 12px;
    }}
    
    .camera-controls {{
        gap: 16px;
    }}
    
    .control-btn {{
        width: 45px;
        height: 45px;
    }}
    
    .capture-btn {{
        width: 70px;
        height: 70px;
    }}
    
    .capture-dot {{
        width: 50px;
        height: 50px;
    }}
    
    .modal {{
        padding: 12px;
    }}
    
    .toast-container {{
        right: 12px;
        left: 12px;
    }}
    
    .toast {{
        max-width: none;
    }}
}}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {{
    :root {{
        --background-color: #121212;
        --text-color: #ffffff;
        --border-color: #333;
        --shadow-color: rgba(255, 255, 255, 0.1);
    }}
    
    .nav-menu {{
        background: #1e1e1e;
    }}
    
    .history-item {{
        background: #1e1e1e;
    }}
    
    .modal-content {{
        background: #1e1e1e;
    }}
    
    .toast {{
        background: #1e1e1e;
        color: white;
    }}
}}

/* PWA Install Prompt */
.install-prompt {{
    position: fixed;
    bottom: 20px;
    left: 20px;
    right: 20px;
    background: white;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 20px var(--shadow-color);
    z-index: 1500;
    animation: slideUp 0.3s ease;
}}

@keyframes slideUp {{
    from {{
        transform: translateY(100%);
        opacity: 0;
    }}
    to {{
        transform: translateY(0);
        opacity: 1;
    }}
}}

.install-prompt h4 {{
    margin-bottom: 8px;
    font-size: 1.1rem;
}}

.install-prompt p {{
    margin-bottom: 16px;
    color: #666;
    font-size: 0.9rem;
}}

.install-prompt-actions {{
    display: flex;
    gap: 12px;
}}

.install-prompt-actions button {{
    flex: 1;
    padding: 12px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
}}

.install-prompt-install {{
    background: var(--primary-color);
    color: white;
}}

.install-prompt-dismiss {{
    background: #f5f5f5;
    color: var(--text-color);
}}
"""
        
        return css_content
    
    def generate_pwa_js(self) -> str:
        """สร้าง PWA JavaScript"""
        js_content = """// ========================================
// PWA JavaScript for Object Detection App
// ========================================

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        
        this.init();
    }
    
    init() {
        this.setupInstallPrompt();
        this.setupOfflineHandling();
        this.setupNotifications();
        this.setupBackgroundSync();
        this.setupPeriodicSync();
    }
    
    // Install Prompt
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });
        
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallButton();
            this.showToast('App installed successfully!', 'success');
        });
        
        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            this.isInstalled = true;
            this.hideInstallButton();
        }
    }
    
    showInstallButton() {
        const installBtn = document.getElementById('install-btn');
        if (installBtn) {
            installBtn.classList.remove('hidden');
            installBtn.addEventListener('click', () => this.installApp());
        }
        
        // Show install prompt after delay
        setTimeout(() => {
            this.showInstallPrompt();
        }, 30000); // 30 seconds
    }
    
    hideInstallButton() {
        const installBtn = document.getElementById('install-btn');
        if (installBtn) {
            installBtn.classList.add('hidden');
        }
    }
    
    async installApp() {
        if (!this.deferredPrompt) return;
        
        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
        } else {
            console.log('User dismissed the install prompt');
        }
        
        this.deferredPrompt = null;
    }
    
    showInstallPrompt() {
        if (this.isInstalled || !this.deferredPrompt) return;
        
        const prompt = document.createElement('div');
        prompt.className = 'install-prompt';
        prompt.innerHTML = `
            <h4>Install Object Detection App</h4>
            <p>Install this app on your device for a better experience and offline access.</p>
            <div class="install-prompt-actions">
                <button class="install-prompt-install">Install</button>
                <button class="install-prompt-dismiss">Not Now</button>
            </div>
        `;
        
        document.body.appendChild(prompt);
        
        prompt.querySelector('.install-prompt-install').addEventListener('click', () => {
            this.installApp();
            prompt.remove();
        });
        
        prompt.querySelector('.install-prompt-dismiss').addEventListener('click', () => {
            prompt.remove();
        });
        
        // Auto dismiss after 10 seconds
        setTimeout(() => {
            if (prompt.parentNode) {
                prompt.remove();
            }
        }, 10000);
    }
    
    // Offline Handling
    setupOfflineHandling() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showToast('Back online!', 'success');
            this.syncPendingData();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showToast('You are offline. Some features may be limited.', 'warning');
        });
        
        // Update UI based on connection status
        this.updateConnectionStatus();
    }
    
    updateConnectionStatus() {
        const statusElements = document.querySelectorAll('.connection-status');
        statusElements.forEach(element => {
            element.textContent = this.isOnline ? 'Online' : 'Offline';
            element.className = `connection-status ${this.isOnline ? 'online' : 'offline'}`;
        });
    }
    
    // Notifications
    async setupNotifications() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('Notification permission granted');
                this.setupPushNotifications();
            }
        }
    }
    
    async setupPushNotifications() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            try {
                const registration = await navigator.serviceWorker.ready;
                
                // Check if already subscribed
                let subscription = await registration.pushManager.getSubscription();
                
                if (!subscription) {
                    // Subscribe to push notifications
                    subscription = await registration.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: this.urlBase64ToUint8Array(
                            'YOUR_VAPID_PUBLIC_KEY' // Replace with actual VAPID key
                        )
                    });
                }
                
                // Send subscription to server
                await this.sendSubscriptionToServer(subscription);
                
            } catch (error) {
                console.error('Error setting up push notifications:', error);
            }
        }
    }
    
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
    
    async sendSubscriptionToServer(subscription) {
        try {
            await fetch('/api/push-subscription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(subscription)
            });
        } catch (error) {
            console.error('Error sending subscription to server:', error);
        }
    }
    
    // Background Sync
    setupBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(registration => {
                // Register for background sync when going offline
                window.addEventListener('offline', () => {
                    registration.sync.register('background-detection');
                });
            });
        }
    }
    
    // Periodic Background Sync
    setupPeriodicSync() {
        if ('serviceWorker' in navigator && 'periodicSync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(async registration => {
                try {
                    await registration.periodicSync.register('periodic-cleanup', {
                        minInterval: 24 * 60 * 60 * 1000, // 24 hours
                    });
                } catch (error) {
                    console.log('Periodic background sync not supported:', error);
                }
            });
        }
    }
    
    // Data Sync
    async syncPendingData() {
        if (!this.isOnline) return;
        
        try {
            // Get pending data from IndexedDB
            const pendingData = await this.getPendingData();
            
            for (const item of pendingData) {
                try {
                    await this.uploadData(item);
                    await this.removePendingData(item.id);
                } catch (error) {
                    console.error('Error syncing data:', error);
                }
            }
            
            if (pendingData.length > 0) {
                this.showToast(`Synced ${pendingData.length} pending items`, 'success');
            }
            
        } catch (error) {
            console.error('Error during data sync:', error);
        }
    }
    
    async getPendingData() {
        // Implementation for getting pending data from IndexedDB
        return [];
    }
    
    async uploadData(data) {
        // Implementation for uploading data to server
        const response = await fetch('/api/sync-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
    }
    
    async removePendingData(id) {
        // Implementation for removing data from IndexedDB
    }
    
    // Utility Methods
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        const container = document.getElementById('toast-container');
        if (container) {
            container.appendChild(toast);
            
            // Auto remove after 3 seconds
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 3000);
        }
    }
    
    // Share API
    async shareContent(data) {
        if (navigator.share) {
            try {
                await navigator.share(data);
            } catch (error) {
                console.log('Error sharing:', error);
                this.fallbackShare(data);
            }
        } else {
            this.fallbackShare(data);
        }
    }
    
    fallbackShare(data) {
        // Fallback sharing implementation
        if (navigator.clipboard) {
            navigator.clipboard.writeText(data.url || data.text);
            this.showToast('Link copied to clipboard!', 'success');
        }
    }
    
    // Device Features
    async getDeviceInfo() {
        const info = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            }
        };
        
        // Get battery info if available
        if ('getBattery' in navigator) {
            try {
                const battery = await navigator.getBattery();
                info.battery = {
                    level: battery.level,
                    charging: battery.charging,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime
                };
            } catch (error) {
                console.log('Battery API not available:', error);
            }
        }
        
        // Get network info if available
        if ('connection' in navigator) {
            info.connection = {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt,
                saveData: navigator.connection.saveData
            };
        }
"""