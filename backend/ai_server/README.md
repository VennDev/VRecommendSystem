# AI Server - VRecommendation System

A high-performance FastAPI-based AI server that powers the recommendation engine with advanced machine learning capabilities, real-time model training, and comprehensive data pipeline management.

## Features

- **AI Model Management**: Create, train, and manage recommendation models with multiple algorithms
- **Real-time Analytics**: Prometheus metrics and monitoring integration
- **Task Scheduling**: Automated model training and data processing with flexible scheduling
- **Data Pipeline**: Multiple data source connectors (CSV, SQL, NoSQL, APIs, Message Queues)
- **Authentication**: JWT-based authentication with middleware protection
- **Scalable Architecture**: Microservices design with Redis caching and async processing
- **Docker Ready**: Production and development Docker configurations

## Quick Start

### Using Docker (Recommended)

1. **Navigate to AI Server directory:**
```bash
cd backend/ai_server
```

2. **Start with Docker Compose:**
```bash
# Development mode with hot reload
docker-compose -f docker-compose.dev.yml up -d

# Production mode
docker-compose up -d
```

3. **Access the API:**
- **Swagger UI**: http://localhost:9999/docs
- **ReDoc**: http://localhost:9999/redoc
- **Health Check**: http://localhost:9999/api/v1/health

### Manual Development Setup

1. **Install Poetry (if not installed):**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Install dependencies:**
```bash
poetry install
```

3. **Configure environment:**
```bash
cp example-env .env
# Edit .env with your configuration
```

4. **Run the server:**
```bash
poetry run server
```

## Configuration

### Environment Variables

Create a `.env` file based on `example-env`:

```env
# Server Configuration
HOST=0.0.0.0
PORT=9999

# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=shop

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=root
MONGODB_PASSWORD=password

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT Configuration
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

### Configuration Files

The `config/` directory contains:
- `local.yaml`: Main application configuration
- `restaurant_data.yaml`: Sample data configuration

## API Documentation

### Authentication

All private endpoints require JWT authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

### Core Endpoints

#### Model Management

```bash
# Create a new recommendation model
POST /api/v1/create_model
{
    "model_id": "my_model",
    "model_type": "collaborative_filtering",
    "parameters": {
        "learning_rate": 0.01,
        "epochs": 100,
        "embedding_dim": 64
    }
}

# List all models
GET /api/v1/list_models

# Get model details
GET /api/v1/model/{model_id}
```

#### Task Scheduling

```bash
# Add a scheduled model training task
POST /api/v1/add_model_task
{
    "task_name": "daily_retrain",
    "model_id": "my_model",
    "interval": "daily",
    "interactions_data_chef_id": "user_interactions",
    "item_features_data_chef_id": "item_features"
}

# List all scheduled tasks
GET /api/v1/list_tasks

# Remove a task
POST /api/v1/remove_model_task
{
    "task_name": "daily_retrain"
}
```

#### Data Chef Management

```bash
# Create data chef from CSV
POST /api/v1/create_data_chef_from_csv
{
    "data_chef_id": "csv_interactions",
    "file_path": "/data/interactions.csv",
    "delimiter": ",",
    "has_header": true
}

# Create data chef from SQL
POST /api/v1/create_data_chef_from_sql
{
    "data_chef_id": "sql_users",
    "query": "SELECT user_id, item_id, rating FROM user_ratings",
    "connection_string": "mysql://user:pass@localhost/db"
}

# Create data chef from NoSQL
POST /api/v1/create_data_chef_from_nosql
{
    "data_chef_id": "mongo_items",
    "collection": "products",
    "database": "ecommerce",
    "query": {}
}

# List all data chefs
GET /api/v1/list_data_chefs
```

#### Scheduler Control

```bash
# Stop scheduler
POST /api/v1/stop_scheduler
{
    "timeout": 30
}

# Restart scheduler
POST /api/v1/restart_scheduler
{
    "timeout": 30
}
```

## Architecture

### Project Structure

```
src/ai_server/
├── config/             # Configuration management
├── handlers/           # Business logic handlers
├── initialize/         # Application initialization
├── metrics/            # Prometheus metrics
├── middlewares/        # Authentication and request middleware
├── models/             # ML models and data models
├── routers/            # API route definitions
├── schemas/            # Pydantic request/response schemas
├── services/           # Core business services
├── tasks/              # Background task definitions
├── utils/              # Utility functions
└── main.py            # Application entry point
```

### Key Components

#### 1. Model Service (`services/model_service.py`)
- Handles ML model lifecycle (create, train, save, load)
- Supports multiple algorithms: collaborative filtering, content-based, hybrid
- Manages model versioning and metadata

#### 2. Scheduler Service (`services/scheduler_service.py`)
- Manages background tasks and cron jobs
- Supports flexible scheduling (daily, weekly, custom intervals)
- Handles task dependencies and error recovery

#### 3. Data Chef Service (`services/data_chef_service.py`)
- Abstracts data source connections
- Supports multiple data formats and protocols
- Handles data transformation and validation

#### 4. Metrics Service (`metrics/`)
- Prometheus integration for monitoring
- Custom metrics for model performance
- System health and performance tracking

## Machine Learning Models

### Supported Algorithms

1. **Collaborative Filtering**
   - Matrix Factorization
   - Neural Collaborative Filtering
   - SVD++

2. **Content-Based Filtering**
   - TF-IDF similarity
   - Deep learning embeddings
   - Feature-based recommendations

3. **Hybrid Models**
   - Weighted combination
   - Switching hybrid
   - Mixed recommendations

### Model Training Examples

#### Basic Collaborative Filtering Model

```python
# Example model configuration
{
    "model_id": "cf_model_v1",
    "model_type": "collaborative_filtering",
    "algorithm": "matrix_factorization",
    "parameters": {
        "embedding_dim": 64,
        "learning_rate": 0.01,
        "regularization": 0.001,
        "epochs": 100,
        "batch_size": 256
    },
    "data_sources": {
        "interactions": "user_item_ratings",
        "users": "user_features",
        "items": "item_features"
    }
}
```

#### Advanced Neural Model

```python
{
    "model_id": "neural_cf_v2",
    "model_type": "neural_collaborative_filtering",
    "parameters": {
        "embedding_dim": 128,
        "hidden_layers": [256, 128, 64],
        "dropout_rate": 0.2,
        "activation": "relu",
        "optimizer": "adam",
        "learning_rate": 0.001,
        "epochs": 200
    }
}
```

## Monitoring & Metrics

### Prometheus Metrics

The server exposes the following metrics at `/metrics`:

- `ai_server_models_total`: Total number of trained models
- `ai_server_training_duration_seconds`: Model training time
- `ai_server_prediction_requests_total`: Number of prediction requests
- `ai_server_data_chef_executions_total`: Data pipeline executions
- `ai_server_scheduler_tasks_active`: Currently active scheduled tasks

### Health Checks

```bash
# Basic health check
GET /api/v1/health
Response: {"status": "healthy", "timestamp": "2024-01-01T12:00:00Z"}

# Detailed system status
GET /api/v1/system/status
Response: {
    "database": "connected",
    "redis": "connected",
    "scheduler": "running",
    "models_loaded": 5,
    "active_tasks": 3
}
```

## Development

### Setting up Development Environment

1. **Clone and setup:**
```bash
git clone <repository>
cd backend/ai_server
poetry install --with dev
```

2. **Run tests:**
```bash
poetry run pytest tests/
```

3. **Code formatting:**
```bash
poetry run black src/
poetry run flake8 src/
```

4. **Development server with hot reload:**
```bash
poetry run uvicorn ai_server.main:app --reload --host 0.0.0.0 --port 9999
```

### Adding New Models

1. **Create model class in `models/`:**
```python
from ai_server.models.base import BaseModel

class MyCustomModel(BaseModel):
    def __init__(self, **params):
        super().__init__(**params)

    def train(self, data):
        # Training logic
        pass

    def predict(self, user_id, item_ids):
        # Prediction logic
        pass
```

2. **Register in model factory:**
```python
# In services/model_service.py
MODEL_REGISTRY = {
    "my_custom_model": MyCustomModel,
    # ... other models
}
```

### Adding New Data Sources

1. **Create data chef class:**
```python
from ai_server.services.data_chef_base import DataChefBase

class CustomDataChef(DataChefBase):
    def fetch_data(self):
        # Data fetching logic
        pass

    def transform_data(self, data):
        # Data transformation logic
        pass
```

2. **Register the data chef:**
```python
# In services/data_chef_service.py
DATA_CHEF_TYPES = {
    "custom": CustomDataChef,
    # ... other types
}
```

## Docker Configuration

### Development Mode

The `docker-compose.dev.yml` provides:
- Hot reload with volume mounting
- Development dependencies
- Debug logging
- Port forwarding for development tools

```yaml
version: '3.8'
services:
  ai_server_dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src
      - ./config:/app/config
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
```

### Production Mode

The main `docker-compose.yml` provides:
- Optimized production image
- Health checks
- Resource limits
- Security configurations

## Troubleshooting

### Common Issues

1. **Port already in use:**
```bash
# Check what's using the port
lsof -i :9999
# Kill the process or change port in .env
```

2. **Database connection issues:**
```bash
# Verify database is running
docker ps | grep mysql
# Check connection from container
docker exec -it vrecom_ai_server ping mysql
```

3. **Model training failures:**
```bash
# Check logs
docker logs vrecom_ai_server
# Verify data chef connections
curl http://localhost:9999/api/v1/list_data_chefs
```

4. **Memory issues during training:**
```bash
# Monitor container resources
docker stats vrecom_ai_server
# Adjust batch size or model parameters
```

### Debugging

Enable debug mode:
```env
DEBUG=true
LOG_LEVEL=debug
```

View detailed logs:
```bash
# Docker logs
docker logs -f vrecom_ai_server

# Local development logs
tail -f logs/ai_server.log
```

## Performance Tuning

### Model Training Optimization

1. **Batch Size**: Adjust based on available memory
2. **Learning Rate**: Use learning rate scheduling
3. **Regularization**: Prevent overfitting
4. **Early Stopping**: Stop training when validation loss plateaus

### System Performance

1. **Redis Caching**: Enable for frequently accessed data
2. **Database Connection Pooling**: Configure optimal pool size
3. **Async Operations**: Use async/await for I/O operations
4. **Resource Limits**: Set appropriate CPU/memory limits in Docker

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Run the test suite (`poetry run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Create a Pull Request

## Support

- **Documentation**: Check the `/docs` endpoint when server is running
- **Issues**: Create an issue on GitHub
- **API Reference**: Visit `/docs` for interactive API documentation
- **Metrics**: Monitor at `/metrics` endpoint for Prometheus integration
