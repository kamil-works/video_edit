"""
Celery tasks for video processing
"""

from celery import Celery
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.services.video_processor import VideoProcessor
from app.core.storage import update_job_status, get_download_url

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "video_processor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.process_video_task": {"queue": "video_processing"}
    },
    worker_concurrency=settings.max_concurrent_jobs,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

@celery_app.task(bind=True, max_retries=2)
def process_video_task(self, job_id: str, video_url: str, customer_name: str,
                      intro_clip: Optional[str] = None,
                      outro_clip: Optional[str] = None,
                      transition_style: str = "fade",
                      overlay_settings: Dict[str, Any] = None,
                      encoding_preset: str = "standard"):
    """
    Celery task for processing videos
    """
    overlay_settings = overlay_settings or {}
    
    async def progress_callback(progress: float, message: str):
        """Update job progress"""
        try:
            await update_job_status(
                job_id, 
                status="processing",
                progress=progress,
                message=message
            )
            logger.info(f"Job {job_id}: {progress:.1%} - {message}")
        except Exception as e:
            logger.error(f"Error updating job progress: {e}")
    
    async def run_processing():
        """Run the video processing asynchronously"""
        try:
            # Update job status to processing
            await update_job_status(
                job_id,
                status="processing",
                progress=0.0,
                message="Starting video processing..."
            )
            
            # Initialize video processor
            processor = VideoProcessor()
            
            # Process the video
            output_path = await processor.process_video(
                job_id=job_id,
                video_url=video_url,
                customer_name=customer_name,
                intro_clip=intro_clip,
                outro_clip=outro_clip,
                transition_style=transition_style,
                overlay_settings=overlay_settings,
                encoding_preset=encoding_preset,
                progress_callback=progress_callback
            )
            
            # Get download URL
            download_url = await get_download_url(output_path)
            
            # Update job status to completed
            await update_job_status(
                job_id,
                status="completed",
                progress=1.0,
                message="Video processing completed successfully",
                result_url=download_url,
                completed_at=datetime.utcnow().isoformat()
            )
            
            logger.info(f"Job {job_id} completed successfully")
            return {"status": "success", "output_path": output_path, "download_url": download_url}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job {job_id} failed: {error_msg}")
            
            # Update job status to failed
            try:
                await update_job_status(
                    job_id,
                    status="failed",
                    progress=0.0,
                    message="Video processing failed",
                    error=error_msg
                )
            except Exception as update_error:
                logger.error(f"Error updating job status: {update_error}")
            
            # Re-raise the exception for Celery retry mechanism
            raise self.retry(exc=e, countdown=60, max_retries=2)
    
    try:
        # Run the async processing function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_processing())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Task execution failed for job {job_id}: {e}")
        raise

@celery_app.task
def cleanup_expired_jobs():
    """
    Cleanup expired job files and data
    """
    try:
        # This would implement cleanup logic
        # Remove files older than settings.job_expiry_hours
        logger.info("Cleanup task executed")
        return {"status": "success", "message": "Cleanup completed"}
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise