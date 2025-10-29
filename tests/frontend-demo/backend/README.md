# Frontend Demo Backend

Backend API server cho dự án demo tích hợp với hệ thống VRecommendation. Được xây dựng với Node.js, Express và SQLite.

## 🚀 Tính năng

- **Xác thực người dùng**: Đăng ký, đăng nhập với JWT
- **Quản lý sản phẩm**: CRUD sản phẩm với phân trang, tìm kiếm, bộ lọc
- **Tương tác người dùng**: Thích sản phẩm, xem chi tiết, ghi nhận lượt xem
- **Gợi ý thông minh**: Tích hợp với VRecommendation AI API
- **Database**: SQLite với dữ liệu mẫu
- **Rate limiting**: Bảo vệ API khỏi spam
- **CORS**: Hỗ trợ frontend React

## 📋 Yêu cầu hệ thống

- Node.js >= 16.0.0
- npm >= 8.0.0
- VRecommendation service đang chạy (optional)

## 🛠️ Cài đặt

### 1. Cài đặt dependencies
```bash
cd VRecommendation/tests/frontend-demo/backend
npm install
```

### 2. Khởi tạo database
```bash
npm run init-db
```

### 3. Cấu hình môi trường (optional)
```bash
# Sao chép và chỉnh sửa file .env
cp .env .env.local

# Chỉnh sửa các thông số cần thiết
nano .env.local
```

### 4. Khởi động server
```bash
# Development mode (với auto-reload)
npm run dev

# Production mode
npm start
```

Server sẽ chạy tại: http://localhost:3001

## 📊 Cấu hình môi trường

Các biến môi trường trong file `.env`:

```bash
# Backend Configuration
PORT=3001
NODE_ENV=development

# Database
DB_PATH=./database/demo.db

# JWT
JWT_SECRET=your-super-secret-jwt-key-for-demo-app
JWT_EXPIRES_IN=24h

# CORS
CORS_ORIGIN=http://localhost:5173

# VRecommendation API
VRECOMMENDATION_API_URL=http://localhost:9999
VRECOMMENDATION_API_BASE_URL=http://localhost:9999/api/v1
DEFAULT_MODEL_ID=default_model
```

## 🗄️ Cấu trúc Database

### Bảng users
- `id`: Primary key
- `username`: Tên đăng nhập (unique)
- `email`: Email (unique)
- `password_hash`: Mật khẩu đã hash
- `full_name`: Tên đầy đủ
- `avatar_url`: URL avatar
- `created_at`, `updated_at`: Timestamps

### Bảng categories
- `id`: Primary key
- `name`: Tên danh mục
- `description`: Mô tả
- `icon`: Icon emoji

### Bảng products
- `id`: Primary key
- `name`: Tên sản phẩm
- `description`: Mô tả
- `price`: Giá
- `category_id`: FK đến categories
- `rating`: Đánh giá (1-5)
- `review_count`: Số lượt review
- `stock_quantity`: Số lượng tồn kho
- `is_featured`: Sản phẩm nổi bật

### Bảng user_interactions
- `id`: Primary key
- `user_id`: FK đến users
- `product_id`: FK đến products
- `interaction_type`: 'like', 'view', 'purchase', 'cart', 'wishlist'
- `rating`: Đánh giá (optional)
- `created_at`: Timestamp

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register` - Đăng ký tài khoản
- `POST /api/auth/login` - Đăng nhập
- `POST /api/auth/verify-token` - Xác thực token
- `POST /api/auth/refresh-token` - Làm mới token
- `POST /api/auth/logout` - Đăng xuất

### Products
- `GET /api/products` - Lấy danh sách sản phẩm (phân trang, bộ lọc)
- `GET /api/products/featured` - Sản phẩm nổi bật
- `GET /api/products/categories` - Danh sách categories
- `GET /api/products/:id` - Chi tiết sản phẩm
- `POST /api/products/:id/like` - Thích/bỏ thích sản phẩm (yêu cầu auth)
- `GET /api/products/user/liked` - Sản phẩm đã thích (yêu cầu auth)

### Recommendations
- `GET /api/recommendations/for-user/:userId` - Gợi ý cho user cụ thể
- `GET /api/recommendations/for-me` - Gợi ý cho user hiện tại (yêu cầu auth)
- `GET /api/recommendations/similar/:productId` - Sản phẩm tương tự
- `POST /api/recommendations/feedback` - Gửi feedback (yêu cầu auth)
- `GET /api/recommendations/stats` - Thống kê tương tác (yêu cầu auth)

### Utility
- `GET /health` - Health check
- `GET /api` - API documentation

## 🔐 Authentication

API sử dụng JWT Bearer token cho authentication:

```bash
Authorization: Bearer <token>
```

### Demo account
- Username: `demo_user`
- Email: `demo@example.com`
- Password: `123456`

## 🤖 Tích hợp VRecommendation

Backend tự động gọi VRecommendation API để lấy gợi ý sản phẩm:

```
GET /api/v1/recommend/{user_id}/{model_id}/{n}
```

### Fallback behavior
- Nếu VRecommendation service không khả dụng
- API sẽ trả về sản phẩm phổ biến nhất
- Client vẫn nhận được response hợp lệ

## 📝 Ví dụ sử dụng API

### Đăng nhập
```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo_user", "password": "123456"}'
```

### Lấy sản phẩm
```bash
curl http://localhost:3001/api/products?page=1&limit=12
```

### Lấy gợi ý sản phẩm
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:3001/api/recommendations/for-me?n=10
```

## 🚨 Rate Limiting

API có rate limiting để bảo vệ:

- General: 200 requests/15 phút
- Auth endpoints: 10 requests/15 phút
- Products/Recommendations: 30-60 requests/15 phút

## 🐛 Debug & Logging

Server ghi log tất cả requests:
```
[2024-01-15T10:30:00.123Z] GET /api/products - 127.0.0.1
```

Lỗi database và API được ghi chi tiết trong console.

## 🔧 Development

### Scripts có sẵn
```bash
npm start          # Khởi động production
npm run dev        # Development với nodemon
npm run init-db    # Khởi tạo database và seed data
```

### Cấu trúc thư mục
```
backend/
├── database/           # SQLite database
├── middleware/         # Express middleware
├── routes/            # API routes
├── scripts/           # Utility scripts
├── public/            # Static files
├── .env              # Environment config
├── server.js         # Main server file
└── package.json      # Dependencies
```

## 🔄 Tích hợp với Frontend

Backend được thiết kế để hoạt động với React frontend:

- CORS được cấu hình cho `http://localhost:5173`
- Response format nhất quán với `{ success, message, data }`
- Error handling chi tiết
- JWT token cho session management

## 📞 Support

Nếu gặp vấn đề:

1. Kiểm tra VRecommendation service đang chạy
2. Xem log server trong console
3. Kiểm tra database đã được khởi tạo
4. Verify network connectivity với frontend

---

💡 **Tip**: Sử dụng `GET /api` để xem full API documentation và test endpoints.