# VRecommendSystem API Collection

This directory contains Bruno API collections for testing VRecommendSystem endpoints.

## 📋 Overview

Bruno is a fast, git-friendly, open-source API client. This collection provides ready-to-use API requests for all VRecommendSystem endpoints.

## 🚀 Getting Started

### 1. Install Bruno

Download and install Bruno from: https://www.usebruno.com/

### 2. Open Collection

1. Launch Bruno
2. Click "Open Collection"
3. Navigate to this directory (`vrecom_api/`)
4. Click "Select Folder"

### 3. Configure Base URLs

The collection uses the following default URLs:
- API Server: `http://localhost:2030`
- AI Server: `http://localhost:9999`

Update the URLs in individual requests if your ports differ.

## 📁 Collection Structure

```
vrecom_api/
├── api_server/              # API Server endpoints
│   ├── auth/               # Authentication (Google OAuth)
│   │   ├── login_google.bru
│   │   ├── check_auth_status.bru
│   │   └── logout.bru
│   ├── recommendations/    # Get recommendations
│   │   └── recommend.bru
│   └── ping.bru           # Health check
│
└── ai_server/              # AI Server endpoints
    ├── models/             # Model management
    │   ├── create_model.bru
    │   ├── list_models.bru
    │   ├── get_model_info.bru
    │   └── delete_model.bru
    ├── tasks/              # Task scheduler
    │   ├── add_model_task.bru
    │   ├── list_tasks.bru
    │   ├── remove_model_task.bru
    │   ├── rename_task.bru
    │   └── update_task_interval.bru
    ├── data_chefs/         # Data pipelines
    │   ├── create_data_chef_from_csv.bru
    │   ├── create_data_chef_from_sql.bru
    │   ├── list_data_chefs.bru
    │   ├── get_data_chef.bru
    │   └── delete_data_chef.bru
    ├── scheduler/          # Scheduler control
    │   ├── stop_scheduler.bru
    │   └── restart_scheduler.bru
    ├── metrics/            # System metrics
    │   ├── get_total_running_tasks.bru
    │   ├── get_total_activated_tasks.bru
    │   ├── get_total_activating_models.bru
    │   ├── get_scheduler_status.bru
    │   └── get_server_logs.bru
    ├── recommendations/    # Get recommendations
    │   └── recommend.bru
    ├── health.bru         # Health check
    └── main.bru           # Root endpoint
```

## 🧪 Testing Workflow

### 1. Start Services

```bash
# Start all services with Docker
./docker-start.sh up

# Or start individually
cd backend/api_server && go run main.go
cd backend/ai_server && poetry run server
```

### 2. Test Health Endpoints

- API Server: `GET http://localhost:2030/api/v1/ping`
- AI Server: `GET http://localhost:9999/api/v1/health`

### 3. Create a Model

Use `ai_server/models/create_model.bru`:

```json
{
  "model_id": "my_model",
  "model_type": "svd",
  "model_config": {
    "n_factors": 100,
    "n_epochs": 20,
    "lr_all": 0.005,
    "reg_all": 0.02
  }
}
```

### 4. Create Data Chef

Use `ai_server/data_chefs/create_data_chef_from_csv.bru` or SQL variant.

### 5. Add Training Task

Use `ai_server/tasks/add_model_task.bru`:

```json
{
  "task_name": "daily_training",
  "model_id": "my_model",
  "interactions_data_chef_id": "interactions_chef",
  "interval": "daily"
}
```

### 6. Get Recommendations

Use `ai_server/recommendations/recommend.bru`:
```
GET /api/v1/recommend/user123/my_model/10
```

## 🔐 Authentication

### API Server (OAuth)

The API Server uses Google OAuth for authentication:

1. Access `auth/login_google.bru` to initiate OAuth flow
2. Complete Google authentication in browser
3. Session cookie will be stored automatically
4. Use `auth/check_auth_status.bru` to verify session

### AI Server

The AI Server requires authentication token in request headers:

```
Authorization: Bearer <your-token>
```

## 📝 Common Request Examples

### Create SVD Model

```json
POST /api/v1/create_model
{
  "model_id": "svd_model",
  "model_type": "svd",
  "model_config": {
    "n_factors": 100,
    "n_epochs": 20
  }
}
```

### Create NMF Model

```json
POST /api/v1/create_model
{
  "model_id": "nmf_model",
  "model_type": "nmf",
  "model_config": {
    "n_factors": 50,
    "n_epochs": 15
  }
}
```

### Create Data Chef from CSV

```json
POST /api/v1/create_data_chef_from_csv
{
  "data_chef_id": "csv_interactions",
  "file_path": "/data/interactions.csv",
  "user_column": "user_id",
  "item_column": "item_id",
  "rating_column": "rating"
}
```

### Schedule Training Task

```json
POST /api/v1/add_model_task
{
  "task_name": "hourly_training",
  "model_id": "my_model",
  "interactions_data_chef_id": "interactions_chef",
  "interval": "hourly"
}
```

## 🔄 Task Intervals

Available intervals for scheduled tasks:
- `hourly`: Every hour
- `daily`: Every day at midnight
- `weekly`: Every week
- `monthly`: Every month
- Custom cron expressions

## 📊 Monitoring

### Check Metrics

- Total running tasks: `GET /api/v1/get_total_running_tasks`
- Active models: `GET /api/v1/get_total_activating_models`
- Scheduler status: `GET /api/v1/get_scheduler_status`
- Server logs: `GET /api/v1/get_server_logs?limit=100`

### Prometheus

Access Prometheus metrics at: http://localhost:9090

## 🐛 Troubleshooting

### Connection Refused

- Verify services are running: `./docker-start.sh status`
- Check port configuration in `.env`
- View service logs: `./docker-start.sh logs <service_name>`

### Authentication Errors

- Ensure you've completed OAuth flow for API Server
- Check token is present in request headers for AI Server
- Verify Redis is running for session storage

### Model Training Fails

- Check data chef is properly configured
- Verify CSV/database connection
- Review AI Server logs: `./docker-start.sh logs ai_server`

## 📚 Additional Resources

- [Bruno Documentation](https://docs.usebruno.com/)
- [Project README](../README.md)
- [Docker Setup Guide](../DOCKER_SETUP.md)
- [System Architecture](../diagrams/System.drawio.png)

## 💡 Tips

1. **Environment Variables**: Use Bruno's environment feature to switch between dev/staging/prod
2. **Collections**: Organize related requests into folders
3. **Pre-request Scripts**: Add authentication token generation if needed
4. **Tests**: Add response assertions for automated testing
5. **Version Control**: Bruno collections are git-friendly - commit them!
