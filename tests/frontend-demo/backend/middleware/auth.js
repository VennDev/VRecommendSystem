const jwt = require('jsonwebtoken');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
require('dotenv').config();

// Kết nối database
const dbPath = path.join(__dirname, '..', 'database', 'demo.db');
const db = new sqlite3.Database(dbPath);

// Middleware xác thực JWT
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
        return res.status(401).json({
            error: 'Access token required',
            message: 'Vui lòng đăng nhập để tiếp tục'
        });
    }

    jwt.verify(token, process.env.JWT_SECRET || 'your-super-secret-jwt-key-for-demo-app', (err, user) => {
        if (err) {
            console.error('JWT verification error:', err.message);
            return res.status(403).json({
                error: 'Invalid or expired token',
                message: 'Token không hợp lệ hoặc đã hết hạn'
            });
        }

        // Kiểm tra user còn tồn tại trong database
        db.get(
            'SELECT id, username, email, full_name, is_active FROM users WHERE id = ? AND is_active = 1',
            [user.userId],
            (err, row) => {
                if (err) {
                    console.error('Database error:', err.message);
                    return res.status(500).json({
                        error: 'Database error',
                        message: 'Lỗi cơ sở dữ liệu'
                    });
                }

                if (!row) {
                    return res.status(401).json({
                        error: 'User not found or inactive',
                        message: 'Người dùng không tồn tại hoặc đã bị khóa'
                    });
                }

                // Thêm thông tin user vào request
                req.user = {
                    id: row.id,
                    username: row.username,
                    email: row.email,
                    full_name: row.full_name,
                    ...user
                };

                next();
            }
        );
    });
};

// Middleware tùy chọn - không bắt buộc đăng nhập
const optionalAuth = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        req.user = null;
        return next();
    }

    jwt.verify(token, process.env.JWT_SECRET || 'your-super-secret-jwt-key-for-demo-app', (err, user) => {
        if (err) {
            req.user = null;
        } else {
            // Kiểm tra user trong database
            db.get(
                'SELECT id, username, email, full_name FROM users WHERE id = ? AND is_active = 1',
                [user.userId],
                (err, row) => {
                    if (!err && row) {
                        req.user = {
                            id: row.id,
                            username: row.username,
                            email: row.email,
                            full_name: row.full_name,
                            ...user
                        };
                    } else {
                        req.user = null;
                    }
                    next();
                }
            );
            return;
        }
        next();
    });
};

// Tạo JWT token
const generateToken = (userId, username, email) => {
    const payload = {
        userId: userId,
        username: username,
        email: email,
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hours
    };

    return jwt.sign(payload, process.env.JWT_SECRET || 'your-super-secret-jwt-key-for-demo-app', {
        expiresIn: process.env.JWT_EXPIRES_IN || '24h'
    });
};

// Verify JWT token (utility function)
const verifyToken = (token) => {
    try {
        return jwt.verify(token, process.env.JWT_SECRET || 'your-super-secret-jwt-key-for-demo-app');
    } catch (error) {
        return null;
    }
};

// Middleware kiểm tra quyền admin (nếu cần)
const requireAdmin = (req, res, next) => {
    if (!req.user) {
        return res.status(401).json({
            error: 'Authentication required',
            message: 'Vui lòng đăng nhập'
        });
    }

    // Kiểm tra quyền admin (có thể mở rộng sau)
    if (req.user.username !== 'admin' && req.user.id !== 1) {
        return res.status(403).json({
            error: 'Admin access required',
            message: 'Chỉ admin mới có quyền truy cập'
        });
    }

    next();
};

// Rate limiting middleware (đơn giản)
const rateLimitMap = new Map();
const rateLimit = (maxRequests = 100, windowMs = 15 * 60 * 1000) => {
    return (req, res, next) => {
        const clientId = req.ip || req.connection.remoteAddress;
        const now = Date.now();

        if (!rateLimitMap.has(clientId)) {
            rateLimitMap.set(clientId, { count: 1, resetTime: now + windowMs });
        } else {
            const client = rateLimitMap.get(clientId);

            if (now > client.resetTime) {
                client.count = 1;
                client.resetTime = now + windowMs;
            } else {
                client.count++;

                if (client.count > maxRequests) {
                    return res.status(429).json({
                        error: 'Too many requests',
                        message: 'Quá nhiều yêu cầu, vui lòng thử lại sau',
                        retryAfter: Math.ceil((client.resetTime - now) / 1000)
                    });
                }
            }
        }

        next();
    };
};

module.exports = {
    authenticateToken,
    optionalAuth,
    generateToken,
    verifyToken,
    requireAdmin,
    rateLimit
};
