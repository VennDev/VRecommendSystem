@echo off
setlocal enabledelayedexpansion

:: Colors for output (Windows CMD doesn't support colors by default, but we'll use echo with formatting)
echo.
echo ================================================
echo  VRecommendation System - Windows Startup
echo ================================================
echo.

:: Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found. Copying from .env.example...
    if exist .env.example (
        copy .env.example .env >nul
        echo SUCCESS: .env file created successfully
        echo WARNING: Please edit .env file with your configuration before proceeding
        echo.
        pause
        exit /b 1
    ) else (
        echo ERROR: .env.example not found. Cannot create .env file
        pause
        exit /b 1
    )
)

echo SUCCESS: Configuration file found
echo.

:: Check if frontend .env exists
if not exist frontend\project\.env (
    echo WARNING: Frontend .env not found. Copying from .env.example...
    if exist frontend\project\.env.example (
        copy frontend\project\.env.example frontend\project\.env >nul
        echo SUCCESS: Frontend .env created
    )
)

:: Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=up

if "%COMMAND%"=="up" goto :start
if "%COMMAND%"=="start" goto :start
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="down" goto :stop
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="restart" goto :restart
if "%COMMAND%"=="logs" goto :logs
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="help" goto :help
goto :help

:start
echo Starting all services...
docker-compose up -d
echo.
echo ================================================
echo  Services Status
echo ================================================
docker-compose ps
echo.
echo ================================================
echo  Access URLs
echo ================================================
echo   Frontend:    http://localhost:5173
echo   API Server:  http://localhost:2030
echo   AI Server:   http://localhost:9999
echo   Prometheus:  http://localhost:9090
echo.
echo SUCCESS: All services started successfully!
goto :end

:build
echo Building all Docker images...
docker-compose build
echo SUCCESS: Build completed
goto :end

:stop
echo Stopping all services...
docker-compose down
echo SUCCESS: All services stopped
goto :end

:restart
echo Restarting all services...
docker-compose restart
echo SUCCESS: All services restarted
goto :end

:logs
set SERVICE=%2
if "%SERVICE%"=="" (
    echo Showing logs for all services...
    docker-compose logs -f
) else (
    echo Showing logs for %SERVICE%...
    docker-compose logs -f %SERVICE%
)
goto :end

:clean
echo.
echo WARNING: This will remove all containers, volumes, and images
set /p REPLY="Are you sure? (y/N) "
if /i "%REPLY%"=="y" (
    echo Cleaning up...
    docker-compose down -v --rmi all
    echo SUCCESS: Cleanup completed
) else (
    echo Cleanup cancelled
)
goto :end

:status
echo ================================================
echo  Services Status
echo ================================================
docker-compose ps
goto :end

:help
echo VRecommendation System - Windows Docker Management Script
echo.
echo Usage: start.cmd [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   up, start       Start all services (default)
echo   build           Build all Docker images
echo   down, stop      Stop all services
echo   restart         Restart all services
echo   logs [service]  Show logs (optionally for specific service)
echo   status          Show status of all services
echo   clean           Remove all containers, volumes, and images
echo   help            Show this help message
echo.
echo Examples:
echo   start.cmd up                    # Start all services
echo   start.cmd build                 # Build images
echo   start.cmd logs                  # Show all logs
echo   start.cmd logs api_server       # Show API server logs
echo   start.cmd clean                 # Clean everything
goto :end

:end
echo.
pause
