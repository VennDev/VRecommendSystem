@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  VRecommendation System - Development Setup
echo ================================================
echo.

:: Check for required tools
echo [1/8] Checking system requirements...
echo.

:: Check Docker
echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found. Please install Docker Desktop first.
    echo Visit: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo SUCCESS: Docker found

:: Check Docker Compose
echo Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose not found. Please install Docker Compose.
    pause
    exit /b 1
)
echo SUCCESS: Docker Compose found

:: Check Node.js (optional for frontend development)
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Node.js not found. Frontend local development will not be available.
    echo Visit: https://nodejs.org/ to install Node.js
    set NODE_AVAILABLE=false
) else (
    echo SUCCESS: Node.js found
    set NODE_AVAILABLE=true
)

:: Check Go (optional for API server development)
echo Checking Go installation...
go version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Go not found. API Server local development will not be available.
    echo Visit: https://golang.org/dl/ to install Go
    set GO_AVAILABLE=false
) else (
    echo SUCCESS: Go found
    set GO_AVAILABLE=true
)

:: Check Python and Poetry (optional for AI server development)
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Python not found. AI Server local development will not be available.
    echo Visit: https://python.org/ to install Python
    set PYTHON_AVAILABLE=false
) else (
    echo SUCCESS: Python found
    set PYTHON_AVAILABLE=true

    echo Checking Poetry installation...
    poetry --version >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Poetry not found. AI Server local development will not be available.
        echo Visit: https://python-poetry.org/ to install Poetry
        set POETRY_AVAILABLE=false
    ) else (
        echo SUCCESS: Poetry found
        set POETRY_AVAILABLE=true
    )
)

echo.
echo [2/8] Setting up environment files...
echo.

:: Setup main .env file
if not exist ".env" (
    echo Creating main .env file...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo SUCCESS: Main .env file created
    ) else (
        echo Creating default .env file...
        (
            echo # VRecommendation System Configuration
            echo.
            echo # API Server
            echo API_SERVER_PORT=2030
            echo API_SERVER_HOST=0.0.0.0
            echo.
            echo # AI Server
            echo AI_SERVER_PORT=9999
            echo AI_SERVER_HOST=0.0.0.0
            echo.
            echo # Frontend
            echo FRONTEND_PORT=5173
            echo.
            echo # Redis
            echo REDIS_PORT=6379
            echo.
            echo # Prometheus
            echo PROMETHEUS_PORT=9090
        ) > .env
        echo SUCCESS: Default .env file created
    )
) else (
    echo SUCCESS: Main .env file already exists
)

:: Setup AI Server .env
if not exist "backend\ai_server\.env" (
    echo Creating AI Server .env file...
    if exist "backend\ai_server\example-env" (
        copy backend\ai_server\example-env backend\ai_server\.env >nul
        echo SUCCESS: AI Server .env file created
    ) else (
        echo WARNING: AI Server example-env not found
    )
) else (
    echo SUCCESS: AI Server .env file already exists
)

:: Setup API Server .env
if not exist "backend\api_server\.env" (
    echo Creating API Server .env file...
    if exist "backend\api_server\example-env" (
        copy backend\api_server\example-env backend\api_server\.env >nul
        echo SUCCESS: API Server .env file created
    ) else (
        echo WARNING: API Server example-env not found
    )
) else (
    echo SUCCESS: API Server .env file already exists
)

:: Setup Frontend .env
if not exist "frontend\project\.env" (
    echo Creating Frontend .env file...
    if exist "frontend\project\.env.example" (
        copy frontend\project\.env.example frontend\project\.env >nul
        echo SUCCESS: Frontend .env file created
    ) else (
        echo Creating default Frontend .env file...
        (
            echo # Frontend Configuration
            echo VITE_API_SERVER_URL=http://localhost:2030
            echo VITE_AI_SERVER_URL=http://localhost:9999
        ) > frontend\project\.env
        echo SUCCESS: Default Frontend .env file created
    )
) else (
    echo SUCCESS: Frontend .env file already exists
)

echo.
echo [3/8] Creating necessary directories...
echo.

:: Create directories
if not exist "logs" mkdir logs
if not exist "backend\ai_server\logs" mkdir backend\ai_server\logs
if not exist "backend\api_server\logs" mkdir backend\api_server\logs
if not exist "backend\ai_server\models" mkdir backend\ai_server\models
if not exist "backend\ai_server\outputs" mkdir backend\ai_server\outputs

echo SUCCESS: Directories created

echo.
echo [4/8] Installing dependencies (optional)...
echo.

set /p INSTALL_DEPS="Do you want to install development dependencies? (y/N) "
if /i "%INSTALL_DEPS%"=="y" (

    if "%NODE_AVAILABLE%"=="true" (
        echo Installing Frontend dependencies...
        cd frontend\project
        call npm install
        cd ..\..
        echo SUCCESS: Frontend dependencies installed
    )

    if "%GO_AVAILABLE%"=="true" (
        echo Installing API Server dependencies...
        cd backend\api_server
        go mod download
        cd ..\..
        echo SUCCESS: API Server dependencies installed
    )

    if "%POETRY_AVAILABLE%"=="true" (
        echo Installing AI Server dependencies...
        cd backend\ai_server
        poetry install
        cd ..\..
        echo SUCCESS: AI Server dependencies installed
    )
)

echo.
echo [5/8] Building Docker images...
echo.

set /p BUILD_IMAGES="Do you want to build Docker images now? (Y/n) "
if /i not "%BUILD_IMAGES%"=="n" (
    echo Building Docker images... This may take a while...
    docker-compose build
    if errorlevel 1 (
        echo WARNING: Some images failed to build. You can build them later.
    ) else (
        echo SUCCESS: Docker images built successfully
    )
) else (
    echo SKIPPED: Docker image building
)

echo.
echo [6/8] Testing Docker setup...
echo.

set /p TEST_DOCKER="Do you want to test the Docker setup? (Y/n) "
if /i not "%TEST_DOCKER%"=="n" (
    echo Starting services for testing...
    docker-compose up -d

    echo Waiting for services to start...
    timeout /t 30 /nobreak >nul

    echo Testing service endpoints...
    curl -f http://localhost:2030/api/v1/ping >nul 2>&1
    if errorlevel 1 (
        echo WARNING: API Server test failed
    ) else (
        echo SUCCESS: API Server is responding
    )

    curl -f http://localhost:9999/api/v1/health >nul 2>&1
    if errorlevel 1 (
        echo WARNING: AI Server test failed
    ) else (
        echo SUCCESS: AI Server is responding
    )

    curl -f http://localhost:5173 >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Frontend test failed
    ) else (
        echo SUCCESS: Frontend is responding
    )

    echo Stopping test services...
    docker-compose down

) else (
    echo SKIPPED: Docker testing
)

echo.
echo [7/8] Setting up development scripts...
echo.

:: Make sure start scripts are executable and present
if exist "start.cmd" (
    echo SUCCESS: Main start script found
) else (
    echo WARNING: Main start.cmd not found
)

if exist "backend\ai_server\start.cmd" (
    echo SUCCESS: AI Server start script found
) else (
    echo WARNING: AI Server start.cmd not found
)

if exist "backend\api_server\start.cmd" (
    echo SUCCESS: API Server start script found
) else (
    echo WARNING: API Server start.cmd not found
)

if exist "frontend\project\start.cmd" (
    echo SUCCESS: Frontend start script found
) else (
    echo WARNING: Frontend start.cmd not found
)

echo.
echo [8/8] Setup completed!
echo.

echo ================================================
echo  Development Environment Summary
echo ================================================
echo.
echo System Requirements:
if "%NODE_AVAILABLE%"=="true" (
    echo   Node.js: INSTALLED
) else (
    echo   Node.js: NOT FOUND
)
if "%GO_AVAILABLE%"=="true" (
    echo   Go: INSTALLED
) else (
    echo   Go: NOT FOUND
)
if "%PYTHON_AVAILABLE%"=="true" (
    echo   Python: INSTALLED
) else (
    echo   Python: NOT FOUND
)
if "%POETRY_AVAILABLE%"=="true" (
    echo   Poetry: INSTALLED
) else (
    echo   Poetry: NOT FOUND
)
echo   Docker: INSTALLED
echo   Docker Compose: INSTALLED
echo.

echo Configuration Files:
echo   Main .env: CREATED
echo   AI Server .env: CREATED
echo   API Server .env: CREATED
echo   Frontend .env: CREATED
echo.

echo Quick Start Commands:
echo   start.cmd                    # Start all services
echo   start.cmd build              # Build all images
echo   start.cmd logs               # View logs
echo   start.cmd status             # Check status
echo.

echo Individual Service Commands:
echo   backend\ai_server\start.cmd        # AI Server
echo   backend\api_server\start.cmd       # API Server
echo   frontend\project\start.cmd         # Frontend
echo.

echo Access URLs (after starting):
echo   Frontend:    http://localhost:5173
echo   API Server:  http://localhost:2030
echo   AI Server:   http://localhost:9999
echo   Prometheus:  http://localhost:9090
echo.

echo Next Steps:
echo   1. Review and edit .env files if needed
echo   2. Run 'start.cmd' to start all services
echo   3. Open http://localhost:5173 in your browser
echo   4. Check the README files for detailed documentation
echo.

echo ================================================
echo  Setup Complete! Happy coding!
echo ================================================

pause
