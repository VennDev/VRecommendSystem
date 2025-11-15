-- Create interactions table for recommendation system
CREATE TABLE IF NOT EXISTS interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    rating FLOAT NOT NULL DEFAULT 1.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data for testing
INSERT INTO interactions (user_id, item_id, rating) VALUES
('user1', 'item1', 5.0),
('user1', 'item2', 4.0),
('user1', 'item3', 3.0),
('user2', 'item1', 4.5),
('user2', 'item4', 5.0),
('user3', 'item2', 3.5),
('user3', 'item3', 4.5),
('user3', 'item5', 5.0),
('user4', 'item1', 5.0),
('user4', 'item3', 4.0),
('user4', 'item4', 3.5),
('user5', 'item2', 4.5),
('user5', 'item4', 5.0),
('user5', 'item5', 4.0);
