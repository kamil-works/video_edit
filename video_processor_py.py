"""
Video processing service using FFmpeg
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, Dict, Any
import httpx
import asyncio
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.temp_dir = settings.temp_storage_path
        self.output_dir = settings.local_storage_path
        self.assets_dir = settings.assets_path
        
    async def download_video(self, url: str, output_path: str) -> bool:
        """Download video from URL"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    
                    with open(output_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            
            logger.info(f"Downloaded video to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json", 
                "-show_format", "-show_streams", video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            else:
                logger.error(f"ffprobe error: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
    
    def create_text_overlay(self, text: str, output_path: str, duration: float = 5.0) -> bool:
        """Create a text overlay video"""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=black:size=1920x1080:duration={duration}",
                "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error creating text overlay: {e}")
            return False
    
    def apply_transition(self, input1: str, input2: str, output: str, 
                        transition_type: str = "fade", duration: float = 1.0) -> bool:
        """Apply transition between two videos"""
        try:
            if transition_type == "fade":
                # Crossfade transition
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input1, "-i", input2,
                    "-filter_complex",
                    f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset=0[v]",
                    "-map", "[v]",
                    "-c:v", "libx264", "-preset", "medium",
                    output
                ]
            elif transition_type == "slide":
                # Slide transition
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input1, "-i", input2,
                    "-filter_complex",
                    f"[0:v][1:v]xfade=transition=slideright:duration={duration}:offset=0[v]",
                    "-map", "[v]",
                    "-c:v", "libx264", "-preset", "medium",
                    output
                ]
            else:  # cut (no transition)
                # Simple concatenation
                return self.concatenate_videos([input1, input2], output)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Transition error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying transition: {e}")
            return False
    
    def concatenate_videos(self, video_paths: list, output_path: str) -> bool:
        """Concatenate multiple videos"""
        try:
            # Create a temporary file list for ffmpeg
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for video_path in video_paths:
                    f.write(f"file '{os.path.abspath(video_path)}'\n")
                filelist_path = f.name
            
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", filelist_path,
                    "-c", "copy",
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0
                
                if not success:
                    logger.error(f"Concatenation error: {result.stderr}")
                
                return success
                
            finally:
                os.unlink(filelist_path)
                
        except Exception as e:
            logger.error(f"Error concatenating videos: {e}")
            return False
    
    def add_watermark(self, input_path: str, output_path: str, 
                     watermark_path: str, position: str = "bottom-right") -> bool:
        """Add watermark to video"""
        try:
            # Position mapping
            positions = {
                "top-left": "10:10",
                "top-right": "main_w-overlay_w-10:10",
                "bottom-left": "10:main_h-overlay_h-10",
                "bottom-right": "main_w-overlay_w-10:main_h-overlay_h-10",
                "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
            }
            
            pos = positions.get(position, positions["bottom-right"])
            
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-i", watermark_path,
                "-filter_complex",
                f"[0:v][1:v]overlay={pos}",
                "-c:a", "copy",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Watermark error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            return False
    
    def encode_video(self, input_path: str, output_path: str, 
                    preset: str = "standard") -> bool:
        """Encode video with specific settings"""
        try:
            # Encoding presets
            presets = {
                "standard": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "128k"],
                "high": ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "256k"],
                "mobile": ["-c:v", "libx264", "-preset", "fast", "-crf", "28", "-s", "1280x720", "-c:a", "aac", "-b:a", "96k"],
                "web": ["-c:v", "libx264", "-preset", "medium", "-crf", "25", "-s", "1920x1080", "-c:a", "aac", "-b:a", "128k"]
            }
            
            encoding_params = presets.get(preset, presets["standard"])
            
            cmd = ["ffmpeg", "-y", "-i", input_path] + encoding_params + [output_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Encoding error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error encoding video: {e}")
            return False
    
    async def process_video(self, job_id: str, video_url: str, customer_name: str,
                          intro_clip: Optional[str] = None,
                          outro_clip: Optional[str] = None,
                          transition_style: str = "fade",
                          overlay_settings: Dict[str, Any] = None,
                          encoding_preset: str = "standard",
                          progress_callback=None) -> str:
        """
        Main video processing pipeline
        """
        overlay_settings = overlay_settings or {}
        temp_files = []
        
        try:
            if progress_callback:
                await progress_callback(0.1, "Starting video processing...")
            
            # Create temp file for downloaded video
            input_video = os.path.join(self.temp_dir, f"{job_id}_input.mp4")
            temp_files.append(input_video)
            
            # Download video
            if not await self.download_video(video_url, input_video):
                raise Exception("Failed to download video")
            
            if progress_callback:
                await progress_callback(0.3, "Video downloaded, processing...")
            
            # Prepare video segments
            video_segments = []
            
            # Add intro if specified
            if intro_clip:
                intro_path = os.path.join(self.assets_dir, "intros", intro_clip)
                if os.path.exists(intro_path):
                    video_segments.append(intro_path)
                    logger.info(f"Added intro: {intro_path}")
            
            # Add main video
            video_segments.append(input_video)
            
            # Add outro if specified
            if outro_clip:
                outro_path = os.path.join(self.assets_dir, "outros", outro_clip)
                if os.path.exists(outro_path):
                    video_segments.append(outro_path)
                    logger.info(f"Added outro: {outro_path}")
            
            if progress_callback:
                await progress_callback(0.5, "Concatenating video segments...")
            
            # Concatenate videos
            concat_output = os.path.join(self.temp_dir, f"{job_id}_concat.mp4")
            temp_files.append(concat_output)
            
            if not self.concatenate_videos(video_segments, concat_output):
                raise Exception("Failed to concatenate videos")
            
            # Apply overlays if specified
            current_video = concat_output
            
            if overlay_settings.get("add_customer_text"):
                if progress_callback:
                    await progress_callback(0.7, "Adding customer text overlay...")
                
                text_overlay_video = os.path.join(self.temp_dir, f"{job_id}_text.mp4")
                temp_files.append(text_overlay_video)
                
                # This would need more sophisticated text overlay implementation
                # For now, skip text overlay
                logger.info("Text overlay requested but not implemented in this version")
            
            if overlay_settings.get("watermark_path"):
                if progress_callback:
                    await progress_callback(0.8, "Adding watermark...")
                
                watermark_video = os.path.join(self.temp_dir, f"{job_id}_watermark.mp4")
                temp_files.append(watermark_video)
                
                watermark_path = os.path.join(self.assets_dir, "logos", overlay_settings["watermark_path"])
                if os.path.exists(watermark_path):
                    if self.add_watermark(current_video, watermark_video, watermark_path):
                        current_video = watermark_video
            
            # Final encoding
            if progress_callback:
                await progress_callback(0.9, "Final encoding...")
            
            final_output = os.path.join(self.output_dir, f"{job_id}_final.mp4")
            
            if not self.encode_video(current_video, final_output, encoding_preset):
                raise Exception("Failed to encode final video")
            
            if progress_callback:
                await progress_callback(1.0, "Video processing completed!")
            
            logger.info(f"Video processing completed: {final_output}")
            return final_output
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            raise
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.error(f"Error cleaning up temp file {temp_file}: {e}")
    
    def get_processing_progress(self, log_output: str) -> float:
        """Parse FFmpeg output to get processing progress"""
        try:
            # This is a simplified progress parser
            # In a real implementation, you'd parse FFmpeg output more thoroughly
            if "frame=" in log_output:
                # Extract frame information and calculate progress
                # This would require knowing the total frames
                pass
            return 0.5  # Placeholder
        except Exception:
            return 0.0