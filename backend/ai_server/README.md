# AI Server - VRecommendation System

A high-performance machine learning service built with FastAPI that powers intelligent recommendations through advanced algorithms, real-time training, and flexible data integration. The AI Server handles all machine learning operations including model training, prediction serving, and data pipeline management.

## Overview

The AI Server is the core machine learning component of the VRecommendation system. It provides:

- Multiple recommendation algorithms (SVD, collaborative filtering, matrix factorization)
- Automated model training with configurable schedules
- Real-time and batch prediction APIs
- Multi-source data ingestion (CSV, SQL, NoSQL, APIs, Kafka)
- Model versioning and metadata tracking
- Prometheus metrics integration
- Task scheduling and background job management

## Features

### Machine Learning Capabilities

- **Multiple Algorithms**: Support for SVD, matrix factorization, and collaborative filtering
- **Incremental Learning**: Train models incrementally from streaming data sources
- **Hyperparameter Tuning**: Configurable model parameters for optimization
- **Model Persistence**: Automatic model saving with versioning
- **Metadata Tracking**: Comprehensive training statistics and model information

### Data Integration

- **CSV Files**: Local file processing with chunked reading for large files
- **SQL Databases**: MySQL, PostgreSQL, and other SQL-compatible databases
- **NoSQL Databases**: MongoDB and document stores
- **REST APIs**: Paginated and non-paginated API data fetching
- **Kafka Streams**: Real-time data consumption from Kafka topics
- **Data Transformation**: Automatic column renaming and data validation

### System Management

- **Task Scheduler**: Flexible scheduling for automated model retraining
- **Background Jobs**: Asynchronous task execution with monitoring
- **Health Monitoring**: Comprehensive health checks and status endpoints
- **Prometheus Metrics**: Built-in metrics collection for monitoring
- **Logging**: Structured logging with configurable levels

## Architecture

### Technology Stack

- **Framework**: FastAPI 0.104.1
- **Machine Learning**: NumPy, Pandas, Scikit-learn, SciPy
- **Data Processing**: Pandas for data manipulation
- **Task Scheduling**: APScheduler for job scheduling
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Monitoring**: Prometheus client for metrics
- **Database**: Kafka consumer, SQL/NoSQL connectors

### Project Structure

```
backend/ai_server/
├── src/
│   └── ai_server/
│       ├── handlers/              # Business logic handlers
│       │   ├── create_data_chef_handler.py
│       │   ├── model_handler.py
│       │   └── task_handler.py
│       │
│       ├── models/                # ML model implementations
│       │   ├── base_model.py      # Base class for all models
│       │   ├── svd_model.py       # SVD algorithm
│       │   └── collaborative_filtering_model.py
│       │
│       ├── routers/               # API route definitions
│       │   ├── data_chef_routes.py
│       │   ├── model_routes.py
│       │   ├── recommend_routes.py
│       │   └── task_routes.py
│       │
│       ├── services/              # Core business services
│       │   ├── data_chef_service.py
│       │   ├── model_service.py
│       │   ├── recommend_service.py
│       │   └── scheduler_service.py
│       │
│       ├── tasks/                 # Background task implementations
│       │   ├── model_trainer_task.py
│       │   └── base_task.py
│       │
│       ├── utils/                 # Utility functions
│       │   ├── result_processing.py
│       │   └── validators.py
│       │
│       ├── metrics/               # Prometheus metrics
│       │   ├── model_metrics.py
│       │   └── scheduler_metrics.py
│       │
│       ├── middlewares/           # Custom middleware
│       │   └── auth_middleware.py
│       │
│       └── main.py                # Application entry point
│
├── config/                        # Configuration files
│   ├── local.yaml                 # Main configuration
│   └── restaurant_data.yaml       # Data source definitions
│
├── models/                        # Trained model storage
│   ├── {model_id}.pkl             # Serialized model
│   ├── {model_id}_config.json     # Model configuration
│   └── {model_id}_metadata.json   # Training metadata
│
├── tasks/                         # Task definition files
│   └── {task_name}.json           # Scheduled task configs
│
├── data/                          # Data storage directory
│   └── uploads/                   # Uploaded CSV files
│
├── logs/                          # Application logs
├── tests/                         # Test suite
├── Dockerfile                     # Production Docker image
├── pyproject.toml                 # Poetry dependencies
└── README.md                      # This file
```

## Quick Start

### Using Docker (Recommended)

1. **Start from project root**:

```bash
cd VRecommendation
docker-compose up ai_server -d
```

2. **Verify the service**:

```bash
curl http://localhost:9999/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-23T10:00:00Z"
}
```

3. **Access API documentation**:

- Swagger UI: http://localhost:9999/docs
- ReDoc: http://localhost:9999/redoc

### Local Development Setup

1. **Install Poetry** (if not already installed):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Install dependencies**:

```bash
cd backend/ai_server
poetry install
```

3. **Configure environment**:

```bash
cp example-env .env
```

Edit `.env` with your configuration:

```env
# Server
HOST=0.0.0.0
PORT=9999
DEBUG=true

# Database connections (optional)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=your_user
MONGODB_PASSWORD=your_password

# Kafka (optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=ai_server_group
```

4. **Run the server**:

```bash
poetry run server
```

The server will start at http://localhost:9999

## Configuration

### Environment Variables

The AI Server uses environment variables for configuration:

```env
# Server Configuration
HOST=0.0.0.0                    # Bind address
PORT=9999                        # Server port
DEBUG=false                      # Debug mode
LOG_LEVEL=info                   # Logging level

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=password
MYSQL_DATABASE=database_name

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_GROUP_ID=vrecom_ai_server_group
KAFKA_DEFAULT_TOPIC=interactions

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### Data Chef Configuration

Data sources are configured in `config/restaurant_data.yaml`:

```yaml
# CSV Data Source
csv_data:
  type: csv
  path: /app/data/uploads/interactions.csv
  rename_columns: "userId:user_id,itemId:item_id,rating:rating"

# SQL Data Source
sql_data:
  type: sql
  query: "SELECT user_id, item_id, rating FROM interactions"
  rename_columns: ""

# NoSQL Data Source
nosql_data:
  type: nosql
  database: ecommerce
  collection: interactions
  rename_columns: "userId:user_id,itemId:item_id"

# Kafka Data Source
kafka_data:
  type: messaging_queue
  brokers: kafka:9093
  topic: interactions
  group_id: model_consumer_group
  rename_columns: ""
```

### Model Configuration

Models are configured in JSON files in the `models/` directory:

```json
{
  "model_name": "Production Recommendation Model",
  "model_id": "prod_model",
  "type": "svd",
  "algorithm": "svd",
  "hyperparameters": {
    "n_components": 50,
    "algorithm": "randomized",
    "n_iter": 10,
    "random_state": 42,
    "tol": 0.0
  },
  "message": "Main production model for user recommendations"
}
```

### Task Configuration

Training tasks are configured in JSON files in the `tasks/` directory:

```json
{
  "task_name": "hourly_retrain",
  "model_id": "prod_model",
  "interactions_data_chef_id": "kafka_data",
  "item_features_data_chef_id": null,
  "user_features_data_chef_id": null,
  "interval": 3600
}
```

- `interval`: Training frequency in seconds (minimum: 10)
- `interactions_data_chef_id`: Required data chef for user-item interactions
- `item_features_data_chef_id`: Optional data chef for item features
- `user_features_data_chef_id`: Optional data chef for user features

## API Reference

### Base URL

```
http://localhost:9999/api/v1
```

### Health & Status

#### Health Check

```http
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-23T10:00:00Z"
}
```

### Model Management

#### List All Models

```http
GET /api/v1/list_models
```

Response:
```json
{
  "models": [
    {
      "model_id": "prod_model",
      "model_name": "Production Model",
      "type": "svd",
      "created_at": "2024-11-23T09:00:00Z",
      "last_trained": "2024-11-23T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### Get Model Details

```http
GET /api/v1/get_model?model_id=prod_model
```

Response:
```json
{
  "model_id": "prod_model",
  "model_type": "SVDRecommendationModel",
  "hyperparameters": {
    "n_components": 50,
    "n_iter": 10
  },
  "training_stats": {
    "n_users": 1000,
    "n_items": 500,
    "n_interactions": 5000,
    "sparsity": 0.99
  }
}
```

#### Delete Model

```http
DELETE /api/v1/delete_model?model_id=old_model
```

Response:
```json
{
  "message": "Model deleted successfully",
  "model_id": "old_model"
}
```

### Data Chef Management

#### List All Data Chefs

```http
GET /api/v1/list_data_chefs
```

Response:
```json
{
  "data_chefs": [
    {
      "name": "csv_data",
      "type": "csv",
      "path": "/app/data/uploads/interactions.csv"
    },
    {
      "name": "kafka_data",
      "type": "messaging_queue",
      "topic": "interactions"
    }
  ],
  "total": 2
}
```

#### Create CSV Data Chef

```http
POST /api/v1/create_data_chef_from_csv
Content-Type: application/json

{
  "name": "my_csv_data",
  "path": "/app/data/uploads/data.csv",
  "rename_columns": "userId:user_id,itemId:item_id,rating:rating"
}
```

#### Create SQL Data Chef

```http
POST /api/v1/create_data_chef_from_sql
Content-Type: application/json

{
  "name": "my_sql_data",
  "query": "SELECT user_id, item_id, rating FROM interactions WHERE created_at > NOW() - INTERVAL 30 DAY",
  "rename_columns": ""
}
```

#### Create NoSQL Data Chef

```http
POST /api/v1/create_data_chef_from_nosql
Content-Type: application/json

{
  "name": "my_mongo_data",
  "database": "ecommerce",
  "collection": "interactions",
  "rename_columns": "userId:user_id,itemId:item_id"
}
```

#### Delete Data Chef

```http
DELETE /api/v1/delete_data_chef?name=old_data_chef
```

### Task Management

#### List All Tasks

```http
GET /api/v1/list_tasks
```

Response:
```json
{
  "tasks": [
    {
      "task_name": "hourly_retrain",
      "model_id": "prod_model",
      "interval": 3600,
      "next_run": "2024-11-23T11:00:00Z",
      "status": "scheduled"
    }
  ],
  "total": 1
}
```

#### Add Model Task

```http
POST /api/v1/add_model_task
Content-Type: application/json

{
  "task_name": "my_training_task",
  "model_id": "my_model",
  "interactions_data_chef_id": "kafka_data",
  "item_features_data_chef_id": null,
  "user_features_data_chef_id": null,
  "interval": 3600
}
```

Response:
```json
{
  "message": "Task added successfully",
  "task_name": "my_training_task"
}
```

#### Remove Model Task

```http
DELETE /api/v1/remove_model_task?task_name=my_training_task
```

### Scheduler Control

#### Get Scheduler Status

```http
GET /api/v1/get_scheduler_status
```

Response:
```json
{
  "status": "running",
  "active_jobs": 3,
  "uptime_seconds": 3600
}
```

#### Stop Scheduler

```http
POST /api/v1/stop_scheduler
Content-Type: application/json

{
  "timeout": 30
}
```

#### Restart Scheduler

```http
POST /api/v1/restart_scheduler
Content-Type: application/json

{
  "timeout": 30
}
```

### Recommendations

#### Get Recommendations

```http
POST /api/v1/recommend
Content-Type: application/json

{
  "user_id": "user123",
  "model_id": "prod_model",
  "n": 10
}
```

Response:
```json
{
  "user_id": "user123",
  "model_id": "prod_model",
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

## Machine Learning Models

### SVD (Singular Value Decomposition)

The primary algorithm for collaborative filtering. SVD decomposes the user-item interaction matrix into latent factors.

**Hyperparameters**:

```json
{
  "n_components": 50,        // Number of latent factors
  "algorithm": "randomized", // "randomized" or "arpack"
  "n_iter": 10,             // Number of iterations for randomized SVD
  "random_state": 42,       // Random seed for reproducibility
  "tol": 0.0                // Tolerance for convergence
}
```

**When to use**: Best for large-scale collaborative filtering with sparse data.

### Model Training Process

1. **Data Loading**: Fetch data from configured data chef
2. **Preprocessing**: Convert to user-item matrix format
3. **Training**: Apply SVD algorithm to learn latent factors
4. **Validation**: Calculate training statistics and metrics
5. **Persistence**: Save model, configuration, and metadata
6. **Metrics**: Record training time and performance metrics

### Training Statistics

After training, the system tracks:

- `n_users`: Number of unique users in training data
- `n_items`: Number of unique items in training data
- `n_interactions`: Total number of user-item interactions
- `sparsity`: Percentage of empty cells in the matrix
- `density`: Percentage of filled cells in the matrix
- `avg_interactions_per_user`: Average interactions per user
- `avg_interactions_per_item`: Average interactions per item
- `mean_rating`: Average rating value
- `std_rating`: Standard deviation of ratings
- `min_rating`: Minimum rating value
- `max_rating`: Maximum rating value

## Data Processing

### Data Chef System

The Data Chef system provides a unified interface for accessing multiple data sources.

#### CSV Processing

```python
# Automatic chunked reading for large files
# Configurable batch size
# Handles missing values and data cleaning
```

Configuration:
```yaml
csv_data:
  type: csv
  path: /app/data/file.csv
  rename_columns: "oldName:newName"
```

#### SQL Databases

```python
# Connection pooling for performance
# Parameterized queries for security
# Automatic retry on connection failures
```

Configuration:
```yaml
sql_data:
  type: sql
  query: "SELECT * FROM table"
  rename_columns: ""
```

#### Kafka Streaming

```python
# Real-time message consumption
# Automatic offset management
# Configurable timeout and batch size
```

Configuration:
```yaml
kafka_data:
  type: messaging_queue
  brokers: kafka:9093
  topic: interactions
  group_id: consumer_group
  rename_columns: ""
```

**Important**: Kafka consumers read incrementally from the last committed offset. To retrain with all historical data, reset the consumer group offset:

```bash
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group consumer_group \
  --reset-offsets \
  --to-earliest \
  --topic interactions \
  --execute
```

### Data Transformation

Automatic column renaming for data standardization:

```yaml
rename_columns: "userId:user_id,itemId:item_id,rating:rating"
```

The system expects these standard columns:
- `user_id`: User identifier
- `item_id`: Item identifier
- `rating`: Interaction strength (numeric)
- `timestamp`: Interaction time (optional)

## Task Scheduling

### Scheduling Intervals

The system supports two scheduling modes:

**Minutely Scheduling** (for intervals < 60 seconds):
```json
{
  "interval": 30  // Runs every minute at second 30
}
```

**Cyclic Scheduling** (for intervals >= 60 seconds):
```json
{
  "interval": 3600  // Runs every 3600 seconds (1 hour)
}
```

### Task Execution Flow

1. **Trigger**: Scheduler triggers task at specified interval
2. **Validation**: Check if model is already training
3. **Thread Creation**: Spawn background thread for training
4. **Data Loading**: Create data generators from data chefs
5. **Batch Processing**: Process data in batches
6. **Model Training**: Train model with accumulated data
7. **Finalization**: Save trained model and metadata
8. **Cleanup**: Release resources and update status

### Monitoring Training Tasks

View training logs:

```bash
docker logs vrecom_ai_server 2>&1 | grep "Training"
```

Common log messages:
- "Training task triggered": Task started
- "Background training started": Training thread created
- "Training initialization completed": Setup successful
- "Batch N processed": Progress update
- "Training completed successfully": Training finished
- "Model saved successfully": Model persisted

## Monitoring & Metrics

### Prometheus Metrics

The server exposes metrics at `/metrics` endpoint for Prometheus scraping.

**Model Metrics**:
- `ai_server_models_total`: Total number of models
- `ai_server_model_training_duration_seconds`: Training time per model
- `ai_server_model_predictions_total`: Number of predictions served
- `ai_server_model_training_errors_total`: Training failures

**Scheduler Metrics**:
- `ai_server_scheduler_tasks_total`: Total scheduled tasks
- `ai_server_scheduler_tasks_running`: Currently running tasks
- `ai_server_scheduler_task_execution_duration_seconds`: Task execution time

**Data Chef Metrics**:
- `ai_server_data_chef_executions_total`: Data chef invocations
- `ai_server_data_chef_errors_total`: Data chef failures
- `ai_server_data_chef_records_processed_total`: Records processed

### Health Monitoring

The health endpoint provides system status:

```bash
curl http://localhost:9999/api/v1/health
```

Monitor continuously:

```bash
watch -n 5 'curl -s http://localhost:9999/api/v1/health'
```

### Logging

Structured logging with configurable levels:

```python
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

View logs:

```bash
# Docker logs
docker logs -f vrecom_ai_server

# Filter by level
docker logs vrecom_ai_server 2>&1 | grep ERROR

# Search for specific events
docker logs vrecom_ai_server 2>&1 | grep "model_id"
```

## Development

### Running Tests

```bash
cd backend/ai_server

# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_models.py -v

# Run with coverage
poetry run pytest tests/ --cov=ai_server --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code with Black
poetry run black src/

# Lint with Flake8
poetry run flake8 src/

# Type checking with MyPy
poetry run mypy src/

# Sort imports
poetry run isort src/
```

### Adding a New ML Algorithm

1. **Create model class**:

```python
# src/ai_server/models/my_algorithm.py
from ai_server.models.base_model import BaseRecommendationModel
import numpy as np

class MyAlgorithmModel(BaseRecommendationModel):
    def __init__(self, **hyperparameters):
        super().__init__(**hyperparameters)
        self.param1 = hyperparameters.get('param1', 10)
        
    def fit(self, interactions_df, item_features=None, user_features=None):
        """Train the model with interaction data."""
        # Convert dataframe to matrix
        self.user_ids = interactions_df['user_id'].unique()
        self.item_ids = interactions_df['item_id'].unique()
        
        # Create user-item matrix
        matrix = self._create_interaction_matrix(interactions_df)
        
        # Training logic here
        self.trained = True
        
    def predict(self, user_id, n=5):
        """Generate top-N recommendations for a user."""
        if not self.trained:
            raise ValueError("Model not trained")
            
        # Prediction logic here
        predictions = []
        return predictions
```

2. **Register in model service**:

```python
# src/ai_server/services/model_service.py
from ai_server.models.my_algorithm import MyAlgorithmModel

MODEL_REGISTRY = {
    'svd': SVDRecommendationModel,
    'my_algorithm': MyAlgorithmModel,
    # ... other models
}
```

3. **Add tests**:

```python
# tests/test_my_algorithm.py
def test_my_algorithm_training():
    model = MyAlgorithmModel(param1=20)
    # Test implementation
```

### Adding a New Data Source

1. **Create data chef function**:

```python
# src/ai_server/services/data_chef_service.py
def _cook_my_source(param1, param2):
    """Fetch data from custom source."""
    try:
        # Connection logic
        connection = create_connection(param1, param2)
        
        # Data fetching
        for record in fetch_records(connection):
            yield {
                'user_id': record['user'],
                'item_id': record['item'],
                'rating': record['value']
            }
    finally:
        connection.close()
```

2. **Add to data type enum**:

```python
class DataType(Enum):
    CSV = "csv"
    SQL = "sql"
    MY_SOURCE = "my_source"
```

3. **Add to router**:

```python
@router.post("/create_data_chef_from_my_source")
async def create_data_chef_my_source(config: MySourceConfig):
    # Implementation
    pass
```

## Docker Configuration

### Development Mode

The development Docker setup includes:

- Volume mounts for hot reload
- Debug logging enabled
- Development dependencies
- Port 9999 exposed

```bash
docker-compose -f docker-compose.dev.yml up ai_server
```

### Production Mode

Production configuration:

- Optimized Python image
- Production dependencies only
- Health checks configured
- Resource limits set

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY . .
CMD ["poetry", "run", "server"]
```

### Resource Limits

Configure in `docker-compose.yml`:

```yaml
ai_server:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

## Troubleshooting

### Model Training Fails

**Symptom**: Training completes but no recommendations generated

**Solution**: Check if user exists in training data

```bash
# View model metadata
docker exec vrecom_ai_server cat models/model_id_metadata.json

# Check training stats
curl http://localhost:9999/api/v1/get_model?model_id=model_id
```

### Kafka Consumer Not Reading Data

**Symptom**: Training logs show 0 batches processed

**Causes**:
1. Consumer group offset already at end
2. No new messages in topic
3. Wrong topic configuration

**Solution**:

```bash
# Check consumer group status
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group your_group \
  --describe

# Reset offset if needed
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group your_group \
  --reset-offsets \
  --to-earliest \
  --topic your_topic \
  --execute
```

### High Memory Usage

**Symptom**: Container OOM killed or slow performance

**Solution**:

1. Reduce batch size in data chef configuration
2. Lower `n_components` in model hyperparameters
3. Increase container memory limits
4. Clear old model files

```bash
# Remove old models
docker exec vrecom_ai_server rm -f models/old_model*

# Restart with more memory
docker-compose up -d --force-recreate ai_server
```

### Database Connection Errors

**Symptom**: Data chef fails with connection timeout

**Solution**:

1. Verify database credentials in `.env`
2. Check network connectivity from container
3. Verify firewall rules

```bash
# Test MySQL connection from container
docker exec vrecom_ai_server python -c "
import pymysql
conn = pymysql.connect(
    host='mysql_host',
    user='user',
    password='pass',
    database='db'
)
print('Connected successfully')
"

# Test MongoDB connection
docker exec vrecom_ai_server python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://user:pass@host:27017/')
print(client.server_info())
"
```

### Scheduler Not Running Tasks

**Symptom**: No training logs, tasks not executing

**Solution**:

```bash
# Check scheduler status
curl http://localhost:9999/api/v1/get_scheduler_status

# Restart scheduler
curl -X POST http://localhost:9999/api/v1/restart_scheduler \
  -H "Content-Type: application/json" \
  -d '{"timeout": 30}'

# Check for task configuration errors
docker exec vrecom_ai_server ls -la tasks/
docker exec vrecom_ai_server cat tasks/task_name.json
```

## Performance Optimization

### Training Performance

1. **Batch Size**: Adjust in data chef implementation
2. **Hyperparameters**: Lower `n_components` and `n_iter` for faster training
3. **Data Sampling**: Use subset of data for frequent retraining
4. **Parallel Processing**: Use multiple workers if needed

### Prediction Performance

1. **Model Caching**: Keep trained models in memory
2. **Batch Predictions**: Request multiple users at once
3. **Pre-computation**: Cache common recommendations

### Resource Management

1. **Memory**: Monitor with `docker stats`
2. **CPU**: Adjust number of components in SVD
3. **Disk**: Regularly clean old model files
4. **Network**: Use connection pooling for databases

## Security Best Practices

### Production Deployment

- Change default JWT secrets
- Use strong database passwords
- Enable HTTPS for external access
- Implement rate limiting
- Use environment-specific configurations
- Enable audit logging
- Restrict network access
- Use secrets management systems

### Data Protection

- Encrypt sensitive data at rest
- Use secure database connections (SSL/TLS)
- Sanitize user inputs
- Implement data retention policies
- Regular security audits

## Support

For issues, questions, or contributions:

- GitHub Issues: Report bugs and request features
- Documentation: Check `/docs` endpoint when server is running
- API Reference: Visit `/docs` for interactive Swagger UI
- Logs: Use `docker logs` for debugging
- Metrics: Monitor at `/metrics` endpoint

## License

This component is part of the VRecommendation system. See the main project LICENSE.txt file for details.