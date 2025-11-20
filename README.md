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

## Features

- Microservices architecture with Docker containerization
- AI-powered recommendations using collaborative filtering
- RESTful API with Go Fiber backend
- Modern React frontend with Vite
- Real-time data processing with multiple data source support
- Redis caching and session management
- Prometheus monitoring and metrics
- Scheduled model training with configurable intervals
- Support for CSV, SQL, NoSQL, API, and messaging queue data sources

## Quick Start

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- Git

### 1. Clone Repository

```bash
git clone <repository-url>
cd VRecommendation
```

### 2. Environment Setup

```bash
# Copy development environment (optional)
cp example-env .env

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
```

### 5. Access Services

- Frontend: http://localhost:5173
- API Server: http://localhost:2030
- AI Server: http://localhost:9999
- Prometheus: http://localhost:9090

## Project Structure

```
VRecommendation/
├── backend/
│   ├── api_server/          # Go API server
│   │   ├── main.go
│   │   ├── internal/        # Internal packages
│   │   ├── pkg/             # Public packages
│   │   └── config/          # Configuration files
│   └── ai_server/           # Python AI server
│       ├── src/             # Source code
│       ├── config/          # Configuration files
│       ├── models/          # Trained models
│       └── tasks/           # Scheduled tasks
├── frontend/
│   └── project/             # React + Vite frontend
│       ├── src/
│       ├── public/
│       └── package.json
├── tests/
│   ├── demo-website/        # Demo application
│   └── kafka-server/        # Kafka test server
├── docs/                    # Documentation
├── diagrams/                # Architecture diagrams
├── docker-compose.yml       # Service orchestration
├── Makefile                 # Build automation
└── README.md                # This file
```

## Available Commands

### Using Makefile

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

# Testing
make test             # Run all tests
make test-api         # Run API server tests
make test-ai          # Run AI server tests

# Maintenance
make clean            # Clean containers and volumes
make clean-all        # Full cleanup

# Utilities
make help             # Show all available commands
```

### Using Command Scripts

#### Windows

```cmd
start.cmd           # Start all services
stop.cmd            # Stop all services
test-system.cmd     # Run system tests
```

#### Linux/Mac

```bash
./docker-start.sh   # Start services
./run_backend.sh    # Backend development
./run_frontend.sh   # Frontend development
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

# External Databases (Optional)
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_USER=your-user
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=your-database

MONGODB_HOST=your-mongodb-host
MONGODB_PORT=27017
MONGODB_USERNAME=your-user
MONGODB_PASSWORD=your-password
```

### Service Configuration

Each service has its own configuration directory:

- API Server: `backend/api_server/config/`
- AI Server: `backend/ai_server/config/`
- Frontend: `frontend/project/`

## Data Sources

The AI server supports multiple data source types through the Data Chef system:

### Supported Data Sources

1. **CSV Files**: Local or uploaded CSV files
2. **SQL Databases**: MySQL, PostgreSQL, etc.
3. **NoSQL Databases**: MongoDB, etc.
4. **REST APIs**: External API endpoints
5. **Message Queues**: Kafka.

### Creating Data Chefs

```bash
# Create CSV data chef
POST /api/v1/create_data_chef_from_csv
{
  "name": "my_data",
  "path": "/path/to/file.csv",
  "rename_columns": "userId:user_id,itemId:item_id"
}

# Create SQL data chef
POST /api/v1/create_data_chef_from_sql
{
  "name": "my_data",
  "query": "SELECT * FROM interactions",
  "rename_columns": "userId:user_id,itemId:item_id"
}
```

## Model Training

### Scheduling Model Training

Models can be trained on a schedule using the task system:

```bash
# Add training task
POST /api/v1/add_model_task
{
  "task_name": "daily_training",
  "model_id": "my_model",
  "interactions_data_chef_id": "my_data",
  "interval": 3600
}

# List tasks
GET /api/v1/list_tasks

# Remove task
DELETE /api/v1/remove_model_task?task_name=daily_training
```

### Interval Configuration

- Intervals less than 60 seconds: Scheduled every minute at specific second
- Intervals 60 seconds or more: Scheduled using cyclic intervals
- Minimum interval: 10 seconds
- Maximum interval: Unlimited

## API Documentation

### API Server (Port 2030)

```bash
# Health check
GET /api/v1/ping

# Authentication
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET /api/v1/auth/status

# Activity logs (requires auth)
GET /api/v1/activity-logs/all

# Recommendations
GET /api/v1/recommend?user_id=123&model_id=my_model&n=5
```

### AI Server (Port 9999)

```bash
# Health check
GET /api/v1/health

# Models
GET /api/v1/list_models
POST /api/v1/create_model
DELETE /api/v1/delete_model?model_id=my_model

# Data Chefs
GET /api/v1/list_data_chefs
POST /api/v1/create_data_chef_from_csv
POST /api/v1/create_data_chef_from_sql
DELETE /api/v1/delete_data_chef?name=my_data

# Tasks
GET /api/v1/list_tasks
POST /api/v1/add_model_task
DELETE /api/v1/remove_model_task

# Scheduler
GET /api/v1/get_scheduler_status
POST /api/v1/stop_scheduler
POST /api/v1/restart_scheduler

# Recommendations
POST /api/v1/recommend
{
  "user_id": "123",
  "model_id": "my_model",
  "n": 5
}
```

## Testing

### Demo Website

A demo e-commerce website is provided for testing:

```bash
cd tests/demo-website
npm install
npm start
```

Access at: http://localhost:3500

### Kafka Test Server

A standalone Kafka server for testing message queue integration:

```bash
cd tests/kafka-server
docker-compose up -d
```

Access Kafka UI at: http://localhost:8080

### System Tests

```bash
# Run all tests
make test

# Or use Windows script
test-system.cmd
```

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check Docker
docker --version
docker-compose --version

# Check service status
docker-compose ps

# View logs
docker-compose logs
```

#### Port Conflicts

Default ports used: 2030, 9999, 5173, 9090, 6379

```bash
# Check port usage (Linux/Mac)
lsof -i :2030

# Check port usage (Windows)
netstat -ano | findstr :2030
```

#### Connection Errors

- Verify all services are running: `docker-compose ps`
- Check network connectivity: `docker network inspect vrecom_network`
- Ensure environment variables are set correctly
- Review service logs: `docker-compose logs <service_name>`

#### Database Connection Issues

- Ensure external database credentials are correct in `.env`
- Verify network access to external databases
- Check firewall rules
- Test connection manually using database client

### Log Analysis

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service
docker-compose logs ai_server
docker-compose logs api_server

# Filter logs
docker-compose logs ai_server | grep ERROR
```

## Development

### Development Workflow

1. Start services: `docker-compose up -d`
2. Make changes to code
3. Test changes: `make test`
4. Rebuild if needed: `docker-compose up -d --build`

### Hot Reload

Services are configured with volume mounts for hot reloading:

- Frontend: Changes to `frontend/project/src/` are auto-reloaded
- AI Server: Changes to `backend/ai_server/src/` are auto-reloaded
- API Server: Requires rebuild for Go changes

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## Monitoring

### Prometheus Metrics

Access Prometheus at http://localhost:9090

Available metrics:
- Request counts and latencies
- Model training metrics
- Scheduler status
- System resource usage

### Service Health

```bash
# Check all services
make health

# Individual health checks
curl http://localhost:2030/api/v1/ping
curl http://localhost:9999/api/v1/health
```

## Production Deployment

### Production Checklist

- [ ] Change default JWT secrets
- [ ] Use strong database passwords
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up log aggregation
- [ ] Configure backup strategy
- [ ] Set resource limits
- [ ] Enable monitoring and alerts

### Security Considerations

- Use environment variables for secrets
- Never commit sensitive data to version control
- Keep dependencies updated
- Use network isolation
- Implement rate limiting
- Enable authentication for all endpoints

## Support

- Issues: Create an issue on GitHub
- Documentation: Check `docs/` directory
- Logs: Use `make logs` for debugging

## License

See LICENSE.txt for details.
