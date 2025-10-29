const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const { authenticateToken, optionalAuth, rateLimit } = require('../middleware/auth');
require('dotenv').config();

const router = express.Router();

// Kết nối database
const dbPath = path.join(__dirname, '..', 'database', 'demo.db');
const db = new sqlite3.Database(dbPath);

// Rate limiting cho products API
const productsRateLimit = rateLimit(60, 15 * 60 * 1000); // 60 requests per 15 minutes

/**
 * GET /api/products
 * Lấy danh sách sản phẩm với phân trang và bộ lọc
 */
router.get('/', productsRateLimit, optionalAuth, (req, res) => {
    try {
        const {
            page = 1,
            limit = 12,
            category_id,
            featured,
            search,
            sort_by = 'created_at',
            sort_order = 'DESC',
            min_price,
            max_price
        } = req.query;

        // Validate pagination
        const pageNum = Math.max(1, parseInt(page));
        const limitNum = Math.min(50, Math.max(1, parseInt(limit))); // Max 50 items per page
        const offset = (pageNum - 1) * limitNum;

        // Build WHERE clause
        let whereConditions = [];
        let params = [];

        if (category_id) {
            whereConditions.push('p.category_id = ?');
            params.push(parseInt(category_id));
        }

        if (featured === 'true') {
            whereConditions.push('p.is_featured = 1');
        }

        if (search) {
            whereConditions.push('(p.name LIKE ? OR p.description LIKE ?)');
            const searchTerm = `%${search}%`;
            params.push(searchTerm, searchTerm);
        }

        if (min_price) {
            whereConditions.push('p.price >= ?');
            params.push(parseFloat(min_price));
        }

        if (max_price) {
            whereConditions.push('p.price <= ?');
            params.push(parseFloat(max_price));
        }

        const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

        // Validate sort parameters
        const validSortFields = ['name', 'price', 'rating', 'created_at', 'review_count'];
        const sortField = validSortFields.includes(sort_by) ? sort_by : 'created_at';
        const sortDirection = sort_order.toUpperCase() === 'ASC' ? 'ASC' : 'DESC';

        // Main query
        const query = `
            SELECT
                p.*,
                c.name as category_name,
                c.icon as category_icon,
                CASE WHEN ul.user_id IS NOT NULL THEN 1 ELSE 0 END as is_liked
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN user_interactions ul ON p.id = ul.product_id
                AND ul.user_id = ?
                AND ul.interaction_type = 'like'
            ${whereClause}
            ORDER BY p.${sortField} ${sortDirection}
            LIMIT ? OFFSET ?
        `;

        // Count query for pagination
        const countQuery = `
            SELECT COUNT(*) as total
            FROM products p
            ${whereClause}
        `;

        // Execute count query first
        const countParams = params.slice(); // Copy params for count query
        db.get(countQuery, countParams, (err, countResult) => {
            if (err) {
                console.error('Database error:', err.message);
                return res.status(500).json({
                    error: 'Database error',
                    message: 'Lỗi cơ sở dữ liệu'
                });
            }

            const total = countResult.total;
            const totalPages = Math.ceil(total / limitNum);

            // Execute main query
            const queryParams = [req.user ? req.user.id : null, ...params, limitNum, offset];
            db.all(query, queryParams, (err, rows) => {
                if (err) {
                    console.error('Database error:', err.message);
                    return res.status(500).json({
                        error: 'Database error',
                        message: 'Lỗi cơ sở dữ liệu'
                    });
                }

                res.json({
                    success: true,
                    data: {
                        products: rows,
                        pagination: {
                            current_page: pageNum,
                            total_pages: totalPages,
                            total_items: total,
                            items_per_page: limitNum,
                            has_next: pageNum < totalPages,
                            has_prev: pageNum > 1
                        },
                        filters: {
                            category_id: category_id || null,
                            featured: featured === 'true',
                            search: search || null,
                            sort_by: sortField,
                            sort_order: sortDirection,
                            min_price: min_price || null,
                            max_price: max_price || null
                        }
                    }
                });
            });
        });
    } catch (error) {
        console.error('Get products error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * GET /api/products/featured
 * Lấy sản phẩm nổi bật
 */
router.get('/featured', productsRateLimit, optionalAuth, (req, res) => {
    try {
        const limit = Math.min(20, Math.max(1, parseInt(req.query.limit) || 8));

        const query = `
            SELECT
                p.*,
                c.name as category_name,
                c.icon as category_icon,
                CASE WHEN ul.user_id IS NOT NULL THEN 1 ELSE 0 END as is_liked
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN user_interactions ul ON p.id = ul.product_id
                AND ul.user_id = ?
                AND ul.interaction_type = 'like'
            WHERE p.is_featured = 1
            ORDER BY p.rating DESC, p.review_count DESC
            LIMIT ?
        `;

        db.all(query, [req.user ? req.user.id : null, limit], (err, rows) => {
            if (err) {
                console.error('Database error:', err.message);
                return res.status(500).json({
                    error: 'Database error',
                    message: 'Lỗi cơ sở dữ liệu'
                });
            }

            res.json({
                success: true,
                data: {
                    products: rows
                }
            });
        });
    } catch (error) {
        console.error('Get featured products error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * GET /api/products/categories
 * Lấy danh sách categories
 */
router.get('/categories', productsRateLimit, (req, res) => {
    try {
        const query = `
            SELECT
                c.*,
                COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id, c.name, c.description, c.icon
            ORDER BY c.name ASC
        `;

        db.all(query, [], (err, rows) => {
            if (err) {
                console.error('Database error:', err.message);
                return res.status(500).json({
                    error: 'Database error',
                    message: 'Lỗi cơ sở dữ liệu'
                });
            }

            res.json({
                success: true,
                data: {
                    categories: rows
                }
            });
        });
    } catch (error) {
        console.error('Get categories error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * GET /api/products/:id
 * Lấy chi tiết sản phẩm
 */
router.get('/:id', productsRateLimit, optionalAuth, (req, res) => {
    try {
        const productId = parseInt(req.params.id);

        if (!productId || productId < 1) {
            return res.status(400).json({
                error: 'Invalid product ID',
                message: 'ID sản phẩm không hợp lệ'
            });
        }

        const query = `
            SELECT
                p.*,
                c.name as category_name,
                c.icon as category_icon,
                c.description as category_description,
                CASE WHEN ul.user_id IS NOT NULL THEN 1 ELSE 0 END as is_liked
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN user_interactions ul ON p.id = ul.product_id
                AND ul.user_id = ?
                AND ul.interaction_type = 'like'
            WHERE p.id = ?
        `;

        db.get(query, [req.user ? req.user.id : null, productId], (err, product) => {
            if (err) {
                console.error('Database error:', err.message);
                return res.status(500).json({
                    error: 'Database error',
                    message: 'Lỗi cơ sở dữ liệu'
                });
            }

            if (!product) {
                return res.status(404).json({
                    error: 'Product not found',
                    message: 'Không tìm thấy sản phẩm'
                });
            }

            // Ghi nhận lượt xem nếu user đã đăng nhập
            if (req.user) {
                db.run(
                    'INSERT INTO user_interactions (user_id, product_id, interaction_type) VALUES (?, ?, ?)',
                    [req.user.id, productId, 'view'],
                    (err) => {
                        if (err) {
                            console.error('Failed to record view:', err.message);
                        }
                    }
                );
            }

            res.json({
                success: true,
                data: {
                    product: product
                }
            });
        });
    } catch (error) {
        console.error('Get product detail error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * POST /api/products/:id/like
 * Thích/bỏ thích sản phẩm
 */
router.post('/:id/like', productsRateLimit, authenticateToken, (req, res) => {
    try {
        const productId = parseInt(req.params.id);
        const userId = req.user.id;

        if (!productId || productId < 1) {
            return res.status(400).json({
                error: 'Invalid product ID',
                message: 'ID sản phẩm không hợp lệ'
            });
        }

        // Kiểm tra sản phẩm tồn tại
        db.get('SELECT id FROM products WHERE id = ?', [productId], (err, product) => {
            if (err) {
                console.error('Database error:', err.message);
                return res.status(500).json({
                    error: 'Database error',
                    message: 'Lỗi cơ sở dữ liệu'
                });
            }

            if (!product) {
                return res.status(404).json({
                    error: 'Product not found',
                    message: 'Không tìm thấy sản phẩm'
                });
            }

            // Kiểm tra đã like chưa
            db.get(
                'SELECT id FROM user_interactions WHERE user_id = ? AND product_id = ? AND interaction_type = "like"',
                [userId, productId],
                (err, existingLike) => {
                    if (err) {
                        console.error('Database error:', err.message);
                        return res.status(500).json({
                            error: 'Database error',
                            message: 'Lỗi cơ sở dữ liệu'
                        });
                    }

                    if (existingLike) {
                        // Bỏ like
                        db.run(
                            'DELETE FROM user_interactions WHERE user_id = ? AND product_id = ? AND interaction_type = "like"',
                            [userId, productId],
                            function(err) {
                                if (err) {
                                    console.error('Database error:', err.message);
                                    return res.status(500).json({
                                        error: 'Database error',
                                        message: 'Lỗi cơ sở dữ liệu'
                                    });
                                }

                                res.json({
                                    success: true,
                                    message: 'Đã bỏ thích sản phẩm',
                                    data: {
                                        is_liked: false,
                                        action: 'unliked'
                                    }
                                });
                            }
                        );
                    } else {
                        // Thêm like
                        db.run(
                            'INSERT INTO user_interactions (user_id, product_id, interaction_type) VALUES (?, ?, "like")',
                            [userId, productId],
                            function(err) {
                                if (err) {
                                    console.error('Database error:', err.message);
                                    return res.status(500).json({
                                        error: 'Database error',
                                        message: 'Lỗi cơ sở dữ liệu'
                                    });
                                }

                                res.json({
                                    success: true,
                                    message: 'Đã thích sản phẩm',
                                    data: {
                                        is_liked: true,
                                        action: 'liked'
                                    }
                                });
                            }
                        );
                    }
                }
            );
        });
    } catch (error) {
        console.error('Like product error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * GET /api/products/user/liked
 * Lấy danh sách sản phẩm đã thích
 */
router.get('/user/liked', productsRateLimit, authenticateToken, (req, res) => {
    try {
        const userId = req.user.id;
        const { page = 1, limit = 12 } = req.query;

        const pageNum = Math.max(1, parseInt(page));
        const limitNum = Math.min(50, Math.max(1, parseInt(limit)));
        const offset = (pageNum - 1) * limitNum;

        const query = `
            SELECT
                p.*,
                c.name as category_name,
                c.icon as category_icon,
                ui.created_at as liked_at
            FROM user_interactions ui
            JOIN products p ON ui.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE ui.user_id = ? AND ui.interaction_type = 'like'
            ORDER BY ui.created_at DESC
            LIMIT ? OFFSET ?
        `;

        const countQuery = `
            SELECT COUNT(*) as total
            FROM user_interactions ui
            WHERE ui.user_id = ? AND ui.interaction_type = 'like'
        `;

        // Get total count
        db.get(countQuery, [userId], (err, countResult) => {
            if (err) {
                console.error('Database error:', err.message);
                return res.status(500).json({
                    error: 'Database error',
                    message: 'Lỗi cơ sở dữ liệu'
                });
            }

            const total = countResult.total;
            const totalPages = Math.ceil(total / limitNum);

            // Get liked products
            db.all(query, [userId, limitNum, offset], (err, rows) => {
                if (err) {
                    console.error('Database error:', err.message);
                    return res.status(500).json({
                        error: 'Database error',
                        message: 'Lỗi cơ sở dữ liệu'
                    });
                }

                res.json({
                    success: true,
                    data: {
                        products: rows.map(row => ({
                            ...row,
                            is_liked: true
                        })),
                        pagination: {
                            current_page: pageNum,
                            total_pages: totalPages,
                            total_items: total,
                            items_per_page: limitNum,
                            has_next: pageNum < totalPages,
                            has_prev: pageNum > 1
                        }
                    }
                });
            });
        });
    } catch (error) {
        console.error('Get liked products error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

module.exports = router;
