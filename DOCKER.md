# Docker Deployment Guide

This document provides comprehensive information about deploying the Invoice Reimbursement System using Docker.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment Modes](#deployment-modes)
- [Management Scripts](#management-scripts)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Troubleshooting](#troubleshooting)
- [Production Considerations](#production-considerations)
- [Backup & Recovery](#backup--recovery)

## 🎯 Overview

The Docker deployment provides a complete containerized solution with:

- **Multi-service architecture**: Backend API, Frontend UI, Vector Database
- **Service discovery**: Automatic networking between containers
- **Health monitoring**: Built-in health checks for all services
- **Data persistence**: Volumes for uploads, logs, and database
- **Environment isolation**: Separate configurations for dev/prod

## 🔧 Prerequisites

### System Requirements

- **Docker**: v20.10 or higher
- **Docker Compose**: v2.0 or higher  
- **Memory**: Minimum 4GB RAM available for Docker
- **Storage**: At least 10GB free disk space
- **Network**: Ports 6333, 8000, 8501 available

### Required Accounts

- **Google AI Studio**: For Gemini API key
  - Get your API key: [AI Studio](https://aistudio.google.com/app/apikey)

### Installation Check

```bash
# Check Docker installation
docker --version
docker-compose --version

# Check Docker is running
docker info

# Check available resources
docker system df
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Reimbursement_RAG

# Make scripts executable
chmod +x docker-setup.sh
chmod +x docker-health-check.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (REQUIRED: Add your Gemini API key)
nano .env
```

**Critical Configuration:**

```bash
# REQUIRED: Your Gemini API key
GOOGLE_API_KEY=your_actual_api_key_here

# Optional: Qdrant cloud configuration
QDRANT_API_KEY=your_qdrant_key_if_using_cloud
```

### 3. Deploy

```bash
# Complete setup (build + start + health check)
./docker-setup.sh setup

# Or manual steps:
docker-compose build
docker-compose up -d
./docker-health-check.sh
```

### 4. Access Services

- **Frontend**: <http://localhost:8501>
- **Backend API**: <http://localhost:8000>
- **API Documentation**: <http://localhost:8000/docs>
- **Qdrant Dashboard**: <http://localhost:6333/dashboard>

## ⚙️ Configuration

### Environment Variables

The system uses the following configuration hierarchy:

1. **Docker Compose environment** (highest priority)
2. **`.env` file**
3. **Default values** (lowest priority)

### Key Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Main environment configuration |
| `.env.docker` | Docker-specific template |
| `docker-compose.yml` | Production deployment |
| `docker-compose.dev.yml` | Development deployment |
| `docker-compose.prod.yml` | Production with resource limits |

### Service Configuration

#### Backend (FastAPI)

```yaml
environment:
  - APP_NAME=Invoice Reimbursement System
  - DEBUG=false
  - LOG_LEVEL=INFO
  - GOOGLE_API_KEY=${GOOGLE_API_KEY}
  - QDRANT_URL=http://qdrant:6333
```

#### Frontend (Streamlit)

```yaml
environment:
  - STREAMLIT_API_BASE_URL=http://backend:8000
  - STREAMLIT_API_TIMEOUT=300
  - STREAMLIT_DEFAULT_CURRENCY=INR
```

#### Qdrant (Vector Database)

```yaml
environment:
  - QDRANT__SERVICE__HTTP_PORT=6333
  - QDRANT__SERVICE__GRPC_PORT=6334
```

## 🎭 Deployment Modes

### Development Mode

**Features:**

- Hot reload enabled
- Debug logging
- Code mounting
- Faster iteration

```bash
# Start development mode
./docker-setup.sh start-dev

# Or directly
docker-compose -f docker-compose.dev.yml up -d
```

### Production Mode

**Features:**

- Optimized images
- No hot reload
- Production logging
- Resource limits

```bash
# Start production mode
./docker-setup.sh start

# Or with resource limits
docker-compose -f docker-compose.prod.yml up -d
```

### Comparison

| Aspect | Development | Production |
|--------|-------------|------------|
| Build Time | Faster (cached) | Slower (optimized) |
| Image Size | Larger | Smaller |
| Hot Reload | ✅ Yes | ❌ No |
| Debug Logs | ✅ Yes | ❌ No |
| Resource Limits | ❌ No | ✅ Yes |
| Security | Basic | Enhanced |

## 🛠️ Management Scripts

### docker-setup.sh

Main management script for Docker operations:

```bash
# Setup and management
./docker-setup.sh setup          # Initial setup
./docker-setup.sh start          # Start production
./docker-setup.sh start-dev      # Start development
./docker-setup.sh stop           # Stop services
./docker-setup.sh restart        # Restart services

# Monitoring
./docker-setup.sh status         # Show status
./docker-setup.sh logs           # Show all logs
./docker-setup.sh logs backend   # Show specific service logs

# Maintenance
./docker-setup.sh cleanup        # Clean unused resources
./docker-setup.sh reset          # Complete reset
```

### docker-health-check.sh

Health monitoring script:

```bash
# Health checks
./docker-health-check.sh check      # Full health check
./docker-health-check.sh containers # Container status only
./docker-health-check.sh endpoints  # Service endpoints only
./docker-health-check.sh resources  # Resource usage
```

## 📊 Monitoring & Health Checks

### Built-in Health Checks

Each service includes health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/quick"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Monitoring Commands

```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Service logs
docker-compose logs -f backend

# Health status
curl http://localhost:8000/api/v1/health
```

### Health Check Endpoints

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Backend | `/api/v1/health/quick` | Quick health check |
| Backend | `/api/v1/health` | Detailed health info |
| Frontend | `/_stcore/health` | Streamlit health |
| Qdrant | `/health` | Database health |

## 🔧 Troubleshooting

### Common Issues

#### 1. Services Not Starting

**Problem**: Containers exit immediately

**Solutions:**

```bash
# Check logs
./docker-setup.sh logs

# Check environment
grep GOOGLE_API_KEY .env

# Verify API key is set
echo $GOOGLE_API_KEY
```

#### 2. Port Conflicts

**Problem**: "Port already in use"

**Solutions:**

```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different ports
docker-compose -p custom-prefix up -d
```

#### 3. Memory Issues

**Problem**: Containers getting killed (OOMKilled)

**Solutions:**

```bash
# Check memory usage
docker stats

# Increase Docker memory in Docker Desktop
# Settings > Resources > Memory > 4GB+

# Use production config with limits
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. API Connection Issues

**Problem**: Frontend can't connect to backend

**Solutions:**

```bash
# Check network connectivity
docker network ls
docker network inspect reimbursement_rag_invoice-network

# Verify service names
docker-compose ps

# Check backend health
curl http://localhost:8000/api/v1/health/quick
```

### Debug Steps

1. **Check container status**:

   ```bash
   docker-compose ps
   ./docker-health-check.sh containers
   ```

2. **Review logs**:

   ```bash
   ./docker-setup.sh logs
   docker-compose logs backend
   ```

3. **Test connectivity**:

   ```bash
   curl -v http://localhost:8000/api/v1/health/quick
   curl -v http://localhost:8501/_stcore/health
   ```

4. **Resource check**:

   ```bash
   docker stats
   docker system df
   ```

## 🏭 Production Considerations

### Security

1. **Environment Variables**:

   ```bash
   # Use secrets for sensitive data
   GOOGLE_API_KEY=<secure-api-key>
   
   # Restrict allowed hosts
   ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
   ```

2. **Network Security**:

   ```yaml
   # Use specific network configurations
   networks:
     invoice-network:
       driver: bridge
       ipam:
         config:
           - subnet: 172.20.0.0/16
   ```

3. **Resource Limits**:

   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
         cpus: '2.0'
   ```

### Scaling

1. **Horizontal Scaling**:

   ```bash
   # Scale backend service
   docker-compose up -d --scale backend=3
   ```

2. **Load Balancing**:
   Use nginx or cloud load balancer in front of services.

### Backup Strategy

1. **Data Volumes**:

   ```bash
   # Backup Qdrant data
   docker run --rm -v qdrant_data:/data -v $(pwd):/backup ubuntu tar czf /backup/qdrant-backup.tar.gz -C /data .
   
   # Backup uploads
   docker run --rm -v prod_uploads:/data -v $(pwd):/backup ubuntu tar czf /backup/uploads-backup.tar.gz -C /data .
   ```

2. **Configuration**:

   ```bash
   # Backup environment
   cp .env .env.backup
   cp docker-compose.yml docker-compose.backup.yml
   ```

## 💾 Backup & Recovery

### Automated Backup Script

Create a backup script:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup Qdrant data
docker run --rm \
  -v qdrant_data:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  ubuntu tar czf /backup/qdrant.tar.gz -C /data .

# Backup uploads
docker run --rm \
  -v prod_uploads:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  ubuntu tar czf /backup/uploads.tar.gz -C /data .

# Backup configuration
cp .env "$BACKUP_DIR/"
cp docker-compose*.yml "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

### Recovery Process

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: $0 <backup-directory>"
  exit 1
fi

# Stop services
./docker-setup.sh stop

# Restore Qdrant data
docker run --rm \
  -v qdrant_data:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  ubuntu tar xzf /backup/qdrant.tar.gz -C /data

# Restore uploads
docker run --rm \
  -v prod_uploads:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  ubuntu tar xzf /backup/uploads.tar.gz -C /data

# Restore configuration
cp "$BACKUP_DIR/.env" .env

# Restart services
./docker-setup.sh start

echo "Restore completed from: $BACKUP_DIR"
```

## 📞 Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Run the health check: `./docker-health-check.sh`
3. Review logs: `./docker-setup.sh logs`
4. Create an issue with:
   - Docker version (`docker --version`)
   - System info (`docker system info`)
   - Error logs
   - Configuration (without sensitive data)
