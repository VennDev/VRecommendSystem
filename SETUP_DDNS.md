# Hướng dẫn cấu hình DDNS cho VRecommendation System

## Cấu hình mặc định (Localhost)

Dự án mặc định chạy trên localhost. Không cần thay đổi gì cả.

## Chuyển sang DDNS (vennv.ddns.net)

Chỉ cần làm 3 bước:

### 1. Cấu hình Backend API Server

Mở file `backend/api_server/.env` và sửa:

```bash
# Thay đổi FRONTEND_URL
FRONTEND_URL=http://vennv.ddns.net:5173

# Thay đổi ALLOWED_ORIGINS
ALLOWED_ORIGINS=http://vennv.ddns.net:5173,https://vennv.ddns.net:5173

# Thay đổi GOOGLE_CALLBACK_URL
GOOGLE_CALLBACK_URL=http://vennv.ddns.net:2030/api/v1/auth/google/callback

# Điền Google OAuth credentials (bắt buộc!)
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
```

### 2. Cấu hình Frontend

Mở file `frontend/project/.env` và sửa:

```bash
# Comment localhost và uncomment DDNS
# VITE_AI_SERVER_URL=http://localhost:9999
# VITE_API_SERVER_URL=http://localhost:2030

VITE_AI_SERVER_URL=http://vennv.ddns.net:9999
VITE_API_SERVER_URL=http://vennv.ddns.net:2030
```

### 3. Cập nhật Google OAuth Console

1. Vào https://console.cloud.google.com/apis/credentials
2. Chọn OAuth 2.0 Client ID của bạn
3. Thêm vào **Authorized JavaScript origins**:
   - `http://vennv.ddns.net:5173`
4. Thêm vào **Authorized redirect URIs**:
   - `http://vennv.ddns.net:2030/api/v1/auth/google/callback`

### 4. Restart tất cả services

```bash
# Windows
stop.cmd
start.cmd

# Linux/Mac
./stop-local.sh
./start-local.sh
```

## Chuyển về Localhost

Chỉ cần comment/uncomment lại các dòng trong file `.env`:

**Backend (`backend/api_server/.env`):**
```bash
FRONTEND_URL=
ALLOWED_ORIGINS=
GOOGLE_CALLBACK_URL=
```

**Frontend (`frontend/project/.env`):**
```bash
VITE_AI_SERVER_URL=http://localhost:9999
VITE_API_SERVER_URL=http://localhost:2030
```

Sau đó restart lại services.

## Lưu ý quan trọng

1. **File .env không được commit vào Git** - Chỉ có `example-env` mới được commit
2. **Phải restart services** sau khi thay đổi .env
3. **Phải cấu hình Google OAuth Console** trước khi sử dụng DDNS
4. **Ports cần mở** trên router/firewall:
   - 5173 (Frontend)
   - 2030 (API Server)
   - 9999 (AI Server)
