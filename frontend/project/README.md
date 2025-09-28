# VRecommendation Frontend

A modern React TypeScript application for managing AI recommendation models.

## Features

- 🤖 AI Model Management
- 📊 Real-time Dashboard
- 🔄 Task Scheduling
- 📈 Data Pipeline Management
- 🔐 Google OAuth Authentication
- 🌙 Dark/Light Theme Support

## Quick Start

1. Install dependencies:
```bash
npm install
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Update API URLs in `.env` if needed (defaults work for local development)

4. Start development server:
```bash
npm run dev
```

## Configuration

### API URLs

All API configurations are centralized in `src/config/api.ts`. You can:

1. **For development**: Use default localhost URLs
2. **For production**: Set environment variables in `.env`:
   ```
   VITE_AI_SERVER_URL=https://your-ai-server.com
   VITE_AUTH_SERVER_URL=https://your-auth-server.com
   ```

### Environment Variables

- `VITE_AI_SERVER_URL`: AI Server base URL
- `VITE_AUTH_SERVER_URL`: Authentication server base URL

## Project Structure

```
src/
├── components/          # React components
├── contexts/           # React contexts (Auth, Theme)
├── services/           # API service layer
├── config/            # Configuration files
└── types/             # TypeScript type definitions
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Authentication

The app uses Google OAuth for authentication. Make sure your backend is configured with proper Google OAuth credentials.

## API Integration

All API calls are centralized in `src/services/api.ts` and use configuration from `src/config/api.ts`. This makes it easy to:

- Change API URLs for different environments
- Add new endpoints
- Modify request configurations
- Handle authentication consistently