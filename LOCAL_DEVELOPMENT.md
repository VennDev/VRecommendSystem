# VRecommendation - Local Development Guide (Non-Docker)

This guide explains how to run the VRecommendation system locally **without Docker**.

## 📋 Prerequisites

Before running locally, ensure you have the following installed:

| Component | Version | Purpose | Download |
|-----------|---------|---------|----------|
| **Go** | 1.24+ | API Server | [golang.org/dl](https://golang.org/dl/) |
| **Python** | 3.9+ | AI Server | [python.org](https://python.org/downloads/) |
| **Poetry** | Latest | Python dependency management | `pip install poetry` or [python-poetry.org](https://python-poetry.org/docs/) |
| **Node.js** | 18+ | Frontend | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ | Frontend package manager | Comes with Node.js |

### Optional External Services

Depending on your configuration, you may also need:

- **Redis** - For caching (default port: 6379)
- **MySQL** - For relational data (default port: 3306)
- **MongoDB** - For document storage (default port: 27017)
- **Kafka** - For message streaming (default port: 9092)

## 🚀 Quick Start

### Windows

```cmd
# 1. Check dependencies
start-local.cmd check

# 2. Install project dependencies
install-deps.cmd

# 3. Start all services
start-local.cmd

# 4. Stop all services
stop-local.cmd
```

### Linux/Unix/macOS

```bash
# Make scripts executable (first time only)
chmod +x start-local.sh stop-local.sh install-deps.sh

# 1. Check dependencies
./start-local.sh check

# 2. Install project dependencies
./install-deps.sh

# 3. Start all services
./start-local.sh

# 4. Stop all services
./stop-local.sh
```

## 📁 Scripts Overview

| Script (Windows) | Script (Linux/Unix) | Description |
|-----------------|---------------------|-------------|
| `start-local.cmd` | `start-local.sh` | Start services locally (no Docker) |
| `stop-local.cmd` | `stop-local.sh` | Stop local services |
| `install-deps.cmd` | `install-deps.sh` | Install project dependencies |

## 📖 Detailed Usage

### Starting Services

#### Start All Services

**Windows:**
```cmd
start-local.cmd
# or
start-local.cmd start
```

**Linux/Unix:**
```bash
./start-local.sh
# or
./start-local.sh start
```

#### Start Individual Services

**Windows:**
```cmd
start-local.cmd ai        # Start only AI Server
start-local.cmd api       # Start only API Server
start-local.cmd frontend  # Start only Frontend
```

**Linux/Unix:**
```bash
./start-local.sh ai        # Start only AI Server
./start-local.sh api       # Start only API Server
./start-local.sh frontend  # Start only Frontend
```

### Stopping Services

**Windows:**
```cmd
stop-local.cmd            # Stop all services
stop-local.cmd ai         # Stop only AI Server
stop-local.cmd api        # Stop only API Server
stop-local.cmd frontend   # Stop only Frontend
```

**Linux/Unix:**
```bash
./stop-local.sh            # Stop all services
./stop-local.sh ai         # Stop only AI Server
./stop-local.sh api        # Stop only API Server
./stop-local.sh frontend   # Stop only Frontend
```

### Check Status

**Windows:**
```cmd
start-local.cmd status
# or
stop-local.cmd status
```

**Linux/Unix:**
```bash
./start-local.sh status
# or
./stop-local.sh status
```

### Installing Dependencies

**Windows:**
```cmd
install-deps.cmd           # Install all dependencies
install-deps.cmd ai        # Install only AI Server deps
install-deps.cmd api       # Install only API Server deps
install-deps.cmd frontend  # Install only Frontend deps
install-deps.cmd check     # Check system dependencies
```

**Linux/Unix:**
```bash
./install-deps.sh           # Install all dependencies
./install-deps.sh ai        # Install only AI Server deps
./install-deps.sh api       # Install only API Server deps
./install-deps.sh frontend  # Install only Frontend deps
./install-deps.sh check     # Check system dependencies
```

### View Logs (Linux/Unix only)

```bash
./start-local.sh logs          # View all logs
./start-local.sh logs ai       # View AI Server logs
./start-local.sh logs api      # View API Server logs
./start-local.sh logs frontend # View Frontend logs
```

On Windows, logs are displayed in separate terminal windows.

## 🌐 Service URLs

After starting the services, access them at:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | React application |
| **API Server** | http://localhost:2030 | Go REST API |
| **AI Server** | http://localhost:9999 | Python FastAPI |
| **AI Server Docs** | http://localhost:9999/docs | Swagger documentation |

### Health Check Endpoints

| Service | Health Check URL |
|---------|-----------------|
| API Server | http://localhost:2030/api/v1/ping |
| AI Server | http://localhost:9999/api/v1/health |

## ⚙️ Environment Configuration

### Automatic Configuration

The `start-local.cmd` and `start-local.sh` scripts automatically:

1. Create `.env` files from `example-env` templates
2. Configure URLs to use `localhost` instead of Docker service names
3. Set up appropriate local development settings

### Manual Configuration

If you need to customize settings, edit these `.env` files:

| File | Purpose |
|------|---------|
| `.env` | Root environment configuration |
| `backend/api_server/.env` | API Server configuration |
| `backend/ai_server/.env` | AI Server configuration |
| `frontend/project/.env` | Frontend configuration |

### Key Configuration Changes for Local Development

When running locally (vs Docker), these settings are automatically adjusted:

| Setting | Docker Value | Local Value |
|---------|--------------|-------------|
| `REDIS_HOST` | `redis` | `localhost` |
| `MYSQL_HOST` | `mysql` | `localhost` |
| `MONGODB_HOST` | `mongodb` | `localhost` |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9093` | `localhost:9092` |
| `AI_SERVER_URL` | `http://ai_server:9999` | `http://localhost:9999` |
| `VITE_API_SERVER_URL` | `http://api_server:2030` | `http://localhost:2030` |

## 🔧 Troubleshooting

### Port Already in Use

If you see "port already in use" errors:

**Windows:**
```cmd
# Check what's using a port
netstat -aon | findstr ":9999"
netstat -aon | findstr ":2030"
netstat -aon | findstr ":5173"

# Kill process by PID
taskkill /PID <PID> /F
```

**Linux/Unix:**
```bash
# Check what's using a port
lsof -i :9999
lsof -i :2030
lsof -i :5173

# Kill process by port
kill $(lsof -ti :9999)
```

### Poetry Not Found

```bash
# Install Poetry
pip install poetry

# Or on macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### Go Modules Not Downloading

```bash
cd backend/api_server
go mod download
go mod tidy
```

### npm Install Fails

```bash
cd frontend/project
rm -rf node_modules package-lock.json
npm install
```

### External Services Not Available

If Redis, MySQL, MongoDB, or Kafka are not running, you may see connection errors. Either:

1. **Start them with Docker:**
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   docker run -d -p 27017:27017 mongo:latest
   ```

2. **Install and run locally:**
   - Redis: https://redis.io/download
   - MySQL: https://dev.mysql.com/downloads/
   - MongoDB: https://www.mongodb.com/try/download/community
   - Kafka: https://kafka.apache.org/downloads

3. **Disable features that require them** (check configuration)

## 📊 Comparison: Local vs Docker

| Aspect | Local Development | Docker |
|--------|-------------------|--------|
| **Startup Speed** | Faster (no container overhead) | Slower (container startup) |
| **Hot Reload** | Native support | Requires volume mounts |
| **Debugging** | Easy (direct access) | Requires remote debugging |
| **Resource Usage** | Lower | Higher (container overhead) |
| **Environment Parity** | May differ from production | Closer to production |
| **Setup Complexity** | Requires all tools installed | Only requires Docker |
| **External Services** | Must be managed separately | All included |

## 🤝 Tips for Local Development

1. **Use `start-local.cmd check` / `./start-local.sh check`** before starting to ensure all dependencies are installed.

2. **Start services individually** during development to see logs in real-time.

3. **Keep external services running** in Docker while running the main services locally:
   ```bash
   # Start only infrastructure services via Docker
   docker-compose up -d redis kafka zookeeper
   ```

4. **Use IDE debugging** - Since services run locally, you can attach debuggers directly:
   - **Go (API Server)**: Use VS Code or GoLand debugger
   - **Python (AI Server)**: Use PyCharm or VS Code debugger
   - **React (Frontend)**: Use browser DevTools

5. **Check service status** if something seems wrong:
   ```bash
   ./start-local.sh status   # Linux/Unix
   start-local.cmd status    # Windows
   ```

## 📝 Command Reference

### start-local (Windows: `start-local.cmd` / Linux: `./start-local.sh`)

| Command | Description |
|---------|-------------|
| `start` / `up` | Start all services (default) |
| `stop` / `down` | Stop all services |
| `restart` | Restart all services |
| `status` | Check service status |
| `install` | Install all dependencies |
| `check` | Check system dependencies |
| `ai` | Start only AI Server |
| `api` | Start only API Server |
| `frontend` | Start only Frontend |
| `logs [service]` | View logs (Linux only) |
| `help` | Show help |

### install-deps (Windows: `install-deps.cmd` / Linux: `./install-deps.sh`)

| Command | Description |
|---------|-------------|
| `all` | Install all dependencies (default) |
| `ai` | Install AI Server dependencies |
| `api` | Install API Server dependencies |
| `frontend` | Install Frontend dependencies |
| `check` | Check system dependencies |
| `help` | Show help |

### stop-local (Windows: `stop-local.cmd` / Linux: `./stop-local.sh`)

| Command | Description |
|---------|-------------|
| `all` | Stop all services (default) |
| `ai` | Stop AI Server |
| `api` | Stop API Server |
| `frontend` | Stop Frontend |
| `status` | Check service status |
| `help` | Show help |