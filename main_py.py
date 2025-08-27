#!/usr/bin/env python3
"""
Main application entry point for the video editing system
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.web.routes import router as web_router
from app.core.config import settings
from app.core.storage import init_storage
from app.workers.celery_app import celery_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    logger.info("Starting Video Editor System...")
    await init_storage()
    logger.info("Storage initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Video Editor System...")

app = FastAPI(
    title="Video Editor System",
    description="Containerized video editing system with FFmpeg",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "video-editor"}

@app.get("/")
async def root():
    """Root endpoint redirects to web interface"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )