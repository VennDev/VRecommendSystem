# Docker Setup Guide - VRecommendation System

## 📋 Tổng quan

Hệ thống VRecommendation được thiết kế để chạy hoàn toàn trên Docker với các service sau:
- **API Server** (Go): Port 2030
- **AI Server** (Python): Port 9999
- **Frontend** (React + Vite): Port 5173
- **Redis**: Port 6379
- **Prometheus**: Port 9090

## 🚀 Khởi động nhanh

### 1. Chuẩn bị môi trường

```bash
# Copy file .env mẫu
cp .env.example .env

# Copy file .env cho frontend
cp frontend/project/.env.example frontend/project/.env
```

### 2. Chỉnh sửa cấu hình

Mở file `.env` và cập nhật các giá trị cần thiết:

```env
# Ports
API_SERVER_PORT=2030
AI_SERVER_PORT=9999
FRONTEND_PORT=5173

# Database (nếu cần)
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=shop
```

### 3. Khởi động hệ thống

```bash
# Sử dụng script tiện lợi
./docker-start.sh up

# Hoặc dùng docker-compose trực tiếp
docker-compose up -d
```

## 📝 Các lệnh quản lý

### Khởi động services

```bash
./docker-start.sh up
# hoặc
docker-compose up -d
```

### Dừng services

```bash
./docker-start.sh down
# hoặc
docker-compose down
```

### Build lại images

```bash
./docker-start.sh build
# hoặc
docker-compose build
```

### Xem logs

```bash
# Xem tất cả logs
./docker-start.sh logs

# Xem logs của service cụ thể
./docker-start.sh logs api_server
./docker-start.sh logs ai_server
./docker-start.sh logs frontend
```

### Restart services

```bash
./docker-start.sh restart
# hoặc
docker-compose restart
```

### Kiểm tra trạng thái

```bash
./docker-start.sh status
# hoặc
docker-compose ps
```

### Dọn dẹp hoàn toàn

```bash
./docker-start.sh clean
# Lệnh này sẽ xóa:
# - Tất cả containers
# - Tất cả volumes
# - Tất cả images
```

## 🔧 Cấu hình Port

Tất cả cấu hình port được quản lý tập trung tại file `.env` ở root project:

```env
# API Server
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=2030

# AI Server
AI_SERVER_HOST=0.0.0.0
AI_SERVER_PORT=9999

# Frontend
FRONTEND_PORT=5173

# Redis
REDIS_PORT=6379

# Prometheus
PROMETHEUS_PORT=9090
```

### Thay đổi port

1. Mở file `.env`
2. Thay đổi giá trị port mong muốn
3. Restart services:

```bash
./docker-start.sh restart
```

## 🌐 URLs truy cập

Sau khi khởi động thành công, bạn có thể truy cập:

- **Frontend**: http://localhost:5173
- **API Server**: http://localhost:2030
- **AI Server**: http://localhost:9999
- **Prometheus**: http://localhost:9090

## 📂 Cấu trúc thư mục

```
.
├── docker-compose.yml          # Main docker-compose file
├── docker-start.sh             # Quản lý script
├── .env                        # Cấu hình chung
├── .env.example                # Mẫu cấu hình
│
├── backend/
│   ├── api_server/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── config/
│   │
│   └── ai_server/
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── config/
│
└── frontend/
    └── project/
        ├── Dockerfile
        ├── .env
        └── .env.example
```

## 🔍 Troubleshooting

### Port đã được sử dụng

```bash
# Kiểm tra port nào đang sử dụng
lsof -i :2030
lsof -i :9999
lsof -i :5173

# Thay đổi port trong .env hoặc kill process
kill -9 <PID>
```

### Service không khởi động

```bash
# Xem logs chi tiết
docker-compose logs -f <service_name>

# Ví dụ:
docker-compose logs -f api_server
docker-compose logs -f ai_server
```

### Rebuild từ đầu

```bash
# Dừng và xóa containers
docker-compose down

# Build lại images
docker-compose build --no-cache

# Khởi động lại
docker-compose up -d
```

### Database connection issues

1. Kiểm tra cấu hình database trong `.env`
2. Đảm bảo MySQL/MongoDB đang chạy
3. Kiểm tra network connectivity:

```bash
docker-compose exec api_server ping mysql
docker-compose exec ai_server ping mongodb
```

## 🔐 Bảo mật

### Development

- Sử dụng `.env` cho local development
- KHÔNG commit file `.env` vào git

### Production

- Sử dụng Docker secrets hoặc environment variables từ orchestration tool
- Thay đổi tất cả passwords mặc định
- Sử dụng HTTPS cho tất cả services
- Giới hạn CORS origins

## 📊 Monitoring

Prometheus có sẵn tại http://localhost:9090 để monitor AI Server.

### Metrics có sẵn:

- Task execution time
- Model training metrics
- Server health status

## 🔄 Development Workflow

### 1. Development với hot-reload

Dockerfile đã mount volumes cho development:

```yaml
volumes:
  - ./frontend/project/src:/app/src      # Frontend source
  - ./backend/ai_server/src:/app/src     # AI Server source
  - ./backend/api_server/logs:/app/logs  # API Server logs
```

### 2. Testing changes

```bash
# Restart service sau khi thay đổi code
docker-compose restart <service_name>

# Xem logs để debug
docker-compose logs -f <service_name>
```

### 3. Production build

```bash
# Build production images
docker-compose build

# Deploy với production config
docker-compose -f docker-compose.prod.yml up -d
```

## 🆘 Support

Nếu gặp vấn đề, kiểm tra:

1. Logs: `./docker-start.sh logs`
2. Status: `./docker-start.sh status`
3. Configuration: Đảm bảo `.env` được cấu hình đúng
4. Network: Kiểm tra Docker network connectivity

## 📚 Tài liệu tham khảo

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Project Architecture](./diagrams/System.drawio.png)
