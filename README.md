# VRecommendSystem

## 📋 Overview

VRecommendSystem is a powerful recommendation engine with microservices architecture, supporting diverse machine learning algorithms and high scalability.

## 🏗️ System Architecture

- **API Server** (Go/Fiber): Backend API gateway handling authentication and routing
- **AI Server** (Python/FastAPI): ML engine with support for collaborative filtering
- **Frontend** (React/TypeScript): Management and monitoring dashboard
- **Redis**: Caching layer
- **Prometheus**: Monitoring and metrics

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd VRecommendSystem

# 2. Copy and configure environment
cp .env.example .env
cp frontend/project/.env.example frontend/project/.env

# 3. Start all services
./docker-start.sh up
```

**Access URLs:**
- Frontend: http://localhost:5173
- API Server: http://localhost:2030
- AI Server: http://localhost:9999
- Prometheus: http://localhost:9090

For detailed Docker setup, see: [DOCKER_SETUP.md](./DOCKER_SETUP.md)

### Development Setup (Without Docker)

#### Backend - API Server (Go)

```bash
cd backend/api_server
cp example-env .env
# Configure .env as needed
go mod download
go run main.go
```

#### Backend - AI Server (Python)

```bash
cd backend/ai_server
poetry install
poetry run server
```

#### Frontend

```bash
cd frontend/project
npm install
npm run dev
```

## ⚙️ Port Configuration

All ports are centrally managed in the `.env` file:

```env
# API Server
API_SERVER_PORT=2030

# AI Server
AI_SERVER_PORT=9999

# Frontend
FRONTEND_PORT=5173

# Redis
REDIS_PORT=6379

# Prometheus
PROMETHEUS_PORT=9090
```

To change ports:
1. Update the `.env` file
2. Restart services: `./docker-start.sh restart`

## 📦 Services

### API Server (Port 2030)

- Authentication & Authorization
- Request routing
- Redis caching
- Proxy requests to AI Server

**Health check:** `GET http://localhost:2030/api/v1/ping`

### AI Server (Port 9999)

- Model training & management
- Recommendation engine
- Data chefs (ETL pipelines)
- Scheduler for batch jobs

**Health check:** `GET http://localhost:9999/api/v1/health`

### Frontend (Port 5173)

- Model management dashboard
- Task scheduler interface
- Logs viewer
- Metrics visualization

## 📝 Docker Commands

```bash
# Start services
./docker-start.sh up

# Stop services
./docker-start.sh down

# Rebuild images
./docker-start.sh build

# View logs
./docker-start.sh logs

# View logs for specific service
./docker-start.sh logs api_server
./docker-start.sh logs ai_server

# Check status
./docker-start.sh status

# Clean everything
./docker-start.sh clean
```

## 🛠️ Development

### Hot reload enabled for:

- Frontend: Vite HMR
- AI Server: Volume mount for `/src`
- API Server: Rebuild required

### Testing

```bash
# API Server
cd backend/api_server
go test ./...

# AI Server
cd backend/ai_server
poetry run pytest
```

## 📊 Monitoring

Prometheus metrics available at: http://localhost:9090

**AI Server Metrics:**
- Model training time
- Task execution duration
- Active models count
- Scheduler status

## 🔐 Environment Variables

### API Server
- `STATUS_DEV`: dev/test/prod
- `HOST_ADDRESS`: Bind address
- `HOST_PORT`: Port number
- `AI_SERVER_URL`: AI Server URL
- `REDIS_HOST`, `REDIS_PORT`: Redis config

### AI Server
- `HOST`: Bind address
- `PORT`: Port number
- `MYSQL_*`: MySQL configuration
- `MONGODB_*`: MongoDB configuration

### Frontend
- `VITE_API_SERVER_URL`: API Server URL
- `VITE_AI_SERVER_URL`: AI Server URL
- `VITE_SUPABASE_*`: Supabase config

## 🧪 API Testing

Bruno API collection is available in the `vrecom_api/` directory for testing all endpoints.

**Available Collections:**
- `api_server/`: API Server endpoints (Authentication, Ping)
- `ai_server/`: AI Server endpoints (Models, Tasks, Data Chefs, Scheduler, Metrics)

To use:
1. Install [Bruno](https://www.usebruno.com/)
2. Open the `vrecom_api` folder as a collection
3. Start testing endpoints

## 📚 Documentation

- [Docker Setup Guide](./DOCKER_SETUP.md)
- [System Architecture](./diagrams/System.drawio.png)
- [API Documentation](./vrecom_api/)

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

See [LICENSE.txt](./LICENSE.txt)
