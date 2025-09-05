# AI Server

A FastAPI-based AI server for recommendation systems.

## Quick Start

### Using Docker (Recommended)

#### Development Environment with Hot Reload
```bash
# Windows
docker-scripts.bat dev-up

# Unix/Linux/Mac
./docker-scripts.sh dev-up
```

#### Production Environment
```bash
# Windows
docker-scripts.bat prod-up

# Unix/Linux/Mac
./docker-scripts.sh prod-up
```

### Manual Setup

1. Install dependencies:
```bash
poetry install
```

2. Run the application:
```bash
poetry run server
```

## Docker Features

- **Hot Reload**: Development environment automatically restarts when code changes
- **Volume Mounting**: Local changes are immediately reflected in the container
- **Easy Management**: Use helper scripts for common Docker operations
- **Production Ready**: Separate production configuration without dev dependencies

## API Documentation

Once running, access the API documentation at:
- **Swagger UI**: http://localhost:9999/docs
- **ReDoc**: http://localhost:9999/redoc

## Docker Commands

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker usage instructions.

### Quick Commands
```bash
# Start development with hot reload
docker-scripts.bat dev-up     # Windows
./docker-scripts.sh dev-up    # Unix/Linux/Mac

# View logs
docker-scripts.bat dev-logs   # Windows
./docker-scripts.sh dev-logs  # Unix/Linux/Mac

# Stop containers
docker-scripts.bat dev-down   # Windows
./docker-scripts.sh dev-down  # Unix/Linux/Mac
```

## Configuration

Configuration files are located in the `config/` directory:
- `local.yaml` - Main configuration file
- `restaurant_data.yaml` - Restaurant data configuration

Environment variables can be set in `.env` file.

## Development

The project uses Poetry for dependency management and includes:
- FastAPI for the web framework
- Uvicorn as the ASGI server
- Loguru for logging
- SQLAlchemy for database operations
- Redis for caching
- MongoDB for NoSQL operations

## Project Structure

```
├── src/ai_server/          # Main application code
├── config/                 # Configuration files
├── tests/                  # Test files
├── tasks/                  # Task definitions
├── logs/                   # Log files
├── outputs/                # Output files
├── docker-compose.yml      # Production Docker setup
├── docker-compose.dev.yml  # Development Docker setup
├���─ Dockerfile              # Production Docker image
├── Dockerfile.dev          # Development Docker image
└── docker-scripts.*        # Helper scripts for Docker management
```