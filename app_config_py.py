"""
Configuration settings for the video editing system
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Video Editor System"
    debug: bool = False
    environment: str = "production"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Redis/Celery settings
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Storage settings
    storage_type: str = "local"  # local, s3
    local_storage_path: str = "/app/outputs"
    temp_storage_path: str = "/app/temp"
    upload_path: str = "/app/uploads"
    assets_path: str = "/app/assets"
    
    # S3 settings (optional)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None
    s3_endpoint_url: Optional[str] = None
    
    # Video processing settings
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    allowed_formats: list = ["mp4", "avi", "mov", "mkv", "webm"]
    output_format: str = "mp4"
    default_resolution: str = "1920x1080"
    default_bitrate: str = "2M"
    default_fps: int = 30
    
    # Job settings
    job_expiry_hours: int = 24
    max_concurrent_jobs: int = 3
    
    # Security
    max_filename_length: int = 255
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_intro_path(self) -> str:
        return os.path.join(self.assets_path, "intros")
    
    def get_outro_path(self) -> str:
        return os.path.join(self.assets_path, "outros")
    
    def get_logos_path(self) -> str:
        return os.path.join(self.assets_path, "logos")

settings = Settings()