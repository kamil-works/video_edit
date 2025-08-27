# Containerized Video Editor System

A comprehensive video editing system built with FastAPI and FFmpeg, designed for easy deployment on Coolify. Features a REST API for video processing with customizable intros, outros, and overlays, plus a web interface for configuration.

## ✨ Features

### 🎬 Core Video Processing
- Download videos from URLs
- Add custom intro and outro clips
- Apply smooth transitions (fade, cut, slide)
- Customer name overlays and watermarks
- Multiple encoding presets (mobile, standard, high quality)
- Async job processing with progress tracking

### 🌐 API & Web Interface
- **REST API** for programmatic access
- **Web Dashboard** for non-technical users
- **Asset Management** - upload/manage intro/outro clips
- **Job Monitoring** - real-time progress tracking
- **Settings Panel** - configure encoding and storage options

### 🚀 Deployment Ready
- **Docker containerized** with FFmpeg pre-installed
- **Coolify compatible** with provided compose files
- **Redis-backed** job queue for scalability
- **S3 support** for cloud storage integration
- **Health checks** and monitoring endpoints

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   REST API      │    │   Celery Worker │
│   (Dashboard)   │◄──►│   (FastAPI)     │◄──►│   (FFmpeg)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Redis Queue   │
                    │   (Job Status)  │
                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd video-editor-system
cp .env.example .env
# Edit .env with your settings
```

### 2. Local Development

```bash
# Using Docker Compose
docker-compose up -d

# Or run individually
docker build -t video-editor .
docker run -p 8000:8000 video-editor
```

### 3. Coolify Deployment

1. **Create New Project** in Coolify
2. **Import Repository** or use Git integration
3. **Set Environment Variables** from `.env.example`
4. **Use provided** `coolify-docker-compose.yml`
5. **Deploy** and access via your domain

## 📚 API Documentation

### Process Video
```bash
POST /api/v1/process
Content-Type: application/json

{
  "video_url": "https://example.com/video.mp4",
  "customer_name": "John Doe",
  "intro_clip": "intro-branded.mp4",
  "outro_clip": "outro-subscribe.mp4",
  "transition_style": "fade",
  "encoding_preset": "standard"
}
```

### Check Job Status
```bash
GET /api/v1/status/{job_id}

# Response:
{
  "job_id": "uuid-here",
  "status": "processing",
  "progress": 0.65,
  "message": "Adding outro clip...",
  "result_url": null
}
```

### Download Result
```bash
GET /api/v1/result/{job_id}

# Response:
{
  "job_id": "uuid-here",
  "status": "completed",
  "download_url": "https://your-storage/final-video.mp4",
  "completed_at": "2024-01-01T12:00:00Z"
}
```

## 🎛️ Web Interface

Access the web dashboard at `http://localhost:8000` (or your deployed URL):

- **📊 Dashboard** - Submit new jobs, view progress, download results
- **📁 Assets** - Upload and manage intro/outro clips and logos  
- **⚙️ Jobs** - Monitor all processing jobs with real-time updates
- **🔧 Settings** - Configure encoding presets and storage options

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STORAGE_TYPE` | Storage backend (`local` or `s3`) | `local` |
| `MAX_CONCURRENT_JOBS` | Worker concurrency | `3` |
| `JOB_EXPIRY_HOURS` | Job data retention | `24` |
| `AWS_ACCESS_KEY_ID` | S3 access key (if using S3) | - |
| `S3_BUCKET` | S3 bucket name | - |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

### Asset Organization
```
assets/
├── intros/          # Intro video clips
├── outros/          # Outro video clips  
└── logos/           # Watermark images (PNG/SVG)
```

### Encoding Presets
- **Mobile**: 720p, optimized for mobile devices
- **Standard**: 1080p, balanced quality/size  
- **High**: 1080p, maximum quality

## 🐳 Docker & Deployment

### Build Custom Image
```bash
docker build -t your-registry/video-editor:latest .
docker push your-registry/video-editor:latest
```

### Production Considerations
- **Volume Persistence**: Mount volumes for assets and outputs
- **Resource Limits**: Configure memory/CPU limits for workers
- **Storage**: Use S3 for production file storage
- **Monitoring**: Monitor Redis queue and worker health
- **Scaling**: Add more worker containers for higher throughput

### Coolify Environment Setup
```bash
# Required
FQDN=your-video-editor.com
DOCKER_IMAGE=your-registry/video-editor:latest

# Optional S3 Storage  
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=your-bucket
```

## 🔧 Development

### Project Structure
```
app/
├── api/             # REST API routes
├── core/            # Configuration and storage
├── services/        # Video processing logic  
├── workers/         # Celery tasks
├── web/             # Web interface routes
├── templates/       # HTML templates
└── static/          # CSS/JS assets
```

### Adding New Features
1. **Video Processing**: Extend `VideoProcessor` class
2. **API Endpoints**: Add routes to `app/api/routes.py`
3. **Web Interface**: Update templates and add JS functionality
4. **Storage**: Implement new storage backends in `app/core/storage.py`

### Testing
```bash
# Run tests (if implemented)
python -m pytest

# Manual API testing
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"video_url":"https://example.com/test.mp4","customer_name":"Test"}'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**FFmpeg not found**
```bash
# Verify FFmpeg installation in container
docker exec -it container_name ffmpeg -version
```

**Redis connection failed**
```bash
# Check Redis container status
docker-compose ps redis
docker-compose logs redis
```

**Video processing stuck**
```bash
# Check worker logs
docker-compose logs worker

# Monitor Celery queue
# Access Flower at http://localhost:5555
```

**File upload errors**
```bash
# Check volume permissions
ls -la ./uploads ./assets ./outputs

# Fix permissions if needed
sudo chown -R 1000:1000 ./uploads ./assets ./outputs
```

### Performance Optimization

- **Worker Scaling**: Increase `MAX_CONCURRENT_JOBS` based on CPU cores
- **Memory Management**: Monitor memory usage during large file processing
- **Storage**: Use SSD storage for temporary files for better performance
- **Network**: Ensure stable internet for video downloads

### Monitoring

**Health Endpoints**
- Application: `GET /health`
- Celery Workers: Monitor via Flower UI
- Redis: `redis-cli ping`

**Log Locations**
- Application: Docker container logs
- Worker: Docker container logs  
- Redis: Redis container logs

## 🔒 Security Considerations

- **File Validation**: Only allow whitelisted video formats
- **Size Limits**: Configure maximum file size limits
- **Input Sanitization**: Sanitize customer names and file paths
- **Access Control**: Implement authentication for production use
- **Storage Security**: Use secure S3 bucket policies
- **Network**: Use HTTPS in production (handled by Coolify)

## 🎯 Roadmap

### Planned Features
- [ ] **Authentication & Authorization** - Multi-user support
- [ ] **Batch Processing** - Process multiple videos at once  
- [ ] **Advanced Overlays** - Dynamic text animations, logos
- [ ] **Template System** - Save and reuse processing templates
- [ ] **Webhook Support** - Notify external systems on completion
- [ ] **Video Analytics** - Duration, resolution, format analysis
- [ ] **Preview Generation** - Create thumbnails and preview clips
- [ ] **Watermark Positioning** - Drag & drop watermark placement

### Performance Improvements
- [ ] **Parallel Processing** - Multi-threaded FFmpeg operations
- [ ] **Caching Layer** - Cache processed assets
- [ ] **CDN Integration** - Distribute output files globally
- [ ] **Queue Priority** - Prioritize certain jobs
- [ ] **Resource Monitoring** - Auto-scale workers based on load

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check `/docs` endpoint when running
- **Community**: Join our Discord/Slack (if available)

---

Built with ❤️ using FastAPI, FFmpeg, and Docker
