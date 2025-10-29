const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const bcrypt = require('bcryptjs');

// Đường dẫn đến file database
const dbPath = path.join(__dirname, '..', 'database', 'demo.db');

// Tạo kết nối database
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Lỗi khi tạo database:', err.message);
        return;
    }
    console.log('✅ Đã kết nối thành công đến SQLite database');
});

// Khởi tạo các bảng
const initializeTables = () => {
    return new Promise((resolve, reject) => {
        // Bảng users
        const createUsersTable = `
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                avatar_url TEXT DEFAULT '/images/default-avatar.png',
                preferences TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        `;

        // Bảng categories
        const createCategoriesTable = `
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '📦',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `;

        // Bảng products
        const createProductsTable = `
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2) DEFAULT 0.00,
                category_id INTEGER,
                image_url TEXT DEFAULT '/images/default-product.png',
                rating DECIMAL(2,1) DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                stock_quantity INTEGER DEFAULT 0,
                is_featured INTEGER DEFAULT 0,
                tags TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        `;

        // Bảng user_interactions (likes, views, purchases)
        const createInteractionsTable = `
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL CHECK(interaction_type IN ('like', 'view', 'purchase', 'cart', 'wishlist')),
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                interaction_data TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        `;

        // Bảng user_sessions
        const createSessionsTable = `
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        `;

        // Tạo các bảng tuần tự
        db.serialize(() => {
            db.run(createUsersTable, (err) => {
                if (err) reject(err);
                else console.log('✅ Đã tạo bảng users');
            });

            db.run(createCategoriesTable, (err) => {
                if (err) reject(err);
                else console.log('✅ Đã tạo bảng categories');
            });

            db.run(createProductsTable, (err) => {
                if (err) reject(err);
                else console.log('✅ Đã tạo bảng products');
            });

            db.run(createInteractionsTable, (err) => {
                if (err) reject(err);
                else console.log('✅ Đã tạo bảng user_interactions');
            });

            db.run(createSessionsTable, (err) => {
                if (err) reject(err);
                else {
                    console.log('✅ Đã tạo bảng user_sessions');
                    resolve();
                }
            });
        });
    });
};

// Thêm dữ liệu mẫu
const seedSampleData = async () => {
    return new Promise(async (resolve, reject) => {
        try {
            // Hash password cho user mẫu
            const hashedPassword = await bcrypt.hash('123456', 10);

            // Dữ liệu categories
            const categories = [
                { name: 'Điện tử', description: 'Thiết bị điện tử và công nghệ', icon: '📱' },
                { name: 'Thời trang', description: 'Quần áo và phụ kiện', icon: '👕' },
                { name: 'Gia đình & Nhà cửa', description: 'Đồ dùng gia đình', icon: '🏠' },
                { name: 'Thể thao', description: 'Dụng cụ và trang phục thể thao', icon: '⚽' },
                { name: 'Sách & Văn phòng phẩm', description: 'Sách và đồ dùng văn phòng', icon: '📚' },
                { name: 'Làm đẹp & Sức khỏe', description: 'Mỹ phẩm và sản phẩm chăm sóc sức khỏe', icon: '💄' }
            ];

            // Users mẫu
            const users = [
                { username: 'demo_user', email: 'demo@example.com', password_hash: hashedPassword, full_name: 'Demo User' },
                { username: 'john_doe', email: 'john@example.com', password_hash: hashedPassword, full_name: 'John Doe' },
                { username: 'jane_smith', email: 'jane@example.com', password_hash: hashedPassword, full_name: 'Jane Smith' },
                { username: 'alice_wong', email: 'alice@example.com', password_hash: hashedPassword, full_name: 'Alice Wong' }
            ];

            // Products mẫu
            const products = [
                { name: 'iPhone 15 Pro', description: 'Điện thoại thông minh cao cấp từ Apple', price: 999.99, category_id: 1, rating: 4.8, review_count: 1250, stock_quantity: 50, is_featured: 1 },
                { name: 'Samsung Galaxy S24', description: 'Điện thoại Android flagship', price: 899.99, category_id: 1, rating: 4.6, review_count: 890, stock_quantity: 30, is_featured: 1 },
                { name: 'MacBook Pro M3', description: 'Laptop chuyên nghiệp cho sáng tạo', price: 1999.99, category_id: 1, rating: 4.9, review_count: 456, stock_quantity: 20, is_featured: 1 },
                { name: 'Áo polo nam', description: 'Áo polo cotton cao cấp', price: 29.99, category_id: 2, rating: 4.3, review_count: 234, stock_quantity: 100 },
                { name: 'Quần jeans nữ', description: 'Quần jeans skinny fit thời trang', price: 49.99, category_id: 2, rating: 4.5, review_count: 567, stock_quantity: 75 },
                { name: 'Bàn làm việc gỗ', description: 'Bàn làm việc hiện đại', price: 199.99, category_id: 3, rating: 4.4, review_count: 123, stock_quantity: 25 },
                { name: 'Ghế gaming', description: 'Ghế chơi game ergonomic', price: 299.99, category_id: 3, rating: 4.7, review_count: 345, stock_quantity: 15, is_featured: 1 },
                { name: 'Giày chạy bộ Nike', description: 'Giày thể thao chuyên dụng', price: 129.99, category_id: 4, rating: 4.6, review_count: 789, stock_quantity: 40 },
                { name: 'Bóng đá FIFA', description: 'Bóng đá chính thức', price: 39.99, category_id: 4, rating: 4.2, review_count: 156, stock_quantity: 60 },
                { name: 'Sách học JavaScript', description: 'Hướng dẫn lập trình JS từ cơ bản đến nâng cao', price: 24.99, category_id: 5, rating: 4.8, review_count: 234, stock_quantity: 80 },
                { name: 'Kem dưỡng da', description: 'Kem dưỡng ẩm chống lão hóa', price: 45.99, category_id: 6, rating: 4.5, review_count: 678, stock_quantity: 90 },
                { name: 'Serum vitamin C', description: 'Serum làm sáng da', price: 35.99, category_id: 6, rating: 4.7, review_count: 445, stock_quantity: 55 }
            ];

            console.log('🌱 Bắt đầu seed dữ liệu...');

            // Insert categories
            const insertCategory = db.prepare('INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)');
            for (let cat of categories) {
                insertCategory.run(cat.name, cat.description, cat.icon);
            }
            insertCategory.finalize();
            console.log('✅ Đã thêm categories');

            // Insert users
            const insertUser = db.prepare('INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)');
            for (let user of users) {
                insertUser.run(user.username, user.email, user.password_hash, user.full_name);
            }
            insertUser.finalize();
            console.log('✅ Đã thêm users');

            // Insert products
            const insertProduct = db.prepare(`
                INSERT INTO products (name, description, price, category_id, rating, review_count, stock_quantity, is_featured)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            `);
            for (let product of products) {
                insertProduct.run(
                    product.name,
                    product.description,
                    product.price,
                    product.category_id,
                    product.rating,
                    product.review_count,
                    product.stock_quantity,
                    product.is_featured || 0
                );
            }
            insertProduct.finalize();
            console.log('✅ Đã thêm products');

            // Thêm một số interactions mẫu
            const interactions = [
                { user_id: 1, product_id: 1, interaction_type: 'like', rating: 5 },
                { user_id: 1, product_id: 3, interaction_type: 'like', rating: 5 },
                { user_id: 1, product_id: 7, interaction_type: 'view' },
                { user_id: 2, product_id: 1, interaction_type: 'view' },
                { user_id: 2, product_id: 2, interaction_type: 'like', rating: 4 },
                { user_id: 3, product_id: 4, interaction_type: 'like', rating: 4 },
                { user_id: 3, product_id: 5, interaction_type: 'purchase', rating: 5 },
                { user_id: 4, product_id: 8, interaction_type: 'like', rating: 5 },
                { user_id: 4, product_id: 10, interaction_type: 'view' }
            ];

            const insertInteraction = db.prepare(`
                INSERT INTO user_interactions (user_id, product_id, interaction_type, rating)
                VALUES (?, ?, ?, ?)
            `);
            for (let interaction of interactions) {
                insertInteraction.run(
                    interaction.user_id,
                    interaction.product_id,
                    interaction.interaction_type,
                    interaction.rating || null
                );
            }
            insertInteraction.finalize();
            console.log('✅ Đã thêm user interactions');

            resolve();
        } catch (error) {
            reject(error);
        }
    });
};

// Hàm chính
const main = async () => {
    try {
        console.log('🚀 Bắt đầu khởi tạo database...\n');

        await initializeTables();
        console.log('\n📋 Hoàn thành tạo bảng!');

        await seedSampleData();
        console.log('\n🎉 Hoàn thành khởi tạo database và dữ liệu mẫu!');

        console.log('\n📊 Thông tin đăng nhập demo:');
        console.log('- Username: demo_user');
        console.log('- Email: demo@example.com');
        console.log('- Password: 123456');

        console.log('\n💡 Chạy lệnh sau để khởi động server:');
        console.log('npm run dev');

    } catch (error) {
        console.error('❌ Lỗi khi khởi tạo database:', error.message);
    } finally {
        db.close((err) => {
            if (err) {
                console.error('Lỗi khi đóng database:', err.message);
            } else {
                console.log('\n🔒 Đã đóng kết nối database');
            }
        });
    }
};

// Chạy script
main();
