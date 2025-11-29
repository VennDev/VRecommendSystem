# VRecommendation Admin Portal

## 🛡️ Localhost Only Admin Interface

Admin Portal là một giao diện web riêng biệt dành cho quản lý SuperAdmin features như **Email Whitelist**. Portal này được thiết kế để **CHỈ** có thể truy cập từ **localhost (127.0.0.1)**.

## ⚠️ Tại sao cần Admin Portal?

Khi chạy VRecommendation qua Docker, trang SuperAdmin (`/super-admin`) trên frontend không thể truy cập từ các thiết bị khác trong mạng LAN vì lý do bảo mật:

- **Frontend chính** (`http://192.168.x.x:5173`) - Có thể truy cập từ LAN
- **SuperAdmin API** (`/api/v1/local/*`) - Chỉ cho phép localhost truy cập

Admin Portal giải quyết vấn đề này bằng cách:
1. Chạy trên một port riêng (3456) và **chỉ bind localhost**
2. Proxy requests đến API server với Host header `localhost`
3. Cung cấp giao diện quản lý whitelist đầy đủ

## 🚀 Cách sử dụng

### Yêu cầu
- Node.js >= 16.x
- API Server đang chạy trên port 2030

### Khởi động

**Windows:**
```cmd
cd admin-portal
start.cmd
```

**Linux/macOS:**
```bash
cd admin-portal
chmod +x start.sh
./start.sh
```

**Hoặc sử dụng npm:**
```bash
cd admin-portal
npm install
npm start
```

### Truy cập
Sau khi khởi động, mở trình duyệt và truy cập:
```
http://127.0.0.1:3456
```

> ⚠️ **Lưu ý**: Bạn **PHẢI** truy cập từ máy đang chạy Admin Portal. Không thể truy cập từ các máy khác trong mạng LAN.

## 📋 Tính năng

- ✅ Xem danh sách email trong whitelist
- ✅ Thêm email mới vào whitelist
- ✅ Chỉnh sửa trạng thái (active/inactive) và ghi chú
- ✅ Xóa email khỏi whitelist
- ✅ Thống kê tổng số email, active, inactive
- ✅ Giao diện dark theme hiện đại
- ✅ Real-time connection status

## 🔒 Bảo mật

Admin Portal được thiết kế với nhiều lớp bảo mật:

1. **Bind localhost only**: Server chỉ lắng nghe trên `127.0.0.1`, không phải `0.0.0.0`
2. **IP Check middleware**: Double-check client IP trước mỗi request
3. **Host header injection**: Tất cả requests đến API đều có Host header `localhost`
4. **Không expose ra Docker network**: Không có trong docker-compose.yml

```
                    ┌─────────────────────────────────────┐
                    │         Admin Portal (3456)         │
                    │         127.0.0.1 ONLY              │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ Host: localhost
                                   ▼
┌─────────────┐              ┌─────────────────────────────────────┐
│  LAN User   │──────X───────│         API Server (2030)           │
│ 192.168.x.x │   BLOCKED    │  checkLocalhost() → 403 Forbidden   │
└─────────────┘              └─────────────────────────────────────┘
```

## ⚙️ Cấu hình

Bạn có thể thay đổi cấu hình qua environment variables:

| Variable | Default | Mô tả |
|----------|---------|-------|
| `ADMIN_PORTAL_PORT` | `3456` | Port của Admin Portal |
| `API_SERVER_URL` | `http://localhost:2030` | URL của API Server |

**Ví dụ:**
```bash
# Windows
set ADMIN_PORTAL_PORT=4000
set API_SERVER_URL=http://localhost:2030
npm start

# Linux/macOS
ADMIN_PORTAL_PORT=4000 API_SERVER_URL=http://localhost:2030 npm start
```

## 🐛 Troubleshooting

### Admin Portal không thể kết nối đến API Server
```
[ERROR] Failed to fetch whitelist: connect ECONNREFUSED
```
**Giải pháp**: Đảm bảo API Server đang chạy trên port 2030
```bash
docker ps | grep vrecom_api_server
```

### Truy cập bị từ chối (403 Forbidden)
```
Access denied. This portal is only accessible from localhost.
```
**Giải pháp**: Đảm bảo bạn đang truy cập từ `http://127.0.0.1:3456` hoặc `http://localhost:3456`

### Port đã được sử dụng
```
[ERROR] EADDRINUSE: address already in use
```
**Giải pháp**: Đổi port bằng environment variable
```bash
set ADMIN_PORTAL_PORT=4567
npm start
```

## 📁 Cấu trúc thư mục

```
admin-portal/
├── package.json        # Dependencies và scripts
├── server.js           # Express server (localhost only)
├── start.cmd           # Windows startup script
├── start.sh            # Linux/macOS startup script
├── README.md           # Documentation
└── public/
    └── index.html      # Web interface
```

## 🔄 So sánh với SuperAdmin Page

| Tính năng | SuperAdmin Page (`/super-admin`) | Admin Portal |
|-----------|----------------------------------|--------------|
| Truy cập từ LAN | ❌ Không | ❌ Không |
| Truy cập từ localhost | ✅ Có | ✅ Có |
| Port | 5173 (Frontend) | 3456 (Riêng biệt) |
| Cần Docker | ✅ Có | ❌ Không |
| Giao diện | React + Tailwind | Vanilla HTML/CSS/JS |
| Kích thước | ~100MB (node_modules) | ~5MB |

## 📝 License

MIT License - VennDev © 2024