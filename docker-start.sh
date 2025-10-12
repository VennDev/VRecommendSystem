#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== VRecommendation System - Docker Setup ===${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created successfully${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env file with your configuration before proceeding${NC}"
        echo ""
        exit 1
    else
        echo -e "${RED}✗ .env.example not found. Cannot create .env file${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Configuration file found${NC}"
echo ""

# Check if frontend .env exists
if [ ! -f frontend/project/.env ]; then
    echo -e "${YELLOW}⚠️  Frontend .env not found. Copying from .env.example...${NC}"
    if [ -f frontend/project/.env.example ]; then
        cp frontend/project/.env.example frontend/project/.env
        echo -e "${GREEN}✓ Frontend .env created${NC}"
    fi
fi

# Parse command line arguments
COMMAND=${1:-up}

case $COMMAND in
    up|start)
        echo -e "${GREEN}Starting all services...${NC}"
        docker-compose up -d
        echo ""
        echo -e "${GREEN}=== Services Status ===${NC}"
        docker-compose ps
        echo ""
        echo -e "${GREEN}=== Access URLs ===${NC}"
        echo -e "  🌐 Frontend:    ${YELLOW}http://localhost:5173${NC}"
        echo -e "  🔧 API Server:  ${YELLOW}http://localhost:2030${NC}"
        echo -e "  🤖 AI Server:   ${YELLOW}http://localhost:9999${NC}"
        echo -e "  📊 Prometheus:  ${YELLOW}http://localhost:9090${NC}"
        echo ""
        echo -e "${GREEN}✓ All services started successfully!${NC}"
        ;;

    build)
        echo -e "${GREEN}Building all Docker images...${NC}"
        docker-compose build
        echo -e "${GREEN}✓ Build completed${NC}"
        ;;

    down|stop)
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker-compose down
        echo -e "${GREEN}✓ All services stopped${NC}"
        ;;

    restart)
        echo -e "${YELLOW}Restarting all services...${NC}"
        docker-compose restart
        echo -e "${GREEN}✓ All services restarted${NC}"
        ;;

    logs)
        SERVICE=${2:-}
        if [ -z "$SERVICE" ]; then
            echo -e "${GREEN}Showing logs for all services...${NC}"
            docker-compose logs -f
        else
            echo -e "${GREEN}Showing logs for ${SERVICE}...${NC}"
            docker-compose logs -f $SERVICE
        fi
        ;;

    clean)
        echo -e "${YELLOW}⚠️  This will remove all containers, volumes, and images${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Cleaning up...${NC}"
            docker-compose down -v --rmi all
            echo -e "${GREEN}✓ Cleanup completed${NC}"
        else
            echo -e "${YELLOW}Cleanup cancelled${NC}"
        fi
        ;;

    status)
        echo -e "${GREEN}=== Services Status ===${NC}"
        docker-compose ps
        ;;

    help|*)
        echo -e "${GREEN}VRecommendation System - Docker Management Script${NC}"
        echo ""
        echo "Usage: ./docker-start.sh [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  up, start       Start all services (default)"
        echo "  build           Build all Docker images"
        echo "  down, stop      Stop all services"
        echo "  restart         Restart all services"
        echo "  logs [service]  Show logs (optionally for specific service)"
        echo "  status          Show status of all services"
        echo "  clean           Remove all containers, volumes, and images"
        echo "  help            Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./docker-start.sh up          # Start all services"
        echo "  ./docker-start.sh build       # Build images"
        echo "  ./docker-start.sh logs        # Show all logs"
        echo "  ./docker-start.sh logs api_server  # Show API server logs"
        echo "  ./docker-start.sh clean       # Clean everything"
        ;;
esac
