"""
Storage abstraction layer for job data and file storage
"""

import os
import json
import aiofiles
import boto3
from typing import Optional, Dict, Any
from datetime import datetime
import redis.asyncio as redis
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client for job status storage
redis_client = None

async def init_storage():
    """Initialize storage backends"""
    global redis_client
    
    try:
        # Initialize Redis
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Create necessary directories
        os.makedirs(settings.local_storage_path, exist_ok=True)
        os.makedirs(settings.temp_storage_path, exist_ok=True)
        os.makedirs(settings.upload_path, exist_ok=True)
        os.makedirs(settings.get_intro_path(), exist_ok=True)
        os.makedirs(settings.get_outro_path(), exist_ok=True)
        os.makedirs(settings.get_logos_path(), exist_ok=True)
        
        logger.info("Storage directories created")
        
    except Exception as e:
        logger.error(f"Storage initialization failed: {e}")
        raise

async def store_job_info(job_id: str, job_data: Dict[str, Any]) -> bool:
    """Store job information in Redis"""
    try:
        job_data["created_at"] = datetime.utcnow().isoformat()
        await redis_client.hset(f"job:{job_id}", mapping=job_data)
        await redis_client.expire(f"job:{job_id}", settings.job_expiry_hours * 3600)
        return True
    except Exception as e:
        logger.error(f"Error storing job info: {e}")
        return False

async def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status from Redis"""
    try:
        job_data = await redis_client.hgetall(f"job:{job_id}")
        if not job_data:
            return None
            
        # Convert progress to float if exists
        if "progress" in job_data:
            try:
                job_data["progress"] = float(job_data["progress"])
            except (ValueError, TypeError):
                job_data["progress"] = 0.0
        
        return job_data
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return None

async def update_job_status(job_id: str, **updates) -> bool:
    """Update job status in Redis"""
    try:
        # Convert progress to string for Redis storage
        if "progress" in updates:
            updates["progress"] = str(updates["progress"])
            
        updates["updated_at"] = datetime.utcnow().isoformat()
        await redis_client.hset(f"job:{job_id}", mapping=updates)
        return True
    except Exception as e:
        logger.error(f"Error updating job status: {e}")
        return False

async def get_download_url(file_path: str) -> str:
    """Generate download URL for processed video"""
    try:
        if settings.storage_type == "s3":
            return await upload_to_s3_and_get_url(file_path)
        else:
            # For local storage, return relative path
            filename = os.path.basename(file_path)
            return f"/api/v1/download/{filename}"
    except Exception as e:
        logger.error(f"Error generating download URL: {e}")
        return ""

async def upload_to_s3_and_get_url(file_path: str) -> str:
    """Upload file to S3 and return download URL"""
    try:
        if not all([settings.aws_access_key_id, settings.aws_secret_access_key, settings.s3_bucket]):
            raise ValueError("S3 configuration incomplete")
            
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url
        )
        
        filename = os.path.basename(file_path)
        s3_key = f"processed-videos/{filename}"
        
        # Upload file
        s3_client.upload_file(file_path, settings.s3_bucket, s3_key)
        
        # Generate presigned URL (valid for 24 hours)
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.s3_bucket, 'Key': s3_key},
            ExpiresIn=86400
        )
        
        # Clean up local file after successful upload
        try:
            os.remove(file_path)
        except OSError:
            pass
            
        return download_url
        
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        # Fallback to local storage
        filename = os.path.basename(file_path)
        return f"/api/v1/download/{filename}"

class FileManager:
    """File management utilities"""
    
    @staticmethod
    async def save_uploaded_file(file_data: bytes, filename: str, subfolder: str = "") -> str:
        """Save uploaded file to assets directory"""
        try:
            # Sanitize filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            if len(safe_filename) > settings.max_filename_length:
                safe_filename = safe_filename[:settings.max_filename_length]
            
            # Determine save path
            if subfolder:
                save_dir = os.path.join(settings.assets_path, subfolder)
            else:
                save_dir = settings.upload_path
                
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, safe_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
                
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    @staticmethod
    def list_assets(asset_type: str) -> list:
        """List available assets (intros, outros, logos)"""
        try:
            asset_dirs = {
                "intros": settings.get_intro_path(),
                "outros": settings.get_outro_path(),
                "logos": settings.get_logos_path()
            }
            
            asset_dir = asset_dirs.get(asset_type)
            if not asset_dir or not os.path.exists(asset_dir):
                return []
            
            files = []
            for filename in os.listdir(asset_dir):
                file_path = os.path.join(asset_dir, filename)
                if os.path.isfile(file_path):
                    # Get file info
                    stat = os.stat(file_path)
                    files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return sorted(files, key=lambda x: x["filename"])
            
        except Exception as e:
            logger.error(f"Error listing assets: {e}")
            return []
    
    @staticmethod
    def delete_asset(asset_type: str, filename: str) -> bool:
        """Delete an asset file"""
        try:
            asset_dirs = {
                "intros": settings.get_intro_path(),
                "outros": settings.get_outro_path(),
                "logos": settings.get_logos_path()
            }
            
            asset_dir = asset_dirs.get(asset_type)
            if not asset_dir:
                return False
                
            file_path = os.path.join(asset_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted asset: {file_path}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error deleting asset: {e}")
            return False