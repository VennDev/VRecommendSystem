# Makefile for managing the VRecommendation project

# Variables
COMPOSE_FILE = docker-compose.yml
IMAGE_NAME = vrecommendation:latest
LOGS_DIR = logs

# Default target
.PHONY: all
all: build up

# Build the Docker image for vrecommendation
.PHONY: build
build:
	@echo "Building Docker image $(IMAGE_NAME)..."
	docker build -t $(IMAGE_NAME) .

# Start all services in the background
.PHONY: up
up: prepare
	@echo "Starting services with docker-compose..."
	docker-compose -f $(COMPOSE_FILE) up -d

# Start services with proper order (infrastructure first)
.PHONY: start
start: prepare
	@echo "Starting application..."
	docker-compose -f $(COMPOSE_FILE) up -d vrecommendation

# Prepare necessary directories and files
.PHONY: prepare
prepare:
	@echo "Preparing logs directory and init.sql..."
	-@mkdir $(LOGS_DIR) 2> nul || echo "Logs directory already exists"
#	-@type nul > $(INIT_SQL) 2> nul || echo "init.sql already exists"

# Stop and remove all containers
.PHONY: down
down:
	@echo "Stopping and removing services..."
	docker-compose -f $(COMPOSE_FILE) down

# Remove containers and volumes (data will be lost)
.PHONY: clean
clean:
	@echo "Removing containers and volumes..."
	docker-compose -f $(COMPOSE_FILE) down -v

# Restart all services
.PHONY: restart
restart: down start

# View logs for vrecommendation service
.PHONY: logs
logs:
	@echo "Viewing logs for vrecommendation..."
	docker-compose -f $(COMPOSE_FILE) logs vrecommendation

# View logs for all services
.PHONY: logs-all
logs-all:
	@echo "Viewing logs for all services..."
	docker-compose -f $(COMPOSE_FILE) logs

# Check status of all containers
.PHONY: ps
ps:
	@echo "Checking container status..."
	docker-compose -f $(COMPOSE_FILE) ps

# Check health of all containers
.PHONY: health
health:
	@echo "Checking health status..."
	docker-compose -f $(COMPOSE_FILE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"

# Debug network connectivity
.PHONY: debug-network
debug-network:
	@echo "Testing network connectivity..."
	docker-compose -f $(COMPOSE_FILE) exec vrecommendation nslookup kafka || echo "DNS resolution failed"
	docker-compose -f $(COMPOSE_FILE) exec vrecommendation ping -c 3 kafka || echo "Ping failed"

# Remove dangling images
.PHONY: prune
prune:
	@echo "Removing dangling Docker images..."
	docker image prune -f

# Full rebuild (clean build and start)
.PHONY: rebuild
rebuild: clean build start

# Help command to display available targets
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make build         - Build the Docker image for vrecommendation"
	@echo "  make up            - Start all services in the background"
	@echo "  make start         - Start services with proper startup order"
	@echo "  make down          - Stop and remove all containers"
	@echo "  make clean         - Remove containers and volumes"
	@echo "  make restart       - Restart all services"
	@echo "  make rebuild       - Full rebuild (clean, build, start)"
	@echo "  make logs          - View logs for vrecommendation service"
	@echo "  make logs-all      - View logs for all services"
	@echo "  make ps            - Check status of all containers"
	@echo "  make health        - Check health status of all containers"
	@echo "  make debug-network - Debug network connectivity"
	@echo "  make prune         - Remove dangling Docker images"
	@echo "  make help          - Show this help message"
