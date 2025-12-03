"""
Test Configuration Management System
Comprehensive configuration for all testing scenarios
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEnvironment(Enum):
    """Test environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"
    CI = "ci"

class TestType(Enum):
    """Test types"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    E2E = "e2e"
    SECURITY = "security"
    LOAD = "load"
    STRESS = "stress"

class BrowserType(Enum):
    """Supported browser types"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"

@dataclass
class DatabaseConfig:
    """Database configuration for testing"""
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "test_db"
    username: str = "test_user"
    password: str = "test_password"
    connection_pool_size: int = 10
    timeout: int = 30
    
    def get_connection_string(self) -> str:
        """Get database connection string"""
        if self.type == "sqlite":
            return f"sqlite:///{self.database}.db"
        elif self.type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == "mysql":
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")

@dataclass
class APIConfig:
    """API configuration for testing"""
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    headers: Dict[str, str] = field(default_factory=lambda: {
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    auth_token: Optional[str] = None
    verify_ssl: bool = True
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication if available"""
        headers = self.headers.copy()
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

@dataclass
class PerformanceThresholds:
    """Performance testing thresholds"""
    response_time_ms: float = 2000.0  # milliseconds
    memory_usage_mb: float = 500.0    # megabytes
    cpu_usage_percent: float = 80.0   # percentage
    accuracy_threshold: float = 0.95  # detection accuracy
    throughput_rps: float = 100.0     # requests per second
    error_rate_percent: float = 1.0   # error rate percentage
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class LoadTestConfig:
    """Load testing configuration"""
    concurrent_users: int = 10
    ramp_up_time: int = 60  # seconds
    test_duration: int = 300  # seconds
    requests_per_user: int = 100
    think_time: float = 1.0  # seconds between requests
    spawn_rate: float = 1.0  # users per second
    
    def get_total_requests(self) -> int:
        """Calculate total requests"""
        return self.concurrent_users * self.requests_per_user

@dataclass
class BrowserConfig:
    """Browser configuration for E2E testing"""
    browser_type: BrowserType = BrowserType.CHROME
    headless: bool = True
    window_width: int = 1920
    window_height: int = 1080
    implicit_wait: int = 10
    page_load_timeout: int = 30
    script_timeout: int = 30
    download_directory: Optional[str] = None
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    
    def get_chrome_options(self) -> List[str]:
        """Get Chrome browser options"""
        options = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            f"--window-size={self.window_width},{self.window_height}"
        ]
        
        if self.headless:
            options.append("--headless")
        
        if self.user_agent:
            options.append(f"--user-agent={self.user_agent}")
        
        if self.proxy:
            options.append(f"--proxy-server={self.proxy}")
        
        if self.download_directory:
            options.append(f"--download-directory={self.download_directory}")
        
        return options

@dataclass
class TestDataConfig:
    """Test data configuration"""
    test_data_path: str = "test_data"
    test_images_path: str = "test_data/images"
    test_videos_path: str = "test_data/videos"
    test_documents_path: str = "test_data/documents"
    fixtures_path: str = "test_data/fixtures"
    mock_data_path: str = "test_data/mocks"
    sample_size: int = 100
    generate_test_data: bool = True
    
    def ensure_directories(self):
        """Ensure all test data directories exist"""
        paths = [
            self.test_data_path,
            self.test_images_path,
            self.test_videos_path,
            self.test_documents_path,
            self.fixtures_path,
            self.mock_data_path
        ]
        
        for path in paths:
            Path(path).mkdir(parents=True, exist_ok=True)

@dataclass
class ReportingConfig:
    """Test reporting configuration"""
    output_path: str = "test_results"
    report_format: List[str] = field(default_factory=lambda: ["json", "html", "xml"])
    include_screenshots: bool = True
    include_logs: bool = True
    include_metrics: bool = True
    generate_charts: bool = True
    email_reports: bool = False
    email_recipients: List[str] = field(default_factory=list)
    slack_webhook: Optional[str] = None
    
    def ensure_output_directory(self):
        """Ensure output directory exists"""
        Path(self.output_path).mkdir(parents=True, exist_ok=True)

@dataclass
class SecurityTestConfig:
    """Security testing configuration"""
    enable_security_tests: bool = True
    sql_injection_tests: bool = True
    xss_tests: bool = True
    csrf_tests: bool = True
    authentication_tests: bool = True
    authorization_tests: bool = True
    input_validation_tests: bool = True
    rate_limiting_tests: bool = True
    ssl_tests: bool = True
    
    def get_enabled_tests(self) -> List[str]:
        """Get list of enabled security tests"""
        enabled = []
        if self.sql_injection_tests:
            enabled.append("sql_injection")
        if self.xss_tests:
            enabled.append("xss")
        if self.csrf_tests:
            enabled.append("csrf")
        if self.authentication_tests:
            enabled.append("authentication")
        if self.authorization_tests:
            enabled.append("authorization")
        if self.input_validation_tests:
            enabled.append("input_validation")
        if self.rate_limiting_tests:
            enabled.append("rate_limiting")
        if self.ssl_tests:
            enabled.append("ssl")
        return enabled

@dataclass
class CIConfig:
    """CI/CD configuration"""
    enable_ci_mode: bool = False
    parallel_execution: bool = True
    max_workers: int = 4
    fail_fast: bool = False
    retry_failed_tests: bool = True
    max_retries: int = 2
    coverage_threshold: float = 80.0
    quality_gate_enabled: bool = True
    
    def is_ci_environment(self) -> bool:
        """Check if running in CI environment"""
        ci_indicators = [
            "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS",
            "GITLAB_CI", "JENKINS_URL", "TRAVIS", "CIRCLECI"
        ]
        return any(os.getenv(indicator) for indicator in ci_indicators)

@dataclass
class TestConfig:
    """Main test configuration class"""
    environment: TestEnvironment = TestEnvironment.LOCAL
    enabled_test_types: List[TestType] = field(default_factory=lambda: [
        TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE, TestType.E2E
    ])
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    performance: PerformanceThresholds = field(default_factory=PerformanceThresholds)
    load_test: LoadTestConfig = field(default_factory=LoadTestConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    test_data: TestDataConfig = field(default_factory=TestDataConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    security: SecurityTestConfig = field(default_factory=SecurityTestConfig)
    ci: CIConfig = field(default_factory=CIConfig)
    
    # General settings
    debug_mode: bool = False
    verbose_logging: bool = False
    log_level: str = "INFO"
    random_seed: int = 42
    
    def __post_init__(self):
        """Post-initialization setup"""
        self.test_data.ensure_directories()
        self.reporting.ensure_output_directory()
        
        # Set CI mode if detected
        if self.ci.is_ci_environment():
            self.ci.enable_ci_mode = True
            self.browser.headless = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert configuration to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def to_yaml(self) -> str:
        """Convert configuration to YAML string"""
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfig':
        """Create configuration from dictionary"""
        # Convert nested dictionaries to dataclass instances
        if 'database' in data:
            data['database'] = DatabaseConfig(**data['database'])
        if 'api' in data:
            data['api'] = APIConfig(**data['api'])
        if 'performance' in data:
            data['performance'] = PerformanceThresholds(**data['performance'])
        if 'load_test' in data:
            data['load_test'] = LoadTestConfig(**data['load_test'])
        if 'browser' in data:
            data['browser'] = BrowserConfig(**data['browser'])
        if 'test_data' in data:
            data['test_data'] = TestDataConfig(**data['test_data'])
        if 'reporting' in data:
            data['reporting'] = ReportingConfig(**data['reporting'])
        if 'security' in data:
            data['security'] = SecurityTestConfig(**data['security'])
        if 'ci' in data:
            data['ci'] = CIConfig(**data['ci'])
        
        # Convert enum strings back to enums
        if 'environment' in data and isinstance(data['environment'], str):
            data['environment'] = TestEnvironment(data['environment'])
        if 'enabled_test_types' in data:
            data['enabled_test_types'] = [
                TestType(t) if isinstance(t, str) else t 
                for t in data['enabled_test_types']
            ]
        if 'browser' in data and 'browser_type' in data['browser']:
            if isinstance(data['browser']['browser_type'], str):
                data['browser']['browser_type'] = BrowserType(data['browser']['browser_type'])
        
        return cls(**data)
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'TestConfig':
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_yaml_file(cls, file_path: str) -> 'TestConfig':
        """Load configuration from YAML file"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    def save_to_json_file(self, file_path: str):
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            f.write(self.to_json())
    
    def save_to_yaml_file(self, file_path: str):
        """Save configuration to YAML file"""
        with open(file_path, 'w') as f:
            f.write(self.to_yaml())
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate API configuration
        if not self.api.base_url:
            issues.append("API base URL is required")
        
        # Validate performance thresholds
        if self.performance.response_time_ms <= 0:
            issues.append("Response time threshold must be positive")
        if self.performance.accuracy_threshold < 0 or self.performance.accuracy_threshold > 1:
            issues.append("Accuracy threshold must be between 0 and 1")
        
        # Validate load test configuration
        if self.load_test.concurrent_users <= 0:
            issues.append("Concurrent users must be positive")
        if self.load_test.test_duration <= 0:
            issues.append("Test duration must be positive")
        
        # Validate paths
        if not Path(self.test_data.test_data_path).exists():
            issues.append(f"Test data path does not exist: {self.test_data.test_data_path}")
        
        return issues
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        env_configs = {
            TestEnvironment.DEVELOPMENT: {
                "debug_mode": True,
                "verbose_logging": True,
                "api.timeout": 60,
                "performance.response_time_ms": 5000
            },
            TestEnvironment.STAGING: {
                "debug_mode": False,
                "verbose_logging": True,
                "api.timeout": 30,
                "performance.response_time_ms": 3000
            },
            TestEnvironment.PRODUCTION: {
                "debug_mode": False,
                "verbose_logging": False,
                "api.timeout": 15,
                "performance.response_time_ms": 2000
            },
            TestEnvironment.CI: {
                "browser.headless": True,
                "ci.enable_ci_mode": True,
                "ci.parallel_execution": True,
                "reporting.include_screenshots": False
            }
        }
        
        return env_configs.get(self.environment, {})
    
    def apply_environment_config(self):
        """Apply environment-specific configuration"""
        env_config = self.get_environment_config()
        
        for key, value in env_config.items():
            if '.' in key:
                # Handle nested attributes
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
            else:
                setattr(self, key, value)

def create_default_config() -> TestConfig:
    """Create default test configuration"""
    return TestConfig()

def create_ci_config() -> TestConfig:
    """Create CI-optimized test configuration"""
    config = TestConfig(
        environment=TestEnvironment.CI,
        enabled_test_types=[TestType.UNIT, TestType.INTEGRATION]
    )
    config.browser.headless = True
    config.ci.enable_ci_mode = True
    config.ci.parallel_execution = True
    config.reporting.include_screenshots = False
    return config

def create_performance_config() -> TestConfig:
    """Create performance testing configuration"""
    config = TestConfig(
        environment=TestEnvironment.STAGING,
        enabled_test_types=[TestType.PERFORMANCE, TestType.LOAD]
    )
    config.load_test.concurrent_users = 50
    config.load_test.test_duration = 600
    config.performance.response_time_ms = 1000
    return config

def load_config_from_environment() -> TestConfig:
    """Load configuration from environment variables"""
    config = create_default_config()
    
    # Override with environment variables
    if os.getenv("TEST_ENVIRONMENT"):
        config.environment = TestEnvironment(os.getenv("TEST_ENVIRONMENT"))
    
    if os.getenv("API_BASE_URL"):
        config.api.base_url = os.getenv("API_BASE_URL")
    
    if os.getenv("DATABASE_URL"):
        # Parse database URL
        db_url = os.getenv("DATABASE_URL")
        if db_url.startswith("sqlite"):
            config.database.type = "sqlite"
            config.database.database = db_url.split("///")[-1].replace(".db", "")
        elif db_url.startswith("postgresql"):
            config.database.type = "postgresql"
            # Parse PostgreSQL URL
    
    if os.getenv("BROWSER_HEADLESS"):
        config.browser.headless = os.getenv("BROWSER_HEADLESS").lower() == "true"
    
    if os.getenv("CONCURRENT_USERS"):
        config.load_test.concurrent_users = int(os.getenv("CONCURRENT_USERS"))
    
    config.apply_environment_config()
    return config

def main():
    """Main function for testing configuration"""
    # Create default configuration
    config = create_default_config()
    
    print("Default Configuration:")
    print(config.to_yaml())
    
    # Validate configuration
    issues = config.validate()
    if issues:
        print("\nConfiguration Issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("\nConfiguration is valid!")
    
    # Save configuration examples
    config.save_to_json_file("test_config_example.json")
    config.save_to_yaml_file("test_config_example.yaml")
    
    # Create CI configuration
    ci_config = create_ci_config()
    ci_config.save_to_yaml_file("test_config_ci.yaml")
    
    # Create performance configuration
    perf_config = create_performance_config()
    perf_config.save_to_yaml_file("test_config_performance.yaml")
    
    print("\nConfiguration files created:")
    print("- test_config_example.json")
    print("- test_config_example.yaml")
    print("- test_config_ci.yaml")
    print("- test_config_performance.yaml")

if __name__ == "__main__":
    main()