const express = require('express');
const bcrypt = require('bcryptjs');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const { generateToken, verifyToken, rateLimit } = require('../middleware/auth');
require('dotenv').config();

const router = express.Router();

// Kết nối database
const dbPath = path.join(__dirname, '..', 'database', 'demo.db');
const db = new sqlite3.Database(dbPath);

// Rate limiting cho auth routes
const authRateLimit = rateLimit(10, 15 * 60 * 1000); // 10 requests per 15 minutes

/**
 * POST /api/auth/register
 * Đăng ký tài khoản mới
 */
router.post('/register', authRateLimit, async (req, res) => {
    try {
        const { username, email, password, full_name } = req.body;

        // Validation
        if (!username || !email || !password) {
            return res.status(400).json({
                error: 'Missing required fields',
                message: 'Vui lòng điền đầy đủ thông tin bắt buộc'
            });
        }

        if (password.length < 6) {
            return res.status(400).json({
                error: 'Password too short',
                message: 'Mật khẩu phải có ít nhất 6 ký tự'
            });
        }

        // Kiểm tra email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return res.status(400).json({
                error: 'Invalid email format',
                message: 'Định dạng email không hợp lệ'
            });
        }

        // Kiểm tra username và email đã tồn tại chưa
        db.get(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            [username, email],
            async (err, row) => {
                if (err) {
                    console.error('Database error:', err.message);
                    return res.status(500).json({
                        error: 'Database error',
                        message: 'Lỗi cơ sở dữ liệu'
                    });
                }

                if (row) {
                    return res.status(409).json({
                        error: 'User already exists',
                        message: 'Tên đăng nhập hoặc email đã được sử dụng'
                    });
                }

                try {
                    // Hash password
                    const saltRounds = 10;
                    const password_hash = await bcrypt.hash(password, saltRounds);

                    // Tạo user mới
                    db.run(
                        'INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
                        [username, email, password_hash, full_name || username],
                        function(err) {
                            if (err) {
                                console.error('Insert error:', err.message);
                                return res.status(500).json({
                                    error: 'Failed to create user',
                                    message: 'Không thể tạo tài khoản'
                                });
                            }

                            const userId = this.lastID;

                            // Tạo JWT token
                            const token = generateToken(userId, username, email);

                            res.status(201).json({
                                success: true,
                                message: 'Đăng ký thành công',
                                data: {
                                    user: {
                                        id: userId,
                                        username: username,
                                        email: email,
                                        full_name: full_name || username
                                    },
                                    token: token
                                }
                            });
                        }
                    );
                } catch (hashError) {
                    console.error('Hash error:', hashError.message);
                    res.status(500).json({
                        error: 'Password hashing failed',
                        message: 'Lỗi mã hóa mật khẩu'
                    });
                }
            }
        );
    } catch (error) {
        console.error('Register error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * POST /api/auth/login
 * Đăng nhập
 */
router.post('/login', authRateLimit, (req, res) => {
    try {
        const { username, password } = req.body;

        // Validation
        if (!username || !password) {
            return res.status(400).json({
                error: 'Missing credentials',
                message: 'Vui lòng nhập tên đăng nhập và mật khẩu'
            });
        }

        // Tìm user (có thể đăng nhập bằng username hoặc email)
        db.get(
            'SELECT id, username, email, password_hash, full_name, avatar_url FROM users WHERE (username = ? OR email = ?) AND is_active = 1',
            [username, username],
            async (err, user) => {
                if (err) {
                    console.error('Database error:', err.message);
                    return res.status(500).json({
                        error: 'Database error',
                        message: 'Lỗi cơ sở dữ liệu'
                    });
                }

                if (!user) {
                    return res.status(401).json({
                        error: 'Invalid credentials',
                        message: 'Tên đăng nhập hoặc mật khẩu không đúng'
                    });
                }

                try {
                    // Kiểm tra password
                    const passwordMatch = await bcrypt.compare(password, user.password_hash);

                    if (!passwordMatch) {
                        return res.status(401).json({
                            error: 'Invalid credentials',
                            message: 'Tên đăng nhập hoặc mật khẩu không đúng'
                        });
                    }

                    // Tạo JWT token
                    const token = generateToken(user.id, user.username, user.email);

                    // Cập nhật thời gian đăng nhập cuối
                    db.run(
                        'UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                        [user.id]
                    );

                    res.json({
                        success: true,
                        message: 'Đăng nhập thành công',
                        data: {
                            user: {
                                id: user.id,
                                username: user.username,
                                email: user.email,
                                full_name: user.full_name,
                                avatar_url: user.avatar_url
                            },
                            token: token
                        }
                    });
                } catch (compareError) {
                    console.error('Password compare error:', compareError.message);
                    res.status(500).json({
                        error: 'Authentication failed',
                        message: 'Lỗi xác thực'
                    });
                }
            }
        );
    } catch (error) {
        console.error('Login error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * POST /api/auth/verify-token
 * Xác thực token
 */
router.post('/verify-token', (req, res) => {
    try {
        const { token } = req.body;

        if (!token) {
            return res.status(400).json({
                error: 'Token required',
                message: 'Token là bắt buộc'
            });
        }

        const decoded = verifyToken(token);

        if (!decoded) {
            return res.status(401).json({
                error: 'Invalid token',
                message: 'Token không hợp lệ'
            });
        }

        // Kiểm tra user còn tồn tại
        db.get(
            'SELECT id, username, email, full_name, avatar_url FROM users WHERE id = ? AND is_active = 1',
            [decoded.userId],
            (err, user) => {
                if (err) {
                    console.error('Database error:', err.message);
                    return res.status(500).json({
                        error: 'Database error',
                        message: 'Lỗi cơ sở dữ liệu'
                    });
                }

                if (!user) {
                    return res.status(401).json({
                        error: 'User not found',
                        message: 'Người dùng không tồn tại'
                    });
                }

                res.json({
                    success: true,
                    message: 'Token hợp lệ',
                    data: {
                        user: {
                            id: user.id,
                            username: user.username,
                            email: user.email,
                            full_name: user.full_name,
                            avatar_url: user.avatar_url
                        }
                    }
                });
            }
        );
    } catch (error) {
        console.error('Verify token error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * POST /api/auth/refresh-token
 * Làm mới token
 */
router.post('/refresh-token', (req, res) => {
    try {
        const { token } = req.body;

        if (!token) {
            return res.status(400).json({
                error: 'Token required',
                message: 'Token là bắt buộc'
            });
        }

        const decoded = verifyToken(token);

        if (!decoded) {
            return res.status(401).json({
                error: 'Invalid token',
                message: 'Token không hợp lệ'
            });
        }

        // Tạo token mới
        const newToken = generateToken(decoded.userId, decoded.username, decoded.email);

        res.json({
            success: true,
            message: 'Token đã được làm mới',
            data: {
                token: newToken
            }
        });
    } catch (error) {
        console.error('Refresh token error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * POST /api/auth/logout
 * Đăng xuất (có thể mở rộng để blacklist token)
 */
router.post('/logout', (req, res) => {
    // Trong phiên bản đơn giản này, chỉ trả về thành công
    // Có thể mở rộng để thêm token vào blacklist
    res.json({
        success: true,
        message: 'Đăng xuất thành công'
    });
});

module.exports = router;
