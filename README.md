# VRecommendation System

A comprehensive AI-powered recommendation system with microservices architecture, featuring real-time data processing, machine learning models, and a modern web interface.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │   AI Server     │
│   (React+Vite)  │◄──►│   (Go/Fiber)    │◄──►│   (Python)      │
│   Port: 5173    │    │   Port: 2030    │    │   Port: 9999    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │     Redis       │    │   Prometheus    │
                    │   (Cache/DB)    │    │  (Monitoring)   │
                    │   Port: 6379    │    │   Port: 9090    │
                    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Git**
- **curl** (for testing)

### 1. Clone Repository

```bash
git clone <repository-url>
cd VRecommendation
```

### 2. Environment Setup

```bash
# Copy development environment
copy .env.development .env

# Or use the Makefile
make install
```

### 3. Start All Services

```bash
# Using Docker Compose
docker-compose up -d

# Or using Makefile
make start
```

### 4. Verify Installation

```bash
# Check all services
make health

# Or manually
curl http://localhost:2030/api/v1/ping
curl http://localhost:9999/api/v1/health
curl http://localhost:5173
```

### 5. Access Services

- **Frontend**: http://localhost:5173
- **API Server**: http://localhost:2030
- **AI Server**: http://localhost:9999
- **Prometheus**: http://localhost:9090

## Available Commands

### Using Makefile (Recommended)

```bash
# Installation & Setup
make install          # Install dependencies and setup environment
make build            # Build all Docker images

# Service Management
make start            # Start all services
make stop             # Stop all services
make restart          # Restart all services
make status           # Show service status

# Development
make dev              # Start development environment
make dev-api          # Run API server locally
make dev-ai           # Run AI server locally
make dev-frontend     # Run frontend locally

# Monitoring & Logs
make logs             # Show all service logs
make logs-api         # Show API server logs
make logs-ai          # Show AI server logs
make health           # Check service health
make urls             # Show all service URLs

# Testing
make test             # Run all tests
make test-api         # Run API server tests
make test-ai          # Run AI server tests

# Maintenance
make clean            # Clean containers and volumes
make clean-all        # Full cleanup
make backup           # Backup data
make update           # Update services

# Utilities
make help             # Show all available commands
```

### Using Command Scripts

#### Windows

```cmd
# Start services
start.cmd

# Stop services
stop.cmd

# Test system
test-system.cmd
```

#### Linux/Mac

```bash
# Start services
./docker-start.sh

# Backend development
./run_backend.sh

# Frontend development
./run_frontend.sh
```

## Configuration

### Environment Variables

Key environment variables in `.env`:

```env
# Authentication
JWT_SECRET_KEY=your-jwt-secret-key
SESSION_SECRET=your-session-secret

# API Server
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=2030

# AI Server
AI_SERVER_HOST=0.0.0.0
AI_SERVER_PORT=9999

# Frontend
FRONTEND_PORT=5173
VITE_API_SERVER_URL=http://localhost:2030
VITE_AI_SERVER_URL=http://localhost:9999

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Database (MySQL/MongoDB)
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=your-password

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Service Configuration

Each service has its own configuration directory:

- **API Server**: `backend/api_server/config/`
- **AI Server**: `backend/ai_server/config/`
- **Frontend**: `frontend/project/`

## Testing

### System Tests

```bash
# Run comprehensive system tests
make test

# Or use Windows script
test-system.cmd
```

### Manual Testing

```bash
# API Server
curl http://localhost:2030/api/v1/ping
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:2030/api/v1/activity-logs/all

# AI Server
curl http://localhost:9999/api/v1/health
curl http://localhost:9999/api/v1/list_models
curl http://localhost:9999/api/v1/list_tasks

# Frontend
curl http://localhost:5173
```

## Troubleshooting

### Common Issues

#### 1. Services Not Starting

```bash
# Check Docker
docker --version
docker-compose --version

# Check service status
make status
docker-compose ps

# View logs
make logs
```

#### 2. Port Conflicts

Default ports used: `2030`, `9999`, `5173`, `9090`, `6379`

```bash
# Check port usage (Windows)
netstat -ano | findstr :2030

# Kill process using port (Windows)
taskkill /PID <PID> /F
```

#### 3. CORS Issues

- Ensure `CORS_ORIGINS` includes your frontend URL
- Check AI server logs for CORS errors
- Verify frontend is accessing correct API URLs

#### 4. Authentication Issues

```bash
# Check JWT secret configuration
echo %JWT_SECRET_KEY%

# Verify token format
# JWT tokens should start with "eyJ"
```

#### 5. Docker Issues

```bash
# Clean Docker system
make docker-clean

# Full Docker reset
make docker-reset

# Rebuild images
make rebuild
```

### Log Analysis

```bash
# View specific service logs
make logs-api
make logs-ai
make logs-frontend

# Follow logs in real-time
docker-compose logs -f

# Filter logs
docker-compose logs ai_server | grep ERROR
```

## 🏃‍♂️ Development

### Development Workflow

1. **Setup Development Environment**
   ```bash
   make dev
   ```

2. **Run Services Individually**
   ```bash
   # API Server (Go)
   make dev-api

   # AI Server (Python)
   make dev-ai

   # Frontend (React+Vite)
   make dev-frontend
   ```

3. **Make Changes and Test**
   ```bash
   # Test your changes
   make test

   # Check service health
   make health
   ```

4. **Build and Deploy**
   ```bash
   make build
   make start
   ```

### Code Structure

```
VRecommendation/
├── backend/
│   ├── api_server/          # Go API server
│   │   ├── main.go
│   │   ├── internal/
│   │   ├── pkg/
│   │   └── config/
│   └── ai_server/           # Python AI server
│       ├── src/
│       ├── config/
│       ├── models/
│       └── tasks/
├── frontend/
│   └── project/             # React + Vite frontend
│       ├── src/
│       ├── public/
│       └── package.json
├── docs/                    # Documentation
├── diagrams/               # Architecture diagrams
├── docker-compose.yml      # Service orchestration
├── Makefile               # Build automation
└── README.md             # This file
```

## Monitoring

### Service Health

```bash
# Check all services
make health

# Prometheus metrics
curl http://localhost:9090/metrics

# Service status
make status
```

### Performance Monitoring

- **Prometheus**: http://localhost:9090
- **Service Logs**: `make logs`
- **Redis Monitoring**: `make shell-redis`

## Data Management

### Backup

```bash
# Create backup
make backup

# Backup Redis data
make db-backup
```

### Database Operations

```bash
# Reset Redis
make db-reset

# Open Redis CLI
make shell-redis

# View Redis data
docker-compose exec redis redis-cli
```

## Production Deployment

### Production Setup

1. **Configure Environment**
   ```bash
   # Create production .env
   cp .env.development .env.production
   # Edit with production values
   ```

2. **Deploy**
   ```bash
   make prod-build
   make prod
   ```

3. **Monitoring**
   ```bash
   make health
   make logs
   ```

### Security Considerations

- Change default JWT secrets
- Use strong passwords for databases
- Configure proper CORS origins
- Enable HTTPS in production
- Use Docker secrets for sensitive data

## API Documentation

### API Server (Go) - Port 2030

```bash
# Health check
GET /api/v1/ping

# Activity logs (requires auth)
GET /api/v1/activity-logs/all
```

### AI Server (Python) - Port 9999

```bash
# Health check
GET /api/v1/health

# List models
GET /api/v1/list_models

# List tasks
GET /api/v1/list_tasks

# List data chefs
GET /api/v1/list_data_chefs

# Scheduler status
GET /api/v1/get_scheduler_status

# Get recommendations
POST /api/v1/recommend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Use descriptive commit messages

## Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check `docs/` directory
- **Logs**: Use `make logs` for debugging
- **System Test**: Run `test-system.cmd` (Windows) or `make test`

## Changelog

### v1.0.0
- Initial release
- Microservices architecture
- Docker containerization
- Makefile automation
- Comprehensive testing
- CORS support
- JWT authentication
- Redis caching
- Prometheus monitoring

---
