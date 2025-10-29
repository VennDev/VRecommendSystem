# Frontend - VRecommendation System

A modern, responsive React TypeScript application that provides a comprehensive dashboard for managing AI recommendation models, scheduling tasks, and monitoring system performance. Built with cutting-edge technologies for optimal user experience.

## Features

- **AI Model Management**: Create, configure, and monitor recommendation models
- **Real-time Dashboard**: Interactive charts and system metrics visualization
- **Task Scheduling**: Visual interface for managing automated ML tasks
- **Data Pipeline Management**: Configure and monitor data chefs and sources
- **Google OAuth Authentication**: Secure login with Google integration
- **Dark/Light Theme**: Toggle between themes with persistent preferences
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Real-time Updates**: Live data updates and notifications
- **Analytics & Insights**: Comprehensive system performance analytics
- **Modern UI/UX**: Built with Tailwind CSS and DaisyUI components

## Quick Start

### Using Docker (Recommended)

1. **Navigate to frontend directory:**
```bash
cd frontend/project
```

2. **Start with Docker Compose:**
```bash
# Development mode with hot reload
docker-compose up -d

# Or from project root
cd ../../
docker-compose up frontend -d
```

3. **Access the application:**
- **Development**: http://localhost:5173
- **Production**: http://localhost:5173 (or configured port)

### Manual Development Setup

1. **Prerequisites:**
```bash
# Install Node.js 18+ and npm
node --version  # Should be 18.x or higher
npm --version
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API endpoints
```

4. **Start development server:**
```bash
npm run dev
```

5. **Open in browser:**
```
http://localhost:5173
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Endpoints
VITE_API_SERVER_URL=http://localhost:2030
VITE_AI_SERVER_URL=http://localhost:9999
```

### API Configuration

The application automatically configures API endpoints based on environment variables. You can also modify `src/config/api.ts`:

```typescript
export const API_CONFIG = {
  API_SERVER: import.meta.env.VITE_API_SERVER_URL || 'http://localhost:2030',
  AI_SERVER: import.meta.env.VITE_AI_SERVER_URL || 'http://localhost:9999',
}
```

## Architecture

### Project Structure

```
frontend/project/
├── public/                 # Static assets
│   ├── icons/             # Application icons
│   ├── images/            # Images and graphics
│   └── manifest.json      # PWA manifest
├── src/                   # Source code
│   ├── components/        # React components
│   │   ├── common/        # Reusable UI components
│   │   ├── forms/         # Form components
│   │   ├── layout/        # Layout components
│   │   └── ui/            # Base UI components
│   ├── contexts/          # React contexts
│   │   ├── AuthContext.tsx    # Authentication state
│   │   ├── ThemeContext.tsx   # Theme management
│   │   └── NotificationContext.tsx # Notifications
│   ├── hooks/             # Custom React hooks
│   │   ├── useApi.ts      # API interaction hooks
│   │   ├── useAuth.ts     # Authentication hooks
│   │   └── useWebSocket.ts # Real-time updates
│   ├── pages/             # Page components
│   │   ├── Dashboard/     # Main dashboard
│   │   ├── Models/        # Model management
│   │   ├── Tasks/         # Task scheduling
│   │   ├── DataChefs/     # Data pipeline management
│   │   ├── Analytics/     # System analytics
│   │   └── Settings/      # User settings
│   ├── services/          # API services
│   │   ├── api.ts         # Base API service
│   │   ├── auth.ts        # Authentication service
│   │   ├── models.ts      # Model management service
│   │   └── websocket.ts   # WebSocket service
│   ├── types/             # TypeScript type definitions
│   │   ├── api.ts         # API response types
│   │   ├── models.ts      # Model-related types
│   │   └── user.ts        # User-related types
│   ├── utils/             # Utility functions
│   │   ├── format.ts      # Data formatting
│   │   ├── validation.ts  # Form validation
│   │   └── constants.ts   # Application constants
│   ├── styles/            # Styling files
│   │   ├── globals.css    # Global styles
│   │   └── components.css # Component-specific styles
│   ├── App.tsx            # Main App component
│   ├── main.tsx           # Application entry point
│   └── vite-env.d.ts      # Vite type definitions
├── index.html             # HTML template
├── package.json           # Dependencies and scripts
├── tailwind.config.js     # Tailwind CSS configuration
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
└── Dockerfile             # Docker configuration
```

### Key Components

#### 1. Authentication System (`src/contexts/AuthContext.tsx`)
- Google OAuth integration
- JWT token management
- Protected route handling
- User session persistence

#### 2. API Service Layer (`src/services/`)
- Centralized API communication
- Error handling and retry logic
- Request/response interceptors
- Type-safe API calls

#### 3. Real-time Features (`src/hooks/useWebSocket.ts`)
- Live model training updates
- Real-time metrics display
- System status monitoring
- Push notifications

#### 4. Theme System (`src/contexts/ThemeContext.tsx`)
- Dark/light mode toggle
- Theme persistence
- Component theme adaptation
- System preference detection

## User Interface

### Main Dashboard

The dashboard provides an overview of:
- **System Status**: Health of API server, AI server, and databases
- **Active Models**: Currently running recommendation models
- **Recent Tasks**: Latest scheduled tasks and their status
- **Performance Metrics**: System performance charts and statistics
- **Quick Actions**: Common operations like creating models or scheduling tasks

### Model Management

Comprehensive model management interface:
- **Model Gallery**: Visual display of all available models
- **Create Model Wizard**: Step-by-step model creation process
- **Model Configuration**: Advanced parameter tuning interface
- **Training Progress**: Real-time training progress tracking
- **Performance Analytics**: Model accuracy and performance metrics

### Task Scheduling

Intuitive task scheduling system:
- **Calendar View**: Visual task scheduling calendar
- **Task Templates**: Pre-configured task templates
- **Dependency Management**: Set up task dependencies
- **Execution History**: View past task executions and results
- **Real-time Monitoring**: Live task execution status

### Data Chef Management

Data pipeline configuration interface:
- **Source Configuration**: Set up various data sources (CSV, SQL, NoSQL, API)
- **Data Preview**: Preview data before processing
- **Transformation Rules**: Configure data transformation logic
- **Validation Settings**: Set up data quality checks
- **Performance Monitoring**: Track data processing performance

## Authentication & Security

### Google OAuth Integration

The application uses Google OAuth for secure authentication:

1. **Login Flow:**
   - User clicks "Sign in with Google"
   - Redirected to Google OAuth consent screen
   - After consent, user is redirected back with authorization code
   - Frontend exchanges code for JWT token via API server
   - Token is stored securely and used for API authentication

2. **Token Management:**
   - Automatic token refresh
   - Secure token storage
   - Token expiration handling
   - Logout functionality

### Security Features

- **HTTPS Enforcement**: Redirects HTTP to HTTPS in production
- **CSRF Protection**: Cross-site request forgery protection
- **XSS Prevention**: Content sanitization and CSP headers
- **Secure Headers**: Security headers implementation
- **Route Protection**: Private routes require authentication

## Features Deep Dive

### Real-time Dashboard Features

```typescript
// Example of real-time metrics component
const MetricsDisplay: React.FC = () => {
  const { data: metrics, error } = useWebSocket('/api/v1/metrics');

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Active Models"
        value={metrics?.activeModels || 0}
        trend={metrics?.modelTrend}
        icon={<BrainIcon />}
      />
      <MetricCard
        title="Training Tasks"
        value={metrics?.runningTasks || 0}
        trend={metrics?.taskTrend}
        icon={<TaskIcon />}
      />
      {/* More metric cards */}
    </div>
  );
};
```

### Model Creation Wizard

Step-by-step model creation process:

1. **Model Type Selection**: Choose from collaborative filtering, content-based, or hybrid models
2. **Data Source Configuration**: Select and configure data sources
3. **Parameter Tuning**: Adjust model hyperparameters with helpful tooltips
4. **Validation Setup**: Configure cross-validation and evaluation metrics
5. **Training Configuration**: Set training schedule and resource allocation
6. **Review & Deploy**: Final review before model deployment

### Advanced Task Scheduling

```typescript
// Example task scheduling interface
interface TaskScheduleConfig {
  name: string;
  modelId: string;
  schedule: {
    type: 'cron' | 'interval' | 'once';
    expression: string;
    timezone: string;
  };
  dataChefs: {
    interactions: string;
    userFeatures?: string;
    itemFeatures?: string;
  };
  notifications: {
    onSuccess: boolean;
    onFailure: boolean;
    email?: string[];
  };
}
```

## Available Scripts

### Development Scripts

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Run TypeScript type checking
npm run type-check

# Run ESLint for code quality
npm run lint

# Fix ESLint issues automatically
npm run lint:fix

# Run Prettier for code formatting
npm run format

# Check Prettier formatting
npm run format:check
```

### Testing Scripts

```bash
# Run unit tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run E2E tests (if configured)
npm run test:e2e
```

### Build & Deployment Scripts

```bash
# Build for production
npm run build

# Build and analyze bundle size
npm run build:analyze

# Build for specific environment
npm run build:staging
npm run build:production

# Deploy to staging
npm run deploy:staging

# Deploy to production
npm run deploy:production
```

## Development

### Development Workflow

1. **Setup development environment:**
```bash
git clone <repository>
cd frontend/project
npm install
cp .env.example .env
```

2. **Start development server:**
```bash
npm run dev
```

3. **Development practices:**
   - Use TypeScript for type safety
   - Follow React best practices
   - Write reusable components
   - Use custom hooks for complex logic
   - Implement proper error boundaries

### Code Style Guidelines

- **TypeScript**: Use strict type checking
- **Components**: Functional components with hooks
- **Styling**: Tailwind CSS utility classes
- **State Management**: React Context for global state
- **File Naming**: PascalCase for components, camelCase for utilities
- **Import Order**: External libraries, internal modules, relative imports

### Adding New Features

1. **Create component:**
```typescript
// src/components/MyNewComponent.tsx
import React from 'react';

interface MyNewComponentProps {
  title: string;
  onAction: () => void;
}

export const MyNewComponent: React.FC<MyNewComponentProps> = ({
  title,
  onAction
}) => {
  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <h2 className="card-title">{title}</h2>
        <div className="card-actions justify-end">
          <button className="btn btn-primary" onClick={onAction}>
            Action
          </button>
        </div>
      </div>
    </div>
  );
};
```

2. **Add API service:**
```typescript
// src/services/myService.ts
import { api } from './api';

export const myService = {
  async getData(): Promise<MyData[]> {
    const response = await api.get('/api/v1/my-data');
    return response.data;
  },

  async createData(data: CreateMyData): Promise<MyData> {
    const response = await api.post('/api/v1/my-data', data);
    return response.data;
  }
};
```

3. **Create custom hook:**
```typescript
// src/hooks/useMyData.ts
import { useState, useEffect } from 'react';
import { myService } from '../services/myService';

export const useMyData = () => {
  const [data, setData] = useState<MyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await myService.getData();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error, refetch: fetchData };
};
```

## Docker Configuration

### Development Docker Setup

```dockerfile
# Development Dockerfile
FROM node:18-alpine AS development

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Production Docker Setup

```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS production

WORKDIR /app
RUN npm install -g serve

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

EXPOSE 5173

CMD ["sh", "-c", "serve -s dist -l ${FRONTEND_PORT:-5173}"]
```

### Docker Commands

```bash
# Build development image
docker build -f Dockerfile.dev -t vrecom-frontend-dev .

# Run development container
docker run -p 5173:5173 -v $(pwd):/app vrecom-frontend-dev

# Build production image
docker build -t vrecom-frontend .

# Run production container
docker run -p 5173:5173 vrecom-frontend
```

## Troubleshooting

### Common Issues

1. **Development server won't start:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check port availability
lsof -i :5173
```

2. **API connection issues:**
```bash
# Verify API server is running
curl http://localhost:2030/api/v1/ping

# Check environment variables
echo $VITE_API_SERVER_URL

# Check browser network tab for CORS issues
```

3. **Build issues:**
```bash
# Clean build directory
rm -rf dist

# Run type checking
npm run type-check

# Check for linting errors
npm run lint
```

4. **Authentication problems:**
```bash
# Check Google OAuth configuration
# Verify redirect URLs in Google Console
# Check browser console for errors
# Verify JWT token in localStorage
```

### Debug Mode

Enable debug mode by setting Vite's development mode:
```bash
npm run dev
```

This provides:
- Detailed error logging
- API request/response logging
- Component render tracking
- State change monitoring

## Progressive Web App (PWA)

The application includes PWA features:

- **Offline Capability**: Basic offline functionality
- **Install Prompt**: Users can install the app on their devices
- **Push Notifications**: Real-time notifications support
- **App Manifest**: Proper app metadata for installation
- **Service Worker**: Background sync and caching

### PWA Configuration

```javascript
// vite.config.ts PWA plugin configuration
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
      manifest: {
        name: 'VRecommendation Dashboard',
        short_name: 'VRecom',
        description: 'AI Recommendation System Management Dashboard',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          }
        ]
      }
    })
  ]
});
```

## Performance Optimization

### Optimization Strategies

1. **Code Splitting**: Lazy load routes and components
2. **Bundle Analysis**: Analyze and optimize bundle size
3. **Image Optimization**: Use next-gen image formats
4. **Caching**: Implement proper caching strategies
5. **Tree Shaking**: Remove unused code
6. **Compression**: Enable gzip/brotli compression

### Performance Monitoring

```typescript
// Performance monitoring utility
export const performanceMonitor = {
  markStart: (name: string) => {
    performance.mark(`${name}-start`);
  },

  markEnd: (name: string) => {
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);

    const measures = performance.getEntriesByName(name);
    const measure = measures[measures.length - 1];
    console.log(`${name} took ${measure.duration.toFixed(2)}ms`);
  }
};
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the coding standards and guidelines
4. Write tests for new functionality
5. Update documentation
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Create a Pull Request

### Code Review Guidelines

- Ensure type safety with TypeScript
- Follow React best practices
- Write meaningful component and function names
- Add proper error handling
- Include unit tests for complex logic
- Update documentation for new features
- Verify responsive design works on all devices

## Support

- **Live Documentation**: Available at the running application
- **Component Storybook**: Run `npm run storybook` (if configured)
- **Issues**: Create an issue on GitHub
- **Development Console**: Check browser console for detailed error messages
- **Network Tab**: Monitor API calls in browser developer tools

## Acknowledgments

- **React Team**: For the amazing React framework
- **Vite Team**: For the lightning-fast build tool
- **Tailwind CSS**: For the utility-first CSS framework
- **DaisyUI**: For the beautiful component library
- **TypeScript Team**: For type safety and developer experience
