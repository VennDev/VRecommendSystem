# Makefile for managing the VRecommendation project

# Variables
COMPOSE_FILE = docker-compose.yml
IMAGE_NAME = vrecommendation_ai:latest
LOGS_DIR = logs
ENV_FILE = .env

# Default target
.PHONY: all
all: prepare build up

# Check if required files exist (Windows compatible)
.PHONY: check
check:
	@echo "Checking required files..."
	@if not exist $(COMPOSE_FILE) (echo Error: $(COMPOSE_FILE) not found && exit 1)
	@if not exist Dockerfile (echo Error: Dockerfile not found && exit 1)
	@if not exist $(ENV_FILE) echo Warning: $(ENV_FILE) not found, using default values
	@echo "All required files found"

# Prepare necessary directories and files
.PHONY: prepare
prepare:
	@echo "Preparing environment..."
	@if not exist $(LOGS_DIR) mkdir $(LOGS_DIR)
	@if not exist src mkdir src
	@if not exist config mkdir config
	@if not exist tasks mkdir tasks
	@if not exist models mkdir models
	@echo "Environment prepared"

# Build the Docker image for vrecommendation_ai
.PHONY: build
build: prepare
	@echo "Building Docker image $(IMAGE_NAME)..."
	docker build -t $(IMAGE_NAME) .
	@echo "Docker image built successfully"

# Start all services in the background
.PHONY: up
up: prepare
	@echo "Starting all services with docker-compose..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "All services started"

# Start only the main application service
.PHONY: start
start: prepare
	@echo "Starting VRecommendation AI service..."
	docker-compose -f $(COMPOSE_FILE) up -d vrecommendation_ai
	@echo "VRecommendation AI service started"

# Start services with logs visible (foreground)
.PHONY: up-logs
up-logs: prepare
	@echo "Starting all services with logs..."
	docker-compose -f $(COMPOSE_FILE) up

# Stop all services
.PHONY: stop
stop:
	@echo "Stopping all services..."
	docker-compose -f $(COMPOSE_FILE) stop
	@echo "All services stopped"

# Stop and remove all containers
.PHONY: down
down:
	@echo "Stopping and removing services..."
	docker-compose -f $(COMPOSE_FILE) down
	@echo "Services stopped and removed"

# Remove containers, networks, and volumes (data will be lost)
.PHONY: clean
clean:
	@echo "Removing containers, networks, and volumes..."
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	@echo "Removing unused Docker images..."
	docker image prune -f
	@echo "Cleanup completed"

# Full cleanup including built images
.PHONY: clean-all
clean-all: clean
	@echo "Removing built images..."
	-docker rmi $(IMAGE_NAME) 2>nul || echo "Image already removed"
	docker system prune -f
	@echo "Full cleanup completed"

# Restart all services
.PHONY: restart
restart: down up

# Restart only the main application
.PHONY: restart-app
restart-app:
	@echo "Restarting VRecommendation AI service..."
	docker-compose -f $(COMPOSE_FILE) restart vrecommendation_ai
	@echo "VRecommendation AI service restarted"

# View logs for vrecommendation service
.PHONY: logs
logs:
	@echo "Viewing logs for vrecommendation_ai..."
	docker-compose -f $(COMPOSE_FILE) logs -f vrecommendation_ai

# View logs for prometheus service
.PHONY: logs-prometheus
logs-prometheus:
	@echo "Viewing logs for prometheus..."
	docker-compose -f $(COMPOSE_FILE) logs -f prometheus_vrecommendation_ai

# View logs for all services
.PHONY: logs-all
logs-all:
	@echo "Viewing logs for all services..."
	docker-compose -f $(COMPOSE_FILE) logs -f

# Show status of all services
.PHONY: status
status:
	@echo "Service status:"
	docker-compose -f $(COMPOSE_FILE) ps

# Execute shell in the main container
.PHONY: shell
shell:
	@echo "Opening shell in vrecommendation_ai container..."
	docker-compose -f $(COMPOSE_FILE) exec vrecommendation_ai /bin/bash

# Execute shell with sh (fallback)
.PHONY: sh
sh:
	@echo "Opening sh shell in vrecommendation_ai container..."
	docker-compose -f $(COMPOSE_FILE) exec vrecommendation_ai /bin/sh

# Pull latest images
.PHONY: pull
pull:
	@echo "Pulling latest images..."
	docker-compose -f $(COMPOSE_FILE) pull
	@echo "Images updated"

# Rebuild and restart (useful for development)
.PHONY: rebuild
rebuild: clean-all build up
	@echo "Rebuild completed"

# Health check
.PHONY: health
health:
	@echo "Checking service health..."
	@curl -f http://localhost:9999/health >nul 2>&1 && echo "Main service is healthy" || echo "Main service is not responding"
	@curl -f http://localhost:9090/-/healthy >nul 2>&1 && echo "Prometheus is healthy" || echo "Prometheus is not responding"

# Show help
.PHONY: help
help:
	@echo "VRecommendation AI Project - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  prepare     - Create necessary directories"
	@echo "  check       - Check if required files exist"
	@echo "  build       - Build Docker images"
	@echo ""
	@echo "Service Management:"
	@echo "  up          - Start all services in background"
	@echo "  up-logs     - Start all services with logs visible"
	@echo "  start       - Start only the main application"
	@echo "  stop        - Stop all services"
	@echo "  down        - Stop and remove containers"
	@echo "  restart     - Restart all services"
	@echo "  restart-app - Restart only the main application"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs        - View logs for main application"
	@echo "  logs-prometheus - View logs for Prometheus"
	@echo "  logs-all    - View logs for all services"
	@echo "  status      - Show status of all services"
	@echo "  health      - Check service health"
	@echo ""
	@echo "Development:"
	@echo "  shell       - Open bash shell in main container"
	@echo "  sh          - Open sh shell in main container"
	@echo "  rebuild     - Full rebuild and restart"
	@echo ""
	@echo "Maintenance:"
	@echo "  pull        - Pull latest images"
	@echo "  clean       - Remove containers and volumes"
	@echo "  clean-all   - Full cleanup including images"
	@echo ""
	@echo "Usage Examples:"
	@echo "  make build up    - Build and start services"
	@echo "  make logs        - View application logs"
	@echo "  make shell       - Access container shell"
	@echo "  make health      - Check if services are running"