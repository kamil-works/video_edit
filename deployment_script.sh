#!/bin/bash

# Video Editor System Deployment Script
# This script helps deploy the containerized video editing system

set -e

echo "🎬 Video Editor System Deployment"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="video-editor"
DOCKER_TAG="latest"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "All dependencies are available"
}

setup_environment() {
    log_info "Setting up environment..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file not found. Creating from example..."
        if [ -f ".env.example" ]; then
            cp .env.example $ENV_FILE
            log_success "Environment file created. Please edit $ENV_FILE with your settings."
            log_warning "Deployment paused. Please configure your environment variables and run again."
            exit 1
        else
            log_error ".env.example file not found!"
            exit 1
        fi
    fi
    
    log_success "Environment configuration found"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    directories=("uploads" "outputs" "assets/intros" "assets/outros" "assets/logos" "temp")
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_success "Created directory: $dir"
    done
    
    # Set proper permissions
    chmod 755 uploads outputs assets temp
    chmod -R 755 assets/
    
    log_success "Directory structure created"
}

build_image() {
    log_info "Building Docker image..."
    
    docker build -t $DOCKER_IMAGE:$DOCKER_TAG . || {
        log_error "Failed to build Docker image"
        exit 1
    }
    
    log_success "Docker image built successfully"
}

start_services() {
    log_info "Starting services with Docker Compose..."
    
    # Stop existing services
    docker-compose down 2>/dev/null || true
    
    # Start services
    docker-compose up -d || {
        log_error "Failed to start services"
        exit 1
    }
    
    log_success "Services started successfully"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    timeout 30s bash -c 'until docker-compose exec -T redis redis-cli ping | grep PONG; do sleep 1; done' || {
        log_error "Redis failed to start"
        exit 1
    }
    log_success "Redis is ready"
    
    # Wait for main application
    log_info "Waiting for main application..."
    timeout 60s bash -c 'until curl -s http://localhost:8000/health | grep healthy; do sleep 2; done' || {
        log_error "Main application failed to start"
        exit 1
    }
    log_success "Main application is ready"
    
    # Check worker
    log_info "Checking worker status..."
    sleep 5
    if docker-compose ps worker | grep -q "Up"; then
        log_success "Worker is running"
    else
        log_warning "Worker may not be running properly. Check logs with: docker-compose logs worker"
    fi
}

show_status() {
    echo ""
    log_success "🎉 Deployment completed successfully!"
    echo ""
    echo "Services Status:"
    echo "================"
    docker-compose ps
    echo ""
    echo "Access Points:"
    echo "=============="
    echo "📊 Web Dashboard: http://localhost:8000"
    echo "🔧 API Documentation: http://localhost:8000/docs"
    echo "📈 Celery Monitor (Flower): http://localhost:5555"
    echo "❤️  Health Check: http://localhost:8000/health"
    echo ""
    echo "Useful Commands:"
    echo "================"
    echo "View logs: docker-compose logs -f [service_name]"
    echo "Stop services: docker-compose down"
    echo "Restart services: docker-compose restart"
    echo "Scale workers: docker-compose up -d --scale worker=3"
    echo ""
}

# Main deployment process
main() {
    case "${1:-deploy}" in
        "deploy")
            echo "Starting full deployment..."
            check_dependencies
            setup_environment
            create_directories
            build_image
            start_services
            wait_for_services
            show_status
            ;;
        "start")
            log_info "Starting existing services..."
            docker-compose up -d
            wait_for_services
            show_status
            ;;
        "stop")
            log_info "Stopping services..."
            docker-compose down
            log_success "Services stopped"
            ;;
        "restart")
            log_info "Restarting services..."
            docker-compose restart
            wait_for_services
            show_status
            ;;
        "rebuild")
            log_info "Rebuilding and redeploying..."
            docker-compose down
            build_image
            start_services
            wait_for_services
            show_status
            ;;
        "logs")
            log_info "Showing logs..."
            docker-compose logs -f "${2:-}"
            ;;
        "status")
            echo "Services Status:"
            docker-compose ps
            echo ""
            echo "System Health:"
            curl -s http://localhost:8000/health || echo "❌ Application not responding"
            ;;
        "clean")
            log_warning "This will remove all containers, volumes, and images. Are you sure? (y/N)"
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                docker-compose down -v --rmi all
                docker system prune -f
                log_success "Cleanup completed"
            else
                log_info "Cleanup cancelled"
            fi
            ;;
        "setup-coolify")
            log_info "Setting up for Coolify deployment..."
            if [ ! -f "coolify-docker-compose.yml" ]; then
                log_error "coolify-docker-compose.yml not found!"
                exit 1
            fi
            
            echo ""
            echo "Coolify Deployment Instructions:"
            echo "==============================="
            echo "1. Create a new project in Coolify"
            echo "2. Add a new service with the following settings:"
            echo "   - Type: Docker Compose"
            echo "   - Repository: $(git remote get-url origin 2>/dev/null || echo 'your-git-repo')"
            echo "   - Compose file: coolify-docker-compose.yml"
            echo ""
            echo "3. Set these environment variables in Coolify:"
            echo "   FQDN=your-domain.com"
            echo "   DOCKER_IMAGE=your-registry/video-editor:latest"
            echo "   PORT=8000"
            echo ""
            echo "4. Optional S3 configuration:"
            echo "   STORAGE_TYPE=s3"
            echo "   AWS_ACCESS_KEY_ID=your_key"
            echo "   AWS_SECRET_ACCESS_KEY=your_secret"
            echo "   S3_BUCKET=your_bucket"
            echo ""
            echo "5. Deploy the service"
            log_success "Coolify setup guide displayed"
            ;;
        "help"|"-h"|"--help")
            echo "Video Editor System Deployment Script"
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  deploy     - Full deployment (default)"
            echo "  start      - Start existing services"
            echo "  stop       - Stop services"
            echo "  restart    - Restart services"
            echo "  rebuild    - Rebuild images and redeploy"
            echo "  logs [svc] - Show logs (optionally for specific service)"
            echo "  status     - Show service status"
            echo "  clean      - Remove all containers and images"
            echo "  setup-coolify - Show Coolify deployment instructions"
            echo "  help       - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 deploy          # Full deployment"
            echo "  $0 logs worker     # Show worker logs"
            echo "  $0 restart         # Restart all services"
            echo "  $0 setup-coolify   # Coolify deployment guide"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Trap to ensure cleanup on script exit
trap 'echo ""; log_info "Script interrupted. You can resume with: $0 start"' INT

# Run main function with all arguments
main "$@"