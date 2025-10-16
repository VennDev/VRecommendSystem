@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  AI Server - VRecommendation System
echo ================================================
echo.

:: Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: pyproject.toml not found. Please run this script from the AI Server directory.
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
echo Starting AI Server in development mode with hot reload...
echo.
if exist "docker-compose.dev.yml" (
    docker-compose -f docker-compose.dev.yml up -d
    echo.
    echo SUCCESS: AI Server started in development mode
    echo Access: http://localhost:9999
    echo API Docs: http://localhost:9999/docs
    echo Health Check: http://localhost:9999/api/v1/health
) else (
    echo Development mode using local Poetry installation...
    echo Checking Poetry installation...
    poetry --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Poetry not found. Please install Poetry first.
        echo Visit: https://python-poetry.org/docs/
        pause
        exit /b 1
    )
    echo Installing dependencies...
    poetry install
    echo Starting server...
    poetry run server
)
goto :end

:prod
echo Starting AI Server in production mode...
echo.
docker-compose up -d
echo.
echo SUCCESS: AI Server started in production mode
echo Access: http://localhost:9999
echo API Docs: http://localhost:9999/docs
echo Health Check: http://localhost:9999/api/v1/health
goto :end

:build
echo Building AI Server Docker image...
echo.
docker-compose build --no-cache
echo SUCCESS: Build completed
goto :end

:logs
echo Showing AI Server logs...
echo Press Ctrl+C to exit logs
echo.
if exist "docker-compose.dev.yml" (
    docker-compose -f docker-compose.dev.yml logs -f
) else (
    docker-compose logs -f
)
goto :end

:stop
echo Stopping AI Server...
echo.
if exist "docker-compose.dev.yml" (
    docker-compose -f docker-compose.dev.yml down
) else (
    docker-compose down
)
echo SUCCESS: AI Server stopped
goto :end

:clean
echo.
echo WARNING: This will remove all AI Server containers, volumes, and images
set /p REPLY="Are you sure? (y/N) "
if /i "%REPLY%"=="y" (
    echo Cleaning up AI Server...
    if exist "docker-compose.dev.yml" (
        docker-compose -f docker-compose.dev.yml down -v --rmi all
    ) else (
        docker-compose down -v --rmi all
    )
    echo SUCCESS: Cleanup completed
) else (
    echo Cleanup cancelled
)
goto :end

:install
echo Installing AI Server dependencies...
echo.
echo Checking Poetry installation...
poetry --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Poetry not found. Please install Poetry first.
    echo Visit: https://python-poetry.org/docs/
    pause
    exit /b 1
)
echo Installing dependencies...
poetry install
echo SUCCESS: Dependencies installed
goto :end

:test
echo Running AI Server tests...
echo.
echo Checking Poetry installation...
poetry --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Poetry not found. Please install Poetry first.
    pause
    exit /b 1
)
echo Running tests...
poetry run pytest tests/
goto :end

:help
echo AI Server - Windows Management Script
echo.
echo Usage: start.cmd [COMMAND]
echo.
echo Commands:
echo   dev             Start in development mode with hot reload (default)
echo   prod            Start in production mode
echo   build           Build Docker image
echo   logs            Show container logs
echo   stop            Stop the server
echo   clean           Remove all containers, volumes, and images
echo   install         Install dependencies using Poetry
echo   test            Run tests
echo   help            Show this help message
echo.
echo Examples:
echo   start.cmd                       # Start in development mode
echo   start.cmd dev                   # Start in development mode
echo   start.cmd prod                  # Start in production mode
echo   start.cmd build                 # Build Docker image
echo   start.cmd logs                  # Show logs
echo   start.cmd test                  # Run tests
echo.
echo Development Requirements:
echo   - Poetry (for local development)
echo   - Docker and Docker Compose (for containerized deployment)
echo   - Python 3.9+ (for local development)
echo.
echo Configuration:
echo   - Edit .env file for environment variables
echo   - Edit config/local.yaml for application settings
goto :end

:end
echo.
pause
