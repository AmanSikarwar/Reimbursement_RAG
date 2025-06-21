# Makefile for Invoice Reimbursement System
# This Makefile provides convenient shortcuts for common development tasks

.PHONY: help setup build start start-dev stop restart status logs health clean reset

# Default target
help: ## Show this help message
	@echo "Invoice Reimbursement System - Available Commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make setup     # Initial setup and start"
	@echo "  make start-dev # Start in development mode"
	@echo "  make logs      # View all logs"
	@echo "  make health    # Check service health"

# Docker Setup Commands
setup: ## Complete setup (build, start, health check)
	@echo "🚀 Setting up Invoice Reimbursement System..."
	@./docker-setup.sh setup

build: ## Build Docker images
	@echo "🔨 Building Docker images..."
	@docker-compose build

start: ## Start services in production mode
	@echo "▶️  Starting services (production mode)..."
	@./docker-setup.sh start

start-dev: ## Start services in development mode (hot reload)
	@echo "🔧 Starting services (development mode)..."
	@./docker-setup.sh start-dev

stop: ## Stop all services
	@echo "⏹️  Stopping services..."
	@./docker-setup.sh stop

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	@./docker-setup.sh restart

# Monitoring Commands
status: ## Show service status and URLs
	@echo "📊 Service Status:"
	@./docker-setup.sh status

logs: ## Show logs for all services
	@echo "📋 Service Logs:"
	@./docker-setup.sh logs

logs-backend: ## Show backend logs only
	@echo "📋 Backend Logs:"
	@./docker-setup.sh logs backend

logs-frontend: ## Show frontend logs only
	@echo "📋 Frontend Logs:"
	@./docker-setup.sh logs frontend

logs-qdrant: ## Show Qdrant logs only
	@echo "📋 Qdrant Logs:"
	@./docker-setup.sh logs qdrant

health: ## Run health check on all services
	@echo "🏥 Running health checks..."
	@./docker-health-check.sh

# Maintenance Commands
clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	@./docker-setup.sh cleanup

reset: ## Complete reset (WARNING: removes all data)
	@echo "⚠️  Resetting environment (this will remove all data)..."
	@./docker-setup.sh reset

# Development Commands
shell-backend: ## Open shell in backend container
	@docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	@docker-compose exec frontend /bin/bash

shell-qdrant: ## Open shell in Qdrant container
	@docker-compose exec qdrant /bin/bash

# Environment Commands
env-check: ## Check environment configuration
	@echo "🔍 Checking environment configuration..."
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		if grep -q "GOOGLE_API_KEY=your_gemini_api_key_here" .env; then \
			echo "⚠️  GOOGLE_API_KEY needs to be set in .env"; \
		else \
			echo "✅ GOOGLE_API_KEY is configured"; \
		fi; \
	else \
		echo "❌ .env file not found. Run 'make env-setup'"; \
	fi

env-setup: ## Setup environment file from template
	@echo "📝 Setting up environment file..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env from template"; \
		echo "⚠️  Please edit .env and set your GOOGLE_API_KEY"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

# Testing Commands
test-api: ## Test API endpoints
	@echo "🧪 Testing API endpoints..."
	@curl -s http://localhost:8000/api/v1/health/quick && echo "✅ Backend API is responding" || echo "❌ Backend API is not responding"
	@curl -s http://localhost:8501/_stcore/health && echo "✅ Frontend is responding" || echo "❌ Frontend is not responding"
	@curl -s http://localhost:6333/health && echo "✅ Qdrant is responding" || echo "❌ Qdrant is not responding"

# Backup Commands
backup: ## Create backup of data and configuration
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@DATE=$$(date +%Y%m%d_%H%M%S); \
	 mkdir -p backups/$$DATE; \
	 docker run --rm -v qdrant_data:/data -v $$(pwd)/backups/$$DATE:/backup ubuntu tar czf /backup/qdrant.tar.gz -C /data . 2>/dev/null || echo "No Qdrant data to backup"; \
	 docker run --rm -v reimbursement_rag_uploads:/data -v $$(pwd)/backups/$$DATE:/backup ubuntu tar czf /backup/uploads.tar.gz -C /data . 2>/dev/null || echo "No uploads to backup"; \
	 cp .env backups/$$DATE/ 2>/dev/null || echo "No .env file to backup"; \
	 echo "✅ Backup created in backups/$$DATE"

# URL Commands
open-frontend: ## Open frontend in browser
	@echo "🌐 Opening frontend..."
	@open http://localhost:8501 || xdg-open http://localhost:8501 || echo "Please open http://localhost:8501 in your browser"

open-api: ## Open API documentation in browser
	@echo "📚 Opening API documentation..."
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Please open http://localhost:8000/docs in your browser"

open-qdrant: ## Open Qdrant dashboard in browser
	@echo "🔍 Opening Qdrant dashboard..."
	@open http://localhost:6333/dashboard || xdg-open http://localhost:6333/dashboard || echo "Please open http://localhost:6333/dashboard in your browser"

# Docker Compose aliases for direct access
up: start ## Alias for start
down: stop ## Alias for stop
ps: status ## Alias for status

# Quick development workflow
dev: env-check start-dev health open-frontend ## Complete development setup
