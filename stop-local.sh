#!/bin/bash

# VRecommendation System - Stop Local Services Script
# For Linux/Unix systems

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

echo ""
echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}   VRecommendation System - Stop Local Services         ${NC}"
echo -e "${BLUE}========================================================${NC}"
echo ""

# ========================================
# Stop Service by PID file
# ========================================
stop_service_by_pid() {
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
            echo -e "  ${GREEN}[OK]${NC} $name stopped (was PID: $PID)"
        else
            echo -e "  ${YELLOW}[INFO]${NC} $name was not running (stale PID file)"
        fi
        rm -f "$pid_file"
    else
        echo -e "  ${YELLOW}[INFO]${NC} No PID file for $name"
    fi
}

# ========================================
# Stop Service by Port
# ========================================
stop_service_by_port() {
    local port=$1
    local name=$2

    # Try to find process using lsof
    if command -v lsof &> /dev/null; then
        PID=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
            sleep 1
            # Force kill if still running
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID 2>/dev/null
            fi
            echo -e "  ${GREEN}[OK]${NC} Killed process on port $port (PID: $PID)"
            return 0
        fi
    fi

    # Fallback to fuser
    if command -v fuser &> /dev/null; then
        PID=$(fuser $port/tcp 2>/dev/null)
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
            sleep 1
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID 2>/dev/null
            fi
            echo -e "  ${GREEN}[OK]${NC} Killed process on port $port (PID: $PID)"
            return 0
        fi
    fi

    echo -e "  ${YELLOW}[INFO]${NC} $name was not running on port $port"
    return 1
}

# ========================================
# Stop AI Server
# ========================================
stop_ai() {
    echo -e "${BLUE}[INFO]${NC} Stopping AI Server..."
    stop_service_by_pid "ai_server"
    stop_service_by_port 9999 "AI Server"
    echo ""
}

# ========================================
# Stop API Server
# ========================================
stop_api() {
    echo -e "${BLUE}[INFO]${NC} Stopping API Server..."
    stop_service_by_pid "api_server"
    stop_service_by_port 2030 "API Server"
    echo ""
}

# ========================================
# Stop Frontend
# ========================================
stop_frontend() {
    echo -e "${BLUE}[INFO]${NC} Stopping Frontend..."
    stop_service_by_pid "frontend"
    stop_service_by_port 5173 "Frontend"
    echo ""
}

# ========================================
# Stop All Services
# ========================================
stop_all() {
    echo -e "${BLUE}[INFO]${NC} Stopping all local services..."
    echo ""

    # Stop by PID files first
    stop_service_by_pid "ai_server"
    stop_service_by_pid "api_server"
    stop_service_by_pid "frontend"

    # Then cleanup by port
    echo ""
    echo "Cleaning up any remaining processes..."

    for port in 9999 2030 5173; do
        if command -v lsof &> /dev/null; then
            PID=$(lsof -ti :$port 2>/dev/null)
            if [ -n "$PID" ]; then
                kill $PID 2>/dev/null
                echo "  Killed process on port $port"
            fi
        elif command -v fuser &> /dev/null; then
            fuser -k $port/tcp 2>/dev/null && echo "  Killed process on port $port"
        fi
    done

    echo ""
    echo -e "${GREEN}========================================================${NC}"
    echo -e "${GREEN}   All services stopped                                 ${NC}"
    echo -e "${GREEN}========================================================${NC}"
    echo ""
}

# ========================================
# Check Status
# ========================================
check_status() {
    echo -e "${BLUE}[INFO]${NC} Checking service status..."
    echo ""

    # Check AI Server
    echo "AI Server (port 9999):"
    if (lsof -i :9999 &>/dev/null 2>&1) || (netstat -tuln 2>/dev/null | grep -q ":9999 ") || (ss -tuln 2>/dev/null | grep -q ":9999 "); then
        echo -e "  ${GREEN}[RUNNING]${NC} http://localhost:9999"
    else
        echo -e "  ${RED}[STOPPED]${NC} Not running"
    fi

    # Check API Server
    echo "API Server (port 2030):"
    if (lsof -i :2030 &>/dev/null 2>&1) || (netstat -tuln 2>/dev/null | grep -q ":2030 ") || (ss -tuln 2>/dev/null | grep -q ":2030 "); then
        echo -e "  ${GREEN}[RUNNING]${NC} http://localhost:2030"
    else
        echo -e "  ${RED}[STOPPED]${NC} Not running"
    fi

    # Check Frontend
    echo "Frontend (port 5173):"
    if (lsof -i :5173 &>/dev/null 2>&1) || (netstat -tuln 2>/dev/null | grep -q ":5173 ") || (ss -tuln 2>/dev/null | grep -q ":5173 "); then
        echo -e "  ${GREEN}[RUNNING]${NC} http://localhost:5173"
    else
        echo -e "  ${RED}[STOPPED]${NC} Not running"
    fi

    echo ""
}

# ========================================
# Help
# ========================================
show_help() {
    echo -e "${CYAN}VRecommendation System - Stop Local Services${NC}"
    echo ""
    echo "Usage: ./stop-local.sh [COMPONENT]"
    echo ""
    echo "Components:"
    echo "  all             Stop all services (default)"
    echo "  ai              Stop only AI Server (port 9999)"
    echo "  api             Stop only API Server (port 2030)"
    echo "  frontend        Stop only Frontend (port 5173)"
    echo "  status          Check status of all services"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./stop-local.sh                Stop all services"
    echo "  ./stop-local.sh all            Stop all services"
    echo "  ./stop-local.sh ai             Stop only AI Server"
    echo "  ./stop-local.sh status         Check service status"
    echo ""
    echo "Service Ports:"
    echo "  - AI Server:   9999"
    echo "  - API Server:  2030"
    echo "  - Frontend:    5173"
    echo ""
}

# ========================================
# Main
# ========================================
COMPONENT=${1:-all}

case "$COMPONENT" in
    all)
        stop_all
        ;;
    ai)
        stop_ai
        ;;
    api)
        stop_api
        ;;
    frontend|fe)
        stop_frontend
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}[ERROR]${NC} Unknown component: $COMPONENT"
        echo ""
        show_help
        exit 1
        ;;
esac
