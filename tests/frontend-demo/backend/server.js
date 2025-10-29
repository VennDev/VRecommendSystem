const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
require('dotenv').config();

// Import routes
const authRoutes = require('./routes/auth');
const productsRoutes = require('./routes/products');
const recommendationsRoutes = require('./routes/recommendations');

// Import middleware
const { rateLimit } = require('./middleware/auth');

const app = express();
const PORT = process.env.PORT || 3001;

// CORS configuration
const corsOptions = {
    origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    credentials: true,
    optionsSuccessStatus: 200
};

// Middleware
app.use(cors(corsOptions));
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// General rate limiting
const generalRateLimit = rateLimit(200, 15 * 60 * 1000); // 200 requests per 15 minutes
app.use(generalRateLimit);

// Security headers
app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    next();
});

// Request logging middleware
app.use((req, res, next) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${req.method} ${req.url} - ${req.ip}`);
    next();
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        version: process.env.npm_package_version || '1.0.0',
        environment: process.env.NODE_ENV || 'development'
    });
});

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/products', productsRoutes);
app.use('/api/recommendations', recommendationsRoutes);

// Static files (để serve hình ảnh mẫu)
app.use('/images', express.static(path.join(__dirname, 'public', 'images')));

// API documentation endpoint
app.get('/api', (req, res) => {
    res.json({
        name: 'Frontend Demo API',
        version: '1.0.0',
        description: 'API demo tích hợp với VRecommendation system',
        endpoints: {
            auth: {
                'POST /api/auth/register': 'Đăng ký tài khoản mới',
                'POST /api/auth/login': 'Đăng nhập',
                'POST /api/auth/verify-token': 'Xác thực token',
                'POST /api/auth/refresh-token': 'Làm mới token',
                'POST /api/auth/logout': 'Đăng xuất'
            },
            products: {
                'GET /api/products': 'Lấy danh sách sản phẩm (có phân trang và bộ lọc)',
                'GET /api/products/featured': 'Lấy sản phẩm nổi bật',
                'GET /api/products/categories': 'Lấy danh sách categories',
                'GET /api/products/:id': 'Lấy chi tiết sản phẩm',
                'POST /api/products/:id/like': 'Thích/bỏ thích sản phẩm',
                'GET /api/products/user/liked': 'Lấy danh sách sản phẩm đã thích'
            },
            recommendations: {
                'GET /api/recommendations/for-user/:userId': 'Lấy gợi ý sản phẩm cho user (từ VRecommendation)',
                'GET /api/recommendations/for-me': 'Lấy gợi ý sản phẩm cho user hiện tại',
                'GET /api/recommendations/similar/:productId': 'Lấy sản phẩm tương tự',
                'POST /api/recommendations/feedback': 'Gửi feedback về gợi ý',
                'GET /api/recommendations/stats': 'Thống kê về gợi ý sản phẩm'
            }
        },
        authentication: {
            type: 'JWT Bearer Token',
            header: 'Authorization: Bearer <token>',
            note: 'Một số endpoint yêu cầu authentication, một số khác là optional'
        },
        vrecommendation_integration: {
            api_url: process.env.VRECOMMENDATION_API_BASE_URL || 'http://localhost:9999/api/v1',
            default_model_id: process.env.DEFAULT_MODEL_ID || 'default_model',
            note: 'Tích hợp với hệ thống VRecommendation để lấy gợi ý sản phẩm AI'
        }
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Error occurred:', err);

    // Database connection errors
    if (err.code === 'SQLITE_ERROR' || err.code === 'SQLITE_BUSY') {
        return res.status(500).json({
            error: 'Database error',
            message: 'Lỗi cơ sở dữ liệu'
        });
    }

    // JWT errors
    if (err.name === 'JsonWebTokenError') {
        return res.status(401).json({
            error: 'Invalid token',
            message: 'Token không hợp lệ'
        });
    }

    if (err.name === 'TokenExpiredError') {
        return res.status(401).json({
            error: 'Token expired',
            message: 'Token đã hết hạn'
        });
    }

    // Validation errors
    if (err.name === 'ValidationError') {
        return res.status(400).json({
            error: 'Validation error',
            message: 'Dữ liệu không hợp lệ',
            details: err.details
        });
    }

    // Default error
    res.status(500).json({
        error: 'Internal server error',
        message: 'Lỗi máy chủ nội bộ'
    });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Not found',
        message: 'Endpoint không tồn tại',
        path: req.originalUrl
    });
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received. Shutting down gracefully...');
    server.close(() => {
        console.log('Process terminated');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('SIGINT received. Shutting down gracefully...');
    server.close(() => {
        console.log('Process terminated');
        process.exit(0);
    });
});

// Start server
const server = app.listen(PORT, () => {
    console.log('\n🚀 Frontend Demo Backend Server Started!');
    console.log(`📍 Server running on: http://localhost:${PORT}`);
    console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`🔗 VRecommendation API: ${process.env.VRECOMMENDATION_API_BASE_URL || 'http://localhost:9999/api/v1'}`);
    console.log(`📚 API Documentation: http://localhost:${PORT}/api`);
    console.log(`❤️  Health Check: http://localhost:${PORT}/health`);
    console.log('\n📋 Available endpoints:');
    console.log('   POST /api/auth/register - Đăng ký');
    console.log('   POST /api/auth/login - Đăng nhập');
    console.log('   GET /api/products - Danh sách sản phẩm');
    console.log('   GET /api/products/featured - Sản phẩm nổi bật');
    console.log('   GET /api/recommendations/for-me - Gợi ý cho tôi');
    console.log('\n💡 Demo login:');
    console.log('   Username: demo_user');
    console.log('   Password: 123456');
    console.log('\n🔧 Khởi tạo database nếu chưa có:');
    console.log('   npm run init-db');
});

module.exports = app;
