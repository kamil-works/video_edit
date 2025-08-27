"""
File download routes for processed videos
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download processed video file
    """
    try:
        # Sanitize filename to prevent directory traversal
        safe_filename = os.path.basename(filename)
        
        # Check if file exists in outputs directory
        file_path = os.path.join(settings.local_storage_path, safe_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify it's actually a file (not a directory)
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file stats for proper headers
        file_stats = os.stat(file_path)
        
        logger.info(f"Serving download: {safe_filename} ({file_stats.st_size} bytes)")
        
        return FileResponse(
            path=file_path,
            filename=safe_filename,
            media_type='application/octet-stream',
            headers={
                "Content-Length": str(file_stats.st_size),
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error for {filename}: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

@router.get("/preview/{filename}")
async def preview_file(filename: str):
    """
    Stream video file for preview (with proper video MIME type)
    """
    try:
        # Sanitize filename
        safe_filename = os.path.basename(filename)
        
        # Check if file exists
        file_path = os.path.join(settings.local_storage_path, safe_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine MIME type based on file extension
        file_extension = Path(safe_filename).suffix.lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm'
        }
        
        media_type = mime_types.get(file_extension, 'video/mp4')
        
        logger.info(f"Serving preview: {safe_filename}")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview error for {filename}: {e}")
        raise HTTPException(status_code=500, detail="Preview failed")

@router.get("/asset/{asset_type}/{filename}")
async def download_asset(asset_type: str, filename: str):
    """
    Download asset file (intro, outro, logo)
    """
    try:
        # Validate asset type
        if asset_type not in ["intros", "outros", "logos"]:
            raise HTTPException(status_code=400, detail="Invalid asset type")
        
        # Sanitize filename
        safe_filename = os.path.basename(filename)
        
        # Build asset path
        asset_paths = {
            "intros": settings.get_intro_path(),
            "outros": settings.get_outro_path(),
            "logos": settings.get_logos_path()
        }
        
        asset_dir = asset_paths[asset_type]
        file_path = os.path.join(asset_dir, safe_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Determine appropriate MIME type
        file_extension = Path(safe_filename).suffix.lower()
        
        if asset_type == "logos":
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml'
            }
            media_type = mime_types.get(file_extension, 'application/octet-stream')
        else:
            mime_types = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm'
            }
            media_type = mime_types.get(file_extension, 'video/mp4')
        
        logger.info(f"Serving asset: {asset_type}/{safe_filename}")
        
        return FileResponse(
            path=file_path,
            filename=safe_filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset download error: {e}")
        raise HTTPException(status_code=500, detail="Asset download failed")