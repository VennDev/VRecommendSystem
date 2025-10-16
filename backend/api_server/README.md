# API Server - VRecommendation System

A high-performance Go-based API gateway that serves as the central hub for authentication, request routing, and communication between frontend clients and AI services. Built with Fiber framework for maximum performance and scalability.

## Features

- **Authentication & Authorization**: JWT-based auth with Google OAuth integration
- **API Gateway**: Centralized request routing and proxy to AI Server
- **High Performance**: Built with Go Fiber for exceptional speed
- **Redis Caching**: Intelligent caching layer for improved performance
- **Request Proxying**: Seamless communication with AI Server
- **Logging & Monitoring**: Structured logging with Zap logger
- **Security**: CORS, rate limiting, and secure middleware
- **Docker Ready**: Production-ready containerization
- **RESTful API**: Clean, documented API endpoints

## Quick Start

### Using Docker (Recommended)

1. **Navigate to API Server directory:**
```bash
cd backend/api_server
```

2. **Configure environment:**
```bash
cp example-env .env
# Edit .env with your configuration
```

3. **Start with Docker Compose:**
```bash
# Development mode
docker-compose up -d

# Or use the main compose from project root
cd ../../
docker-compose up api_server -d
```

4. **Verify the server is running:**
```bash
curl http://localhost:2030/api/v1/ping
# Response: {"message": "pong", "timestamp": "2024-01-01T12:00:00Z"}
```

### Manual Development Setup

1. **Prerequisites:**
```bash
# Install Go 1.24.4 or later
go version

# Install dependencies
go mod download
```

2. **Configure environment:**
```bash
cp example-env .env
# Edit .env file with your settings
```

3. **Run the server:**
```bash
# Development mode
go run main.go

# Or build and run
go build -o api_server
./api_server
```

## Configuration

### Environment Variables

Create a `.env` file based on `example-env`:

```env
# Development Environment
STATUS_DEV=dev

# Server Configuration
HOST_ADDRESS=0.0.0.0
HOST_PORT=2030
HOST_READ_TIMEOUT=60

# AI Server Configuration
AI_SERVER_URL=http://localhost:9999
AI_SERVER_TIMEOUT=30

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRATION_HOURS=24

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URL=http://localhost:2030/auth/google/callback

# Database Configuration (if needed)
DATABASE_URL=postgres://user:password@localhost/dbname?sslmode=disable

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
```

### Configuration Files

The `config/` directory structure:
```
config/
├── config.yaml         # Main application configuration
├── cors.yaml          # CORS settings
├── database.yaml      # Database configurations
└── oauth.yaml         # OAuth provider settings
```

## API Documentation

### Base URL
```
http://localhost:2030/api/v1
```

### Authentication

#### Google OAuth Login
```bash
# Initiate Google OAuth flow
GET /auth/google

# OAuth callback (handled automatically)
GET /auth/google/callback

# Logout
POST /auth/logout
```

#### JWT Token Usage
Include the JWT token in the Authorization header for protected endpoints:
```bash
Authorization: Bearer <your_jwt_token>
```

### Core Endpoints

#### Health Check
```bash
# Simple ping endpoint
GET /api/v1/ping
Response: {
    "message": "pong",
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0"
}

# Detailed health status
GET /api/v1/health
Response: {
    "status": "healthy",
    "services": {
        "redis": "connected",
        "ai_server": "reachable",
        "database": "connected"
    },
    "uptime": "2h30m45s",
    "memory_usage": "45.2MB"
}
```

#### User Management
```bash
# Get current user profile
GET /api/v1/user/profile
Headers: Authorization: Bearer <token>
Response: {
    "user_id": "12345",
    "email": "user@example.com",
    "name": "John Doe",
    "avatar": "https://...",
    "created_at": "2024-01-01T10:00:00Z"
}

# Update user profile
PUT /api/v1/user/profile
Headers: Authorization: Bearer <token>
Body: {
    "name": "John Updated",
    "preferences": {
        "theme": "dark",
        "notifications": true
    }
}
```

#### AI Server Proxy Endpoints

The API server proxies requests to the AI server with authentication:

```bash
# List AI models (proxied to AI server)
GET /api/v1/ai/models
Headers: Authorization: Bearer <token>

# Create AI model (proxied to AI server)
POST /api/v1/ai/models
Headers: Authorization: Bearer <token>
Body: {
    "model_id": "my_model",
    "model_type": "collaborative_filtering",
    "parameters": {...}
}

# List scheduled tasks (proxied to AI server)
GET /api/v1/ai/tasks
Headers: Authorization: Bearer <token>

# Create data chef (proxied to AI server)
POST /api/v1/ai/data-chefs/csv
Headers: Authorization: Bearer <token>
Body: {
    "data_chef_id": "csv_data",
    "file_path": "/path/to/file.csv"
}
```

#### Cache Management
```bash
# Clear cache
DELETE /api/v1/cache
Headers: Authorization: Bearer <token>

# Get cache statistics
GET /api/v1/cache/stats
Headers: Authorization: Bearer <token>
Response: {
    "total_keys": 1247,
    "memory_usage": "15.2MB",
    "hit_ratio": 0.85,
    "operations": {
        "gets": 15420,
        "sets": 3240,
        "deletes": 120
    }
}
```

## Architecture

### Project Structure

```
backend/api_server/
├── app/                    # Application core
│   ├── controllers/        # HTTP request handlers
│   ├── middleware/         # Custom middleware
│   ├── models/            # Data models and structs
│   └── services/          # Business logic services
├── config/                # Configuration files
├── global/                # Global variables and constants
├── internal/              # Internal application logic
│   ├── auth/              # Authentication logic
│   ├── cache/             # Redis cache operations
│   ├── database/          # Database operations
│   ├── initialize/        # Application initialization
│   └── proxy/             # AI server proxy logic
├── pkg/                   # Reusable packages
│   ├── logger/            # Logging utilities
│   ├── response/          # HTTP response helpers
│   └── utils/             # Common utilities
├── platform/              # Platform-specific code
├── tests/                 # Test files
├── user_logs/             # User activity logs
├── logs/                  # Application logs
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker compose configuration
├── go.mod                 # Go modules
├── go.sum                 # Go modules checksum
├── main.go               # Application entry point
└── Makefile              # Build commands
```

### Key Components

#### 1. Authentication Service (`internal/auth/`)
- JWT token generation and validation
- Google OAuth integration
- User session management
- Role-based access control

#### 2. Proxy Service (`internal/proxy/`)
- Request forwarding to AI server
- Response transformation
- Error handling and retry logic
- Request/response logging

#### 3. Cache Service (`internal/cache/`)
- Redis connection management
- Cache strategies and TTL management
- Cache invalidation patterns
- Performance monitoring

#### 4. Middleware Stack (`app/middleware/`)
- CORS handling
- Rate limiting
- Request logging
- Authentication verification
- Error recovery

## Security Features

### Authentication Flow

1. **User Authentication:**
   - Google OAuth integration
   - JWT token generation
   - Secure token storage recommendations

2. **Request Authorization:**
   - JWT token validation
   - Role-based permissions
   - API key validation (optional)

3. **Security Headers:**
   - CORS configuration
   - Security headers injection
   - Request sanitization

### Example Authentication Implementation

```go
// JWT middleware example
func JWTMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        token := c.Get("Authorization")
        if token == "" {
            return c.Status(401).JSON(fiber.Map{
                "error": "Authorization token required"
            })
        }
        
        // Validate JWT token
        claims, err := ValidateJWT(token)
        if err != nil {
            return c.Status(401).JSON(fiber.Map{
                "error": "Invalid token"
            })
        }
        
        // Store user info in context
        c.Locals("user", claims)
        return c.Next()
    }
}
```

## Request Proxy System

The API server acts as an intelligent proxy to the AI server:

### Proxy Features

1. **Request Transformation:**
   - Add authentication headers
   - Request body validation
   - URL path translation

2. **Response Processing:**
   - Error standardization
   - Response caching
   - Metrics collection

3. **Error Handling:**
   - Circuit breaker pattern
   - Retry mechanisms
   - Graceful degradation

### Proxy Configuration Example

```go
type ProxyConfig struct {
    AIServerURL     string        `json:"ai_server_url"`
    Timeout         time.Duration `json:"timeout"`
    MaxRetries      int           `json:"max_retries"`
    CircuitBreaker  bool          `json:"circuit_breaker"`
}
```

## Monitoring & Logging

### Logging

The server uses structured logging with Zap:

```go
// Log levels: debug, info, warn, error, fatal
logger.Info("Server started",
    zap.String("host", config.Host),
    zap.Int("port", config.Port),
    zap.String("env", config.Environment),
)
```

### Health Monitoring

```bash
# Check server health
curl http://localhost:2030/api/v1/health

# Monitor logs
tail -f logs/api_server.log

# Docker logs
docker logs -f vrecom_api_server
```

### Metrics Collection

The server collects metrics for:
- Request counts and response times
- Error rates and types
- Cache hit/miss ratios
- AI server response times
- Authentication success rates

## Testing

### Running Tests

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run specific test package
go test ./app/controllers

# Run tests with verbose output
go test -v ./...

# Generate coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Example Test Structure

```go
func TestPingHandler(t *testing.T) {
    app := fiber.New()
    app.Get("/ping", controllers.PingHandler)
    
    req := httptest.NewRequest("GET", "/ping", nil)
    resp, _ := app.Test(req)
    
    assert.Equal(t, 200, resp.StatusCode)
}
```

## Development

### Development Workflow

1. **Setup development environment:**
```bash
git clone <repository>
cd backend/api_server
cp example-env .env
go mod download
```

2. **Run with hot reload:**
```bash
# Install air for hot reloading
go install github.com/cosmtrek/air@latest

# Run with hot reload
air
```

3. **Code formatting and linting:**
```bash
# Format code
go fmt ./...

# Run linter (install golangci-lint first)
golangci-lint run
```

### Adding New Endpoints

1. **Create controller:**
```go
// app/controllers/my_controller.go
func MyNewHandler(c *fiber.Ctx) error {
    return c.JSON(fiber.Map{
        "message": "Hello from new endpoint"
    })
}
```

2. **Add route:**
```go
// internal/initialize/router.go
func InitRouter(app *fiber.App) {
    api := app.Group("/api/v1")
    api.Get("/my-endpoint", controllers.MyNewHandler)
}
```

3. **Add tests:**
```go
// tests/my_controller_test.go
func TestMyNewHandler(t *testing.T) {
    // Test implementation
}
```

## Docker Configuration

### Development Docker

```dockerfile
FROM golang:1.24.4 AS development
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
EXPOSE 2030
CMD ["go", "run", "main.go"]
```

### Production Docker

```dockerfile
FROM golang:1.24.4 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o main .

FROM golang:1.24.4
WORKDIR /app
COPY --from=builder /app/main .
COPY --from=builder /app/config ./config
CMD ["./main"]
```

### Docker Commands

```bash
# Build image
docker build -t vrecom-api-server .

# Run container
docker run -p 2030:2030 --env-file .env vrecom-api-server

# View logs
docker logs -f container_name

# Enter container
docker exec -it container_name /bin/bash
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
```bash
# Find process using port 2030
lsof -i :2030
# Kill the process
kill -9 <PID>
```

2. **Redis connection issues:**
```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping
# Check Redis in Docker
docker exec -it vrecom_redis redis-cli ping
```

3. **AI Server unreachable:**
```bash
# Test AI Server connection
curl http://localhost:9999/api/v1/health
# Check network connectivity from container
docker exec -it vrecom_api_server curl http://ai_server:9999/api/v1/health
```

4. **JWT token issues:**
```bash
# Decode JWT token (use online JWT decoder)
# Check token expiration
# Verify JWT secret configuration
```

### Debugging

Enable debug mode:
```env
STATUS_DEV=dev
LOG_LEVEL=debug
```

View detailed logs:
```bash
# Local logs
tail -f logs/api_server.log

# Docker logs
docker logs -f vrecom_api_server

# Follow logs with specific level
grep "ERROR" logs/api_server.log
```

## Performance Optimization

### Optimization Strategies

1. **Connection Pooling:**
   - Configure Redis connection pool
   - Database connection pooling
   - HTTP client connection reuse

2. **Caching:**
   - Response caching for frequent requests
   - User session caching
   - AI server response caching

3. **Resource Management:**
   - Configure appropriate timeouts
   - Set memory limits
   - Use connection limits

### Performance Monitoring

```bash
# Monitor Go application metrics
go tool pprof http://localhost:2030/debug/pprof/profile

# Monitor memory usage
go tool pprof http://localhost:2030/debug/pprof/heap

# Check goroutines
go tool pprof http://localhost:2030/debug/pprof/goroutine
```

## Production Deployment

### Security Checklist

- [ ] Change default JWT secret
- [ ] Configure proper CORS origins
- [ ] Set up HTTPS/TLS
- [ ] Configure rate limiting
- [ ] Set secure headers
- [ ] Use environment-specific configs
- [ ] Enable request logging
- [ ] Set up monitoring and alerting

### Environment Configuration

```env
# Production environment
STATUS_DEV=prod
LOG_LEVEL=warn

# Security
JWT_SECRET=your-production-jwt-secret
GOOGLE_CLIENT_SECRET=your-production-google-secret

# Performance
REDIS_POOL_SIZE=20
HTTP_TIMEOUT=30s
MAX_CONNECTIONS=1000
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow Go coding standards (`go fmt`, `golangci-lint`)
4. Add tests for new functionality
5. Update documentation
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Create a Pull Request

### Code Style Guidelines

- Follow standard Go conventions
- Use meaningful variable and function names
- Add comments for exported functions
- Keep functions small and focused
- Handle errors appropriately
- Write tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE.txt](../../LICENSE.txt) file for details.

## Support

- **API Documentation**: Visit `/api/v1/docs` (if Swagger is enabled)
- **Health Check**: Use `/api/v1/health` to verify service status
- **Issues**: Create an issue on GitHub
- **Logs**: Check `logs/` directory for detailed application logs
- **Performance**: Use built-in profiling endpoints for optimization