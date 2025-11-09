/*
  # Create Recommendation Test System Schema

  ## Overview
  This migration creates the database schema for a recommendation testing system where users can interact with products and receive personalized recommendations.

  ## New Tables
  
  ### `products`
  - `id` (uuid, primary key) - Unique product identifier
  - `name` (text) - Product name
  - `description` (text) - Product description
  - `category` (text) - Product category
  - `image_url` (text) - Product image URL
  - `price` (numeric) - Product price
  - `created_at` (timestamptz) - Creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### `user_interactions`
  - `id` (uuid, primary key) - Unique interaction identifier
  - `user_id` (text) - User identifier (can be anonymous session ID or auth user ID)
  - `product_id` (uuid, foreign key) - Reference to products table
  - `interaction_type` (text) - Type of interaction (view, like, dislike, rating)
  - `rating` (integer) - Rating value (1-5, nullable)
  - `created_at` (timestamptz) - Interaction timestamp

  ### `recommendations`
  - `id` (uuid, primary key) - Unique recommendation identifier
  - `user_id` (text) - User identifier
  - `product_id` (uuid, foreign key) - Recommended product
  - `model_id` (text) - AI model that generated the recommendation
  - `score` (numeric) - Recommendation confidence score
  - `created_at` (timestamptz) - Recommendation timestamp

  ## Security
  - Enable RLS on all tables
  - Allow public read access to products
  - Allow users to read their own interactions and recommendations
  - Allow users to create/update their own interactions
*/

-- Create products table
CREATE TABLE IF NOT EXISTS products (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text DEFAULT '',
  category text NOT NULL,
  image_url text NOT NULL,
  price numeric(10, 2) DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create user_interactions table
CREATE TABLE IF NOT EXISTS user_interactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  interaction_type text NOT NULL CHECK (interaction_type IN ('view', 'like', 'dislike', 'rating')),
  rating integer CHECK (rating >= 1 AND rating <= 5),
  created_at timestamptz DEFAULT now()
);

-- Create recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  model_id text NOT NULL,
  score numeric(10, 4) DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_product_id ON user_interactions(product_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_created_at ON user_interactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

-- Enable Row Level Security
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

-- RLS Policies for products table (public read access)
CREATE POLICY "Anyone can view products"
  ON products FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Only authenticated users can insert products"
  ON products FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Only authenticated users can update products"
  ON products FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Only authenticated users can delete products"
  ON products FOR DELETE
  TO authenticated
  USING (true);

-- RLS Policies for user_interactions table
CREATE POLICY "Users can view their own interactions"
  ON user_interactions FOR SELECT
  TO anon, authenticated
  USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub' OR user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can create their own interactions"
  ON user_interactions FOR INSERT
  TO anon, authenticated
  WITH CHECK (user_id = current_setting('request.jwt.claims', true)::json->>'sub' OR user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can update their own interactions"
  ON user_interactions FOR UPDATE
  TO anon, authenticated
  USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub' OR user_id = current_setting('app.user_id', true))
  WITH CHECK (user_id = current_setting('request.jwt.claims', true)::json->>'sub' OR user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can delete their own interactions"
  ON user_interactions FOR DELETE
  TO anon, authenticated
  USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub' OR user_id = current_setting('app.user_id', true));

-- RLS Policies for recommendations table
CREATE POLICY "Users can view their own recommendations"
  ON recommendations FOR SELECT
  TO anon, authenticated
  USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub' OR user_id = current_setting('app.user_id', true));

CREATE POLICY "System can create recommendations"
  ON recommendations FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "System can delete old recommendations"
  ON recommendations FOR DELETE
  TO authenticated
  USING (true);

-- Insert sample products
INSERT INTO products (name, description, category, image_url, price) VALUES
('Wireless Headphones', 'High-quality wireless headphones with noise cancellation', 'Electronics', 'https://images.pexels.com/photos/3394650/pexels-photo-3394650.jpeg', 99.99),
('Smart Watch', 'Fitness tracking smartwatch with heart rate monitor', 'Electronics', 'https://images.pexels.com/photos/437037/pexels-photo-437037.jpeg', 249.99),
('Coffee Maker', 'Programmable coffee maker with thermal carafe', 'Home & Kitchen', 'https://images.pexels.com/photos/324028/pexels-photo-324028.jpeg', 79.99),
('Yoga Mat', 'Non-slip yoga mat with carrying strap', 'Sports & Fitness', 'https://images.pexels.com/photos/3822356/pexels-photo-3822356.jpeg', 29.99),
('Running Shoes', 'Lightweight running shoes with cushioned sole', 'Sports & Fitness', 'https://images.pexels.com/photos/2529148/pexels-photo-2529148.jpeg', 89.99),
('Backpack', 'Water-resistant laptop backpack with multiple compartments', 'Bags & Luggage', 'https://images.pexels.com/photos/2905238/pexels-photo-2905238.jpeg', 49.99),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 'Home & Office', 'https://images.pexels.com/photos/1112598/pexels-photo-1112598.jpeg', 34.99),
('Water Bottle', 'Stainless steel insulated water bottle', 'Sports & Fitness', 'https://images.pexels.com/photos/3737553/pexels-photo-3737553.jpeg', 24.99),
('Bluetooth Speaker', 'Portable waterproof Bluetooth speaker', 'Electronics', 'https://images.pexels.com/photos/1279088/pexels-photo-1279088.jpeg', 59.99),
('Notebook Set', 'Premium notebook set with pen holder', 'Stationery', 'https://images.pexels.com/photos/159751/book-address-book-learning-learn-159751.jpeg', 19.99),
('Sunglasses', 'Polarized UV protection sunglasses', 'Fashion', 'https://images.pexels.com/photos/701877/pexels-photo-701877.jpeg', 79.99),
('Phone Case', 'Durable protective phone case', 'Electronics', 'https://images.pexels.com/photos/788946/pexels-photo-788946.jpeg', 14.99),
('Plant Pot', 'Ceramic plant pot with drainage hole', 'Home & Garden', 'https://images.pexels.com/photos/1084199/pexels-photo-1084199.jpeg', 22.99),
('Reading Light', 'Clip-on LED reading light', 'Home & Office', 'https://images.pexels.com/photos/2351290/pexels-photo-2351290.jpeg', 16.99),
('Dumbbell Set', '5kg adjustable dumbbell set', 'Sports & Fitness', 'https://images.pexels.com/photos/416717/pexels-photo-416717.jpeg', 44.99),
('Tea Set', 'Elegant porcelain tea set', 'Home & Kitchen', 'https://images.pexels.com/photos/1793037/pexels-photo-1793037.jpeg', 54.99),
('Wall Clock', 'Modern minimalist wall clock', 'Home & Decor', 'https://images.pexels.com/photos/1078057/pexels-photo-1078057.jpeg', 32.99),
('Keyboard', 'Mechanical gaming keyboard with RGB lighting', 'Electronics', 'https://images.pexels.com/photos/1772123/pexels-photo-1772123.jpeg', 119.99),
('Mouse Pad', 'Extended gaming mouse pad', 'Electronics', 'https://images.pexels.com/photos/2115256/pexels-photo-2115256.jpeg', 12.99),
('Candle Set', 'Scented candle set with holder', 'Home & Decor', 'https://images.pexels.com/photos/1123262/pexels-photo-1123262.jpeg', 27.99)
ON CONFLICT DO NOTHING;
