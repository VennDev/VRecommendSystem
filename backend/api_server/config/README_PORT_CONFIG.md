# Cấu hình Port Tập Trung

## Tổng Quan

Dự án VRecommendation đã được cấu hình để quản lý tất cả các port và URL từ một nơi duy nhất. Điều này giúp dễ dàng thay đổi cấu hình mà không cần sửa nhiều file.

## Nơi Cấu Hình Chính

### 1. Backend API Server

**File cấu hình chính:** `backend/api_server/config/local.yml`

```yaml
server:
    host: "0.0.0.0"
    port: 2030                                    # ← Thay đổi port API server tại đây
    ai_server_url: "http://localhost:9999"       # ← Thay đổi URL AI server tại đây
    frontend_url: "http://localhost:5173"        # ← Thay đổi URL frontend tại đây
```

**Biến môi trường (optional, ghi đè config file):**
- `HOST_ADDRESS` - Địa chỉ host của API server (mặc định: 0.0.0.0)
- `HOST_PORT` - Port của API server (mặc định: 2030)
- `AI_SERVER_URL` - URL của AI server (mặc định: http://localhost:9999)
- `FRONTEND_URL` - URL của frontend (mặc định: http://localhost:5173)

### 2. Frontend

**File cấu hình chính:** `frontend/project/src/config/api.ts`

```typescript
export const API_CONFIG = {
  AI_SERVER_URL: getEnvVar('VITE_AI_SERVER_URL', 'http://localhost:9999'),
  AUTH_SERVER_URL: getEnvVar('VITE_API_SERVER_URL', 'http://localhost:2030'),
  // ...
}
```

**Biến môi trường (file `.env`):**
- `VITE_AI_SERVER_URL` - URL của AI server
- `VITE_API_SERVER_URL` - URL của API server

## Cách Thay Đổi Port

### Thay đổi Port API Server (Backend)

#### Cách 1: Thông qua file config (Khuyến nghị)

1. Mở file `backend/api_server/config/local.yml`
2. Thay đổi giá trị `server.port`:
   ```yaml
   server:
       port: 3000  # Thay đổi từ 2030 sang 3000
   ```
3. Khởi động lại API server

#### Cách 2: Thông qua biến môi trường

Thêm vào file `.env` ở root project:
```env
HOST_PORT=3000
```

### Thay đổi Port Frontend

1. Mở file `backend/api_server/config/local.yml`
2. Thay đổi giá trị `server.frontend_url`:
   ```yaml
   server:
       frontend_url: "http://localhost:3001"  # Thay đổi từ 5173 sang 3001
   ```
3. Cập nhật Vite config hoặc package.json để frontend chạy ở port 3001
4. Khởi động lại cả backend và frontend

### Thay đổi Port AI Server

1. Mở file `backend/api_server/config/local.yml`
2. Thay đổi giá trị `server.ai_server_url`:
   ```yaml
   server:
       ai_server_url: "http://localhost:8888"  # Thay đổi từ 9999 sang 8888
   ```
3. Đảm bảo AI server cũng được cấu hình để chạy ở port 8888
4. Khởi động lại API server

## Các File Đã Được Cập Nhật

### Backend Files

1. **`config/local.yml`** - File cấu hình chính
2. **`pkg/setting/section.go`** - Struct để đọc cấu hình server
3. **`internal/initialize/middlewares.go`** - CORS middleware đọc từ config
4. **`internal/handlers/authentication_handler.go`** - OAuth redirect đọc từ config
5. **`internal/handlers/recommend_handler.go`** - AI server URL đọc từ config
6. **`pkg/utils/start_server.go`** - Server startup đọc từ config

### Frontend Files

1. **`src/config/api.ts`** - Centralized API configuration
2. **`src/contexts/AuthContext.tsx`** - Sử dụng API_CONFIG
3. **`src/services/healthCheck.ts`** - Sử dụng API_CONFIG

## Thứ Tự Ưu Tiên Cấu Hình

1. **Biến môi trường** (Environment Variables) - Ưu tiên cao nhất
2. **File config** (`local.yml`) - Ưu tiên thứ hai
3. **Giá trị mặc định** trong code - Chỉ sử dụng khi không có cấu hình

## Ví dụ Kịch Bản

### Kịch bản 1: Chạy trên port khác để tránh xung đột

```yaml
# backend/api_server/config/local.yml
server:
    port: 8080
    frontend_url: "http://localhost:3000"
```

Hoặc sử dụng biến môi trường:
```env
HOST_PORT=8080
FRONTEND_URL=http://localhost:3000
```

### Kịch bản 2: Chạy trong Docker

```yaml
# backend/api_server/config/local.yml
server:
    host: "0.0.0.0"
    port: 2030
    ai_server_url: "http://ai_server:9999"  # Sử dụng Docker service name
    frontend_url: "http://frontend:5173"
```

### Kịch bản 3: Production deployment

```yaml
# backend/api_server/config/production.yml
server:
    host: "0.0.0.0"
    port: 443
    ai_server_url: "https://ai.example.com"
    frontend_url: "https://app.example.com"
```

## Lưu Ý Quan Trọng

1. **Sau khi thay đổi config**, bạn cần khởi động lại tất cả các service liên quan
2. **CORS Configuration**: Khi thay đổi port, CORS sẽ tự động cập nhật dựa trên config
3. **OAuth Callback**: URL callback OAuth sẽ tự động sử dụng `frontend_url` từ config
4. **Health Check**: Frontend sẽ kiểm tra health dựa trên URL trong `api.ts`

## Kiểm Tra Cấu Hình

Để kiểm tra cấu hình hiện tại đang được sử dụng:

```bash
# Xem logs khi khởi động server
# Các giá trị sẽ được log ra console

# Backend API Server
cd backend/api_server
go run main.go

# Trong console logs, bạn sẽ thấy:
# - Server listening on: 0.0.0.0:2030
# - CORS allowed origins
```

## Troubleshooting

### Lỗi: CORS blocked

**Nguyên nhân:** Frontend và backend đang chạy ở port khác nhau nhưng chưa được cấu hình đúng.

**Giải pháp:**
1. Kiểm tra `server.frontend_url` trong `local.yml`
2. Đảm bảo frontend thực sự chạy ở port đó
3. Khởi động lại backend server

### Lỗi: Cannot connect to AI server

**Nguyên nhân:** AI server URL không đúng hoặc AI server chưa chạy.

**Giải pháp:**
1. Kiểm tra `server.ai_server_url` trong `local.yml`
2. Đảm bảo AI server đang chạy
3. Test bằng cách truy cập `http://localhost:9999/api/v1/health`

### Lỗi: OAuth callback failed

**Nguyên nhân:** Frontend URL trong OAuth callback không đúng.

**Giải pháp:**
1. Kiểm tra `server.frontend_url` trong `local.yml`
2. Đảm bảo Google OAuth callback URL được cấu hình đúng trong Google Console
3. Khởi động lại backend server

## Best Practices

1. **Sử dụng file config cho development**: Dễ quản lý và chia sẻ trong team
2. **Sử dụng biến môi trường cho production**: An toàn và linh hoạt
3. **Không hardcode URLs**: Luôn sử dụng config hoặc biến môi trường
4. **Document changes**: Ghi chép lại khi thay đổi cấu hình quan trọng
5. **Test sau khi thay đổi**: Kiểm tra tất cả các tính năng sau khi đổi port

## Liên Hệ

Nếu có vấn đề về cấu hình port, vui lòng liên hệ team dev hoặc tạo issue trên repository.