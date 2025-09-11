# Makefile for managing the VRecommendation project

# Variables
COMPOSE_FILE = docker-compose.yml
IMAGE_NAME = vrecommendation_ai:latest
LOGS_DIR = logs

# Default target
.PHONY: all
all: build up

# Build the Docker image for vrecommendation_ai
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
	docker-compose -f $(COMPOSE_FILE) up -d vrecommendation_ai

# Prepare necessary directories and files
.PHONY: prepare
prepare:
	@echo "Preparing logs directory..."
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
	docker-compose -f $(COMPOSE_FILE) logs vrecommendation_ai

# View logs for all services
.PHONY: logs-all
logs-all:
	@echo "Viewing logs for all services..."
	docker-compose -f $(COMPOSE_FILE) logs