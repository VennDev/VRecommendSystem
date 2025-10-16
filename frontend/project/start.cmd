@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  Frontend - VRecommendation System
echo ================================================
echo.

:: Check if we're in the correct directory
if not exist "package.json" (
    echo ERROR: package.json not found. Please run this script from the Frontend directory.
    echo Current directory: %CD%
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found. Copying from .env.example...
    if exist ".env.example" (
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

:: Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=dev

if "%COMMAND%"=="dev" goto :dev
if "%COMMAND%"=="prod" goto :prod
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="preview" goto :preview
if "%COMMAND%"=="logs" goto :logs
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="install" goto :install
if "%COMMAND%"=="lint" goto :lint
if "%COMMAND%"=="test" goto :test
if "%COMMAND%"=="help" goto :help
goto :help

:dev
echo Starting Frontend in development mode...
echo.
if exist "node_modules" goto :start_dev
echo Installing dependencies first...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:start_dev
echo Starting development server...
echo Access: http://localhost:5173
echo.
npm run dev
goto :end

:prod
echo Starting Frontend in production mode with Docker...
echo.
docker-compose up -d
echo.
echo SUCCESS: Frontend started in production mode
echo Access: http://localhost:5173
goto :end

:build
set BUILD_TYPE=%2
if "%BUILD_TYPE%"=="docker" goto :build_docker

echo Building Frontend for production...
echo.
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js first.
    echo Visit: https://nodejs.org/
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Building...
call npm run build
if exist "dist" (
    echo SUCCESS: Build completed successfully
    echo Built files are in the 'dist' directory
    echo Run 'start.cmd preview' to preview the build
) else (
    echo ERROR: Build failed
)
goto :end

:build_docker
echo Building Frontend Docker image...
echo.
docker-compose build --no-cache
echo SUCCESS: Docker build completed
goto :end

:preview
echo Starting preview server for production build...
echo.
if not exist "dist" (
    echo ERROR: No build found. Run 'start.cmd build' first.
    pause
    exit /b 1
)
echo Preview: http://localhost:4173
echo.
npm run preview
goto :end

:logs
echo Showing Frontend logs...
echo Press Ctrl+C to exit logs
echo.
docker-compose logs -f
goto :end

:stop
echo Stopping Frontend...
echo.
docker-compose down
echo SUCCESS: Frontend stopped
goto :end

:clean
echo.
echo WARNING: This will remove containers, volumes, images, node_modules, and dist folder
set /p REPLY="Are you sure? (y/N) "
if /i "%REPLY%"=="y" (
    echo Cleaning up Frontend...
    docker-compose down -v --rmi all
    if exist "node_modules" (
        echo Removing node_modules...
        rmdir /s /q node_modules
    )
    if exist "dist" (
        echo Removing dist...
        rmdir /s /q dist
    )
    if exist "package-lock.json" (
        echo Removing package-lock.json...
        del package-lock.json
    )
    echo SUCCESS: Cleanup completed
) else (
    echo Cleanup cancelled
)
goto :end

:install
echo Installing Frontend dependencies...
echo.
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js first.
    echo Visit: https://nodejs.org/
    pause
    exit /b 1
)
echo Installing dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo SUCCESS: Dependencies installed
goto :end

:lint
echo Running Frontend linting...
echo.
if not exist "node_modules" (
    echo Installing dependencies first...
    call npm install
)
echo Running ESLint...
call npm run lint
goto :end

:test
echo Running Frontend tests...
echo.
if not exist "node_modules" (
    echo Installing dependencies first...
    call npm install
)
echo Running tests...
if exist "package.json" (
    findstr /c:"\"test\"" package.json >nul
    if not errorlevel 1 (
        call npm test
    ) else (
        echo No test script found in package.json
        echo You can add tests using Vitest, Jest, or other testing frameworks
    )
) else (
    echo ERROR: package.json not found
)
goto :end

:help
echo Frontend - Windows Management Script
echo.
echo Usage: start.cmd [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   dev             Start development server with hot reload (default)
echo   prod            Start in production mode with Docker
echo   build           Build for production
echo   build docker    Build Docker image
echo   preview         Preview production build
echo   logs            Show container logs
echo   stop            Stop the server
echo   clean           Remove all containers, volumes, images, and dependencies
echo   install         Install npm dependencies
echo   lint            Run ESLint
echo   test            Run tests
echo   help            Show this help message
echo.
echo Examples:
echo   start.cmd                       # Start development server
echo   start.cmd dev                   # Start development server
echo   start.cmd prod                  # Start in production mode
echo   start.cmd build                 # Build for production
echo   start.cmd build docker          # Build Docker image
echo   start.cmd preview               # Preview production build
echo   start.cmd lint                  # Run linting
echo.
echo Development Requirements:
echo   - Node.js 18+ (for local development)
echo   - Docker and Docker Compose (for containerized deployment)
echo.
echo Configuration:
echo   - Edit .env file for environment variables
echo   - API endpoints are configured in src/config/api.ts
echo.
echo Access URLs (after starting):
echo   - Development: http://localhost:5173
echo   - Preview: http://localhost:4173
echo   - Production: http://localhost:5173 (Docker)
echo.
echo Framework Information:
echo   - React 18 with TypeScript
echo   - Vite for build tooling
echo   - Tailwind CSS for styling
echo   - DaisyUI for components
goto :end

:end
echo.
pause
