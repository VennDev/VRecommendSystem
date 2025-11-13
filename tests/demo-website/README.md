# VRecommendation Demo Website

A simple demonstration website that integrates with the VRecommendation API server to showcase product recommendations and user interaction tracking.

## Features

- **User Authentication**: Simple login/register system
- **Product Catalog**: Browse all available products
- **User Actions Tracking**:
  - Track product views
  - Track product likes
  - Store all user interactions
- **AI Recommendations**: Get personalized recommendations from the AI server via API server
- **JSON Data Storage**: All data stored in JSON files (users, products, actions)

## Prerequisites

- Node.js 14+ installed
- VRecommendation API Server running on `http://localhost:2030`
- VRecommendation AI Server running on `http://localhost:9999`

## Installation

1. Navigate to the demo website directory:
```bash
cd tests/demo-website
```

2. Install dependencies:
```bash
npm install
```

## Usage

1. Start the demo website:
```bash
npm start
```

Or for development with auto-reload:
```bash
npm run dev
```

2. Open your browser and navigate to:
```
http://localhost:3500
```

3. Login or create a new account:
   - Enter any username and password
   - If the account doesn't exist, it will be created automatically

4. Browse products and interact:
   - Click on products to view them (tracked as "view" action)
   - Click the heart icon to like/unlike products (tracked as "like" action)
   - View AI-powered recommendations based on your interactions

## Configuration

You can configure the following environment variables:

```bash
PORT=3500                                    # Demo website port
API_SERVER_URL=http://localhost:2030        # API server URL
```

## Data Storage

All data is stored in JSON files under the `data/` directory:

- **users.json**: User accounts (username, password, id)
- **products.json**: Product catalog (id, name, description, price, category)
- **user_actions.json**: User interactions (userId, productId, action, timestamp)

## API Endpoints

### Public Routes

- `GET /` - Home page (redirects to login or dashboard)
- `GET /login` - Login page
- `POST /login` - Login/register endpoint
- `GET /logout` - Logout endpoint

### Protected Routes (Require Authentication)

- `GET /dashboard` - Main dashboard with products and recommendations
- `GET /api/products` - Get all products
- `GET /api/products/:id` - Get product details (tracks view)
- `POST /api/products/:id/like` - Like a product
- `DELETE /api/products/:id/like` - Unlike a product
- `GET /api/recommendations` - Get AI recommendations from API server
- `GET /api/user/actions` - Get user's action history

## Integration with VRecommendation System

The demo website integrates with the main VRecommendation system:

1. **API Server Integration**:
   - Uses the `/api/v1/recommend` endpoint to fetch recommendations
   - Proxies requests through the API server for authentication

2. **User Action Tracking**:
   - All user interactions (views, likes) are logged
   - Data can be used to train recommendation models

3. **Recommendation Flow**:
   ```
   User Action → Demo Website → API Server → AI Server → Recommendations
   ```

## Sample Data

The system comes with 5 sample products:

1. Product A (Electronics) - $100
2. Product B (Clothing) - $200
3. Product C (Electronics) - $150
4. Product D (Books) - $80
5. Product E (Electronics) - $250

## Development

### Project Structure

```
demo-website/
├── server.js           # Main Express server
├── package.json        # Node.js dependencies
├── views/              # EJS templates
│   ├── login.ejs      # Login page
│   └── dashboard.ejs  # Main dashboard
├── data/              # JSON data storage
│   ├── users.json     # User accounts
│   ├── products.json  # Product catalog
│   └── user_actions.json  # User interactions
└── README.md          # This file
```

### Adding New Products

Edit `data/products.json` and add new product objects:

```json
{
  "id": 6,
  "name": "Product F",
  "description": "Description F",
  "price": 300,
  "category": "electronics"
}
```

## Troubleshooting

1. **Cannot connect to API server**:
   - Make sure the API server is running on port 2030
   - Check the `API_SERVER_URL` environment variable

2. **No recommendations shown**:
   - Ensure the AI server is running on port 9999
   - Make sure you have trained models available
   - Check the API server logs for errors

3. **Port already in use**:
   - Change the port using the `PORT` environment variable
   ```bash
   PORT=3600 npm start
   ```

## License

MIT
