"""
Web interface routes
"""

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, List
import logging

from app.core.storage import FileManager, get_job_status
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/assets", response_class=HTMLResponse)
async def assets_page(request: Request):
    """Assets management page"""
    # Get asset lists
    intros = FileManager.list_assets("intros")
    outros = FileManager.list_assets("outros")
    logos = FileManager.list_assets("logos")
    
    return templates.TemplateResponse("assets.html", {
        "request": request,
        "intros": intros,
        "outros": outros,
        "logos": logos
    })

@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """Jobs management page"""
    return templates.TemplateResponse("jobs.html", {"request": request})

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": {
            "max_file_size": settings.max_file_size // (1024 * 1024),  # MB
            "allowed_formats": settings.allowed_formats,
            "output_format": settings.output_format,
            "default_resolution": settings.default_resolution,
            "storage_type": settings.storage_type,
            "max_concurrent_jobs": settings.max_concurrent_jobs
        }
    })

@router.post("/upload-asset")
async def upload_asset(
    asset_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload asset file (intro, outro, logo)"""
    try:
        if asset_type not in ["intros", "outros", "logos"]:
            raise HTTPException(status_code=400, detail="Invalid asset type")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Check file size
        file_data = await file.read()
        if len(file_data) > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Save file
        file_path = await FileManager.save_uploaded_file(
            file_data, file.filename, asset_type
        )
        
        return JSONResponse({
            "success": True,
            "message": f"{asset_type.capitalize()} uploaded successfully",
            "filename": file.filename
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@router.delete("/delete-asset/{asset_type}/{filename}")
async def delete_asset(asset_type: str, filename: str):
    """Delete asset file"""
    try:
        if asset_type not in ["intros", "outros", "logos"]:
            raise HTTPException(status_code=400, detail="Invalid asset type")
        
        success = FileManager.delete_asset(asset_type, filename)
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Asset deleted successfully"
            })
        else:
            raise HTTPException(status_code=404, detail="Asset not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Delete failed")

@router.get("/api/assets/{asset_type}")
async def list_assets_api(asset_type: str):
    """API endpoint to list assets"""
    try:
        if asset_type not in ["intros", "outros", "logos"]:
            raise HTTPException(status_code=400, detail="Invalid asset type")
        
        assets = FileManager.list_assets(asset_type)
        return JSONResponse({"assets": assets})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List assets error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list assets")

@router.get("/api/job-status/{job_id}")
async def get_job_status_web(job_id: str):
    """Get job status for web interface"""
    try:
        job_data = await get_job_status(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JSONResponse(job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status")