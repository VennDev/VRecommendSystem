const express = require('express');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const { authenticateToken, optionalAuth, rateLimit } = require('../middleware/auth');
require('dotenv').config();

const router = express.Router();

// Kết nối database
const dbPath = path.join(__dirname, '..', 'database', 'demo.db');
const db = new sqlite3.Database(dbPath);

// Cấu hình VRecommendation API
const VRECOMMENDATION_API_URL = process.env.VRECOMMENDATION_API_BASE_URL || 'http://localhost:9999/api/v1';
const DEFAULT_MODEL_ID = process.env.DEFAULT_MODEL_ID || 'default_model';

// Rate limiting cho recommendations API
const recommendationsRateLimit = rateLimit(30, 15 * 60 * 1000); // 30 requests per 15 minutes

/**
 * GET /api/recommendations/for-user/:userId
 * Lấy gợi ý sản phẩm cho user từ VRecommendation API
 */
router.get('/for-user/:userId', recommendationsRateLimit, optionalAuth, async (req, res) => {
    try {
        const userId = req.params.userId;
        const { model_id = DEFAULT_MODEL_ID, n = 10 } = req.query;

        // Validate parameters
        if (!userId) {
            return res.status(400).json({
                error: 'User ID required',
                message: 'ID người dùng là bắt buộc'
            });
        }

        const numRecommendations = Math.min(50, Math.max(1, parseInt(n) || 10));

        try {
            // Gọi VRecommendation API
            const recommendationUrl = `${VRECOMMENDATION_API_URL}/recommend/${userId}/${model_id}/${numRecommendations}`;
            console.log(`Calling VRecommendation API: ${recommendationUrl}`);

            const response = await axios.get(recommendationUrl, {
                timeout: 10000, // 10 seconds timeout
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Frontend-Demo/1.0'
                }
            });

            const recommendationData = response.data;
            console.log('VRecommendation API response:', recommendationData);

            // Nếu API trả về danh sách product IDs, lấy thông tin chi tiết từ database
            if (recommendationData && recommendationData.recommendations) {
                const productIds = recommendationData.recommendations;

                if (productIds.length === 0) {
                    return res.json({
                        success: true,
                        message: 'Không có gợi ý sản phẩm',
                        data: {
                            recommendations: [],
                            user_id: userId,
                            model_id: model_id,
                            total: 0
                        }
                    });
                }

                // Tạo placeholders cho SQL IN clause
                const placeholders = productIds.map(() => '?').join(',');

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
                    WHERE p.id IN (${placeholders})
                    ORDER BY CASE p.id ${productIds.map((id, index) => `WHEN ${id} THEN ${index}`).join(' ')} END
                `;

                const queryParams = [req.user ? req.user.id : null, ...productIds];

                db.all(query, queryParams, (err, products) => {
                    if (err) {
                        console.error('Database error:', err.message);
                        return res.status(500).json({
                            error: 'Database error',
                            message: 'Lỗi cơ sở dữ liệu'
                        });
                    }

                    // Thêm điểm số gợi ý nếu có
                    const productsWithScores = products.map(product => ({
                        ...product,
                        recommendation_score: recommendationData.scores ?
                            recommendationData.scores[product.id] || 0 : null
                    }));

                    res.json({
                        success: true,
                        message: 'Lấy gợi ý sản phẩm thành công',
                        data: {
                            recommendations: productsWithScores,
                            user_id: userId,
                            model_id: model_id,
                            total: productsWithScores.length,
                            api_response: recommendationData
                        }
                    });
                });
            } else {
                // Trường hợp API trả về format khác
                res.json({
                    success: true,
                    message: 'Nhận được phản hồi từ VRecommendation API',
                    data: {
                        recommendations: [],
                        user_id: userId,
                        model_id: model_id,
                        total: 0,
                        api_response: recommendationData
                    }
                });
            }

        } catch (apiError) {
            console.error('VRecommendation API error:', apiError.message);

            if (apiError.code === 'ECONNREFUSED') {
                return res.status(503).json({
                    error: 'VRecommendation service unavailable',
                    message: 'Dịch vụ gợi ý tạm thời không khả dụng',
                    fallback: true
                });
            }

            if (apiError.response) {
                return res.status(apiError.response.status).json({
                    error: 'VRecommendation API error',
                    message: apiError.response.data?.message || 'Lỗi từ dịch vụ gợi ý',
                    details: apiError.response.data
                });
            }

            // Fallback: trả về sản phẩm phổ biến
            const fallbackQuery = `
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
                ORDER BY p.rating DESC, p.review_count DESC
                LIMIT ?
            `;

            db.all(fallbackQuery, [req.user ? req.user.id : null, numRecommendations], (err, products) => {
                if (err) {
                    console.error('Fallback database error:', err.message);
                    return res.status(500).json({
                        error: 'Service error',
                        message: 'Lỗi dịch vụ gợi ý'
                    });
                }

                res.json({
                    success: true,
                    message: 'Sử dụng gợi ý dự phòng (sản phẩm phổ biến)',
                    data: {
                        recommendations: products,
                        user_id: userId,
                        model_id: model_id,
                        total: products.length,
                        fallback: true,
                        error: apiError.message
                    }
                });
            });
        }

    } catch (error) {
        console.error('Get recommendations error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * GET /api/recommendations/for-me
 * Lấy gợi ý sản phẩm cho user hiện tại
 */
router.get('/for-me', recommendationsRateLimit, authenticateToken, async (req, res) => {
    try {
        const userId = req.user.id;
        const { model_id = DEFAULT_MODEL_ID, n = 10 } = req.query;

        // Forward request to the main recommendation endpoint
        req.params.userId = userId.toString();
        return router.handle(
            { ...req, url: `/for-user/${userId}`, params: { userId: userId.toString() } },
            res
        );

    } catch (error) {
        console.error('Get my recommendations error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * GET /api/recommendations/similar/:productId
 * Lấy sản phẩm tương tự (fallback khi không có VRecommendation)
 */
router.get('/similar/:productId', recommendationsRateLimit, optionalAuth, (req, res) => {
    try {
        const productId = parseInt(req.params.productId);
        const { limit = 6 } = req.query;

        if (!productId || productId < 1) {
            return res.status(400).json({
                error: 'Invalid product ID',
                message: 'ID sản phẩm không hợp lệ'
            });
        }

        const limitNum = Math.min(20, Math.max(1, parseInt(limit)));

        // Lấy thông tin sản phẩm gốc
        db.get('SELECT * FROM products WHERE id = ?', [productId], (err, originalProduct) => {
            if (err) {
                console.error('Database error:', err.message);
                return res.status(500).json({
                    error: 'Database error',
                    message: 'Lỗi cơ sở dữ liệu'
                });
            }

            if (!originalProduct) {
                return res.status(404).json({
                    error: 'Product not found',
                    message: 'Không tìm thấy sản phẩm'
                });
            }

            // Tìm sản phẩm tương tự (cùng category, giá tương đương)
            const query = `
                SELECT
                    p.*,
                    c.name as category_name,
                    c.icon as category_icon,
                    CASE WHEN ul.user_id IS NOT NULL THEN 1 ELSE 0 END as is_liked,
                    ABS(p.price - ?) as price_diff
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN user_interactions ul ON p.id = ul.product_id
                    AND ul.user_id = ?
                    AND ul.interaction_type = 'like'
                WHERE p.id != ?
                    AND p.category_id = ?
                    AND p.price BETWEEN ? AND ?
                ORDER BY p.rating DESC, price_diff ASC, p.review_count DESC
                LIMIT ?
            `;

            const priceMin = originalProduct.price * 0.5; // 50% of original price
            const priceMax = originalProduct.price * 2.0; // 200% of original price

            db.all(query, [
                originalProduct.price,
                req.user ? req.user.id : null,
                productId,
                originalProduct.category_id,
                priceMin,
                priceMax,
                limitNum
            ], (err, similarProducts) => {
                if (err) {
                    console.error('Database error:', err.message);
                    return res.status(500).json({
                        error: 'Database error',
                        message: 'Lỗi cơ sở dữ liệu'
                    });
                }

                res.json({
                    success: true,
                    message: 'Lấy sản phẩm tương tự thành công',
                    data: {
                        original_product: originalProduct,
                        similar_products: similarProducts,
                        total: similarProducts.length
                    }
                });
            });
        });

    } catch (error) {
        console.error('Get similar products error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * POST /api/recommendations/feedback
 * Gửi feedback về gợi ý (để cải thiện model)
 */
router.post('/feedback', recommendationsRateLimit, authenticateToken, (req, res) => {
    try {
        const userId = req.user.id;
        const { product_id, action, rating } = req.body;

        // Validation
        if (!product_id || !action) {
            return res.status(400).json({
                error: 'Missing required fields',
                message: 'Thiếu thông tin bắt buộc'
            });
        }

        const validActions = ['like', 'dislike', 'view', 'purchase', 'ignore'];
        if (!validActions.includes(action)) {
            return res.status(400).json({
                error: 'Invalid action',
                message: 'Hành động không hợp lệ'
            });
        }

        // Lưu feedback vào database
        const feedbackData = {
            user_id: userId,
            product_id: parseInt(product_id),
            interaction_type: action,
            rating: rating ? parseInt(rating) : null,
            interaction_data: JSON.stringify({
                source: 'recommendation',
                timestamp: new Date().toISOString()
            })
        };

        db.run(
            'INSERT INTO user_interactions (user_id, product_id, interaction_type, rating, interaction_data) VALUES (?, ?, ?, ?, ?)',
            [feedbackData.user_id, feedbackData.product_id, feedbackData.interaction_type, feedbackData.rating, feedbackData.interaction_data],
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
                    message: 'Đã ghi nhận phản hồi',
                    data: {
                        feedback_id: this.lastID,
                        action: action,
                        product_id: product_id
                    }
                });
            }
        );

    } catch (error) {
        console.error('Submit feedback error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

/**
 * GET /api/recommendations/stats
 * Thống kê về gợi ý sản phẩm
 */
router.get('/stats', recommendationsRateLimit, authenticateToken, (req, res) => {
    try {
        const userId = req.user.id;

        const statsQueries = {
            totalInteractions: `
                SELECT COUNT(*) as count
                FROM user_interactions
                WHERE user_id = ?
            `,
            likedProducts: `
                SELECT COUNT(*) as count
                FROM user_interactions
                WHERE user_id = ? AND interaction_type = 'like'
            `,
            viewedProducts: `
                SELECT COUNT(*) as count
                FROM user_interactions
                WHERE user_id = ? AND interaction_type = 'view'
            `,
            topCategories: `
                SELECT c.name, c.icon, COUNT(*) as interaction_count
                FROM user_interactions ui
                JOIN products p ON ui.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                WHERE ui.user_id = ?
                GROUP BY c.id, c.name, c.icon
                ORDER BY interaction_count DESC
                LIMIT 5
            `
        };

        const stats = {};
        let completedQueries = 0;
        const totalQueries = Object.keys(statsQueries).length;

        Object.entries(statsQueries).forEach(([key, query]) => {
            db.all(query, [userId], (err, result) => {
                if (err) {
                    console.error(`Stats query error (${key}):`, err.message);
                    stats[key] = key === 'topCategories' ? [] : 0;
                } else {
                    stats[key] = key === 'topCategories' ? result : (result[0]?.count || 0);
                }

                completedQueries++;
                if (completedQueries === totalQueries) {
                    res.json({
                        success: true,
                        message: 'Thống kê thành công',
                        data: {
                            user_id: userId,
                            stats: stats
                        }
                    });
                }
            });
        });

    } catch (error) {
        console.error('Get recommendation stats error:', error.message);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Lỗi máy chủ nội bộ'
        });
    }
});

module.exports = router;
