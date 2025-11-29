# VRecommendation System

A production-ready AI-powered recommendation system built with microservices architecture. The system provides real-time model training, multiple data source integration, and comprehensive REST APIs for building intelligent recommendation features into any application.

## Overview

VRecommendation is a complete recommendation engine that combines machine learning models with a modern web interface. It supports collaborative filtering, content-based filtering, and hybrid recommendation algorithms with real-time data processing from multiple sources including databases, CSV files, REST APIs, and Kafka message queues.

## Architecture

The system consists of three main services:

- **API Server (Go/Fiber)**: High-performance gateway handling authentication, request routing, and caching
- **AI Server (Python/FastAPI)**: Machine learning engine managing model training, data processing, and predictions
- **Frontend (React/TypeScript)**: Modern dashboard for system management and monitoring

Supporting infrastructure:
- **Redis**: Caching layer and session management
- **Kafka**: Real-time event streaming and data ingestion
- **Zookeeper**: Kafka coordination service
- **Prometheus**: Metrics collection and monitoring
- **Kafka UI**: Web interface for Kafka cluster management

All services run in Docker containers orchestrated with Docker Compose.

## Key Features

### Machine Learning
- Support for SVD, matrix factorization, and collaborative filtering algorithms
- Incremental learning from streaming data
- Automatic model retraining on configurable schedules
- Model versioning and metadata tracking
- Real-time prediction API

### Data Integration
- CSV file processing with batch reading
- SQL database connections (MySQL, PostgreSQL)
- NoSQL database support (MongoDB)
- REST API data ingestion
- Kafka message queue consumer
- Automatic data transformation and validation

### System Management
- Web-based administration dashboard
- Real-time metrics and monitoring
- Scheduled task management
- Model lifecycle management
- Data pipeline configuration

### Security & Performance
- JWT-based authentication
- Google OAuth integration
- Redis caching for fast responses
- Connection pooling and resource management
- Prometheus metrics collection

## Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher
- 4GB RAM minimum (8GB recommended)
- 10GB available disk space

Optional for local development:
- Go 1.21 or higher
- Python 3.11 or higher
- Node.js 18 or higher

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/VRecommendation.git
cd VRecommendation
```

### 2. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp example-env .env
```

Edit the `.env` file with your configuration. Key variables:

```env
# JWT Secret (REQUIRED - change this in production)
JWT_SECRET_KEY=your-secure-secret-key-here

# API Server Configuration
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=2030

# AI Server Configuration
AI_SERVER_HOST=0.0.0.0
AI_SERVER_PORT=9999

# Frontend Configuration
FRONTEND_PORT=5173
VITE_API_SERVER_URL=http://localhost:2030
VITE_AI_SERVER_URL=http://localhost:9999

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_PORT=9092
```

### 3. Configure Google OAuth (Optional)

To enable Google login, set up OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URI: `http://localhost:2030/api/v1/auth/google/callback`
4. Update `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_CALLBACK_URL=http://localhost:2030/api/v1/auth/google/callback

# For LAN/ngrok access (optional)
GOOGLE_CALLBACK_URL_PUBLIC=https://your-ngrok-url.ngrok-free.app/api/v1/auth/google/callback
```

### 4. Start All Services

**Windows:**
```cmd
start.cmd
# Or start everything including Admin Portal:
start.cmd all
```

**Linux/macOS:**
```bash
docker-compose up -d
```

This will start all services in the background. First-time startup may take several minutes to download images and build containers.

### 5. Verify Installation

Check that all services are running:

```bash
docker-compose ps
```

All services should show status as "Up". Test the endpoints:

```bash
# Test API Server
curl http://localhost:2030/api/v1/ping

# Test AI Server
curl http://localhost:9999/api/v1/health
```

Expected responses indicate healthy services.

### 6. Access the Application

- **Frontend Dashboard**: http://localhost:5173
- **API Server**: http://localhost:2030
- **AI Server**: http://localhost:9999
- **Admin Portal**: http://127.0.0.1:3456 (localhost only)
- **Prometheus Metrics**: http://localhost:9090
- **Kafka UI**: http://localhost:8080

### 7. Admin Portal (Email Whitelist Management)

The Admin Portal allows you to manage which email addresses can register/login to the system.

**Start Admin Portal:**
```cmd
start.cmd admin
```

Then access: http://127.0.0.1:3456

> **Note:** Admin Portal is only accessible from localhost for security reasons.

**Or start everything together:**
```cmd
start.cmd all
```

## LAN Access

To access the application from other devices on your local network:

### Quick Setup (Windows)
```cmd
start.cmd setup
```

This will:
1. Detect your LAN IP address
2. Update configuration files
3. Rebuild and restart containers

### Manual Setup

1. Find your LAN IP (e.g., `192.168.1.100`)
2. Update `.env`:
```env
HOST_IP=192.168.1.100
VITE_API_SERVER_URL=http://192.168.1.100:2030
VITE_AI_SERVER_URL=http://192.168.1.100:9999
FRONTEND_URL=http://192.168.1.100:5173
```

3. Rebuild frontend:
```bash
docker-compose build frontend
docker-compose up -d
```

4. Open firewall ports (Windows Admin):
```cmd
netsh advfirewall firewall add rule name="VRecom" dir=in action=allow protocol=tcp localport=5173,2030,9999
```

### Google OAuth on LAN

Google OAuth does **not** allow private IP addresses as redirect URIs. Solutions:

1. **Login on server machine** - Login via `http://localhost:5173`, then use from LAN
2. **Use ngrok** - Create public URL for OAuth:
   ```cmd
   ngrok http 2030
   ```
   Then add the ngrok URL to Google Console and set `GOOGLE_CALLBACK_URL_PUBLIC` in `.env`

See [HUONG_DAN_OAUTH_LAN.md](HUONG_DAN_OAUTH_LAN.md) for detailed instructions.

## Project Structure

```
VRecommendation/
├── backend/
│   ├── ai_server/              # Python FastAPI ML service
│   │   ├── src/
│   │   │   └── ai_server/
│   │   │       ├── handlers/   # Business logic handlers
│   │   │       ├── models/     # ML model implementations
│   │   │       ├── routers/    # API route definitions
│   │   │       ├── services/   # Core services
│   │   │       ├── tasks/      # Background tasks
│   │   │       └── utils/      # Utility functions
│   │   ├── config/             # Configuration files
│   │   ├── models/             # Trained model files
│   │   ├── tasks/              # Task definitions (JSON)
│   │   ├── data/               # Data storage
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   └── api_server/             # Go Fiber gateway service
│       ├── app/
│       │   ├── controllers/    # HTTP handlers
│       │   ├── middleware/     # Custom middleware
│       │   └── models/         # Data models
│       ├── internal/
│       │   ├── auth/           # Authentication logic
│       │   ├── cache/          # Redis operations
│       │   ├── initialize/     # App initialization
│       │   └── proxy/          # AI server proxy
│       ├── pkg/                # Reusable packages
│       ├── config/             # Configuration files
│       ├── Dockerfile
│       ├── go.mod
│       └── main.go
│
├── frontend/
│   └── project/                # React TypeScript application
│       ├── src/
│       │   ├── components/     # React components
│       │   ├── pages/          # Page components
│       │   ├── services/       # API services
│       │   ├── contexts/       # React contexts
│       │   └── hooks/          # Custom hooks
│       ├── public/             # Static assets
│       ├── Dockerfile
│       └── package.json
│
├── tests/
│   ├── demo-website/           # Demo e-commerce site
│   ├── kafka-server/           # Standalone Kafka for testing
│   └── test-data/              # Test datasets
│
├── scripts/                    # Utility scripts
├── docs/                       # Additional documentation
├── diagrams/                   # Architecture diagrams
├── docker-compose.yml          # Main orchestration file
├── Makefile                    # Build automation
└── README.md                   # This file
```

## Configuration Guide

### Environment Variables

The system uses a single `.env` file in the project root. Key configuration sections:

#### Authentication & Security

```env
JWT_SECRET_KEY=your-secret-key          # JWT signing secret
SESSION_SECRET=your-session-secret       # Session encryption key
JWT_EXPIRE_MINUTES=1440                  # Token expiration (24 hours)
```

#### Service URLs

```env
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=2030
AI_SERVER_HOST=0.0.0.0
AI_SERVER_PORT=9999
FRONTEND_PORT=5173
```

#### Database Connections

```env
# MySQL
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_USER=your-username
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=your-database

# MongoDB
MONGODB_HOST=your-mongodb-host
MONGODB_PORT=27017
MONGODB_USERNAME=your-username
MONGODB_PASSWORD=your-password
```

#### Kafka Configuration

```env
KAFKA_BOOTSTRAP_SERVERS=kafka:9093      # Internal broker address
KAFKA_PORT=9092                          # External broker port
KAFKA_GROUP_ID=vrecom_consumer_group     # Consumer group ID
```

### Service-Specific Configuration

Each service has additional configuration files:

- **AI Server**: `backend/ai_server/config/`
  - `local.yaml`: Main configuration
  - `restaurant_data.yaml`: Data source definitions

- **API Server**: `backend/api_server/config/`
  - `config.yaml`: Server settings
  - `cors.yaml`: CORS configuration

- **Frontend**: `frontend/project/.env`
  - API endpoint URLs
  - Feature flags

## Usage Guide

### Creating a Recommendation Model

#### 1. Prepare Your Data

Create a data chef to connect to your data source:

```bash
# Using CSV file
curl -X POST http://localhost:9999/api/v1/create_data_chef_from_csv \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_interactions",
    "path": "/app/data/interactions.csv",
    "rename_columns": "userId:user_id,itemId:item_id,rating:rating"
  }'

# Using SQL database
curl -X POST http://localhost:9999/api/v1/create_data_chef_from_sql \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_interactions",
    "query": "SELECT user_id, item_id, rating FROM interactions",
    "rename_columns": ""
  }'

# Using Kafka topic
# Configure in backend/ai_server/config/restaurant_data.yaml:
# my_kafka_data:
#   type: messaging_queue
#   brokers: kafka:9093
#   topic: interactions
#   group_id: my_consumer_group
```

#### 2. Create Model Configuration

Create a JSON file in `backend/ai_server/models/`:

```json
{
  "model_name": "My Recommendation Model",
  "model_id": "my_model",
  "type": "svd",
  "algorithm": "svd",
  "hyperparameters": {
    "n_components": 50,
    "algorithm": "randomized",
    "n_iter": 10,
    "random_state": 42
  },
  "message": "Production recommendation model"
}
```

#### 3. Schedule Training Task

Create a task file in `backend/ai_server/tasks/`:

```json
{
  "task_name": "my_model",
  "model_id": "my_model",
  "interactions_data_chef_id": "my_interactions",
  "item_features_data_chef_id": null,
  "user_features_data_chef_id": null,
  "interval": 3600
}
```

The `interval` is in seconds. The model will automatically retrain at this interval.

#### 4. Restart AI Server

```bash
docker-compose restart ai_server
```

The model will begin training according to the schedule.

#### 5. Get Recommendations

```bash
curl "http://localhost:2030/api/v1/recommend?user_id=user123&model_id=my_model&n=10"
```

Response format:

```json
{
  "user_id": "user123",
  "model_id": "my_model",
  "predictions": {
    "user123": [
      {"item_id": "item456", "score": 4.8},
      {"item_id": "item789", "score": 4.6},
      {"item_id": "item321", "score": 4.3}
    ]
  },
  "n_recommendations": 10,
  "status": "completed",
  "datetime": "2024-11-23T10:30:00Z"
}
```

### Working with Kafka Data Streams

#### Send Data to Kafka

```bash
# Send interaction events
echo '{"user_id": "user1", "item_id": "item1", "rating": 5.0}
{"user_id": "user2", "item_id": "item2", "rating": 4.5}
{"user_id": "user3", "item_id": "item3", "rating": 4.0}' | \
docker exec -i vrecom_kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic interactions
```

#### Verify Messages

```bash
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --from-beginning \
  --max-messages 10
```

#### Monitor Consumer Groups

```bash
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group your_consumer_group \
  --describe
```

This shows the current offset, lag, and consumption status.

### Managing the System

#### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ai_server
docker-compose logs -f api_server

# Last N lines
docker-compose logs --tail=100 ai_server
```

#### Restart Services

```bash
# Restart specific service
docker-compose restart ai_server

# Restart all services
docker-compose restart

# Stop and start (full restart)
docker-compose down
docker-compose up -d
```

#### Monitor System Health

```bash
# Check service status
docker-compose ps

# Check resource usage
docker stats

# View metrics in Prometheus
# Open http://localhost:9090
```

#### Clear Cache

```bash
# Flush all Redis cache
docker exec vrecom_redis redis-cli FLUSHDB

# Clear specific keys
docker exec vrecom_redis redis-cli DEL "key_pattern"
```

## API Reference

### API Server Endpoints (Port 2030)

#### Health Check

```
GET /api/v1/ping
```

Response: `{"message": "pong", "timestamp": "2024-11-23T10:00:00Z"}`

#### Get Recommendations

```
GET /api/v1/recommend?user_id={userId}&model_id={modelId}&n={count}
```

Parameters:
- `user_id`: User identifier (required)
- `model_id`: Model to use for recommendations (required)
- `n`: Number of recommendations (default: 5)

#### Authentication

```
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET /api/v1/auth/status
```

### AI Server Endpoints (Port 9999)

#### Health Check

```
GET /api/v1/health
```

#### Model Management

```
GET /api/v1/list_models
POST /api/v1/create_model
DELETE /api/v1/delete_model?model_id={modelId}
GET /api/v1/get_model?model_id={modelId}
```

#### Data Chef Management

```
GET /api/v1/list_data_chefs
POST /api/v1/create_data_chef_from_csv
POST /api/v1/create_data_chef_from_sql
POST /api/v1/create_data_chef_from_nosql
POST /api/v1/create_data_chef_from_api
DELETE /api/v1/delete_data_chef?name={chefName}
```

#### Task Management

```
GET /api/v1/list_tasks
POST /api/v1/add_model_task
DELETE /api/v1/remove_model_task?task_name={taskName}
```

#### Scheduler Control

```
GET /api/v1/get_scheduler_status
POST /api/v1/stop_scheduler
POST /api/v1/restart_scheduler
```

#### Direct Recommendations

```
POST /api/v1/recommend
{
  "user_id": "user123",
  "model_id": "my_model",
  "n": 10
}
```

## Development

### Local Development Setup

#### Backend Development

For AI Server (Python):

```bash
cd backend/ai_server
poetry install
poetry run server
```

For API Server (Go):

```bash
cd backend/api_server
go mod download
go run main.go
```

#### Frontend Development

```bash
cd frontend/project
npm install
npm run dev
```

### Running Tests

#### AI Server Tests

```bash
cd backend/ai_server
poetry run pytest tests/ -v
```

#### API Server Tests

```bash
cd backend/api_server
go test ./... -v
```

#### Frontend Tests

```bash
cd frontend/project
npm test
```

### Code Quality

#### Python (AI Server)

```bash
# Format code
poetry run black src/

# Lint code
poetry run flake8 src/

# Type checking
poetry run mypy src/
```

#### Go (API Server)

```bash
# Format code
go fmt ./...

# Lint code
golangci-lint run

# Vet code
go vet ./...
```

#### TypeScript (Frontend)

```bash
# Lint code
npm run lint

# Type checking
npm run type-check

# Format code
npm run format
```

### Adding New Features

#### Adding a New ML Algorithm

1. Create model class in `backend/ai_server/src/ai_server/models/`:

```python
from ai_server.models.base_model import BaseRecommendationModel

class MyNewModel(BaseRecommendationModel):
    def __init__(self, **hyperparameters):
        super().__init__(**hyperparameters)
        
    def fit(self, interactions_df, **kwargs):
        # Training implementation
        pass
        
    def predict(self, user_id, n=5):
        # Prediction implementation
        pass
```

2. Register in `backend/ai_server/src/ai_server/services/model_service.py`

3. Add tests in `backend/ai_server/tests/`

4. Update documentation

#### Adding a New Data Source Type

1. Create data chef handler in `backend/ai_server/src/ai_server/services/data_chef_service.py`:

```python
def _cook_my_source(param1, param2):
    # Data fetching logic
    for record in data_source:
        yield record
```

2. Add to `_cook_raw_data_source()` switch statement

3. Create API endpoint in routers

4. Add configuration example

## Production Deployment

### Security Checklist

Before deploying to production:

- [ ] Change all default secrets in `.env`
- [ ] Use strong JWT secret keys
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Set up firewall rules
- [ ] Use environment-specific configurations
- [ ] Enable rate limiting
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Enable monitoring and alerting
- [ ] Review and remove debug endpoints
- [ ] Use secrets management (e.g., Vault, AWS Secrets Manager)

### Docker Production Build

Build optimized production images:

```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Resource Allocation

Recommended minimum resources:

- **API Server**: 512MB RAM, 0.5 CPU
- **AI Server**: 2GB RAM, 1 CPU
- **Frontend**: 256MB RAM, 0.25 CPU
- **Redis**: 512MB RAM, 0.25 CPU
- **Kafka**: 1GB RAM, 0.5 CPU

Adjust in `docker-compose.yml`:

```yaml
services:
  ai_server:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Monitoring Setup

Configure Prometheus targets in `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ai_server'
    static_configs:
      - targets: ['ai_server:9999']
  
  - job_name: 'api_server'
    static_configs:
      - targets: ['api_server:2030']
```

Set up Grafana dashboards for visualization (optional).

### Backup Strategy

#### Database Backups

```bash
# Backup Redis data
docker exec vrecom_redis redis-cli SAVE
docker cp vrecom_redis:/data/dump.rdb ./backups/redis/

# Backup Kafka data
docker exec vrecom_kafka tar -czf /tmp/kafka-backup.tar.gz /var/lib/kafka/data
docker cp vrecom_kafka:/tmp/kafka-backup.tar.gz ./backups/kafka/
```

#### Model Backups

```bash
# Backup trained models
docker cp vrecom_ai_server:/app/models ./backups/models/
```

Automate with cron jobs or use volume backups.

## Troubleshooting

### Common Issues

#### Services Not Starting

Check Docker and Docker Compose versions:

```bash
docker --version        # Should be 20.10+
docker-compose --version # Should be 2.0+
```

Check for port conflicts:

```bash
# Linux/Mac
lsof -i :2030
lsof -i :9999
lsof -i :5173

# Windows
netstat -ano | findstr :2030
```

View service logs for errors:

```bash
docker-compose logs
```

#### Kafka Connection Errors

Verify Kafka is running and accessible:

```bash
docker exec vrecom_kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092
```

Check consumer group status:

```bash
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list
```

Reset consumer offset if needed:

```bash
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group your_group_id \
  --reset-offsets \
  --to-earliest \
  --topic your_topic \
  --execute
```

#### Model Training Not Working

Check if data chef is configured correctly:

```bash
curl http://localhost:9999/api/v1/list_data_chefs
```

Verify data source connectivity from AI server container:

```bash
docker exec vrecom_ai_server python -c "
from ai_server.services.data_chef_service import DataChefService
service = DataChefService()
print(service.list_data_chefs())
"
```

Check task scheduler status:

```bash
curl http://localhost:9999/api/v1/get_scheduler_status
```

View AI server logs for training errors:

```bash
docker-compose logs -f ai_server | grep -i "error\|exception"
```

#### No Recommendations Returned

Verify the model exists and is trained:

```bash
curl http://localhost:9999/api/v1/list_models
```

Check if user exists in training data:

```bash
# View model metadata
docker exec vrecom_ai_server cat models/your_model_metadata.json
```

Clear recommendation cache:

```bash
docker exec vrecom_redis redis-cli KEYS "recommend:*"
docker exec vrecom_redis redis-cli DEL "recommend:user123:my_model:10"
```

#### High Memory Usage

Monitor container resources:

```bash
docker stats
```

Reduce batch sizes in training configuration.

Clear unused data:

```bash
# Clear Redis cache
docker exec vrecom_redis redis-cli FLUSHDB

# Prune Docker system
docker system prune -a
```

### Debug Mode

Enable debug logging by setting in `.env`:

```env
DEBUG=true
LOG_LEVEL=debug
```

Restart services:

```bash
docker-compose restart
```

View detailed logs:

```bash
docker-compose logs -f --tail=100
```

### Getting Help

1. Check service logs: `docker-compose logs <service_name>`
2. Review configuration files for typos or missing values
3. Verify network connectivity between containers
4. Check disk space: `df -h`
5. Review Docker resources: `docker system df`

If issues persist:
- Check the GitHub issues page
- Review documentation in the `docs/` directory
- Enable debug mode and collect logs

## Performance Optimization

### Caching Strategy

The system uses Redis for multiple caching layers:

- **API Response Cache**: Frequently requested recommendations
- **Model Metadata Cache**: Model information and configurations
- **Session Cache**: User session data

Configure cache TTL in `backend/api_server/internal/cache/`:

```go
const (
    RecommendationCacheTTL = 3600  // 1 hour
    ModelMetadataCacheTTL  = 7200  // 2 hours
)
```

### Database Connection Pooling

Configure optimal pool sizes in `.env`:

```env
# API Server
REDIS_POOL_SIZE=20
REDIS_MAX_IDLE=10

# AI Server (adjust in code)
SQL_POOL_SIZE=10
SQL_MAX_OVERFLOW=20
```

### Model Training Optimization

Adjust hyperparameters for faster training:

```json
{
  "hyperparameters": {
    "n_components": 20,
    "n_iter": 5,
    "batch_size": 512
  }
}
```

Lower values train faster but may reduce accuracy.

### Resource Limits

Set appropriate limits in `docker-compose.yml`:

```yaml
services:
  ai_server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following the code style guidelines
4. Add tests for new functionality
5. Update documentation as needed
6. Commit your changes: `git commit -m 'Add new feature'`
7. Push to the branch: `git push origin feature/new-feature`
8. Submit a pull request

### Code Style Guidelines

- **Python**: Follow PEP 8, use Black formatter
- **Go**: Follow Go standard style, use gofmt
- **TypeScript**: Follow Airbnb style guide, use ESLint
- Write meaningful commit messages
- Add comments for complex logic
- Update tests and documentation

## License

This project is licensed under the terms specified in the LICENSE.txt file.

## Support

For questions, issues, or feature requests:

- Open an issue on GitHub
- Check existing documentation in the `docs/` directory
- Review API documentation at service `/docs` endpoints
- Consult troubleshooting section above

## Acknowledgments

Built with open-source technologies:
- FastAPI for Python backend
- Fiber for Go backend
- React and TypeScript for frontend
- Docker for containerization
- Kafka for message streaming
- Redis for caching
- Prometheus for monitoring