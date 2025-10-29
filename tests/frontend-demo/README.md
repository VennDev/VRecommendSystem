# Frontend Demo - VRecommendation Integration

Dự án demo hoàn chỉnh tích hợp với hệ thống VRecommendation, bao gồm backend API và frontend React.

## 🚀 Tổng quan

Đây là một ứng dụng e-commerce demo được thiết kế để showcase khả năng tích hợp với hệ thống gợi ý sản phẩm AI của VRecommendation. Dự án bao gồm:

- **Backend**: Node.js + Express + SQLite với API RESTful
- **Frontend**: React + Vite + Tailwind CSS với UI hiện đại
- **Tích hợp AI**: Gọi VRecommendation API để lấy gợi ý sản phẩm thông minh

## 📁 Cấu trúc dự án

```
frontend-demo/
├── backend/                    # Backend API server
│   ├── database/              # SQLite database
│   ├── middleware/            # Express middleware
│   ├── routes/               # API routes
│   ├── scripts/              # Utility scripts
│   ├── .env                  # Environment config
│   ├── server.js             # Main server file
│   └── package.json          # Dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services & hooks
│   │   ├── utils/           # Utility functions
│   │   └── App.jsx          # Main app component
│   ├── public/              # Static assets
│   ├── index.html           # HTML template
│   └── package.json         # Dependencies
└── README.md                # This file
```

## 🛠️ Cài đặt và chạy

### Yêu cầu hệ thống
- Node.js >= 16.0.0
- npm >= 8.0.0
- VRecommendation system đang chạy (optional, có fallback)

### 1. Khởi động Backend

```bash
cd backend
npm install
npm run init-db
npm run dev
```

Backend sẽ chạy tại: http://localhost:3001

### 2. Khởi động Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend sẽ chạy tại: http://localhost:5173

### 3. Cấu hình VRecommendation (Optional)

Đảm bảo VRecommendation system đang chạy tại:
- AI Server: http://localhost:9999
- API Base: http://localhost:9999/api/v1

Nếu không có, ứng dụng vẫn hoạt động với gợi ý fallback.

## 🎮 Sử dụng

### Tài khoản Demo
- **Username**: `demo_user`
- **Email**: `demo@example.com`  
- **Password**: `123456`

### Tính năng chính

#### 🏠 Trang chủ
- Hiển thị sản phẩm nổi bật
- Gợi ý sản phẩm dành cho user (nếu đã đăng nhập)
- Categories navigation

#### 🛍️ Danh sách sản phẩm
- Phân trang và lọc theo category
- Tìm kiếm sản phẩm
- Sắp xếp theo giá, rating, tên
- Like/unlike sản phẩm (yêu cầu đăng nhập)

#### 📦 Chi tiết sản phẩm
- Thông tin chi tiết sản phẩm
- Sản phẩm tương tự
- Ghi nhận lượt xem (nếu đã đăng nhập)

#### 🤖 Gợi ý thông minh
- Tích hợp VRecommendation AI API
- Gợi ý cá nhân hóa dựa trên hành vi user
- Fallback về sản phẩm phổ biến nếu AI service không khả dụng

#### 👤 Quản lý tài khoản
- Đăng ký/đăng nhập
- Profile cá nhân
- Danh sách sản phẩm đã thích
- Thống kê tương tác

## 🔧 API Endpoints

### Authentication
```
POST /api/auth/login          # Đăng nhập
POST /api/auth/register       # Đăng ký
POST /api/auth/logout         # Đăng xuất
POST /api/auth/verify-token   # Xác thực token
```

### Products
```
GET    /api/products                 # Danh sách sản phẩm
GET    /api/products/featured        # Sản phẩm nổi bật
GET    /api/products/:id             # Chi tiết sản phẩm
POST   /api/products/:id/like        # Thích sản phẩm
GET    /api/products/user/liked      # Sản phẩm đã thích
GET    /api/products/categories      # Danh mục
```

### Recommendations
```
GET    /api/recommendations/for-me           # Gợi ý cho tôi
GET    /api/recommendations/for-user/:id     # Gợi ý cho user
GET    /api/recommendations/similar/:id      # Sản phẩm tương tự
POST   /api/recommendations/feedback         # Gửi feedback
GET    /api/recommendations/stats            # Thống kê
```

## 🤖 Tích hợp VRecommendation

### Flow hoạt động
1. User tương tác với sản phẩm (view, like, purchase)
2. Interactions được lưu vào database
3. Frontend gọi API `/recommendations/for-me`
4. Backend gọi VRecommendation API: `/api/v1/recommend/{user_id}/{model_id}/{n}`
5. Nhận list product IDs và điểm số
6. Query database để lấy thông tin chi tiết sản phẩm
7. Trả về danh sách gợi ý cho frontend

### Fallback Strategy
- Nếu VRecommendation service không khả dụng
- Backend tự động fallback về gợi ý dựa trên:
  - Sản phẩm có rating cao nhất
  - Sản phẩm cùng category đã tương tác
  - Sản phẩm phổ biến

### Configuration
```bash
# Backend .env
VRECOMMENDATION_API_BASE_URL=http://localhost:9999/api/v1
DEFAULT_MODEL_ID=default_model
```

## 🎨 Frontend Features

### Modern UI/UX
- **Design System**: Tailwind CSS với custom components
- **Responsive**: Mobile-first design
- **Animations**: Framer Motion cho smooth transitions
- **Icons**: Lucide React icon set
- **Loading States**: Skeleton loading và spinners
- **Toast Notifications**: React Hot Toast

### State Management
- **React Query**: Server state management và caching
- **Context API**: User authentication state
- **Local State**: Component-level state với useState/useReducer

### Performance Optimizations
- **Lazy Loading**: Route-based code splitting
- **Image Optimization**: Lazy loading với Intersection Observer
- **Caching**: Aggressive caching với React Query
- **Prefetching**: Hover-based prefetching
- **Bundle Splitting**: Vendor và route-based chunks

### Developer Experience
- **Hot Reload**: Vite HMR
- **TypeScript**: Type safety (optional)
- **ESLint**: Code linting
- **Error Boundaries**: Graceful error handling
- **Dev Tools**: React Query DevTools

## 📊 Database Schema

### Users
```sql
users (
  id, username, email, password_hash,
  full_name, avatar_url, preferences,
  created_at, updated_at, is_active
)
```

### Products
```sql
products (
  id, name, description, price, category_id,
  image_url, rating, review_count, stock_quantity,
  is_featured, tags, created_at, updated_at
)
```

### Categories
```sql
categories (
  id, name, description, icon, created_at
)
```

### User Interactions
```sql
user_interactions (
  id, user_id, product_id, interaction_type,
  rating, interaction_data, created_at
)
```

## 🧪 Testing

### Kiểm tra tích hợp
1. Đăng nhập với tài khoản demo
2. Tương tác với một số sản phẩm (view, like)
3. Truy cập `/recommendations` để xem gợi ý
4. Kiểm tra console để xem API calls
5. Test fallback bằng cách tắt VRecommendation service

### Debug
```bash
# Backend logs
npm run dev  # Xem request logs trong console

# Frontend dev tools
# Mở Chrome DevTools -> React Query tab
```

## 🚀 Deployment

### Production Build
```bash
# Backend
cd backend
npm start

# Frontend
cd frontend
npm run build
npm run preview
```

### Environment Variables
```bash
# Backend
PORT=3001
NODE_ENV=production
JWT_SECRET=your-production-secret
VRECOMMENDATION_API_BASE_URL=https://your-vrecom-api.com/api/v1

# Frontend
VITE_API_BASE_URL=https://your-backend-api.com/api
```

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Todo

- [ ] Add product reviews/ratings
- [ ] Implement shopping cart
- [ ] Add payment integration
- [ ] Real-time notifications
- [ ] Advanced search filters
- [ ] Product comparison
- [ ] Wishlist functionality
- [ ] Order history
- [ ] Admin dashboard
- [ ] A/B testing for recommendations

## 🐛 Troubleshooting

### Common Issues

**Backend không khởi động được**
```bash
# Kiểm tra port 3001 có bị chiếm không
lsof -i :3001

# Xóa database và tạo lại
rm -f backend/database/demo.db
npm run init-db
```

**Frontend không kết nối được backend**
```bash
# Kiểm tra CORS settings trong backend/server.js
# Đảm bảo frontend URL được allow
```

**VRecommendation API không hoạt động**
- Ứng dụng vẫn hoạt động bình thường với fallback
- Check logs để xem lý do: timeout, connection refused, etc.
- Verify VRecommendation service endpoints

**Database lỗi**
```bash
# Reset database
cd backend
npm run init-db
```

## 📞 Support

- **Issues**: Tạo issue trên GitHub
- **Email**: support@vrecommendation.com
- **Docs**: Xem documentation đầy đủ tại `/api` endpoint

## 📄 License

MIT License - see LICENSE file for details

---

🎉 **Happy coding!** Hy vọng dự án demo này giúp bạn hiểu cách tích hợp VRecommendation system vào ứng dụng thực tế.