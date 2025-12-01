#!/bin/bash

# VRecommendation System - Local Startup Script (No Docker)
# For Linux/Unix systems

set -e

# Colors
GREEN='\033[0;92m'
RED='\033[0;91m'
YELLOW='\033[0;93m'
BLUE='\033[0;94m'
CYAN='\033[0;96m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# PID files location
PID_DIR="$SCRIPT_DIR/.pids"
mkdir -p "$PID_DIR"

echo ""
echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}   VRecommendation System - Local Startup (No Docker)   ${NC}"
echo -e "${BLUE}========================================================${NC}"
echo ""

# ========================================
# Setup Environment Files
# ========================================
setup_env_files() {
    echo -e "${YELLOW}[INFO]${NC} Checking environment files..."

    # Check/create root .env
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}[INFO]${NC} Creating .env from example-env..."
        if [ -f "example-env" ]; then
            cp "example-env" ".env"
            # Update for local development
            sed -i.bak 's/REDIS_HOST=redis/REDIS_HOST=localhost/g' ".env" 2>/dev/null || \
            sed -i '' 's/REDIS_HOST=redis/REDIS_HOST=localhost/g' ".env"
            sed -i.bak 's/MYSQL_HOST=mysql/MYSQL_HOST=localhost/g' ".env" 2>/dev/null || \
            sed -i '' 's/MYSQL_HOST=mysql/MYSQL_HOST=localhost/g' ".env"
            sed -i.bak 's/MONGODB_HOST=mongodb/MONGODB_HOST=localhost/g' ".env" 2>/dev/null || \
            sed -i '' 's/MONGODB_HOST=mongodb/MONGODB_HOST=localhost/g' ".env"
            sed -i.bak 's/KAFKA_BOOTSTRAP_SERVERS=kafka:9093/KAFKA_BOOTSTRAP_SERVERS=localhost:9092/g' ".env" 2>/dev/null || \
            sed -i '' 's/KAFKA_BOOTSTRAP_SERVERS=kafka:9093/KAFKA_BOOTSTRAP_SERVERS=localhost:9092/g' ".env"
            rm -f ".env.bak" 2>/dev/null
            echo -e "${GREEN}[OK]${NC} Root .env created (local mode)"
        else
            create_default_env
        fi
    else
        echo -e "${GREEN}[OK]${NC} Root .env exists"
    fi

    # Check/create API server .env
    if [ ! -f "backend/api_server/.env" ]; then
        echo -e "${YELLOW}[INFO]${NC} Creating API server .env..."
        if [ -f "backend/api_server/example-env" ]; then
            cp "backend/api_server/example-env" "backend/api_server/.env"
            # Update AI_SERVER_URL for local
            sed -i.bak 's/AI_SERVER_URL=http:\/\/ai_server:/AI_SERVER_URL=http:\/\/localhost:/g' "backend/api_server/.env" 2>/dev/null || \
            sed -i '' 's/AI_SERVER_URL=http:\/\/ai_server:/AI_SERVER_URL=http:\/\/localhost:/g' "backend/api_server/.env"
            rm -f "backend/api_server/.env.bak" 2>/dev/null
            echo -e "${GREEN}[OK]${NC} API server .env created (local mode)"
        else
            create_api_env_local
        fi
    else
        echo -e "${GREEN}[OK]${NC} API server .env exists"
    fi

    # Check/create AI server .env
    if [ ! -f "backend/ai_server/.env" ]; then
        echo -e "${YELLOW}[INFO]${NC} Creating AI server .env..."
        if [ -f "backend/ai_server/example-env" ]; then
            cp "backend/ai_server/example-env" "backend/ai_server/.env"
            echo -e "${GREEN}[OK]${NC} AI server .env created"
        else
            create_ai_env_local
        fi
    else
        echo -e "${GREEN}[OK]${NC} AI server .env exists"
    fi

    # Check/create frontend .env
    if [ ! -f "frontend/project/.env" ]; then
        echo -e "${YELLOW}[INFO]${NC} Creating frontend .env..."
        if [ -f "frontend/project/example-env" ]; then
            cp "frontend/project/example-env" "frontend/project/.env"
            echo -e "${GREEN}[OK]${NC} Frontend .env created"
        else
            create_frontend_env_local
        fi
    else
        echo -e "${GREEN}[OK]${NC} Frontend .env exists"
    fi

    echo ""
}

create_default_env() {
    echo -e "${YELLOW}[INFO]${NC} Creating default .env file for local development..."
    cat > ".env" << 'EOF'
# VRecommendation Environment Configuration - Local Development
# Auto-generated - Please update with your settings

# Environment
STATUS_DEV=dev

# Host Configuration
HOST_IP=localhost

# API Server Configuration
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=2030
API_SERVER_READ_TIMEOUT=60

# AI Server Configuration
AI_SERVER_HOST=0.0.0.0
AI_SERVER_PORT=9999

# Frontend Configuration
FRONTEND_PORT=5173
FRONTEND_URL=http://localhost:5173

# Redis Configuration - For local, use localhost
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Database Configuration (MySQL) - For local development
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=pokiwar0981
MYSQL_DATABASE=shop

# Database Configuration (MongoDB) - For local development
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=root
MONGODB_PASSWORD=password
MONGODB_AUTH_SOURCE=admin

# Kafka Configuration - For local development
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=vrecom_ai_server_group

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
SESSION_SECRET=your-super-secret-session-key-change-in-production

# API URLs for frontend (local development)
VITE_API_SERVER_URL=http://localhost:2030
VITE_AI_SERVER_URL=http://localhost:9999

# Google OAuth - Get from Google Cloud Console
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_CALLBACK_URL=http://localhost:2030/api/v1/auth/google/callback
EOF
    echo -e "${GREEN}[OK]${NC} Default .env created for local development"
}

create_api_env_local() {
    echo -e "${YELLOW}[INFO]${NC} Creating API server .env for local development..."
    cat > "backend/api_server/.env" << 'EOF'
# Environment can be set to 'dev', 'test' or 'prod'
STATUS_DEV=dev
HOST_ADDRESS=0.0.0.0
HOST_PORT=2030
HOST_READ_TIMEOUT=60

# Google OAuth2 credentials
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_CALLBACK_URL=http://localhost:2030/api/v1/auth/google/callback
SESSION_SECRET=your_strong_session_secret

# AI Server Configuration - Local URL
AI_SERVER_URL=http://localhost:9999

# Frontend URL for OAuth redirect
FRONTEND_URL=http://localhost:5173
HOST_IP=localhost
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Redis Configuration - Local
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
EOF
    echo -e "${GREEN}[OK]${NC} API server .env created"
}

create_ai_env_local() {
    echo -e "${YELLOW}[INFO]${NC} Creating AI server .env for local development..."
    cat > "backend/ai_server/.env" << 'EOF'
# Port server
HOST=0.0.0.0
PORT=9999

# Session Secret
SESSION_SECRET=your_strong_session_secret
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Database Configuration (MySQL) - Local
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=pokiwar0981
MYSQL_DATABASE=shop

# Database Configuration (MongoDB) - Local
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=root
MONGODB_PASSWORD=password

# Kafka Configuration - Local
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=vrecom_ai_server_group
EOF
    echo -e "${GREEN}[OK]${NC} AI server .env created"
}

create_frontend_env_local() {
    echo -e "${YELLOW}[INFO]${NC} Creating frontend .env for local development..."
    cat > "frontend/project/.env" << 'EOF'
# API Configuration - Local Development
VITE_AI_SERVER_URL=http://localhost:9999
VITE_API_SERVER_URL=http://localhost:2030
EOF
    echo -e "${GREEN}[OK]${NC} Frontend .env created"
}

# ========================================
# Check Dependencies
# ========================================
check_deps() {
    echo -e "${BLUE}[INFO]${NC} Checking dependencies..."
    echo ""

    local ALL_OK=1

    # Check Go
    echo "Checking Go..."
    if command -v go &> /dev/null; then
        GO_VERSION=$(go version | awk '{print $3}')
        echo -e "  ${GREEN}[OK]${NC} $GO_VERSION"
    else
        echo -e "  ${RED}[MISSING]${NC} Go is not installed"
        echo "  Download from: https://golang.org/dl/"
        ALL_OK=0
    fi

    # Check Python
    echo "Checking Python..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo -e "  ${GREEN}[OK]${NC} $PYTHON_VERSION"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        echo -e "  ${GREEN}[OK]${NC} $PYTHON_VERSION"
    else
        echo -e "  ${RED}[MISSING]${NC} Python is not installed"
        echo "  Download from: https://python.org/downloads/"
        ALL_OK=0
    fi

    # Check Poetry
    echo "Checking Poetry..."
    if command -v poetry &> /dev/null; then
        POETRY_VERSION=$(poetry --version 2>&1)
        echo -e "  ${GREEN}[OK]${NC} $POETRY_VERSION"
    else
        echo -e "  ${RED}[MISSING]${NC} Poetry is not installed"
        echo "  Install with: pip install poetry"
        echo "  Or visit: https://python-poetry.org/docs/"
        ALL_OK=0
    fi

    # Check Node.js
    echo "Checking Node.js..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "  ${GREEN}[OK]${NC} Node.js $NODE_VERSION"
    else
        echo -e "  ${RED}[MISSING]${NC} Node.js is not installed"
        echo "  Download from: https://nodejs.org/"
        ALL_OK=0
    fi

    # Check npm
    echo "Checking npm..."
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo -e "  ${GREEN}[OK]${NC} npm $NPM_VERSION"
    else
        echo -e "  ${RED}[MISSING]${NC} npm is not installed"
        ALL_OK=0
    fi

    echo ""
    if [ "$ALL_OK" -eq 1 ]; then
        echo -e "${GREEN}[SUCCESS]${NC} All dependencies are installed!"
    else
        echo -e "${RED}[WARNING]${NC} Some dependencies are missing. Please install them before running the system."
    fi
    echo ""

    return $((1 - ALL_OK))
}

# Silent dependency check
check_deps_silent() {
    command -v go &> /dev/null && \
    command -v poetry &> /dev/null && \
    command -v node &> /dev/null
}

# ========================================
# Install All Dependencies
# ========================================
install_all() {
    echo -e "${BLUE}[INFO]${NC} Installing all dependencies..."
    echo ""

    # Install AI Server dependencies
    echo -e "${CYAN}[1/3]${NC} Installing AI Server dependencies..."
    if [ -f "backend/ai_server/pyproject.toml" ]; then
        cd backend/ai_server
        poetry install
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK]${NC} AI Server dependencies installed"
        else
            echo -e "${RED}[ERROR]${NC} Failed to install AI Server dependencies"
        fi
        cd ../..
    else
        echo -e "${RED}[ERROR]${NC} pyproject.toml not found"
    fi

    # Install API Server dependencies
    echo ""
    echo -e "${CYAN}[2/3]${NC} Installing API Server dependencies..."
    if [ -f "backend/api_server/go.mod" ]; then
        cd backend/api_server
        go mod download
        go mod tidy
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK]${NC} API Server dependencies installed"
        else
            echo -e "${RED}[ERROR]${NC} Failed to install API Server dependencies"
        fi
        cd ../..
    else
        echo -e "${RED}[ERROR]${NC} go.mod not found"
    fi

    # Install Frontend dependencies
    echo ""
    echo -e "${CYAN}[3/3]${NC} Installing Frontend dependencies..."
    if [ -f "frontend/project/package.json" ]; then
        cd frontend/project
        npm install
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK]${NC} Frontend dependencies installed"
        else
            echo -e "${RED}[ERROR]${NC} Failed to install Frontend dependencies"
        fi
        cd ../..
    else
        echo -e "${RED}[ERROR]${NC} package.json not found"
    fi

    echo ""
    echo -e "${GREEN}[SUCCESS]${NC} Dependency installation completed!"
    echo ""
}

# ========================================
# Start Services
# ========================================
start_ai() {
    echo -e "${BLUE}[INFO]${NC} Starting AI Server..."
    cd "$SCRIPT_DIR/backend/ai_server"

    # Check if already running
    if [ -f "$PID_DIR/ai_server.pid" ]; then
        PID=$(cat "$PID_DIR/ai_server.pid")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}[WARN]${NC} AI Server is already running (PID: $PID)"
            return
        fi
    fi

    poetry run server > "$SCRIPT_DIR/logs/ai_server.log" 2>&1 &
    echo $! > "$PID_DIR/ai_server.pid"
    echo -e "${GREEN}[OK]${NC} AI Server started (PID: $!)"
    echo "  URL: http://localhost:9999"
    echo "  Docs: http://localhost:9999/docs"
    echo "  Logs: $SCRIPT_DIR/logs/ai_server.log"
    cd "$SCRIPT_DIR"
}

start_api() {
    echo -e "${BLUE}[INFO]${NC} Starting API Server..."
    cd "$SCRIPT_DIR/backend/api_server"

    # Check if already running
    if [ -f "$PID_DIR/api_server.pid" ]; then
        PID=$(cat "$PID_DIR/api_server.pid")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}[WARN]${NC} API Server is already running (PID: $PID)"
            return
        fi
    fi

    go run main.go > "$SCRIPT_DIR/logs/api_server.log" 2>&1 &
    echo $! > "$PID_DIR/api_server.pid"
    echo -e "${GREEN}[OK]${NC} API Server started (PID: $!)"
    echo "  URL: http://localhost:2030"
    echo "  Logs: $SCRIPT_DIR/logs/api_server.log"
    cd "$SCRIPT_DIR"
}

start_frontend() {
    echo -e "${BLUE}[INFO]${NC} Starting Frontend..."
    cd "$SCRIPT_DIR/frontend/project"

    # Check if already running
    if [ -f "$PID_DIR/frontend.pid" ]; then
        PID=$(cat "$PID_DIR/frontend.pid")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}[WARN]${NC} Frontend is already running (PID: $PID)"
            return
        fi
    fi

    npm run dev > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"
    echo -e "${GREEN}[OK]${NC} Frontend started (PID: $!)"
    echo "  URL: http://localhost:5173"
    echo "  Logs: $SCRIPT_DIR/logs/frontend.log"
    cd "$SCRIPT_DIR"
}

start_all() {
    echo -e "${BLUE}[INFO]${NC} Starting all services locally (without Docker)..."
    echo ""

    # Check dependencies
    if ! check_deps_silent; then
        echo -e "${RED}[ERROR]${NC} Missing dependencies. Run './start-local.sh check' to see what's missing."
        exit 1
    fi

    # Create logs directory
    mkdir -p "$SCRIPT_DIR/logs"

    echo -e "${YELLOW}[NOTE]${NC} Services will run in background. Use './start-local.sh logs' to view logs."
    echo ""

    # Start services
    echo -e "${CYAN}[1/3]${NC} Starting AI Server (Python/FastAPI)..."
    start_ai
    sleep 3

    echo ""
    echo -e "${CYAN}[2/3]${NC} Starting API Server (Go)..."
    start_api
    sleep 3

    echo ""
    echo -e "${CYAN}[3/3]${NC} Starting Frontend (React/Vite)..."
    start_frontend

    echo ""
    echo -e "${GREEN}========================================================${NC}"
    echo -e "${GREEN}   All services started successfully!                   ${NC}"
    echo -e "${GREEN}========================================================${NC}"
    echo ""
    echo -e "${CYAN}Service URLs:${NC}"
    echo "  - Frontend:    http://localhost:5173"
    echo "  - API Server:  http://localhost:2030"
    echo "  - AI Server:   http://localhost:9999"
    echo ""
    echo -e "${CYAN}Health Check URLs:${NC}"
    echo "  - API Server:  http://localhost:2030/api/v1/ping"
    echo "  - AI Server:   http://localhost:9999/api/v1/health"
    echo "  - AI Server Docs: http://localhost:9999/docs"
    echo ""
    echo -e "${YELLOW}[TIP]${NC} View logs: ./start-local.sh logs [ai|api|frontend]"
    echo -e "${YELLOW}[TIP]${NC} Stop services: ./start-local.sh stop"
    echo ""
}

# ========================================
# Stop Services
# ========================================
stop_service() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"

    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            # Wait a moment and force kill if necessary
            sleep 1
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID" 2>/dev/null
            fi
            echo -e "${GREEN}[OK]${NC} $name stopped (was PID: $PID)"
        else
            echo -e "${YELLOW}[WARN]${NC} $name was not running"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}[WARN]${NC} No PID file for $name"
    fi
}

stop_all() {
    echo -e "${BLUE}[INFO]${NC} Stopping all services..."
    echo ""

    # Stop by PID files
    stop_service "ai_server"
    stop_service "api_server"
    stop_service "frontend"

    # Also try to kill by port as fallback
    echo ""
    echo "Cleaning up any remaining processes..."

    # Kill processes on ports
    for port in 9999 2030 5173; do
        PID=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
            echo "  Killed process on port $port"
        fi
    done

    echo ""
    echo -e "${GREEN}[OK]${NC} All services stopped"
    echo ""
}

# ========================================
# Restart Services
# ========================================
restart_all() {
    echo -e "${BLUE}[INFO]${NC} Restarting all services..."
    stop_all
    sleep 2
    start_all
}

# ========================================
# Check Status
# ========================================
check_status() {
    echo -e "${BLUE}[INFO]${NC} Checking service status..."
    echo ""

    # Check AI Server
    echo "AI Server (port 9999):"
    if lsof -i :9999 &>/dev/null || netstat -tuln 2>/dev/null | grep -q ":9999 "; then
        echo -e "  ${GREEN}[RUNNING]${NC} http://localhost:9999"
    else
        echo -e "  ${RED}[STOPPED]${NC} Not running"
    fi

    # Check API Server
    echo "API Server (port 2030):"
    if lsof -i :2030 &>/dev/null || netstat -tuln 2>/dev/null | grep -q ":2030 "; then
        echo -e "  ${GREEN}[RUNNING]${NC} http://localhost:2030"
    else
        echo -e "  ${RED}[STOPPED]${NC} Not running"
    fi

    # Check Frontend
    echo "Frontend (port 5173):"
    if lsof -i :5173 &>/dev/null || netstat -tuln 2>/dev/null | grep -q ":5173 "; then
        echo -e "  ${GREEN}[RUNNING]${NC} http://localhost:5173"
    else
        echo -e "  ${RED}[STOPPED]${NC} Not running"
    fi

    echo ""
}

# ========================================
# View Logs
# ========================================
view_logs() {
    local service=$1

    case "$service" in
        ai|ai_server)
            echo -e "${BLUE}[INFO]${NC} Showing AI Server logs (Ctrl+C to exit)..."
            tail -f "$SCRIPT_DIR/logs/ai_server.log"
            ;;
        api|api_server)
            echo -e "${BLUE}[INFO]${NC} Showing API Server logs (Ctrl+C to exit)..."
            tail -f "$SCRIPT_DIR/logs/api_server.log"
            ;;
        frontend|fe)
            echo -e "${BLUE}[INFO]${NC} Showing Frontend logs (Ctrl+C to exit)..."
            tail -f "$SCRIPT_DIR/logs/frontend.log"
            ;;
        all|"")
            echo -e "${BLUE}[INFO]${NC} Showing all logs (Ctrl+C to exit)..."
            tail -f "$SCRIPT_DIR/logs/"*.log
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unknown service: $service"
            echo "Usage: ./start-local.sh logs [ai|api|frontend|all]"
            ;;
    esac
}

# ========================================
# Help
# ========================================
show_help() {
    echo -e "${CYAN}VRecommendation System - Local Startup Script (No Docker)${NC}"
    echo ""
    echo "Usage: ./start-local.sh [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start, up       Start all services locally (default)"
    echo "  stop, down      Stop all running services"
    echo "  restart         Restart all services"
    echo "  status          Check status of all services"
    echo "  install         Install all dependencies"
    echo "  check           Check if all dependencies are installed"
    echo "  ai              Start only AI Server"
    echo "  api             Start only API Server"
    echo "  frontend        Start only Frontend"
    echo "  logs [service]  View logs (ai|api|frontend|all)"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start-local.sh                 Start all services"
    echo "  ./start-local.sh status          Check service status"
    echo "  ./start-local.sh stop            Stop all services"
    echo "  ./start-local.sh install         Install dependencies"
    echo "  ./start-local.sh ai              Start only AI Server"
    echo "  ./start-local.sh logs ai         View AI Server logs"
    echo ""
    echo "Requirements:"
    echo "  - Go 1.24+      (for API Server)"
    echo "  - Python 3.9+   (for AI Server)"
    echo "  - Poetry        (for AI Server dependency management)"
    echo "  - Node.js 18+   (for Frontend)"
    echo "  - npm           (for Frontend)"
    echo ""
    echo "Service URLs (after starting):"
    echo "  - Frontend:      http://localhost:5173"
    echo "  - API Server:    http://localhost:2030"
    echo "  - AI Server:     http://localhost:9999"
    echo "  - AI Server Docs: http://localhost:9999/docs"
    echo ""
    echo -e "${YELLOW}Note:${NC} External services (Redis, MySQL, MongoDB, Kafka) must be"
    echo "      running separately if required by your configuration."
    echo ""
}

# ========================================
# Main
# ========================================

# Setup environment files first
setup_env_files

# Parse command
COMMAND=${1:-start}

case "$COMMAND" in
    start|up)
        start_all
        ;;
    stop|down)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        check_status
        ;;
    install)
        install_all
        ;;
    check)
        check_deps
        ;;
    ai)
        mkdir -p "$SCRIPT_DIR/logs"
        start_ai
        ;;
    api)
        mkdir -p "$SCRIPT_DIR/logs"
        start_api
        ;;
    frontend|fe)
        mkdir -p "$SCRIPT_DIR/logs"
        start_frontend
        ;;
    logs)
        view_logs "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}[ERROR]${NC} Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
