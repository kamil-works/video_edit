"""
Celery application configuration
"""

from celery import Celery
from app.core.config import settings

# Create and configure Celery app
celery_app = Celery(
    "video_processor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Import tasks to register them
from app.workers import tasks