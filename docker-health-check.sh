#!/bin/bash

# Health check script for Docker containers
# This script performs comprehensive health checks for all services

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

# Function to check if a service is responsive
check_service() {
    local service_name=$1
    local url=$2
    local timeout=${3:-10}
    
    print_status "Checking $service_name at $url..."
    
    if curl -s --max-time $timeout "$url" > /dev/null; then
        print_success "$service_name is healthy"
        return 0
    else
        print_error "$service_name is not responding"
        return 1
    fi
}

# Function to check Docker containers
check_containers() {
    print_status "Checking Docker containers..."
    
    local containers=("invoice-qdrant" "invoice-backend" "invoice-frontend")
    local all_running=true
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
            if [ "$status" = "healthy" ] || [ "$status" = "no-healthcheck" ]; then
                print_success "$container is running"
            else
                print_error "$container is unhealthy (status: $status)"
                all_running=false
            fi
        else
            print_error "$container is not running"
            all_running=false
        fi
    done
    
    return $([ "$all_running" = true ] && echo 0 || echo 1)
}

# Function to check service endpoints
check_endpoints() {
    print_status "Checking service endpoints..."
    
    local all_healthy=true
    
    # Check Qdrant
    if ! check_service "Qdrant" "http://localhost:6333/health" 5; then
        all_healthy=false
    fi
    
    # Check Backend API
    if ! check_service "Backend API" "http://localhost:8000/api/v1/health/quick" 10; then
        all_healthy=false
    fi
    
    # Check Frontend (Streamlit health endpoint)
    if ! check_service "Frontend" "http://localhost:8501/_stcore/health" 10; then
        all_healthy=false
    fi
    
    return $([ "$all_healthy" = true ] && echo 0 || echo 1)
}

# Function to check resource usage
check_resources() {
    print_status "Checking resource usage..."
    
    # Check Docker stats
    echo "Container Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    # Check disk usage
    echo ""
    echo "Disk Usage:"
    docker system df
}

# Function to run comprehensive health check
run_health_check() {
    echo "========================================="
    echo "  Invoice Reimbursement System Health   "
    echo "========================================="
    echo ""
    
    local overall_health=true
    
    # Check containers
    if ! check_containers; then
        overall_health=false
    fi
    
    echo ""
    
    # Check endpoints
    if ! check_endpoints; then
        overall_health=false
    fi
    
    echo ""
    
    # Check resources
    check_resources
    
    echo ""
    echo "========================================="
    
    if [ "$overall_health" = true ]; then
        print_success "All services are healthy!"
        echo ""
        print_status "Service URLs:"
        echo "  Frontend: http://localhost:8501"
        echo "  Backend API: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo "  Qdrant: http://localhost:6333/dashboard"
        return 0
    else
        print_error "Some services are unhealthy!"
        echo ""
        print_status "Try running:"
        echo "  ./docker-setup.sh logs     # Check logs"
        echo "  ./docker-setup.sh restart  # Restart services"
        return 1
    fi
}

# Function to show help
show_help() {
    echo "Docker Health Check Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  check       - Run comprehensive health check (default)"
    echo "  containers  - Check container status only"
    echo "  endpoints   - Check service endpoints only"
    echo "  resources   - Check resource usage only"
    echo "  help        - Show this help message"
}

# Main script logic
main() {
    case "${1:-check}" in
        "check")
            run_health_check
            ;;
        "containers")
            check_containers
            ;;
        "endpoints")
            check_endpoints
            ;;
        "resources")
            check_resources
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
