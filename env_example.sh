# Application Settings
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0

# Redis/Celery Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Storage Configuration
STORAGE_TYPE=local  # local or s3
LOCAL_STORAGE_PATH=/app/outputs
TEMP_STORAGE_PATH=/app/temp
UPLOAD_PATH=/app/uploads
ASSETS_PATH=/app/assets

# S3 Configuration (if using S3 storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name
S3_ENDPOINT_URL=  # Optional: for S3-compatible services

# Video Processing Settings
MAX_FILE_SIZE=536870912  # 500MB in bytes
OUTPUT_FORMAT=mp4
DEFAULT_RESOLUTION=1920x1080
DEFAULT_BITRATE=2M
DEFAULT_FPS=30

# Job Management
JOB_EXPIRY_HOURS=24
MAX_CONCURRENT_JOBS=3

# Security
MAX_FILENAME_LENGTH=255

# Coolify-specific (for deployment)
FQDN=your-domain.com
DOCKER_IMAGE=your-registry/video-editor:latest