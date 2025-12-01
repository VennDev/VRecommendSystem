#!/bin/bash

# VRecommendation System - Dependency Installation Script
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

echo ""
echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}   VRecommendation System - Dependency Installation     ${NC}"
echo -e "${BLUE}========================================================${NC}"
echo ""

# ========================================
# Check System Dependencies
# ========================================
check_deps() {
    echo -e "${BLUE}[INFO]${NC} Checking system dependencies..."
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
        echo -e "${GREEN}[SUCCESS]${NC} All system dependencies are installed!"
    else
        echo -e "${RED}[WARNING]${NC} Some dependencies are missing. Please install them."
    fi
    echo ""

    return $((1 - ALL_OK))
}

# Silent system dependency check
check_system_deps_silent() {
    command -v go &> /dev/null && \
    command -v poetry &> /dev/null && \
    command -v node &> /dev/null
}

# ========================================
# Install AI Server Dependencies
# ========================================
install_ai() {
    echo -e "${BLUE}[INFO]${NC} Installing AI Server dependencies..."
    echo ""

    if [ ! -f "backend/ai_server/pyproject.toml" ]; then
        echo -e "${RED}[ERROR]${NC} pyproject.toml not found in backend/ai_server"
        return 1
    fi

    echo "Checking Poetry..."
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} Poetry is not installed"
        echo "Install with: pip install poetry"
        return 1
    fi

    cd backend/ai_server
    echo "Installing Python dependencies with Poetry..."
    echo "This may take a few minutes..."
    echo ""

    if poetry install; then
        echo ""
        echo -e "${GREEN}[OK]${NC} AI Server dependencies installed successfully"
    else
        echo -e "${RED}[ERROR]${NC} Failed to install AI Server dependencies"
        cd "$SCRIPT_DIR"
        return 1
    fi

    cd "$SCRIPT_DIR"
}

# ========================================
# Install API Server Dependencies
# ========================================
install_api() {
    echo -e "${BLUE}[INFO]${NC} Installing API Server dependencies..."
    echo ""

    if [ ! -f "backend/api_server/go.mod" ]; then
        echo -e "${RED}[ERROR]${NC} go.mod not found in backend/api_server"
        return 1
    fi

    echo "Checking Go..."
    if ! command -v go &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} Go is not installed"
        echo "Download from: https://golang.org/dl/"
        return 1
    fi

    cd backend/api_server
    echo "Downloading Go modules..."
    echo ""

    if go mod download; then
        echo "Tidying Go modules..."
        go mod tidy || echo -e "${YELLOW}[WARN]${NC} go mod tidy returned warnings"
        echo ""
        echo -e "${GREEN}[OK]${NC} API Server dependencies installed successfully"
    else
        echo -e "${RED}[ERROR]${NC} Failed to download Go modules"
        cd "$SCRIPT_DIR"
        return 1
    fi

    cd "$SCRIPT_DIR"
}

# ========================================
# Install Frontend Dependencies
# ========================================
install_frontend() {
    echo -e "${BLUE}[INFO]${NC} Installing Frontend dependencies..."
    echo ""

    if [ ! -f "frontend/project/package.json" ]; then
        echo -e "${RED}[ERROR]${NC} package.json not found in frontend/project"
        return 1
    fi

    echo "Checking Node.js..."
    if ! command -v node &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} Node.js is not installed"
        echo "Download from: https://nodejs.org/"
        return 1
    fi

    cd frontend/project
    echo "Installing npm packages..."
    echo "This may take a few minutes..."
    echo ""

    if npm install; then
        echo ""
        echo -e "${GREEN}[OK]${NC} Frontend dependencies installed successfully"
    else
        echo -e "${RED}[ERROR]${NC} Failed to install Frontend dependencies"
        cd "$SCRIPT_DIR"
        return 1
    fi

    cd "$SCRIPT_DIR"
}

# ========================================
# Install All Dependencies
# ========================================
install_all() {
    echo -e "${BLUE}[INFO]${NC} Installing all project dependencies..."
    echo ""

    # Check system dependencies first
    if ! check_system_deps_silent; then
        echo -e "${RED}[ERROR]${NC} Missing system dependencies. Please install them first."
        echo "Run: ./install-deps.sh check"
        exit 1
    fi

    # Install AI Server
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}[1/3] AI Server (Python/Poetry)${NC}"
    echo -e "${CYAN}========================================${NC}"
    install_ai || true

    # Install API Server
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}[2/3] API Server (Go)${NC}"
    echo -e "${CYAN}========================================${NC}"
    install_api || true

    # Install Frontend
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}[3/3] Frontend (Node.js/npm)${NC}"
    echo -e "${CYAN}========================================${NC}"
    install_frontend || true

    echo ""
    echo -e "${GREEN}========================================================${NC}"
    echo -e "${GREEN}   All dependencies installed successfully!             ${NC}"
    echo -e "${GREEN}========================================================${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Configure your .env files (run: ./start-local.sh)"
    echo "  2. Start the services: ./start-local.sh start"
    echo ""
}

# ========================================
# Help
# ========================================
show_help() {
    echo -e "${CYAN}VRecommendation System - Dependency Installation${NC}"
    echo ""
    echo "Usage: ./install-deps.sh [COMPONENT]"
    echo ""
    echo "Components:"
    echo "  all             Install all dependencies (default)"
    echo "  ai              Install AI Server dependencies (Python/Poetry)"
    echo "  api             Install API Server dependencies (Go)"
    echo "  frontend        Install Frontend dependencies (Node.js/npm)"
    echo "  check           Check if system dependencies are installed"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./install-deps.sh                Install all dependencies"
    echo "  ./install-deps.sh all            Install all dependencies"
    echo "  ./install-deps.sh ai             Install only AI Server dependencies"
    echo "  ./install-deps.sh api            Install only API Server dependencies"
    echo "  ./install-deps.sh frontend       Install only Frontend dependencies"
    echo "  ./install-deps.sh check          Check system dependencies"
    echo ""
    echo "System Requirements:"
    echo "  - Go 1.24+      (for API Server)"
    echo "  - Python 3.9+   (for AI Server)"
    echo "  - Poetry        (for AI Server dependency management)"
    echo "  - Node.js 18+   (for Frontend)"
    echo "  - npm           (for Frontend)"
    echo ""
    echo "Installation Links:"
    echo "  - Go:       https://golang.org/dl/"
    echo "  - Python:   https://python.org/downloads/"
    echo "  - Poetry:   https://python-poetry.org/docs/ (or: pip install poetry)"
    echo "  - Node.js:  https://nodejs.org/"
    echo ""
}

# ========================================
# Main
# ========================================
COMPONENT=${1:-all}

case "$COMPONENT" in
    all)
        install_all
        ;;
    ai)
        install_ai
        ;;
    api)
        install_api
        ;;
    frontend|fe)
        install_frontend
        ;;
    check)
        check_deps
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
