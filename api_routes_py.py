"""
API routes for video processing
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
import uuid
import logging

from app.core.config import settings
from app.services.video_processor import VideoProcessor
from app.workers.tasks import process_video_task
from app.core.storage import get_job_status, store_job_info
from app.api.download import router as download_router

logger = logging.getLogger(__name__)
router = APIRouter()

# Include download routes
router.include_router(download_router)

class ProcessVideoRequest(BaseModel):
    video_url: HttpUrl
    customer_name: str
    intro_clip: Optional[str] = None  # filename in assets/intros/
    outro_clip: Optional[str] = None  # filename in assets/outros/
    transition_style: str = "fade"  # fade, cut, slide
    overlay_settings: Optional[Dict[str, Any]] = None
    encoding_preset: Optional[str] = "standard"  # standard, high, mobile

class ProcessVideoResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 to 1.0
    message: str
    result_url: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

@router.post("/process", response_model=ProcessVideoResponse)
async def process_video(request: ProcessVideoRequest):
    """
    Start video processing job
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Validate request
        if not request.video_url:
            raise HTTPException(status_code=400, detail="video_url is required")
        
        if not request.customer_name or len(request.customer_name.strip()) == 0:
            raise HTTPException(status_code=400, detail="customer_name is required")
        
        # Store job info
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0.0,
            "message": "Job queued for processing",
            "video_url": str(request.video_url),
            "customer_name": request.customer_name,
            "intro_clip": request.intro_clip,
            "outro_clip": request.outro_clip,
            "transition_style": request.transition_style,
            "overlay_settings": request.overlay_settings or {},
            "encoding_preset": request.encoding_preset
        }
        
        await store_job_info(job_id, job_data)
        
        # Queue the processing task
        process_video_task.delay(
            job_id=job_id,
            video_url=str(request.video_url),
            customer_name=request.customer_name,
            intro_clip=request.intro_clip,
            outro_clip=request.outro_clip,
            transition_style=request.transition_style,
            overlay_settings=request.overlay_settings or {},
            encoding_preset=request.encoding_preset or "standard"
        )
        
        logger.info(f"Started video processing job {job_id}")
        
        return ProcessVideoResponse(
            job_id=job_id,
            status="pending",
            message="Video processing job started successfully"
        )
        
    except Exception as e:
        logger.error(f"Error starting video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job processing status
    """
    try:
        job_data = await get_job_status(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/result/{job_id}")
async def get_job_result(job_id: str):
    """
    Get job result and download URL
    """
    try:
        job_data = await get_job_status(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job_data["status"] != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Job is not completed. Current status: {job_data['status']}"
            )
        
        return {
            "job_id": job_id,
            "status": job_data["status"],
            "download_url": job_data.get("result_url"),
            "completed_at": job_data.get("completed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs")
async def list_jobs():
    """
    List all jobs (for admin interface)
    """
    try:
        # This would need to be implemented in storage layer
        # For now, return empty list
        return {"jobs": []}
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a job
    """
    try:
        # Implementation would depend on storage backend
        # For now, just return success
        return {"message": f"Job {job_id} cancellation requested"}
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))