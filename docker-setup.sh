#!/bin/bash

# Docker setup script for Invoice Reimbursement System
# This script helps set up and manage the Docker environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is installed and running
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Function to check if docker-compose is available
check_docker_compose() {
    print_status "Checking Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    print_success "Docker Compose is available: $COMPOSE_CMD"
}

# Function to check environment variables
check_env() {
    print_status "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found. Copying from .env.example..."
            cp .env.example .env
            print_warning "Please edit .env file with your actual configuration values."
            print_warning "Required: GOOGLE_API_KEY"
        else
            print_error ".env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    # Check for required environment variables
    source .env 2>/dev/null || true
    
    if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_gemini_api_key_here" ]; then
        print_error "GOOGLE_API_KEY is not set in .env file."
        print_error "Please set your Gemini API key in the .env file."
        exit 1
    fi
    
    print_success "Environment configuration looks good"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    $COMPOSE_CMD build --no-cache
    
    print_success "Docker images built successfully"
}

# Function to start services
start_services() {
    local compose_file=${1:-docker-compose.yml}
    
    print_status "Starting services with $compose_file..."
    
    $COMPOSE_CMD -f $compose_file up -d
    
    print_success "Services started successfully"
    print_status "Waiting for services to be ready..."
    
    # Wait for backend to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/health/quick > /dev/null; then
            print_success "Backend is ready!"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            print_warning "Backend is taking longer than expected to start"
        fi
    done
    
    # Wait for frontend to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8501/_stcore/health > /dev/null; then
            print_success "Frontend is ready!"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            print_warning "Frontend is taking longer than expected to start"
        fi
    done
}

# Function to stop services
stop_services() {
    local compose_file=${1:-docker-compose.yml}
    
    print_status "Stopping services..."
    
    $COMPOSE_CMD -f $compose_file down
    
    print_success "Services stopped successfully"
}

# Function to show logs
show_logs() {
    local service=$1
    local compose_file=${2:-docker-compose.yml}
    
    if [ -n "$service" ]; then
        $COMPOSE_CMD -f $compose_file logs -f $service
    else
        $COMPOSE_CMD -f $compose_file logs -f
    fi
}

# Function to show status
show_status() {
    local compose_file=${1:-docker-compose.yml}
    
    print_status "Service status:"
    $COMPOSE_CMD -f $compose_file ps
    
    echo ""
    print_status "Service URLs:"
    echo "  Frontend: http://localhost:8501"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo "  Qdrant: http://localhost:6333"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    # Stop and remove containers
    $COMPOSE_CMD -f docker-compose.yml down --remove-orphans 2>/dev/null || true
    $COMPOSE_CMD -f docker-compose.dev.yml down --remove-orphans 2>/dev/null || true
    
    # Remove unused images
    docker image prune -f
    
    print_success "Cleanup completed"
}

# Function to reset everything
reset() {
    print_warning "This will remove all containers, volumes, and rebuild everything."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Resetting environment..."
        
        # Stop services
        $COMPOSE_CMD -f docker-compose.yml down --volumes --remove-orphans 2>/dev/null || true
        $COMPOSE_CMD -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true
        
        # Remove images
        docker rmi $(docker images | grep -E "(invoice|qdrant)" | awk '{print $3}') 2>/dev/null || true
        
        # Rebuild and start
        build_images
        start_services
        
        print_success "Environment reset completed"
    else
        print_status "Reset cancelled"
    fi
}

# Function to show help
show_help() {
    echo "Docker Setup Script for Invoice Reimbursement System"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup           - Initial setup (check dependencies, build images, start services)"
    echo "  build           - Build Docker images"
    echo "  start           - Start services in production mode"
    echo "  start-dev       - Start services in development mode (with hot reload)"
    echo "  stop            - Stop services"
    echo "  restart         - Restart services"
    echo "  status          - Show service status and URLs"
    echo "  logs [service]  - Show logs (optionally for specific service)"
    echo "  cleanup         - Clean up Docker resources"
    echo "  reset           - Reset entire environment (destructive)"
    echo "  help            - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                 # Initial setup"
    echo "  $0 start-dev             # Start in development mode"
    echo "  $0 logs backend          # Show backend logs"
    echo "  $0 logs                  # Show all logs"
}

# Main script logic
main() {
    case "${1:-setup}" in
        "setup")
            check_docker
            check_docker_compose
            check_env
            build_images
            start_services
            show_status
            ;;
        "build")
            check_docker
            check_docker_compose
            build_images
            ;;
        "start")
            check_docker
            check_docker_compose
            start_services docker-compose.yml
            show_status docker-compose.yml
            ;;
        "start-dev")
            check_docker
            check_docker_compose
            start_services docker-compose.dev.yml
            show_status docker-compose.dev.yml
            ;;
        "stop")
            stop_services docker-compose.yml
            stop_services docker-compose.dev.yml
            ;;
        "restart")
            stop_services docker-compose.yml
            stop_services docker-compose.dev.yml
            start_services docker-compose.yml
            show_status docker-compose.yml
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs $2
            ;;
        "cleanup")
            cleanup
            ;;
        "reset")
            reset
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
