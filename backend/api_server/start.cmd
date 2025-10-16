@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  API Server - VRecommendation System
echo ================================================
echo.

:: Check if we're in the correct directory
if not exist "go.mod" (
    echo ERROR: go.mod not found. Please run this script from the API Server directory.
    echo Current directory: %CD%
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found. Copying from example-env...
    if exist "example-env" (
        copy example-env .env >nul
        echo SUCCESS: .env file created successfully
        echo WARNING: Please edit .env file with your configuration before proceeding
        echo.
        pause
        exit /b 1
    ) else (
        echo ERROR: example-env not found. Cannot create .env file
        pause
        exit /b 1
    )
)

echo SUCCESS: Configuration file found
echo.

:: Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=dev

if "%COMMAND%"=="dev" goto :dev
if "%COMMAND%"=="prod" goto :prod
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="logs" goto :logs
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="install" goto :install
if "%COMMAND%"=="test" goto :test
if "%COMMAND%"=="help" goto :help
goto :help

:dev
echo Starting API Server in development mode...
echo.
echo Checking Go installation...
go version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Go not found. Please install Go first.
    echo Visit: https://golang.org/dl/
    pause
    exit /b 1
)
echo Installing dependencies...
go mod download
echo Starting server in development mode...
echo Access: http://localhost:2030
echo Health Check: http://localhost:2030/api/v1/ping
echo.
go run main.go
goto :end

:prod
echo Starting API Server in production mode...
echo.
docker-compose up -d
echo.
echo SUCCESS: API Server started in production mode
echo Access: http://localhost:2030
echo Health Check: http://localhost:2030/api/v1/ping
goto :end

:build
set BUILD_TYPE=%2
if "%BUILD_TYPE%"=="docker" goto :build_docker

echo Building API Server binary...
echo.
echo Checking Go installation...
go version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Go not found. Please install Go first.
    pause
    exit /b 1
)
echo Building...
go build -o api_server.exe main.go
if exist "api_server.exe" (
    echo SUCCESS: Binary built successfully - api_server.exe
    echo Run with: api_server.exe
) else (
    echo ERROR: Build failed
)
goto :end

:build_docker
echo Building API Server Docker image...
echo.
docker-compose build --no-cache
echo SUCCESS: Docker build completed
goto :end

:logs
echo Showing API Server logs...
echo Press Ctrl+C to exit logs
echo.
docker-compose logs -f
goto :end

:stop
echo Stopping API Server...
echo.
docker-compose down
echo SUCCESS: API Server stopped
goto :end

:clean
echo.
echo WARNING: This will remove all API Server containers, volumes, and images
set /p REPLY="Are you sure? (y/N) "
if /i "%REPLY%"=="y" (
    echo Cleaning up API Server...
    docker-compose down -v --rmi all
    if exist "api_server.exe" (
        del api_server.exe
        echo Removed binary file
    )
    echo SUCCESS: Cleanup completed
) else (
    echo Cleanup cancelled
)
goto :end

:install
echo Installing API Server dependencies...
echo.
echo Checking Go installation...
go version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Go not found. Please install Go first.
    echo Visit: https://golang.org/dl/
    pause
    exit /b 1
)
echo Installing dependencies...
go mod download
go mod tidy
echo SUCCESS: Dependencies installed
goto :end

:test
echo Running API Server tests...
echo.
echo Checking Go installation...
go version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Go not found. Please install Go first.
    pause
    exit /b 1
)
echo Running tests...
go test ./...
echo.
echo Running tests with coverage...
go test -cover ./...
goto :end

:help
echo API Server - Windows Management Script
echo.
echo Usage: start.cmd [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   dev             Start in development mode (default)
echo   prod            Start in production mode with Docker
echo   build           Build Go binary
echo   build docker    Build Docker image
echo   logs            Show container logs
echo   stop            Stop the server
echo   clean           Remove all containers, volumes, images and binaries
echo   install         Install Go dependencies
echo   test            Run tests
echo   help            Show this help message
echo.
echo Examples:
echo   start.cmd                       # Start in development mode
echo   start.cmd dev                   # Start in development mode
echo   start.cmd prod                  # Start in production mode
echo   start.cmd build                 # Build Go binary
echo   start.cmd build docker          # Build Docker image
echo   start.cmd logs                  # Show logs
echo   start.cmd test                  # Run tests
echo.
echo Development Requirements:
echo   - Go 1.24.4+ (for local development)
echo   - Docker and Docker Compose (for containerized deployment)
echo.
echo Configuration:
echo   - Edit .env file for environment variables
echo   - Edit config/ files for application settings
echo.
echo Access URLs (after starting):
echo   - Health Check: http://localhost:2030/api/v1/ping
echo   - API Base: http://localhost:2030/api/v1/
goto :end

:end
echo.
pause
