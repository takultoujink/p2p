"""
Cloud Services Configuration
การกำหนดค่าสำหรับ Cloud Services Integration
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class AWSConfig:
    """AWS configuration"""
    access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    s3_bucket: str = os.getenv("AWS_S3_BUCKET", "object-detection-bucket")
    lambda_role_arn: str = os.getenv("AWS_LAMBDA_ROLE_ARN", "")
    ecs_cluster: str = os.getenv("AWS_ECS_CLUSTER", "object-detection-cluster")
    vpc_id: str = os.getenv("AWS_VPC_ID", "")
    subnet_ids: List[str] = field(default_factory=lambda: os.getenv("AWS_SUBNET_IDS", "").split(","))
    security_group_ids: List[str] = field(default_factory=lambda: os.getenv("AWS_SECURITY_GROUP_IDS", "").split(","))

@dataclass
class GCPConfig:
    """Google Cloud Platform configuration"""
    project_id: str = os.getenv("GCP_PROJECT_ID", "")
    credentials_file: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    region: str = os.getenv("GCP_REGION", "us-central1")
    zone: str = os.getenv("GCP_ZONE", "us-central1-a")
    storage_bucket: str = os.getenv("GCP_STORAGE_BUCKET", "object-detection-gcp-bucket")
    cloud_run_service: str = os.getenv("GCP_CLOUD_RUN_SERVICE", "object-detection-service")
    gke_cluster: str = os.getenv("GCP_GKE_CLUSTER", "object-detection-cluster")

@dataclass
class AzureConfig:
    """Microsoft Azure configuration"""
    subscription_id: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")
    resource_group: str = os.getenv("AZURE_RESOURCE_GROUP", "object-detection-rg")
    location: str = os.getenv("AZURE_LOCATION", "East US")
    storage_account: str = os.getenv("AZURE_STORAGE_ACCOUNT", "objectdetectionstorage")
    container_registry: str = os.getenv("AZURE_CONTAINER_REGISTRY", "objectdetectionacr")
    aks_cluster: str = os.getenv("AZURE_AKS_CLUSTER", "object-detection-aks")

@dataclass
class CDNConfig:
    """CDN configuration"""
    cloudflare_api_token: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    cloudflare_zone_id: str = os.getenv("CLOUDFLARE_ZONE_ID", "")
    aws_cloudfront_distribution_id: str = os.getenv("AWS_CLOUDFRONT_DISTRIBUTION_ID", "")
    gcp_cdn_backend_service: str = os.getenv("GCP_CDN_BACKEND_SERVICE", "")
    azure_cdn_profile: str = os.getenv("AZURE_CDN_PROFILE", "")
    azure_cdn_endpoint: str = os.getenv("AZURE_CDN_ENDPOINT", "")

@dataclass
class DatabaseConfig:
    """Database configuration for cloud services"""
    # AWS RDS
    aws_rds_endpoint: str = os.getenv("AWS_RDS_ENDPOINT", "")
    aws_rds_username: str = os.getenv("AWS_RDS_USERNAME", "")
    aws_rds_password: str = os.getenv("AWS_RDS_PASSWORD", "")
    aws_rds_database: str = os.getenv("AWS_RDS_DATABASE", "object_detection")
    
    # GCP Cloud SQL
    gcp_sql_instance: str = os.getenv("GCP_SQL_INSTANCE", "")
    gcp_sql_username: str = os.getenv("GCP_SQL_USERNAME", "")
    gcp_sql_password: str = os.getenv("GCP_SQL_PASSWORD", "")
    gcp_sql_database: str = os.getenv("GCP_SQL_DATABASE", "object_detection")
    
    # Azure SQL
    azure_sql_server: str = os.getenv("AZURE_SQL_SERVER", "")
    azure_sql_username: str = os.getenv("AZURE_SQL_USERNAME", "")
    azure_sql_password: str = os.getenv("AZURE_SQL_PASSWORD", "")
    azure_sql_database: str = os.getenv("AZURE_SQL_DATABASE", "object_detection")

@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    # AWS CloudWatch
    aws_cloudwatch_log_group: str = os.getenv("AWS_CLOUDWATCH_LOG_GROUP", "/aws/lambda/object-detection")
    aws_cloudwatch_region: str = os.getenv("AWS_CLOUDWATCH_REGION", "us-east-1")
    
    # GCP Stackdriver
    gcp_logging_project: str = os.getenv("GCP_LOGGING_PROJECT", "")
    gcp_monitoring_project: str = os.getenv("GCP_MONITORING_PROJECT", "")
    
    # Azure Monitor
    azure_log_analytics_workspace: str = os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE", "")
    azure_application_insights_key: str = os.getenv("AZURE_APPLICATION_INSIGHTS_KEY", "")
    
    # Third-party monitoring
    datadog_api_key: str = os.getenv("DATADOG_API_KEY", "")
    new_relic_license_key: str = os.getenv("NEW_RELIC_LICENSE_KEY", "")
    prometheus_endpoint: str = os.getenv("PROMETHEUS_ENDPOINT", "")

@dataclass
class SecurityConfig:
    """Security configuration"""
    # Encryption keys
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    
    # API keys
    api_key_header: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    
    # SSL/TLS
    ssl_cert_path: str = os.getenv("SSL_CERT_PATH", "")
    ssl_key_path: str = os.getenv("SSL_KEY_PATH", "")
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])

@dataclass
class ApplicationConfig:
    """Application-specific configuration"""
    app_name: str = os.getenv("APP_NAME", "Object Detection System")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: Environment = Environment(os.getenv("ENVIRONMENT", "development"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Model configuration
    model_path: str = os.getenv("MODEL_PATH", "/models/yolo")
    model_version: str = os.getenv("MODEL_VERSION", "v11")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    
    # Processing configuration
    max_image_size: int = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
    supported_formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png", "bmp"])
    batch_size: int = int(os.getenv("BATCH_SIZE", "32"))
    
    # Cache configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))

@dataclass
class CloudServicesConfig:
    """Main cloud services configuration"""
    aws: AWSConfig = field(default_factory=AWSConfig)
    gcp: GCPConfig = field(default_factory=GCPConfig)
    azure: AzureConfig = field(default_factory=AzureConfig)
    cdn: CDNConfig = field(default_factory=CDNConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    application: ApplicationConfig = field(default_factory=ApplicationConfig)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate AWS configuration
        if not self.aws.access_key_id and not os.getenv("AWS_PROFILE"):
            errors.append("AWS credentials not configured")
        
        # Validate GCP configuration
        if not self.gcp.project_id:
            errors.append("GCP project ID not configured")
        
        # Validate Azure configuration
        if not self.azure.subscription_id:
            errors.append("Azure subscription ID not configured")
        
        # Validate application configuration
        if not self.application.model_path:
            errors.append("Model path not configured")
        
        return errors
    
    def get_provider_config(self, provider: str) -> Dict:
        """Get configuration for specific provider"""
        if provider.lower() == "aws":
            return {
                "access_key_id": self.aws.access_key_id,
                "secret_access_key": self.aws.secret_access_key,
                "region": self.aws.region,
                "s3_bucket": self.aws.s3_bucket
            }
        elif provider.lower() == "gcp":
            return {
                "project_id": self.gcp.project_id,
                "credentials_file": self.gcp.credentials_file,
                "region": self.gcp.region,
                "storage_bucket": self.gcp.storage_bucket
            }
        elif provider.lower() == "azure":
            return {
                "subscription_id": self.azure.subscription_id,
                "tenant_id": self.azure.tenant_id,
                "client_id": self.azure.client_id,
                "resource_group": self.azure.resource_group
            }
        else:
            return {}
    
    def get_database_url(self, provider: str) -> str:
        """Get database URL for specific provider"""
        if provider.lower() == "aws":
            return f"postgresql://{self.database.aws_rds_username}:{self.database.aws_rds_password}@{self.database.aws_rds_endpoint}/{self.database.aws_rds_database}"
        elif provider.lower() == "gcp":
            return f"postgresql://{self.database.gcp_sql_username}:{self.database.gcp_sql_password}@{self.database.gcp_sql_instance}/{self.database.gcp_sql_database}"
        elif provider.lower() == "azure":
            return f"mssql://{self.database.azure_sql_username}:{self.database.azure_sql_password}@{self.database.azure_sql_server}/{self.database.azure_sql_database}"
        else:
            return ""

# Global configuration instance
config = CloudServicesConfig()

# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    "debug": True,
    "log_level": "DEBUG",
    "auto_reload": True,
    "workers": 1
}

STAGING_CONFIG = {
    "debug": False,
    "log_level": "INFO",
    "auto_reload": False,
    "workers": 2
}

PRODUCTION_CONFIG = {
    "debug": False,
    "log_level": "WARNING",
    "auto_reload": False,
    "workers": 4
}

def get_environment_config() -> Dict:
    """Get configuration based on current environment"""
    env = config.application.environment
    
    if env == Environment.DEVELOPMENT:
        return DEVELOPMENT_CONFIG
    elif env == Environment.STAGING:
        return STAGING_CONFIG
    elif env == Environment.PRODUCTION:
        return PRODUCTION_CONFIG
    else:
        return DEVELOPMENT_CONFIG

def load_config_from_file(file_path: str) -> CloudServicesConfig:
    """Load configuration from file"""
    import json
    import yaml
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                data = json.load(f)
            elif file_path.endswith(('.yml', '.yaml')):
                data = yaml.safe_load(f)
            else:
                raise ValueError("Unsupported configuration file format")
        
        # Update environment variables
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    env_key = f"{key.upper()}_{sub_key.upper()}"
                    os.environ[env_key] = str(sub_value)
            else:
                os.environ[key.upper()] = str(value)
        
        # Return new configuration instance
        return CloudServicesConfig()
    
    except Exception as e:
        print(f"Failed to load configuration from {file_path}: {e}")
        return config

def save_config_to_file(config_obj: CloudServicesConfig, file_path: str):
    """Save configuration to file"""
    import json
    import yaml
    from dataclasses import asdict
    
    try:
        data = asdict(config_obj)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                json.dump(data, f, indent=2, default=str)
            elif file_path.endswith(('.yml', '.yaml')):
                yaml.dump(data, f, default_flow_style=False)
            else:
                raise ValueError("Unsupported configuration file format")
        
        print(f"Configuration saved to {file_path}")
    
    except Exception as e:
        print(f"Failed to save configuration to {file_path}: {e}")

# Example usage and testing
if __name__ == "__main__":
    print("🔧 Cloud Services Configuration")
    print("=" * 50)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  • {error}")
    else:
        print("✅ Configuration is valid")
    
    # Display current configuration
    print(f"\n📋 Current Environment: {config.application.environment.value}")
    print(f"🏷️  Application: {config.application.app_name} v{config.application.app_version}")
    print(f"🐛 Debug Mode: {config.application.debug}")
    
    # Display provider configurations
    print("\n☁️  Cloud Providers:")
    print(f"  AWS Region: {config.aws.region}")
    print(f"  GCP Project: {config.gcp.project_id or 'Not configured'}")
    print(f"  Azure Location: {config.azure.location}")
    
    # Display security settings
    print(f"\n🔒 Security:")
    print(f"  Rate Limit: {config.security.rate_limit_per_minute}/min")
    print(f"  CORS Origins: {', '.join(config.security.cors_origins)}")
    
    # Test environment-specific config
    env_config = get_environment_config()
    print(f"\n⚙️  Environment Config:")
    for key, value in env_config.items():
        print(f"  {key}: {value}")
    
    # Example of saving configuration
    # save_config_to_file(config, "cloud_config.yaml")
    
    print("\n✅ Configuration test completed!")