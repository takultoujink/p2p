"""
🚀 API Documentation System
ระบบเอกสาร API ที่ครอบคลุมพร้อม OpenAPI/Swagger, SDK Generation และ Interactive Examples

Features:
- OpenAPI 3.0 Specification
- Interactive Swagger UI
- SDK Generation (Python, JavaScript, Java, C#)
- Code Examples & Tutorials
- API Testing Tools
- Documentation Versioning
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiofiles
import jinja2
import subprocess
import tempfile
import zipfile
import shutil

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import uvicorn

# Configuration Classes
class DocumentationTheme(str, Enum):
    """Documentation themes"""
    SWAGGER = "swagger"
    REDOC = "redoc"
    RAPIDOC = "rapidoc"
    CUSTOM = "custom"

class SDKLanguage(str, Enum):
    """Supported SDK languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    PHP = "php"
    RUBY = "ruby"

@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    path: str
    method: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = None
    deprecated: bool = False

@dataclass
class APIDocumentationConfig:
    """API documentation configuration"""
    title: str = "AI Detection System API"
    description: str = "Comprehensive API for AI-powered detection system"
    version: str = "1.0.0"
    contact: Dict[str, str] = None
    license: Dict[str, str] = None
    servers: List[Dict[str, str]] = None
    theme: DocumentationTheme = DocumentationTheme.SWAGGER
    enable_try_it_out: bool = True
    enable_sdk_generation: bool = True
    supported_languages: List[SDKLanguage] = None
    output_directory: str = "docs"
    
    def __post_init__(self):
        if self.contact is None:
            self.contact = {
                "name": "API Support",
                "email": "api-support@aidetection.com",
                "url": "https://aidetection.com/support"
            }
        
        if self.license is None:
            self.license = {
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            }
        
        if self.servers is None:
            self.servers = [
                {"url": "https://api.aidetection.com/v1", "description": "Production server"},
                {"url": "https://staging-api.aidetection.com/v1", "description": "Staging server"},
                {"url": "http://localhost:8000", "description": "Development server"}
            ]
        
        if self.supported_languages is None:
            self.supported_languages = [
                SDKLanguage.PYTHON,
                SDKLanguage.JAVASCRIPT,
                SDKLanguage.TYPESCRIPT,
                SDKLanguage.JAVA,
                SDKLanguage.CSHARP
            ]

class OpenAPIGenerator:
    """OpenAPI specification generator"""
    
    def __init__(self, config: APIDocumentationConfig):
        self.config = config
        self.endpoints: List[APIEndpoint] = []
        self.schemas: Dict[str, Any] = {}
        self.security_schemes: Dict[str, Any] = {}
        
    def add_endpoint(self, endpoint: APIEndpoint):
        """Add API endpoint"""
        self.endpoints.append(endpoint)
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add data schema"""
        self.schemas[name] = schema
    
    def add_security_scheme(self, name: str, scheme: Dict[str, Any]):
        """Add security scheme"""
        self.security_schemes[name] = scheme
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": self.config.title,
                "description": self.config.description,
                "version": self.config.version,
                "contact": self.config.contact,
                "license": self.config.license
            },
            "servers": self.config.servers,
            "paths": {},
            "components": {
                "schemas": self.schemas,
                "securitySchemes": self.security_schemes
            },
            "tags": self._generate_tags()
        }
        
        # Add paths
        for endpoint in self.endpoints:
            if endpoint.path not in spec["paths"]:
                spec["paths"][endpoint.path] = {}
            
            spec["paths"][endpoint.path][endpoint.method.lower()] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "parameters": endpoint.parameters or [],
                "responses": endpoint.responses or {"200": {"description": "Success"}},
                "deprecated": endpoint.deprecated
            }
            
            if endpoint.request_body:
                spec["paths"][endpoint.path][endpoint.method.lower()]["requestBody"] = endpoint.request_body
            
            if endpoint.examples:
                spec["paths"][endpoint.path][endpoint.method.lower()]["examples"] = endpoint.examples
        
        return spec
    
    def _generate_tags(self) -> List[Dict[str, str]]:
        """Generate API tags"""
        tags = set()
        for endpoint in self.endpoints:
            tags.update(endpoint.tags)
        
        return [{"name": tag, "description": f"{tag} operations"} for tag in sorted(tags)]
    
    def save_spec(self, format: str = "yaml") -> str:
        """Save OpenAPI specification to file"""
        spec = self.generate_openapi_spec()
        output_dir = Path(self.config.output_directory)
        output_dir.mkdir(exist_ok=True)
        
        if format.lower() == "yaml":
            file_path = output_dir / "openapi.yaml"
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
        else:
            file_path = output_dir / "openapi.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
        
        return str(file_path)

class SDKGenerator:
    """SDK generator for multiple programming languages"""
    
    def __init__(self, config: APIDocumentationConfig):
        self.config = config
        self.openapi_spec: Dict[str, Any] = {}
        self.templates_dir = Path(__file__).parent / "templates" / "sdk"
        
    def set_openapi_spec(self, spec: Dict[str, Any]):
        """Set OpenAPI specification"""
        self.openapi_spec = spec
    
    async def generate_python_sdk(self) -> str:
        """Generate Python SDK"""
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir / "python")
        )
        
        # Generate client class
        client_template = template_env.get_template("client.py.j2")
        client_code = client_template.render(
            spec=self.openapi_spec,
            config=self.config
        )
        
        # Generate models
        models_template = template_env.get_template("models.py.j2")
        models_code = models_template.render(
            schemas=self.openapi_spec.get("components", {}).get("schemas", {})
        )
        
        # Generate setup.py
        setup_template = template_env.get_template("setup.py.j2")
        setup_code = setup_template.render(config=self.config)
        
        # Create SDK package
        sdk_dir = Path(self.config.output_directory) / "sdk" / "python"
        sdk_dir.mkdir(parents=True, exist_ok=True)
        
        # Write files
        async with aiofiles.open(sdk_dir / "client.py", 'w') as f:
            await f.write(client_code)
        
        async with aiofiles.open(sdk_dir / "models.py", 'w') as f:
            await f.write(models_code)
        
        async with aiofiles.open(sdk_dir / "setup.py", 'w') as f:
            await f.write(setup_code)
        
        # Create __init__.py
        init_content = f'''"""
{self.config.title} Python SDK
{self.config.description}
"""

from .client import APIClient
from .models import *

__version__ = "{self.config.version}"
__all__ = ["APIClient"]
'''
        async with aiofiles.open(sdk_dir / "__init__.py", 'w') as f:
            await f.write(init_content)
        
        return str(sdk_dir)
    
    async def generate_javascript_sdk(self) -> str:
        """Generate JavaScript SDK"""
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir / "javascript")
        )
        
        # Generate client
        client_template = template_env.get_template("client.js.j2")
        client_code = client_template.render(
            spec=self.openapi_spec,
            config=self.config
        )
        
        # Generate package.json
        package_template = template_env.get_template("package.json.j2")
        package_code = package_template.render(config=self.config)
        
        # Create SDK package
        sdk_dir = Path(self.config.output_directory) / "sdk" / "javascript"
        sdk_dir.mkdir(parents=True, exist_ok=True)
        
        # Write files
        async with aiofiles.open(sdk_dir / "index.js", 'w') as f:
            await f.write(client_code)
        
        async with aiofiles.open(sdk_dir / "package.json", 'w') as f:
            await f.write(package_code)
        
        return str(sdk_dir)
    
    async def generate_all_sdks(self) -> Dict[str, str]:
        """Generate SDKs for all supported languages"""
        results = {}
        
        for language in self.config.supported_languages:
            if language == SDKLanguage.PYTHON:
                results[language.value] = await self.generate_python_sdk()
            elif language == SDKLanguage.JAVASCRIPT:
                results[language.value] = await self.generate_javascript_sdk()
            # Add more languages as needed
        
        return results

class ExampleGenerator:
    """Generate code examples and tutorials"""
    
    def __init__(self, config: APIDocumentationConfig):
        self.config = config
        self.examples: List[Dict[str, Any]] = []
    
    def add_example(self, name: str, description: str, language: str, code: str, 
                   endpoint: str = None, category: str = "general"):
        """Add code example"""
        example = {
            "name": name,
            "description": description,
            "language": language,
            "code": code,
            "endpoint": endpoint,
            "category": category,
            "created_at": datetime.now().isoformat()
        }
        self.examples.append(example)
    
    def generate_curl_examples(self, endpoints: List[APIEndpoint]) -> List[Dict[str, Any]]:
        """Generate cURL examples for endpoints"""
        curl_examples = []
        
        for endpoint in endpoints:
            curl_cmd = f"curl -X {endpoint.method.upper()} \\\n"
            curl_cmd += f"  '{self.config.servers[0]['url']}{endpoint.path}' \\\n"
            curl_cmd += "  -H 'Content-Type: application/json' \\\n"
            curl_cmd += "  -H 'Authorization: Bearer YOUR_API_KEY'"
            
            if endpoint.request_body:
                curl_cmd += " \\\n  -d '{\n    \"example\": \"data\"\n  }'"
            
            self.add_example(
                name=f"{endpoint.method.upper()} {endpoint.path}",
                description=f"cURL example for {endpoint.summary}",
                language="bash",
                code=curl_cmd,
                endpoint=endpoint.path,
                category="curl"
            )
        
        return [ex for ex in self.examples if ex["category"] == "curl"]
    
    def generate_python_examples(self, endpoints: List[APIEndpoint]) -> List[Dict[str, Any]]:
        """Generate Python examples"""
        python_examples = []
        
        for endpoint in endpoints:
            python_code = f'''import requests

# {endpoint.summary}
url = "{self.config.servers[0]['url']}{endpoint.path}"
headers = {{
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}}

'''
            if endpoint.request_body:
                python_code += '''data = {
    "example": "data"
}

response = requests.{method}(url, headers=headers, json=data)
'''.format(method=endpoint.method.lower())
            else:
                python_code += f'response = requests.{endpoint.method.lower()}(url, headers=headers)\n'
            
            python_code += '''
if response.status_code == 200:
    result = response.json()
    print("Success:", result)
else:
    print("Error:", response.status_code, response.text)
'''
            
            self.add_example(
                name=f"Python - {endpoint.summary}",
                description=f"Python example for {endpoint.summary}",
                language="python",
                code=python_code,
                endpoint=endpoint.path,
                category="python"
            )
        
        return [ex for ex in self.examples if ex["category"] == "python"]
    
    def save_examples(self) -> str:
        """Save examples to file"""
        output_dir = Path(self.config.output_directory) / "examples"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Group examples by category
        examples_by_category = {}
        for example in self.examples:
            category = example["category"]
            if category not in examples_by_category:
                examples_by_category[category] = []
            examples_by_category[category].append(example)
        
        # Save each category
        for category, examples in examples_by_category.items():
            file_path = output_dir / f"{category}_examples.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(examples, f, indent=2, ensure_ascii=False)
        
        # Save all examples
        all_examples_path = output_dir / "all_examples.json"
        with open(all_examples_path, 'w', encoding='utf-8') as f:
            json.dump(self.examples, f, indent=2, ensure_ascii=False)
        
        return str(output_dir)

class DocumentationServer:
    """Documentation server with interactive UI"""
    
    def __init__(self, config: APIDocumentationConfig):
        self.config = config
        self.app = FastAPI(
            title=f"{config.title} - Documentation",
            description="Interactive API Documentation",
            version=config.version
        )
        self.setup_middleware()
        self.setup_routes()
        
    def setup_middleware(self):
        """Setup middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def documentation_home():
            """Documentation home page"""
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{self.config.title} - API Documentation</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ text-align: center; margin-bottom: 40px; }}
                    .nav {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 40px; }}
                    .nav a {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                    .nav a:hover {{ background: #0056b3; }}
                    .section {{ margin-bottom: 30px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{self.config.title}</h1>
                    <p>{self.config.description}</p>
                    <p>Version: {self.config.version}</p>
                </div>
                
                <div class="nav">
                    <a href="/swagger">Swagger UI</a>
                    <a href="/redoc">ReDoc</a>
                    <a href="/rapidoc">RapiDoc</a>
                    <a href="/examples">Code Examples</a>
                    <a href="/sdk">Download SDKs</a>
                </div>
                
                <div class="section">
                    <h2>Quick Start</h2>
                    <p>Get started with our API in minutes:</p>
                    <ol>
                        <li>Get your API key from the dashboard</li>
                        <li>Choose your preferred SDK or use direct HTTP calls</li>
                        <li>Check out the interactive examples</li>
                        <li>Start building amazing applications!</li>
                    </ol>
                </div>
                
                <div class="section">
                    <h2>Available Documentation</h2>
                    <ul>
                        <li><strong>Swagger UI</strong>: Interactive API explorer</li>
                        <li><strong>ReDoc</strong>: Beautiful API documentation</li>
                        <li><strong>RapiDoc</strong>: Modern API documentation</li>
                        <li><strong>Code Examples</strong>: Ready-to-use code snippets</li>
                        <li><strong>SDKs</strong>: Client libraries for popular languages</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            return html_content
        
        @self.app.get("/swagger", response_class=HTMLResponse)
        async def swagger_ui():
            """Swagger UI"""
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Swagger UI</title>
                <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
                <script>
                    SwaggerUIBundle({{
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIBundle.presets.standalone
                        ]
                    }});
                </script>
            </body>
            </html>
            """
        
        @self.app.get("/redoc", response_class=HTMLResponse)
        async def redoc():
            """ReDoc UI"""
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ReDoc</title>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
                <style>
                    body {{ margin: 0; padding: 0; }}
                </style>
            </head>
            <body>
                <redoc spec-url='/openapi.json'></redoc>
                <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
            </body>
            </html>
            """
        
        @self.app.get("/examples")
        async def get_examples():
            """Get code examples"""
            examples_dir = Path(self.config.output_directory) / "examples"
            if not examples_dir.exists():
                raise HTTPException(status_code=404, detail="Examples not found")
            
            examples = {}
            for file_path in examples_dir.glob("*_examples.json"):
                category = file_path.stem.replace("_examples", "")
                with open(file_path, 'r', encoding='utf-8') as f:
                    examples[category] = json.load(f)
            
            return examples
        
        @self.app.get("/sdk")
        async def list_sdks():
            """List available SDKs"""
            sdk_dir = Path(self.config.output_directory) / "sdk"
            if not sdk_dir.exists():
                raise HTTPException(status_code=404, detail="SDKs not found")
            
            sdks = []
            for lang_dir in sdk_dir.iterdir():
                if lang_dir.is_dir():
                    sdks.append({
                        "language": lang_dir.name,
                        "download_url": f"/sdk/download/{lang_dir.name}"
                    })
            
            return {"available_sdks": sdks}
        
        @self.app.get("/sdk/download/{language}")
        async def download_sdk(language: str):
            """Download SDK for specific language"""
            sdk_dir = Path(self.config.output_directory) / "sdk" / language
            if not sdk_dir.exists():
                raise HTTPException(status_code=404, detail=f"SDK for {language} not found")
            
            # Create zip file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                    for file_path in sdk_dir.rglob("*"):
                        if file_path.is_file():
                            zip_file.write(file_path, file_path.relative_to(sdk_dir))
                
                return FileResponse(
                    tmp_file.name,
                    media_type="application/zip",
                    filename=f"{self.config.title.lower().replace(' ', '_')}_{language}_sdk.zip"
                )
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run documentation server"""
        uvicorn.run(self.app, host=host, port=port)

class APIDocumentationManager:
    """Main API documentation manager"""
    
    def __init__(self, config: APIDocumentationConfig = None):
        self.config = config or APIDocumentationConfig()
        self.openapi_generator = OpenAPIGenerator(self.config)
        self.sdk_generator = SDKGenerator(self.config)
        self.example_generator = ExampleGenerator(self.config)
        self.server = DocumentationServer(self.config)
        
    def setup_ai_detection_api(self):
        """Setup AI Detection API endpoints"""
        
        # Authentication endpoints
        self.openapi_generator.add_endpoint(APIEndpoint(
            path="/auth/login",
            method="POST",
            summary="User Login",
            description="Authenticate user and get access token",
            tags=["Authentication"],
            parameters=[],
            request_body={
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "password": {"type": "string", "minLength": 8}
                            },
                            "required": ["email", "password"]
                        }
                    }
                }
            },
            responses={
                "200": {
                    "description": "Login successful",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "access_token": {"type": "string"},
                                    "token_type": {"type": "string"},
                                    "expires_in": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "401": {"description": "Invalid credentials"}
            }
        ))
        
        # Detection endpoints
        self.openapi_generator.add_endpoint(APIEndpoint(
            path="/detect/image",
            method="POST",
            summary="Image Detection",
            description="Detect objects in uploaded image",
            tags=["Detection"],
            parameters=[],
            request_body={
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "image": {"type": "string", "format": "binary"},
                                "model": {"type": "string", "enum": ["yolo", "custom"]},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                            },
                            "required": ["image"]
                        }
                    }
                }
            },
            responses={
                "200": {
                    "description": "Detection successful",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detections": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "class": {"type": "string"},
                                                "confidence": {"type": "number"},
                                                "bbox": {
                                                    "type": "array",
                                                    "items": {"type": "number"}
                                                }
                                            }
                                        }
                                    },
                                    "processing_time": {"type": "number"}
                                }
                            }
                        }
                    }
                }
            }
        ))
        
        # Analytics endpoints
        self.openapi_generator.add_endpoint(APIEndpoint(
            path="/analytics/usage",
            method="GET",
            summary="Usage Analytics",
            description="Get usage statistics and metrics",
            tags=["Analytics"],
            parameters=[
                {
                    "name": "period",
                    "in": "query",
                    "schema": {"type": "string", "enum": ["1h", "24h", "7d", "30d"]},
                    "description": "Time period for analytics"
                }
            ],
            responses={
                "200": {
                    "description": "Analytics data",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "total_requests": {"type": "integer"},
                                    "avg_response_time": {"type": "number"},
                                    "error_rate": {"type": "number"},
                                    "top_endpoints": {"type": "array"}
                                }
                            }
                        }
                    }
                }
            }
        ))
        
        # Add schemas
        self.openapi_generator.add_schema("Detection", {
            "type": "object",
            "properties": {
                "class": {"type": "string", "description": "Detected object class"},
                "confidence": {"type": "number", "description": "Detection confidence score"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Bounding box coordinates [x, y, width, height]"
                }
            }
        })
        
        # Add security schemes
        self.openapi_generator.add_security_scheme("BearerAuth", {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        })
    
    async def generate_documentation(self):
        """Generate complete documentation"""
        print("🚀 Generating API documentation...")
        
        # Setup API endpoints
        self.setup_ai_detection_api()
        
        # Generate OpenAPI spec
        print("📝 Generating OpenAPI specification...")
        spec_path = self.openapi_generator.save_spec("yaml")
        json_spec_path = self.openapi_generator.save_spec("json")
        print(f"✅ OpenAPI spec saved to: {spec_path}")
        
        # Set spec for SDK generator
        spec = self.openapi_generator.generate_openapi_spec()
        self.sdk_generator.set_openapi_spec(spec)
        
        # Generate SDKs
        if self.config.enable_sdk_generation:
            print("🔧 Generating SDKs...")
            sdk_paths = await self.sdk_generator.generate_all_sdks()
            for language, path in sdk_paths.items():
                print(f"✅ {language.title()} SDK generated: {path}")
        
        # Generate examples
        print("📚 Generating code examples...")
        self.example_generator.generate_curl_examples(self.openapi_generator.endpoints)
        self.example_generator.generate_python_examples(self.openapi_generator.endpoints)
        examples_path = self.example_generator.save_examples()
        print(f"✅ Examples saved to: {examples_path}")
        
        print("🎉 Documentation generation completed!")
        return {
            "openapi_spec": spec_path,
            "openapi_json": json_spec_path,
            "sdk_paths": sdk_paths if self.config.enable_sdk_generation else {},
            "examples_path": examples_path
        }
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start documentation server"""
        print(f"🌐 Starting documentation server at http://{host}:{port}")
        self.server.run(host, port)

# Sample data generator
def generate_sample_data():
    """Generate sample API documentation"""
    config = APIDocumentationConfig(
        title="AI Detection System API",
        description="Comprehensive API for AI-powered object detection and analytics",
        version="1.0.0"
    )
    
    return APIDocumentationManager(config)

# Main function
async def main():
    """Main function"""
    print("🚀 AI Detection API Documentation Generator")
    print("=" * 50)
    
    # Create documentation manager
    doc_manager = generate_sample_data()
    
    # Generate documentation
    results = await doc_manager.generate_documentation()
    
    print("\n📊 Generation Results:")
    print(f"OpenAPI Spec: {results['openapi_spec']}")
    print(f"Examples: {results['examples_path']}")
    
    if results['sdk_paths']:
        print("SDKs:")
        for lang, path in results['sdk_paths'].items():
            print(f"  - {lang}: {path}")
    
    # Start server
    print("\n🌐 Starting documentation server...")
    print("Available at:")
    print("  - Home: http://localhost:8080")
    print("  - Swagger UI: http://localhost:8080/swagger")
    print("  - ReDoc: http://localhost:8080/redoc")
    print("  - Examples: http://localhost:8080/examples")
    print("  - SDKs: http://localhost:8080/sdk")
    
    doc_manager.start_server()

if __name__ == "__main__":
    asyncio.run(main())