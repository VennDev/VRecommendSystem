# VRecommendSystem

## 📋 Tổng quan

VRecommendSystem là hệ thống recommendation engine mạnh mẽ với kiến trúc microservices, hỗ trợ đa dạng thuật toán machine learning và khả năng mở rộng cao.

## 🏗️ Kiến trúc hệ thống

- **API Server** (Go/Fiber): Backend API gateway xử lý authentication và routing
- **AI Server** (Python/FastAPI): ML engine với support cho collaborative filtering
- **Frontend** (React/TypeScript): Dashboard quản lý và giám sát
- **Redis**: Caching layer
- **Prometheus**: Monitoring và metrics

## 🚀 Khởi động nhanh

### Sử dụng Docker (Khuyến nghị)

```bash
# 1. Clone repository
git clone <repository-url>
cd VRecommendSystem

# 2. Copy và cấu hình environment
cp .env.example .env
cp frontend/project/.env.example frontend/project/.env

# 3. Khởi động toàn bộ hệ thống
./docker-start.sh up
```

**Access URLs:**
- Frontend: http://localhost:5173
- API Server: http://localhost:2030
- AI Server: http://localhost:9999
- Prometheus: http://localhost:9090

Chi tiết setup Docker xem tại: [DOCKER_SETUP.md](./DOCKER_SETUP.md)

### Development Setup (Không dùng Docker)

#### Backend - API Server (Go)

```bash
cd backend/api_server
cp example-env .env
# Cấu hình .env theo nhu cầu
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

## ⚙️ Cấu hình Port

Tất cả port được quản lý tập trung tại file `.env`:

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

Để thay đổi port:
1. Cập nhật file `.env`
2. Restart services: `./docker-start.sh restart`

## 📦 Services

### API Server (Port 2030)

- Authentication & Authorization
- Request routing
- Redis caching
- Proxy requests đến AI Server

**Health check:** `GET http://localhost:2030/api/v1/ping`

### AI Server (Port 9999)

- Model training & management
- Recommendation engine
- Data chefs (ETL pipelines)
- Scheduler cho batch jobs

**Health check:** `GET http://localhost:9999/api/v1/health`

### Frontend (Port 5173)

- Dashboard quản lý models
- Task scheduler interface
- Logs viewer
- Metrics visualization

## 📝 Docker Commands

```bash
# Khởi động
./docker-start.sh up

# Dừng
./docker-start.sh down

# Build lại
./docker-start.sh build

# Xem logs
./docker-start.sh logs

# Xem logs của service cụ thể
./docker-start.sh logs api_server
./docker-start.sh logs ai_server

# Kiểm tra status
./docker-start.sh status

# Dọn dẹp hoàn toàn
./docker-start.sh clean
```

## 🛠️ Development

### Hot reload được enable cho:

- Frontend: Vite HMR
- AI Server: Volume mount cho `/src`
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

Prometheus metrics có sẵn tại: http://localhost:9090

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
