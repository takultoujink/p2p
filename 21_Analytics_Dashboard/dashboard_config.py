"""
Configuration Management for Analytics Dashboard
Comprehensive configuration system with environment-specific settings
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class DatabaseType(Enum):
    """Database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"

class CacheType(Enum):
    """Cache types"""
    REDIS = "redis"
    MEMCACHED = "memcached"
    MEMORY = "memory"
    DISK = "disk"

class DashboardTheme(Enum):
    """Dashboard themes"""
    BOOTSTRAP = "bootstrap"
    MATERIAL = "material"
    DARK = "dark"
    LIGHT = "light"
    CUSTOM = "custom"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: DatabaseType = DatabaseType.SQLITE
    host: str = "localhost"
    port: int = 5432
    database: str = "analytics"
    username: str = ""
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    @property
    def url(self) -> str:
        """Generate database URL"""
        if self.type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}.db"
        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == DatabaseType.MYSQL:
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == DatabaseType.MONGODB:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")

@dataclass
class CacheConfig:
    """Cache configuration"""
    type: CacheType = CacheType.REDIS
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: str = ""
    ttl: int = 300  # seconds
    max_connections: int = 10
    
    @property
    def url(self) -> str:
        """Generate cache URL"""
        if self.type == CacheType.REDIS:
            if self.password:
                return f"redis://:{self.password}@{self.host}:{self.port}/{self.database}"
            else:
                return f"redis://{self.host}:{self.port}/{self.database}"
        elif self.type == CacheType.MEMCACHED:
            return f"memcached://{self.host}:{self.port}"
        else:
            return ""

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    cors_headers: List[str] = field(default_factory=lambda: ["*"])
    rate_limit: str = "100/minute"
    enable_https: bool = False
    ssl_cert_path: str = ""
    ssl_key_path: str = ""

@dataclass
class DashboardConfig:
    """Dashboard-specific configuration"""
    theme: DashboardTheme = DashboardTheme.BOOTSTRAP
    title: str = "AI Detection Analytics"
    subtitle: str = "Real-time Analytics Dashboard"
    logo_url: str = ""
    favicon_url: str = ""
    custom_css: str = ""
    custom_js: str = ""
    show_source_code: bool = False
    enable_dark_mode: bool = True
    default_time_range: str = "24h"
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    max_data_points: int = 1000
    chart_height: int = 400
    enable_export: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["png", "pdf", "html", "csv"])

@dataclass
class MetricsConfig:
    """Metrics collection configuration"""
    collect_usage_stats: bool = True
    collect_detection_metrics: bool = True
    collect_user_behavior: bool = True
    collect_business_metrics: bool = True
    collect_system_metrics: bool = True
    
    # Thresholds
    response_time_threshold: float = 2.0  # seconds
    error_rate_threshold: float = 0.01  # 1%
    accuracy_threshold: float = 0.95  # 95%
    memory_threshold: float = 0.8  # 80%
    cpu_threshold: float = 0.8  # 80%
    
    # Retention
    data_retention_days: int = 90
    aggregation_intervals: List[str] = field(default_factory=lambda: ["1m", "5m", "1h", "1d"])
    
    # Sampling
    enable_sampling: bool = False
    sample_rate: float = 0.1  # 10%

@dataclass
class AlertingConfig:
    """Alerting configuration"""
    enable_alerts: bool = True
    email_alerts: bool = True
    slack_alerts: bool = False
    webhook_alerts: bool = False
    
    # Email settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    
    # Slack settings
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Webhook settings
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    
    # Alert rules
    alert_rules: Dict[str, Any] = field(default_factory=lambda: {
        "high_error_rate": {"threshold": 0.05, "duration": "5m"},
        "slow_response": {"threshold": 5.0, "duration": "5m"},
        "low_accuracy": {"threshold": 0.9, "duration": "10m"},
        "high_memory": {"threshold": 0.9, "duration": "5m"}
    })

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/analytics.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True
    enable_json: bool = False
    enable_structured: bool = True

@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    enable_caching: bool = True
    cache_ttl: int = 300  # seconds
    enable_compression: bool = True
    compression_level: int = 6
    enable_minification: bool = True
    enable_cdn: bool = False
    cdn_url: str = ""
    
    # Database optimization
    enable_connection_pooling: bool = True
    query_timeout: int = 30  # seconds
    enable_query_cache: bool = True
    
    # Chart optimization
    chart_data_limit: int = 1000
    enable_chart_caching: bool = True
    chart_cache_ttl: int = 60  # seconds

@dataclass
class IntegrationConfig:
    """External integrations configuration"""
    # Cloud providers
    aws_access_key: str = ""
    aws_secret_key: str = ""
    aws_region: str = "us-east-1"
    
    gcp_credentials_path: str = ""
    gcp_project_id: str = ""
    
    azure_connection_string: str = ""
    
    # Monitoring services
    prometheus_url: str = ""
    grafana_url: str = ""
    datadog_api_key: str = ""
    newrelic_license_key: str = ""
    
    # Analytics services
    google_analytics_id: str = ""
    mixpanel_token: str = ""
    amplitude_api_key: str = ""

@dataclass
class AnalyticsDashboardConfig:
    """Main analytics dashboard configuration"""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8050
    workers: int = 1
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def to_yaml(self) -> str:
        """Convert configuration to YAML string"""
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsDashboardConfig':
        """Create configuration from dictionary"""
        # Convert enum strings back to enums
        if 'environment' in data:
            data['environment'] = Environment(data['environment'])
        
        if 'database' in data and 'type' in data['database']:
            data['database']['type'] = DatabaseType(data['database']['type'])
        
        if 'cache' in data and 'type' in data['cache']:
            data['cache']['type'] = CacheType(data['cache']['type'])
        
        if 'dashboard' in data and 'theme' in data['dashboard']:
            data['dashboard']['theme'] = DashboardTheme(data['dashboard']['theme'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AnalyticsDashboardConfig':
        """Create configuration from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'AnalyticsDashboardConfig':
        """Create configuration from YAML string"""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'AnalyticsDashboardConfig':
        """Load configuration from file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            return cls.from_yaml(content)
        elif file_path.suffix.lower() == '.json':
            return cls.from_json(content)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def save_to_file(self, file_path: Union[str, Path]):
        """Save configuration to file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                f.write(self.to_yaml())
            elif file_path.suffix.lower() == '.json':
                f.write(self.to_json())
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def load_from_env(self):
        """Load configuration from environment variables"""
        # Database
        if os.getenv('DB_TYPE'):
            self.database.type = DatabaseType(os.getenv('DB_TYPE'))
        if os.getenv('DB_HOST'):
            self.database.host = os.getenv('DB_HOST')
        if os.getenv('DB_PORT'):
            self.database.port = int(os.getenv('DB_PORT'))
        if os.getenv('DB_NAME'):
            self.database.database = os.getenv('DB_NAME')
        if os.getenv('DB_USER'):
            self.database.username = os.getenv('DB_USER')
        if os.getenv('DB_PASSWORD'):
            self.database.password = os.getenv('DB_PASSWORD')
        
        # Cache
        if os.getenv('CACHE_TYPE'):
            self.cache.type = CacheType(os.getenv('CACHE_TYPE'))
        if os.getenv('CACHE_HOST'):
            self.cache.host = os.getenv('CACHE_HOST')
        if os.getenv('CACHE_PORT'):
            self.cache.port = int(os.getenv('CACHE_PORT'))
        if os.getenv('CACHE_PASSWORD'):
            self.cache.password = os.getenv('CACHE_PASSWORD')
        
        # Security
        if os.getenv('SECRET_KEY'):
            self.security.secret_key = os.getenv('SECRET_KEY')
        if os.getenv('JWT_ALGORITHM'):
            self.security.jwt_algorithm = os.getenv('JWT_ALGORITHM')
        
        # Dashboard
        if os.getenv('DASHBOARD_THEME'):
            self.dashboard.theme = DashboardTheme(os.getenv('DASHBOARD_THEME'))
        if os.getenv('DASHBOARD_TITLE'):
            self.dashboard.title = os.getenv('DASHBOARD_TITLE')
        
        # Server
        if os.getenv('HOST'):
            self.host = os.getenv('HOST')
        if os.getenv('PORT'):
            self.port = int(os.getenv('PORT'))
        if os.getenv('DEBUG'):
            self.debug = os.getenv('DEBUG').lower() == 'true'
        if os.getenv('ENVIRONMENT'):
            self.environment = Environment(os.getenv('ENVIRONMENT'))
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate port range
        if not (1 <= self.port <= 65535):
            errors.append(f"Invalid port number: {self.port}")
        
        # Validate database configuration
        if self.database.type != DatabaseType.SQLITE:
            if not self.database.host:
                errors.append("Database host is required for non-SQLite databases")
            if not self.database.username:
                errors.append("Database username is required for non-SQLite databases")
        
        # Validate cache configuration
        if self.cache.type != CacheType.MEMORY:
            if not self.cache.host:
                errors.append("Cache host is required for non-memory cache")
        
        # Validate security
        if self.environment == Environment.PRODUCTION:
            if self.security.secret_key == "your-secret-key-change-in-production":
                errors.append("Secret key must be changed in production")
            if self.debug:
                errors.append("Debug mode should be disabled in production")
        
        # Validate alerting
        if self.alerting.enable_alerts:
            if self.alerting.email_alerts and not self.alerting.email_to:
                errors.append("Email recipients required when email alerts are enabled")
            if self.alerting.slack_alerts and not self.alerting.slack_webhook_url:
                errors.append("Slack webhook URL required when Slack alerts are enabled")
        
        return errors

class ConfigManager:
    """Configuration manager with environment-specific settings"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
    
    def create_default_configs(self):
        """Create default configuration files for different environments"""
        environments = [Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION]
        
        for env in environments:
            config = self._create_env_config(env)
            config_file = self.config_dir / f"{env.value}.yaml"
            config.save_to_file(config_file)
            logger.info(f"Created default config for {env.value}: {config_file}")
    
    def _create_env_config(self, env: Environment) -> AnalyticsDashboardConfig:
        """Create environment-specific configuration"""
        config = AnalyticsDashboardConfig(environment=env)
        
        if env == Environment.DEVELOPMENT:
            config.debug = True
            config.database.echo = True
            config.logging.level = "DEBUG"
            config.dashboard.show_source_code = True
            
        elif env == Environment.STAGING:
            config.debug = False
            config.database.echo = False
            config.logging.level = "INFO"
            config.dashboard.show_source_code = False
            config.security.secret_key = "staging-secret-key"
            
        elif env == Environment.PRODUCTION:
            config.debug = False
            config.database.echo = False
            config.logging.level = "WARNING"
            config.dashboard.show_source_code = False
            config.security.secret_key = "production-secret-key-change-me"
            config.security.enable_https = True
            config.performance.enable_caching = True
            config.performance.enable_compression = True
            config.alerting.enable_alerts = True
        
        return config
    
    def load_config(self, env: Environment) -> AnalyticsDashboardConfig:
        """Load configuration for specific environment"""
        config_file = self.config_dir / f"{env.value}.yaml"
        
        if config_file.exists():
            config = AnalyticsDashboardConfig.from_file(config_file)
        else:
            logger.warning(f"Config file not found: {config_file}. Using default config.")
            config = self._create_env_config(env)
        
        # Load environment variables
        config.load_from_env()
        
        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error(f"Configuration validation errors: {errors}")
            raise ValueError(f"Invalid configuration: {errors}")
        
        return config

def get_config(env: Optional[str] = None) -> AnalyticsDashboardConfig:
    """Get configuration for current environment"""
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    environment = Environment(env.lower())
    config_manager = ConfigManager()
    
    return config_manager.load_config(environment)

def main():
    """Main function for configuration management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analytics Dashboard Configuration Manager")
    parser.add_argument("--create-defaults", action="store_true", help="Create default configuration files")
    parser.add_argument("--env", choices=["development", "staging", "production"], default="development", help="Environment")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    
    args = parser.parse_args()
    
    config_manager = ConfigManager()
    
    if args.create_defaults:
        config_manager.create_default_configs()
        print("Default configuration files created!")
        return
    
    # Load configuration
    env = Environment(args.env)
    config = config_manager.load_config(env)
    
    if args.validate:
        errors = config.validate()
        if errors:
            print(f"Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("Configuration is valid!")
    
    if args.show:
        print(f"Configuration for {env.value}:")
        print(config.to_yaml())

if __name__ == "__main__":
    main()