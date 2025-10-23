# VRecommendation System Makefile
# Cross-platform build and deployment automation

.PHONY: help install build start stop restart clean logs status test dev prod health backup

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Environment detection
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    SHELL := cmd.exe
    .SHELLFLAGS := /c
    RM := del /Q /F
    RMDIR := rmdir /S /Q
    MKDIR := mkdir
    COPY := copy
    MOVE := move
    ECHO := echo
    DOCKER_COMPOSE := docker-compose
    NULL := nul
else
    DETECTED_OS := $(shell uname -s)
    RM := rm -f
    RMDIR := rm -rf
    MKDIR := mkdir -p
    COPY := cp
    MOVE := mv
    ECHO := echo
    DOCKER_COMPOSE := docker-compose
    NULL := /dev/null
endif

help: ## Show this help message
	@$(ECHO) "========================================"
	@$(ECHO) "  VRecommendation System - Makefile"
	@$(ECHO) "========================================"
	@$(ECHO) ""
	@$(ECHO) "Detected OS: $(DETECTED_OS)"
	@$(ECHO) ""
	@$(ECHO) "Available commands:"
ifeq ($(OS),Windows_NT)
	@findstr /R "^[a-zA-Z_-]*:.*##" $(MAKEFILE_LIST) | findstr /V findstr
else
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
endif
	@$(ECHO) ""

# Installation and Setup Commands
install: ## Install dependencies and setup environment
	@$(ECHO) "$(GREEN)Installing dependencies and setting up environment...$(NC)"
ifeq ($(OS),Windows_NT)
	@if not exist .env copy .env.development .env
	@if not exist frontend\project\.env copy frontend\project\.env.example frontend\project\.env
else
	@cp -n .env.development .env 2>$(NULL) || true
	@cp -n frontend/project/.env.example frontend/project/.env 2>$(NULL) || true
endif
	@$(ECHO) "$(GREEN)Environment setup completed!$(NC)"

setup: install ## Alias for install

# Build Commands
build: ## Build all Docker images
	@$(ECHO) "$(GREEN)Building all Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build
	@$(ECHO) "$(GREEN)Build completed!$(NC)"

build-api: ## Build API server only
	@$(ECHO) "$(GREEN)Building API server...$(NC)"
	@$(DOCKER_COMPOSE) build api_server
	@$(ECHO) "$(GREEN)API server build completed!$(NC)"

build-ai: ## Build AI server only
	@$(ECHO) "$(GREEN)Building AI server...$(NC)"
	@$(DOCKER_COMPOSE) build ai_server
	@$(ECHO) "$(GREEN)AI server build completed!$(NC)"

build-frontend: ## Build frontend only
	@$(ECHO) "$(GREEN)Building frontend...$(NC)"
	@$(DOCKER_COMPOSE) build frontend
	@$(ECHO) "$(GREEN)Frontend build completed!$(NC)"

rebuild: ## Rebuild all images from scratch
	@$(ECHO) "$(YELLOW)Rebuilding all images from scratch...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	@$(ECHO) "$(GREEN)Rebuild completed!$(NC)"

# Start Commands
start: ## Start all services
	@$(ECHO) "$(GREEN)Starting all services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@$(ECHO) "$(GREEN)All services started!$(NC)"
	@$(MAKE) status
	@$(MAKE) urls

up: start ## Alias for start

start-logs: ## Start services and show logs
	@$(ECHO) "$(GREEN)Starting all services with logs...$(NC)"
	@$(DOCKER_COMPOSE) up

dev: ## Start services for development
	@$(ECHO) "$(GREEN)Starting services in development mode...$(NC)"
	@$(DOCKER_COMPOSE) up -d redis prometheus
	@$(ECHO) "$(YELLOW)Redis and Prometheus started. Run API and AI servers manually for development.$(NC)"
	@$(ECHO) "$(BLUE)Commands:$(NC)"
	@$(ECHO) "  API Server:  make dev-api"
	@$(ECHO) "  AI Server:   make dev-ai"
	@$(ECHO) "  Frontend:    make dev-frontend"

# Stop Commands
stop: ## Stop all services
	@$(ECHO) "$(YELLOW)Stopping all services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@$(ECHO) "$(GREEN)All services stopped!$(NC)"

down: stop ## Alias for stop

stop-force: ## Force stop all services
	@$(ECHO) "$(RED)Force stopping all services...$(NC)"
	@$(DOCKER_COMPOSE) kill
	@$(DOCKER_COMPOSE) down
	@$(ECHO) "$(GREEN)All services force stopped!$(NC)"

kill: stop-force ## Alias for stop-force

# Restart Commands
restart: ## Restart all services
	@$(ECHO) "$(YELLOW)Restarting all services...$(NC)"
	@$(DOCKER_COMPOSE) restart
	@$(ECHO) "$(GREEN)All services restarted!$(NC)"
	@$(MAKE) status

restart-api: ## Restart API server only
	@$(ECHO) "$(YELLOW)Restarting API server...$(NC)"
	@$(DOCKER_COMPOSE) restart api_server
	@$(ECHO) "$(GREEN)API server restarted!$(NC)"

restart-ai: ## Restart AI server only
	@$(ECHO) "$(YELLOW)Restarting AI server...$(NC)"
	@$(DOCKER_COMPOSE) restart ai_server
	@$(ECHO) "$(GREEN)AI server restarted!$(NC)"

restart-frontend: ## Restart frontend only
	@$(ECHO) "$(YELLOW)Restarting frontend...$(NC)"
	@$(DOCKER_COMPOSE) restart frontend
	@$(ECHO) "$(GREEN)Frontend restarted!$(NC)"

# Status and Monitoring
status: ## Show status of all services
	@$(ECHO) "$(GREEN)Services Status:$(NC)"
	@$(ECHO) "=================="
	@$(DOCKER_COMPOSE) ps

ps: status ## Alias for status

logs: ## Show logs for all services
	@$(DOCKER_COMPOSE) logs -f

logs-api: ## Show API server logs
	@$(DOCKER_COMPOSE) logs -f api_server

logs-ai: ## Show AI server logs
	@$(DOCKER_COMPOSE) logs -f ai_server

logs-frontend: ## Show frontend logs
	@$(DOCKER_COMPOSE) logs -f frontend

logs-redis: ## Show Redis logs
	@$(DOCKER_COMPOSE) logs -f redis

logs-all: ## Show logs for all services (last 50 lines)
	@$(DOCKER_COMPOSE) logs --tail=50

# Service URLs
urls: ## Show service URLs
	@$(ECHO) "$(GREEN)Service URLs:$(NC)"
	@$(ECHO) "=============="
	@$(ECHO) "  Frontend:    http://localhost:5173"
	@$(ECHO) "  API Server:  http://localhost:2030"
	@$(ECHO) "  AI Server:   http://localhost:9999"
	@$(ECHO) "  Prometheus:  http://localhost:9090"
	@$(ECHO) "  Redis:       localhost:6379"
	@$(ECHO) ""

# Development Commands
dev-api: ## Run API server in development mode
	@$(ECHO) "$(GREEN)Starting API server in development mode...$(NC)"
ifeq ($(OS),Windows_NT)
	@cd backend\api_server && go run main.go
else
	@cd backend/api_server && go run main.go
endif

dev-ai: ## Run AI server in development mode
	@$(ECHO) "$(GREEN)Starting AI server in development mode...$(NC)"
ifeq ($(OS),Windows_NT)
	@cd backend\ai_server && poetry run python src/main.py
else
	@cd backend/ai_server && poetry run python src/main.py
endif

dev-frontend: ## Run frontend in development mode
	@$(ECHO) "$(GREEN)Starting frontend in development mode...$(NC)"
ifeq ($(OS),Windows_NT)
	@cd frontend\project && npm run dev
else
	@cd frontend/project && npm run dev
endif

# Test Commands
test: ## Run all tests
	@$(ECHO) "$(GREEN)Running all tests...$(NC)"
	@$(MAKE) test-api
	@$(MAKE) test-ai
	@$(MAKE) test-frontend

test-api: ## Run API server tests
	@$(ECHO) "$(GREEN)Running API server tests...$(NC)"
ifeq ($(OS),Windows_NT)
	@cd backend\api_server && go test ./...
else
	@cd backend/api_server && go test ./...
endif

test-ai: ## Run AI server tests
	@$(ECHO) "$(GREEN)Running AI server tests...$(NC)"
ifeq ($(OS),Windows_NT)
	@cd backend\ai_server && poetry run pytest
else
	@cd backend/ai_server && poetry run pytest
endif

test-frontend: ## Run frontend tests
	@$(ECHO) "$(GREEN)Running frontend tests...$(NC)"
ifeq ($(OS),Windows_NT)
	@cd frontend\project && npm run test
else
	@cd frontend/project && npm run test
endif

# Clean Commands
clean: ## Clean up containers and volumes
	@$(ECHO) "$(YELLOW)Cleaning up containers and volumes...$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@$(ECHO) "$(GREEN)Cleanup completed!$(NC)"

clean-images: ## Remove all project Docker images
	@$(ECHO) "$(RED)Removing all project Docker images...$(NC)"
	@$(DOCKER_COMPOSE) down -v --rmi all
	@$(ECHO) "$(GREEN)Images removed!$(NC)"

clean-all: ## Full cleanup (containers, volumes, images, cache)
	@$(ECHO) "$(RED)Performing full cleanup...$(NC)"
	@$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans
	@docker system prune -af --volumes
	@$(ECHO) "$(GREEN)Full cleanup completed!$(NC)"

prune: clean-all ## Alias for clean-all

# Database Commands
db-reset: ## Reset Redis database
	@$(ECHO) "$(YELLOW)Resetting Redis database...$(NC)"
	@$(DOCKER_COMPOSE) exec redis redis-cli FLUSHALL
	@$(ECHO) "$(GREEN)Redis database reset!$(NC)"

db-backup: ## Backup Redis database
	@$(ECHO) "$(GREEN)Creating Redis backup...$(NC)"
ifeq ($(OS),Windows_NT)
	@if not exist backups mkdir backups
else
	@mkdir -p backups
endif
	@$(DOCKER_COMPOSE) exec redis redis-cli --rdb /data/dump.rdb
	@$(ECHO) "$(GREEN)Redis backup completed!$(NC)"

# Health and Monitoring
health: ## Check health of all services
	@$(ECHO) "$(GREEN)Checking service health...$(NC)"
	@$(ECHO) "=========================="
ifeq ($(OS),Windows_NT)
	@curl -s http://localhost:2030/api/v1/ping >$(NULL) 2>&1 && $(ECHO) "$(GREEN)API Server: UP$(NC)" || $(ECHO) "$(RED)API Server: DOWN$(NC)"
	@curl -s http://localhost:9999/api/v1/health >$(NULL) 2>&1 && $(ECHO) "$(GREEN)AI Server: UP$(NC)" || $(ECHO) "$(RED)AI Server: DOWN$(NC)"
	@curl -s http://localhost:5173 >$(NULL) 2>&1 && $(ECHO) "$(GREEN)Frontend: UP$(NC)" || $(ECHO) "$(RED)Frontend: DOWN$(NC)"
	@curl -s http://localhost:9090/-/healthy >$(NULL) 2>&1 && $(ECHO) "$(GREEN)Prometheus: UP$(NC)" || $(ECHO) "$(RED)Prometheus: DOWN$(NC)"
else
	@curl -s http://localhost:2030/api/v1/ping >/dev/null 2>&1 && echo "$(GREEN)API Server: UP$(NC)" || echo "$(RED)API Server: DOWN$(NC)"
	@curl -s http://localhost:9999/api/v1/health >/dev/null 2>&1 && echo "$(GREEN)AI Server: UP$(NC)" || echo "$(RED)AI Server: DOWN$(NC)"
	@curl -s http://localhost:5173 >/dev/null 2>&1 && echo "$(GREEN)Frontend: UP$(NC)" || echo "$(RED)Frontend: DOWN$(NC)"
	@curl -s http://localhost:9090/-/healthy >/dev/null 2>&1 && echo "$(GREEN)Prometheus: UP$(NC)" || echo "$(RED)Prometheus: DOWN$(NC)"
endif
	@$(ECHO) ""

ping: ## Ping all services
	@$(ECHO) "$(GREEN)Pinging all services...$(NC)"
	@$(ECHO) "======================="
	@curl -s http://localhost:2030/api/v1/ping || $(ECHO) "API Server not responding"
	@curl -s http://localhost:9999/api/v1/health || $(ECHO) "AI Server not responding"
	@$(ECHO) ""

# Production Commands
prod: ## Deploy to production
	@$(ECHO) "$(GREEN)Deploying to production...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.yml up -d --build
	@$(ECHO) "$(GREEN)Production deployment completed!$(NC)"

prod-build: ## Build for production
	@$(ECHO) "$(GREEN)Building for production...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.yml build
	@$(ECHO) "$(GREEN)Production build completed!$(NC)"

# Backup Commands
backup: ## Create backup of all data
	@$(ECHO) "$(GREEN)Creating backup...$(NC)"
ifeq ($(OS),Windows_NT)
	@if not exist backups mkdir backups
	@powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'" > temp_date.txt
	@set /p TIMESTAMP=<temp_date.txt
	@del temp_date.txt
	@docker run --rm -v vrecommendation_redis_data:/data -v %CD%\backups:/backup alpine tar czf /backup/redis_backup_%TIMESTAMP%.tar.gz -C /data .
else
	@mkdir -p backups
	@docker run --rm -v vrecommendation_redis_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/redis_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
endif
	@$(ECHO) "$(GREEN)Backup completed!$(NC)"

# Update Commands
update: ## Update all services
	@$(ECHO) "$(GREEN)Updating all services...$(NC)"
	@$(DOCKER_COMPOSE) pull
	@$(DOCKER_COMPOSE) up -d
	@$(ECHO) "$(GREEN)Update completed!$(NC)"

# Quick Commands (aliases)
quick-start: build start ## Quick start (build and start)
quick-stop: stop clean ## Quick stop (stop and clean)
quick-restart: stop build start ## Quick restart (stop, build, start)

# Docker Commands
docker-clean: ## Clean Docker system
	@$(ECHO) "$(YELLOW)Cleaning Docker system...$(NC)"
	@docker system prune -f
	@$(ECHO) "$(GREEN)Docker system cleaned!$(NC)"

docker-reset: ## Reset Docker completely
	@$(ECHO) "$(RED)Resetting Docker completely...$(NC)"
	@docker system prune -af --volumes
	@$(ECHO) "$(GREEN)Docker reset completed!$(NC)"

# Information Commands
info: ## Show system information
	@$(ECHO) "$(BLUE)System Information$(NC)"
	@$(ECHO) "=================="
	@$(ECHO) "OS: $(DETECTED_OS)"
	@$(ECHO) "Shell: $(SHELL)"
	@docker --version
	@$(DOCKER_COMPOSE) --version
	@$(ECHO) ""

version: info ## Alias for info

# Utility Commands
shell-api: ## Open shell in API server container
	@$(DOCKER_COMPOSE) exec api_server sh

shell-ai: ## Open shell in AI server container
	@$(DOCKER_COMPOSE) exec ai_server bash

shell-redis: ## Open Redis CLI
	@$(DOCKER_COMPOSE) exec redis redis-cli

# Special Windows-specific commands
ifeq ($(OS),Windows_NT)
windows-setup: ## Windows-specific setup
	@$(ECHO) "$(GREEN)Setting up for Windows...$(NC)"
	@$(ECHO) "Checking Docker Desktop..."
	@docker version >$(NULL) 2>&1 || ($(ECHO) "$(RED)Docker Desktop is not running!$(NC)" && exit 1)
	@$(ECHO) "$(GREEN)Docker Desktop is running$(NC)"
	@$(ECHO) "$(GREEN)Windows setup completed!$(NC)"
endif

# Docker Compose version fix
fix-compose: ## Fix docker-compose version warning
	@$(ECHO) "$(YELLOW)Fixing docker-compose.yml version warning...$(NC)"
ifeq ($(OS),Windows_NT)
	@powershell -Command "(Get-Content docker-compose.yml) | Where-Object { $_ -notmatch '^version:' } | Set-Content docker-compose.yml"
else
	@sed -i '/^version:/d' docker-compose.yml
endif
	@$(ECHO) "$(GREEN)Version line removed from docker-compose.yml$(NC)"
