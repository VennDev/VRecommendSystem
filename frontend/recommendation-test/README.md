# Product Recommendation Test Website

This is a test website for the AI-powered recommendation system. Users can browse products, like/dislike them, rate them, and receive personalized recommendations based on their interactions.

## Features

- Browse products by category
- Like/Dislike products
- Rate products (1-5 stars)
- View product details
- Get personalized recommendations using AI models
- Track interaction statistics
- Anonymous session management

## Setup

1. Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5174`

## Environment Variables

- `VITE_SUPABASE_URL` - Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Your Supabase anonymous key
- `VITE_AI_SERVER_URL` - AI Server URL (default: http://localhost:9999)
- `VITE_API_SERVER_URL` - API Server URL (default: http://localhost:2030)

## How It Works

1. **User Interactions**: Users can interact with products through:
   - Viewing products
   - Liking/Disliking products
   - Rating products (1-5 stars)

2. **Data Storage**: All interactions are stored in Supabase database

3. **Recommendations**: When user requests recommendations:
   - The system calls the AI recommendation API with user ID and model ID
   - The AI model analyzes user's interaction history
   - Returns personalized product recommendations with confidence scores

4. **Session Management**: Each user gets a unique anonymous session ID stored in localStorage

## Technology Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS + DaisyUI
- Supabase
- Lucide React (icons)

## Database Schema

The app uses three main tables:

- `products` - Product catalog
- `user_interactions` - User interaction history
- `recommendations` - Generated recommendations

See the Supabase migration file for detailed schema.
