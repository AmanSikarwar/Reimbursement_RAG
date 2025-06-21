# Docker Quick Reference

Quick reference for Docker commands specific to the Invoice Reimbursement System.

## 🚀 Essential Commands

### Setup & Start

```bash
# Complete setup (recommended for first time)
./docker-setup.sh setup

# Start production services
./docker-setup.sh start

# Start development services (with hot reload)
./docker-setup.sh start-dev
```

### Management

```bash
# Stop all services
./docker-setup.sh stop

# Restart services
./docker-setup.sh restart

# View service status
./docker-setup.sh status

# Complete reset (removes all data)
./docker-setup.sh reset
```

### Monitoring

```bash
# Health check all services
./docker-health-check.sh

# View all logs
./docker-setup.sh logs

# View specific service logs
./docker-setup.sh logs backend
./docker-setup.sh logs frontend
./docker-setup.sh logs qdrant
```

## 🔧 Manual Docker Commands

### Container Management

```bash
# View running containers
docker-compose ps

# Stop specific service
docker-compose stop backend

# Start specific service
docker-compose start backend

# Restart specific service
docker-compose restart backend
```

### Logs & Debugging

```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f backend

# View last 100 lines of logs
docker-compose logs --tail=100 backend

# View logs since specific time
docker-compose logs --since="2024-01-01T00:00:00" backend
```

### Images & Builds

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend

# Build without cache
docker-compose build --no-cache

# Pull latest base images
docker-compose pull
```

### Data Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect qdrant_data

# Backup volume
docker run --rm -v qdrant_data:/data -v $(pwd):/backup ubuntu tar czf /backup/qdrant-backup.tar.gz -C /data .

# Remove all volumes (WARNING: This deletes all data)
docker-compose down -v
```

## 🌐 Service URLs

After starting the services:

- **Frontend**: <http://localhost:8501>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>
- **Qdrant**: <http://localhost:6333/dashboard>

## 🚨 Emergency Commands

### If things go wrong

```bash
# Stop everything
docker-compose down

# Remove containers and networks
docker-compose down --remove-orphans

# Remove everything including volumes (ALL DATA LOST)
docker-compose down -v --remove-orphans

# Clean up Docker system
docker system prune -f

# Clean up all unused images
docker image prune -a -f
```

### Nuclear option (complete cleanup)

```bash
# Stop all containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)

# Remove all images
docker rmi $(docker images -q)

# Remove all volumes
docker volume prune -f

# Remove all networks
docker network prune -f
```

## 📊 Useful Monitoring

```bash
# Real-time resource usage
docker stats

# Disk usage
docker system df

# Container processes
docker-compose top

# Network information
docker network ls
docker network inspect <network-name>
```

## 🔐 Environment Variables

Key environment variables you might need to set:

```bash
# Required
export GOOGLE_API_KEY="your-api-key-here"

# Optional
export QDRANT_API_KEY="your-qdrant-key"
export ALLOWED_HOSTS="yourdomain.com"
export DEBUG="false"
export LOG_LEVEL="INFO"
```

## 📝 Configuration Files

- `docker-compose.yml` - Production deployment
- `docker-compose.dev.yml` - Development with hot reload  
- `docker-compose.prod.yml` - Production with resource limits
- `.env` - Environment variables
- `Dockerfile` - Container build instructions
