@echo off
setlocal enabledelayedexpansion

title VRecommendation System - Local Startup (No Docker)

:: Colors (using ANSI escape codes)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "NC=[0m"

echo.
echo %BLUE%========================================================%NC%
echo %BLUE%   VRecommendation System - Local Startup (No Docker)   %NC%
echo %BLUE%========================================================%NC%
echo.

:: Get script directory
cd /d "%~dp0"

:: ========================================
:: Auto-setup .env files
:: ========================================
call :setup_env_files

:: Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=start

if "%COMMAND%"=="start" goto :start_all
if "%COMMAND%"=="up" goto :start_all
if "%COMMAND%"=="stop" goto :stop_all
if "%COMMAND%"=="down" goto :stop_all
if "%COMMAND%"=="restart" goto :restart
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="install" goto :install_all
if "%COMMAND%"=="check" goto :check_deps
if "%COMMAND%"=="ai" goto :start_ai
if "%COMMAND%"=="api" goto :start_api
if "%COMMAND%"=="frontend" goto :start_frontend
if "%COMMAND%"=="help" goto :help
goto :help

:: ========================================
:: Setup Environment Files
:: ========================================
:setup_env_files
echo %YELLOW%[INFO]%NC% Checking environment files...

:: Check/create root .env
if not exist ".env" (
    echo %YELLOW%[INFO]%NC% Creating .env from example-env...
    if exist "example-env" (
        copy "example-env" ".env" >nul
        echo %GREEN%[OK]%NC% Root .env created
    ) else (
        call :create_default_env
    )
) else (
    echo %GREEN%[OK]%NC% Root .env exists
)

:: Check/create API server .env (for local development)
if not exist "backend\api_server\.env" (
    echo %YELLOW%[INFO]%NC% Creating API server .env...
    if exist "backend\api_server\example-env" (
        copy "backend\api_server\example-env" "backend\api_server\.env" >nul
        :: Update for local development
        call :update_api_env_local
        echo %GREEN%[OK]%NC% API server .env created (local mode)
    ) else (
        call :create_api_env_local
    )
) else (
    echo %GREEN%[OK]%NC% API server .env exists
)

:: Check/create AI server .env
if not exist "backend\ai_server\.env" (
    echo %YELLOW%[INFO]%NC% Creating AI server .env...
    if exist "backend\ai_server\example-env" (
        copy "backend\ai_server\example-env" "backend\ai_server\.env" >nul
        echo %GREEN%[OK]%NC% AI server .env created
    ) else (
        call :create_ai_env_local
    )
) else (
    echo %GREEN%[OK]%NC% AI server .env exists
)

:: Check/create frontend .env
if not exist "frontend\project\.env" (
    echo %YELLOW%[INFO]%NC% Creating frontend .env...
    if exist "frontend\project\example-env" (
        copy "frontend\project\example-env" "frontend\project\.env" >nul
        echo %GREEN%[OK]%NC% Frontend .env created
    ) else (
        call :create_frontend_env_local
    )
) else (
    echo %GREEN%[OK]%NC% Frontend .env exists
)

echo.
goto :eof

:create_default_env
echo %YELLOW%[INFO]%NC% Creating default .env file for local development...
(
echo # VRecommendation Environment Configuration - Local Development
echo # Auto-generated - Please update with your settings
echo.
echo # Environment
echo STATUS_DEV=dev
echo.
echo # Host Configuration
echo HOST_IP=localhost
echo.
echo # API Server Configuration
echo API_SERVER_HOST=0.0.0.0
echo API_SERVER_PORT=2030
echo API_SERVER_READ_TIMEOUT=60
echo.
echo # AI Server Configuration
echo AI_SERVER_HOST=0.0.0.0
echo AI_SERVER_PORT=9999
echo.
echo # Frontend Configuration
echo FRONTEND_PORT=5173
echo FRONTEND_URL=http://localhost:5173
echo.
echo # Redis Configuration - For local, use localhost instead of redis
echo REDIS_HOST=localhost
echo REDIS_PORT=6379
echo REDIS_PASSWORD=
echo REDIS_DB=0
echo.
echo # Database Configuration (MySQL) - For local development
echo MYSQL_HOST=localhost
echo MYSQL_PORT=3306
echo MYSQL_USER=admin
echo MYSQL_PASSWORD=pokiwar0981
echo MYSQL_DATABASE=shop
echo.
echo # Database Configuration (MongoDB) - For local development
echo MONGODB_HOST=localhost
echo MONGODB_PORT=27017
echo MONGODB_USERNAME=root
echo MONGODB_PASSWORD=password
echo MONGODB_AUTH_SOURCE=admin
echo.
echo # Kafka Configuration - For local development
echo KAFKA_BOOTSTRAP_SERVERS=localhost:9092
echo KAFKA_GROUP_ID=vrecom_ai_server_group
echo.
echo # JWT Configuration
echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
echo SESSION_SECRET=your-super-secret-session-key-change-in-production
echo.
echo # API URLs for frontend (local development)
echo VITE_API_SERVER_URL=http://localhost:2030
echo VITE_AI_SERVER_URL=http://localhost:9999
echo.
echo # Google OAuth - Get from Google Cloud Console
echo GOOGLE_CLIENT_ID=
echo GOOGLE_CLIENT_SECRET=
echo GOOGLE_CALLBACK_URL=http://localhost:2030/api/v1/auth/google/callback
) > ".env"
echo %GREEN%[OK]%NC% Default .env created for local development
goto :eof

:create_api_env_local
echo %YELLOW%[INFO]%NC% Creating API server .env for local development...
(
echo # Environment can be set to 'dev', 'test' or 'prod'
echo STATUS_DEV=dev
echo HOST_ADDRESS=0.0.0.0
echo HOST_PORT=2030
echo HOST_READ_TIMEOUT=60
echo.
echo # Google OAuth2 credentials
echo GOOGLE_CLIENT_ID=
echo GOOGLE_CLIENT_SECRET=
echo GOOGLE_CALLBACK_URL=http://localhost:2030/api/v1/auth/google/callback
echo SESSION_SECRET=your_strong_session_secret
echo.
echo # AI Server Configuration - Local URL
echo AI_SERVER_URL=http://localhost:9999
echo.
echo # Frontend URL for OAuth redirect
echo FRONTEND_URL=http://localhost:5173
echo HOST_IP=localhost
echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
echo.
echo # Redis Configuration - Local
echo REDIS_HOST=localhost
echo REDIS_PORT=6379
echo REDIS_PASSWORD=
echo REDIS_DB=0
) > "backend\api_server\.env"
echo %GREEN%[OK]%NC% API server .env created
goto :eof

:update_api_env_local
:: Update AI_SERVER_URL to use localhost
powershell -Command "(Get-Content 'backend\api_server\.env') -replace 'AI_SERVER_URL=http://ai_server:', 'AI_SERVER_URL=http://localhost:' | Set-Content 'backend\api_server\.env'" >nul 2>&1
goto :eof

:create_ai_env_local
echo %YELLOW%[INFO]%NC% Creating AI server .env for local development...
(
echo # Port server
echo HOST=0.0.0.0
echo PORT=9999
echo.
echo # Session Secret
echo SESSION_SECRET=your_strong_session_secret
echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
echo.
echo # Database Configuration (MySQL) - Local
echo MYSQL_HOST=localhost
echo MYSQL_PORT=3306
echo MYSQL_USER=admin
echo MYSQL_PASSWORD=pokiwar0981
echo MYSQL_DATABASE=shop
echo.
echo # Database Configuration (MongoDB) - Local
echo MONGODB_HOST=localhost
echo MONGODB_PORT=27017
echo MONGODB_USERNAME=root
echo MONGODB_PASSWORD=password
echo.
echo # Kafka Configuration - Local
echo KAFKA_BOOTSTRAP_SERVERS=localhost:9092
echo KAFKA_GROUP_ID=vrecom_ai_server_group
) > "backend\ai_server\.env"
echo %GREEN%[OK]%NC% AI server .env created
goto :eof

:create_frontend_env_local
echo %YELLOW%[INFO]%NC% Creating frontend .env for local development...
(
echo # API Configuration - Local Development
echo VITE_AI_SERVER_URL=http://localhost:9999
echo VITE_API_SERVER_URL=http://localhost:2030
) > "frontend\project\.env"
echo %GREEN%[OK]%NC% Frontend .env created
goto :eof

:: ========================================
:: Check Dependencies
:: ========================================
:check_deps
echo %BLUE%[INFO]%NC% Checking dependencies...
echo.

set "ALL_OK=1"

:: Check Go
echo Checking Go...
go version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Go is not installed
    echo   Download from: https://golang.org/dl/
    set "ALL_OK=0"
) else (
    for /f "tokens=3" %%v in ('go version') do echo   %GREEN%[OK]%NC% Go %%v
)

:: Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Python is not installed
    echo   Download from: https://python.org/downloads/
    set "ALL_OK=0"
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   %GREEN%[OK]%NC% Python %%v
)

:: Check Poetry
echo Checking Poetry...
poetry --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Poetry is not installed
    echo   Install with: pip install poetry
    echo   Or visit: https://python-poetry.org/docs/
    set "ALL_OK=0"
) else (
    for /f "tokens=3" %%v in ('poetry --version 2^>^&1') do echo   %GREEN%[OK]%NC% Poetry %%v
)

:: Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Node.js is not installed
    echo   Download from: https://nodejs.org/
    set "ALL_OK=0"
) else (
    for /f %%v in ('node --version') do echo   %GREEN%[OK]%NC% Node.js %%v
)

:: Check npm
echo Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% npm is not installed
    set "ALL_OK=0"
) else (
    for /f %%v in ('npm --version') do echo   %GREEN%[OK]%NC% npm %%v
)

echo.
if "%ALL_OK%"=="1" (
    echo %GREEN%[SUCCESS]%NC% All dependencies are installed!
) else (
    echo %RED%[WARNING]%NC% Some dependencies are missing. Please install them before running the system.
)
echo.
goto :end

:: ========================================
:: Install All Dependencies
:: ========================================
:install_all
echo %BLUE%[INFO]%NC% Installing all dependencies...
echo.

:: Install AI Server dependencies
echo %CYAN%[1/3]%NC% Installing AI Server dependencies...
cd backend\ai_server
if exist "pyproject.toml" (
    poetry install
    if errorlevel 1 (
        echo %RED%[ERROR]%NC% Failed to install AI Server dependencies
    ) else (
        echo %GREEN%[OK]%NC% AI Server dependencies installed
    )
) else (
    echo %RED%[ERROR]%NC% pyproject.toml not found
)
cd ..\..

:: Install API Server dependencies
echo.
echo %CYAN%[2/3]%NC% Installing API Server dependencies...
cd backend\api_server
if exist "go.mod" (
    go mod download
    go mod tidy
    if errorlevel 1 (
        echo %RED%[ERROR]%NC% Failed to install API Server dependencies
    ) else (
        echo %GREEN%[OK]%NC% API Server dependencies installed
    )
) else (
    echo %RED%[ERROR]%NC% go.mod not found
)
cd ..\..

:: Install Frontend dependencies
echo.
echo %CYAN%[3/3]%NC% Installing Frontend dependencies...
cd frontend\project
if exist "package.json" (
    call npm install
    if errorlevel 1 (
        echo %RED%[ERROR]%NC% Failed to install Frontend dependencies
    ) else (
        echo %GREEN%[OK]%NC% Frontend dependencies installed
    )
) else (
    echo %RED%[ERROR]%NC% package.json not found
)
cd ..\..

echo.
echo %GREEN%[SUCCESS]%NC% Dependency installation completed!
echo.
goto :end

:: ========================================
:: Start All Services
:: ========================================
:start_all
echo %BLUE%[INFO]%NC% Starting all services locally (without Docker)...
echo.

:: Check dependencies first
call :check_deps_silent
if "%DEPS_OK%"=="0" (
    echo %RED%[ERROR]%NC% Missing dependencies. Run 'start-local.cmd check' to see what's missing.
    goto :end
)

echo %YELLOW%[NOTE]%NC% Each service will start in a separate window.
echo %YELLOW%[NOTE]%NC% Close the windows to stop the services.
echo.

:: Start AI Server
echo %CYAN%[1/3]%NC% Starting AI Server (Python/FastAPI)...
start "VRecommendation - AI Server" cmd /k "cd /d "%~dp0backend\ai_server" && echo Starting AI Server... && poetry run server"
timeout /t 3 /nobreak >nul

:: Start API Server
echo %CYAN%[2/3]%NC% Starting API Server (Go)...
start "VRecommendation - API Server" cmd /k "cd /d "%~dp0backend\api_server" && echo Starting API Server... && go run main.go"
timeout /t 3 /nobreak >nul

:: Start Frontend
echo %CYAN%[3/3]%NC% Starting Frontend (React/Vite)...
start "VRecommendation - Frontend" cmd /k "cd /d "%~dp0frontend\project" && echo Starting Frontend... && npm run dev"

echo.
echo %GREEN%========================================================%NC%
echo %GREEN%   All services started successfully!                   %NC%
echo %GREEN%========================================================%NC%
echo.
echo %CYAN%Service URLs:%NC%
echo   - Frontend:    http://localhost:5173
echo   - API Server:  http://localhost:2030
echo   - AI Server:   http://localhost:9999
echo.
echo %CYAN%Health Check URLs:%NC%
echo   - API Server:  http://localhost:2030/api/v1/ping
echo   - AI Server:   http://localhost:9999/api/v1/health
echo   - AI Server Docs: http://localhost:9999/docs
echo.
echo %YELLOW%[TIP]%NC% To stop services, close their respective terminal windows
echo %YELLOW%[TIP]%NC% Or run: start-local.cmd stop
echo.
goto :end

:: ========================================
:: Start Individual Services
:: ========================================
:start_ai
echo %BLUE%[INFO]%NC% Starting AI Server...
start "VRecommendation - AI Server" cmd /k "cd /d "%~dp0backend\ai_server" && echo Starting AI Server... && poetry run server"
echo %GREEN%[OK]%NC% AI Server started in new window
echo   URL: http://localhost:9999
echo   Docs: http://localhost:9999/docs
goto :end

:start_api
echo %BLUE%[INFO]%NC% Starting API Server...
start "VRecommendation - API Server" cmd /k "cd /d "%~dp0backend\api_server" && echo Starting API Server... && go run main.go"
echo %GREEN%[OK]%NC% API Server started in new window
echo   URL: http://localhost:2030
goto :end

:start_frontend
echo %BLUE%[INFO]%NC% Starting Frontend...
start "VRecommendation - Frontend" cmd /k "cd /d "%~dp0frontend\project" && echo Starting Frontend... && npm run dev"
echo %GREEN%[OK]%NC% Frontend started in new window
echo   URL: http://localhost:5173
goto :end

:: ========================================
:: Stop All Services
:: ========================================
:stop_all
echo %BLUE%[INFO]%NC% Stopping all services...
echo.

:: Kill processes by port
echo Stopping AI Server (port 9999)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":9999" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Stopping API Server (port 2030)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":2030" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Stopping Frontend (port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Also try to kill by window title
taskkill /FI "WINDOWTITLE eq VRecommendation - AI Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq VRecommendation - API Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq VRecommendation - Frontend*" /F >nul 2>&1

echo.
echo %GREEN%[OK]%NC% All services stopped
echo.
goto :end

:: ========================================
:: Restart Services
:: ========================================
:restart
echo %BLUE%[INFO]%NC% Restarting all services...
call :stop_all
timeout /t 2 /nobreak >nul
call :start_all
goto :eof

:: ========================================
:: Check Status
:: ========================================
:status
echo %BLUE%[INFO]%NC% Checking service status...
echo.

:: Check AI Server
echo AI Server (port 9999):
netstat -aon | findstr ":9999" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[STOPPED]%NC% Not running
) else (
    echo   %GREEN%[RUNNING]%NC% http://localhost:9999
)

:: Check API Server
echo API Server (port 2030):
netstat -aon | findstr ":2030" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[STOPPED]%NC% Not running
) else (
    echo   %GREEN%[RUNNING]%NC% http://localhost:2030
)

:: Check Frontend
echo Frontend (port 5173):
netstat -aon | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[STOPPED]%NC% Not running
) else (
    echo   %GREEN%[RUNNING]%NC% http://localhost:5173
)

echo.
goto :end

:: ========================================
:: Silent Dependency Check
:: ========================================
:check_deps_silent
set "DEPS_OK=1"
go version >nul 2>&1
if errorlevel 1 set "DEPS_OK=0"
poetry --version >nul 2>&1
if errorlevel 1 set "DEPS_OK=0"
node --version >nul 2>&1
if errorlevel 1 set "DEPS_OK=0"
goto :eof

:: ========================================
:: Help
:: ========================================
:help
echo %CYAN%VRecommendation System - Local Startup Script (No Docker)%NC%
echo.
echo Usage: start-local.cmd [COMMAND]
echo.
echo Commands:
echo   start, up       Start all services locally (default)
echo   stop, down      Stop all running services
echo   restart         Restart all services
echo   status          Check status of all services
echo   install         Install all dependencies
echo   check           Check if all dependencies are installed
echo   ai              Start only AI Server
echo   api             Start only API Server
echo   frontend        Start only Frontend
echo   help            Show this help message
echo.
echo Examples:
echo   start-local.cmd                 Start all services
echo   start-local.cmd status          Check service status
echo   start-local.cmd stop            Stop all services
echo   start-local.cmd install         Install dependencies
echo   start-local.cmd ai              Start only AI Server
echo.
echo Requirements:
echo   - Go 1.24+      (for API Server)
echo   - Python 3.9+   (for AI Server)
echo   - Poetry        (for AI Server dependency management)
echo   - Node.js 18+   (for Frontend)
echo   - npm           (for Frontend)
echo.
echo Service URLs (after starting):
echo   - Frontend:      http://localhost:5173
echo   - API Server:    http://localhost:2030
echo   - AI Server:     http://localhost:9999
echo   - AI Server Docs: http://localhost:9999/docs
echo.
echo %YELLOW%Note:%NC% External services (Redis, MySQL, MongoDB, Kafka) must be
echo       running separately if required by your configuration.
echo.
goto :end

:end
endlocal
