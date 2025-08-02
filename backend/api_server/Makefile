# Makefile for managing the VRecommendation project

# Variables
COMPOSE_FILE = docker-compose.yml
IMAGE_NAME = vrecommendation:latest
LOGS_DIR = logs
#INIT_SQL = init.sql

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
	@echo "Starting infrastructure services first..."
	docker-compose -f $(COMPOSE_FILE) up -d zookeeper
	@echo "Waiting for Zookeeper to be ready..."
	@sleep 10
	docker-compose -f $(COMPOSE_FILE) up -d kafka
	@echo "Waiting for Kafka to be ready..."
	@sleep 20
#	docker-compose -f $(COMPOSE_FILE) up -d mysql redis
#	@echo "Waiting for databases to be ready..."
#	@sleep 10
	@echo "Starting application..."
	docker-compose -f $(COMPOSE_FILE) up -d vrecommendation kafka-ui

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

# View logs for Kafka service
.PHONY: logs-kafka
logs-kafka:
	@echo "Viewing logs for Kafka..."
	docker-compose -f $(COMPOSE_FILE) logs kafka

# View logs for Zookeeper service
.PHONY: logs-zk
logs-zk:
	@echo "Viewing logs for Zookeeper..."
	docker-compose -f $(COMPOSE_FILE) logs zookeeper

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

# Access MySQL database
#.PHONY: mysql
#mysql:
#	@echo "Accessing MySQL database..."
#	docker-compose -f $(COMPOSE_FILE) exec mysql mysql -u user -pS3cur3P@ssw0rd123

# Access Kafka UI
.PHONY: kafka-ui
kafka-ui:
	@echo "Opening Kafka UI in browser..."
	@start http://localhost:8080 || open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Please open http://localhost:8080 in your browser"

# Check Kafka topics
.PHONY: kafka-topics
kafka-topics:
	@echo "Listing Kafka topics..."
	docker-compose -f $(COMPOSE_FILE) exec kafka kafka-topics --list --bootstrap-server kafka:9092

# Test Kafka connection
.PHONY: kafka-test
kafka-test:
	@echo "Testing Kafka connection..."
	docker-compose -f $(COMPOSE_FILE) exec kafka kafka-broker-api-versions --bootstrap-server kafka:9092

# Create a test topic
.PHONY: kafka-create-topic
kafka-create-topic:
	@echo "Creating test topic..."
	docker-compose -f $(COMPOSE_FILE) exec kafka kafka-topics --create --topic test-topic --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1

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
	@echo "  make logs-kafka    - View logs for Kafka service"
	@echo "  make logs-zk       - View logs for Zookeeper service"
	@echo "  make logs-all      - View logs for all services"
	@echo "  make ps            - Check status of all containers"
	@echo "  make health        - Check health status of all containers"
	@echo "  make mysql         - Access MySQL database"
	@echo "  make kafka-ui      - Open Kafka UI in browser"
	@echo "  make kafka-topics  - List Kafka topics"
	@echo "  make kafka-test    - Test Kafka connection"
	@echo "  make kafka-create-topic - Create a test topic"
	@echo "  make debug-network - Debug network connectivity"
	@echo "  make prune         - Remove dangling Docker images"
	@echo "  make help          - Show this help message"