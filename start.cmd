@echo off
setlocal enabledelayedexpansion

title VRecommendation System - Startup Script

:: Colors (using PowerShell for colored output)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo.
echo %BLUE%========================================================%NC%
echo %BLUE%     VRecommendation System - Windows Startup           %NC%
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
if "%COMMAND%"=="admin" goto :admin_portal
if "%COMMAND%"=="admin-portal" goto :admin_portal
if "%COMMAND%"=="all" goto :start_all
if "%COMMAND%"=="setup" goto :setup_lan
if "%COMMAND%"=="setup-lan" goto :setup_lan
if "%COMMAND%"=="help" goto :help
goto :help

:: ========================================
:: Setup Environment Files
:: ========================================
:setup_env_files
echo %YELLOW%[INFO]%NC% Checking environment files...

:: Check/create root .env
if not exist ".env" (
    echo %YELLOW%[INFO]%NC% Creating .env from .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo %GREEN%[OK]%NC% Root .env created
    ) else (
        echo %RED%[ERROR]%NC% .env.example not found!
        goto :create_default_env
    )
) else (
    echo %GREEN%[OK]%NC% Root .env exists
)

:: Check/create API server .env
if not exist "backend\api_server\.env" (
    echo %YELLOW%[INFO]%NC% Creating API server .env...
    if exist "backend\api_server\example-env" (
        copy "backend\api_server\example-env" "backend\api_server\.env" >nul
        echo %GREEN%[OK]%NC% API server .env created
    ) else (
        call :create_api_env
    )
) else (
    echo %GREEN%[OK]%NC% API server .env exists
)

:: Check/create frontend .env (if example exists)
if not exist "frontend\project\.env" (
    if exist "frontend\project\example-env" (
        echo %YELLOW%[INFO]%NC% Creating frontend .env...
        copy "frontend\project\example-env" "frontend\project\.env" >nul
        echo %GREEN%[OK]%NC% Frontend .env created
    )
)

:: Sync Google OAuth credentials from root .env to api_server .env
call :sync_oauth_credentials

echo.
goto :eof

:create_default_env
echo %YELLOW%[INFO]%NC% Creating default .env file...
(
echo # VRecommendation Environment Configuration
echo # Auto-generated - Please update with your settings
echo.
echo HOST_IP=localhost
echo FRONTEND_PORT=5173
echo VITE_API_SERVER_URL=http://localhost:2030
echo VITE_AI_SERVER_URL=http://localhost:9999
echo API_SERVER_PORT=2030
echo API_SERVER_HOST=0.0.0.0
echo AI_SERVER_PORT=9999
echo AI_SERVER_HOST=0.0.0.0
echo REDIS_HOST=redis
echo REDIS_PORT=6379
echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
echo SESSION_SECRET=your-super-secret-session-key-change-in-production
echo FRONTEND_URL=http://localhost:5173
echo.
echo # Google OAuth - Get from Google Cloud Console
echo GOOGLE_CLIENT_ID=
echo GOOGLE_CLIENT_SECRET=
echo GOOGLE_CALLBACK_URL=http://localhost:2030/api/v1/auth/google/callback
) > ".env"
echo %GREEN%[OK]%NC% Default .env created
goto :eof

:create_api_env
echo %YELLOW%[INFO]%NC% Creating API server .env...
(
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
echo # Frontend URL for OAuth redirect
echo FRONTEND_URL=http://localhost:5173
echo HOST_IP=localhost
echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
) > "backend\api_server\.env"
echo %GREEN%[OK]%NC% API server .env created
goto :eof

:sync_oauth_credentials
:: Read Google credentials from root .env and sync to api_server .env
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="GOOGLE_CLIENT_ID" set "ROOT_CLIENT_ID=%%b"
    if "%%a"=="GOOGLE_CLIENT_SECRET" set "ROOT_CLIENT_SECRET=%%b"
    if "%%a"=="HOST_IP" set "ROOT_HOST_IP=%%b"
    if "%%a"=="FRONTEND_URL" set "ROOT_FRONTEND_URL=%%b"
)

:: Update api_server .env if credentials exist in root
if defined ROOT_CLIENT_ID if not "%ROOT_CLIENT_ID%"=="" (
    echo %YELLOW%[INFO]%NC% Syncing OAuth credentials to API server...

    :: Read current api_server .env and update
    set "TEMP_ENV=%TEMP%\api_env_temp.txt"

    (
    echo STATUS_DEV=dev
    echo HOST_ADDRESS=0.0.0.0
    echo HOST_PORT=2030
    echo HOST_READ_TIMEOUT=60
    echo.
    echo # Google OAuth2 credentials - Synced from root .env
    echo GOOGLE_CLIENT_ID=!ROOT_CLIENT_ID!
    echo GOOGLE_CLIENT_SECRET=!ROOT_CLIENT_SECRET!
    if defined ROOT_HOST_IP (
        echo GOOGLE_CALLBACK_URL=http://!ROOT_HOST_IP!:2030/api/v1/auth/google/callback
    ) else (
        echo GOOGLE_CALLBACK_URL=http://localhost:2030/api/v1/auth/google/callback
    )
    echo SESSION_SECRET=your_strong_session_secret
    echo.
    echo # Frontend URL for OAuth redirect
    if defined ROOT_FRONTEND_URL (
        echo FRONTEND_URL=!ROOT_FRONTEND_URL!
    ) else (
        echo FRONTEND_URL=http://localhost:5173
    )
    if defined ROOT_HOST_IP (
        echo HOST_IP=!ROOT_HOST_IP!
    ) else (
        echo HOST_IP=localhost
    )
    echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
    ) > "backend\api_server\.env"

    echo %GREEN%[OK]%NC% OAuth credentials synced
)
goto :eof

:: ========================================
:: Start Services
:: ========================================
:start
echo %BLUE%[INFO]%NC% Starting all Docker services...
echo.

docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo %RED%[ERROR]%NC% Failed to start services!
    goto :end
)

echo.
echo %GREEN%========================================================%NC%
echo %GREEN%  Services Started Successfully!                        %NC%
echo %GREEN%========================================================%NC%
echo.
docker-compose ps
echo.

:: Get HOST_IP from .env
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="HOST_IP" set "HOST_IP=%%b"
)
if not defined HOST_IP set "HOST_IP=localhost"

echo %BLUE%========================================================%NC%
echo %BLUE%  Access URLs                                           %NC%
echo %BLUE%========================================================%NC%
echo.
echo   %GREEN%Frontend:%NC%      http://localhost:5173
echo                  http://%HOST_IP%:5173  (LAN)
echo.
echo   %GREEN%API Server:%NC%    http://localhost:2030
echo                  http://%HOST_IP%:2030  (LAN)
echo.
echo   %GREEN%AI Server:%NC%     http://localhost:9999
echo                  http://%HOST_IP%:9999  (LAN)
echo.
echo   %GREEN%Kafka UI:%NC%      http://localhost:8080
echo.
echo   %GREEN%Prometheus:%NC%    http://localhost:9090
echo.
echo %YELLOW%========================================================%NC%
echo %YELLOW%  Admin Portal (SuperAdmin - Localhost Only)           %NC%
echo %YELLOW%========================================================%NC%
echo.
echo   To manage Email Whitelist, run:
echo   %GREEN%start.cmd admin%NC%
echo.
echo   Then access: %GREEN%http://127.0.0.1:3456%NC%
echo.
echo   Or run %GREEN%start.cmd all%NC% to start everything including Admin Portal.
echo.

goto :end

:: ========================================
:: Start All (Docker + Admin Portal)
:: ========================================
:start_all
echo %BLUE%[INFO]%NC% Starting all services including Admin Portal...
echo.

:: Start Docker services first
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo %RED%[ERROR]%NC% Failed to start Docker services!
    goto :end
)

echo.
echo %GREEN%[OK]%NC% Docker services started
echo.

:: Get HOST_IP from .env
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="HOST_IP" set "HOST_IP=%%b"
)
if not defined HOST_IP set "HOST_IP=localhost"

:: Start Admin Portal in background
echo %BLUE%[INFO]%NC% Starting Admin Portal in background...

cd admin-portal
if not exist "node_modules" (
    echo %YELLOW%[INFO]%NC% Installing Admin Portal dependencies...
    call npm install >nul 2>&1
)

:: Start Admin Portal in a new minimized window
start "VRecommendation Admin Portal" /min cmd /c "npm start"
cd ..

echo %GREEN%[OK]%NC% Admin Portal started
echo.

echo %GREEN%========================================================%NC%
echo %GREEN%  All Services Started Successfully!                    %NC%
echo %GREEN%========================================================%NC%
echo.
docker-compose ps
echo.
echo %BLUE%========================================================%NC%
echo %BLUE%  Access URLs                                           %NC%
echo %BLUE%========================================================%NC%
echo.
echo   %GREEN%Frontend:%NC%      http://localhost:5173
echo                  http://%HOST_IP%:5173  (LAN)
echo.
echo   %GREEN%API Server:%NC%    http://localhost:2030
echo.
echo   %GREEN%AI Server:%NC%     http://localhost:9999
echo.
echo   %GREEN%Admin Portal:%NC%  http://127.0.0.1:3456 (localhost only)
echo.
echo   %GREEN%Kafka UI:%NC%      http://localhost:8080
echo.
echo   %GREEN%Prometheus:%NC%    http://localhost:9090
echo.

goto :end

:: ========================================
:: Build Services
:: ========================================
:build
echo %BLUE%[INFO]%NC% Building all Docker images...
docker-compose build --no-cache
if %ERRORLEVEL% EQU 0 (
    echo %GREEN%[OK]%NC% Build completed successfully
) else (
    echo %RED%[ERROR]%NC% Build failed!
)
goto :end

:: ========================================
:: Stop Services
:: ========================================
:stop
echo %BLUE%[INFO]%NC% Stopping all services...
docker-compose down
echo %GREEN%[OK]%NC% All services stopped
goto :end

:: ========================================
:: Restart Services
:: ========================================
:restart
echo %BLUE%[INFO]%NC% Restarting all services...
docker-compose restart
echo %GREEN%[OK]%NC% All services restarted
goto :end

:: ========================================
:: Show Logs
:: ========================================
:logs
set SERVICE=%2
if "%SERVICE%"=="" (
    echo %BLUE%[INFO]%NC% Showing logs for all services... (Ctrl+C to exit)
    docker-compose logs -f --tail=100
) else (
    echo %BLUE%[INFO]%NC% Showing logs for %SERVICE%... (Ctrl+C to exit)
    docker-compose logs -f --tail=100 %SERVICE%
)
goto :end

:: ========================================
:: Clean Everything
:: ========================================
:clean
echo.
echo %RED%WARNING: This will remove all containers, volumes, and images!%NC%
set /p REPLY="Are you sure? (y/N): "
if /i "%REPLY%"=="y" (
    echo %BLUE%[INFO]%NC% Cleaning up...
    docker-compose down -v --rmi all
    echo %GREEN%[OK]%NC% Cleanup completed
) else (
    echo %YELLOW%[INFO]%NC% Cleanup cancelled
)
goto :end

:: ========================================
:: Show Status
:: ========================================
:status
echo %BLUE%========================================================%NC%
echo %BLUE%  Services Status                                       %NC%
echo %BLUE%========================================================%NC%
echo.
docker-compose ps
echo.

:: Check Admin Portal
tasklist /fi "WINDOWTITLE eq VRecommendation Admin Portal*" 2>nul | find "node.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo %GREEN%[RUNNING]%NC% Admin Portal (http://127.0.0.1:3456)
) else (
    echo %YELLOW%[STOPPED]%NC% Admin Portal - Run 'start.cmd admin' to start
)
echo.
goto :end

:: ========================================
:: Admin Portal
:: ========================================
:admin_portal
echo %BLUE%========================================================%NC%
echo %BLUE%  Starting Admin Portal (Localhost Only)                %NC%
echo %BLUE%========================================================%NC%
echo.

:: Check if node is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED%[ERROR]%NC% Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    goto :end
)

:: Navigate to admin-portal
cd admin-portal

:: Install dependencies if needed
if not exist "node_modules" (
    echo %YELLOW%[INFO]%NC% Installing Admin Portal dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo %RED%[ERROR]%NC% Failed to install dependencies!
        cd ..
        goto :end
    )
    echo %GREEN%[OK]%NC% Dependencies installed
)

echo.
echo %GREEN%[INFO]%NC% Starting Admin Portal on http://127.0.0.1:3456
echo %YELLOW%[NOTE]%NC% This portal is ONLY accessible from localhost!
echo.
echo Press Ctrl+C to stop the Admin Portal.
echo.

:: Start Admin Portal
call npm start

cd ..
goto :end

:: ========================================
:: Setup LAN Access
:: ========================================
:setup_lan
echo %BLUE%========================================================%NC%
echo %BLUE%  LAN Access Configuration                              %NC%
echo %BLUE%========================================================%NC%
echo.

:: Detect IP addresses
echo %YELLOW%[INFO]%NC% Detecting network configuration...
echo.

set "IP_COUNT=0"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set /a IP_COUNT+=1
    for /f "tokens=* delims= " %%b in ("%%a") do (
        set "IP_!IP_COUNT!=%%b"
        echo   [!IP_COUNT!] %%b
    )
)

if %IP_COUNT% EQU 0 (
    echo %RED%[ERROR]%NC% No IPv4 address found!
    goto :end
)

echo.
if %IP_COUNT% EQU 1 (
    set "SELECTED_IP=!IP_1!"
    echo %GREEN%[INFO]%NC% Auto-selected: !SELECTED_IP!
) else (
    set /p "IP_CHOICE=Select IP number [1-%IP_COUNT%] or enter custom IP: "

    set "VALID=0"
    for /l %%i in (1,1,%IP_COUNT%) do (
        if "!IP_CHOICE!"=="%%i" (
            set "SELECTED_IP=!IP_%%i!"
            set "VALID=1"
        )
    )
    if "!VALID!"=="0" set "SELECTED_IP=!IP_CHOICE!"
)

echo.
echo %BLUE%[INFO]%NC% Using IP: %SELECTED_IP%
echo.
set /p "CONFIRM=Continue with this IP? (Y/n): "
if /i "%CONFIRM%"=="n" (
    echo %YELLOW%[INFO]%NC% Setup cancelled.
    goto :end
)

:: Update .env files
echo.
echo %YELLOW%[INFO]%NC% Updating configuration files...

:: Backup existing .env
if exist ".env" copy ".env" ".env.backup" >nul

:: Create new .env with selected IP
call :create_lan_env "%SELECTED_IP%"

echo %GREEN%[OK]%NC% Configuration updated
echo.

:: Ask to rebuild
set /p "REBUILD=Rebuild Docker containers now? (Y/n): "
if /i not "%REBUILD%"=="n" (
    echo.
    echo %YELLOW%[INFO]%NC% Rebuilding frontend with new configuration...
    docker-compose down
    docker-compose build --no-cache frontend
    docker-compose up -d
    echo %GREEN%[OK]%NC% Containers rebuilt and started
)

echo.
echo %GREEN%========================================================%NC%
echo %GREEN%  LAN Access Configured!                                %NC%
echo %GREEN%========================================================%NC%
echo.
echo   Frontend:    http://%SELECTED_IP%:5173
echo   API Server:  http://%SELECTED_IP%:2030
echo   AI Server:   http://%SELECTED_IP%:9999
echo.
echo %YELLOW%[NOTE]%NC% You may need to open Windows Firewall ports.
echo        Run as Administrator:
echo        netsh advfirewall firewall add rule name="VRecom" dir=in action=allow protocol=tcp localport=5173,2030,9999
echo.

goto :end

:create_lan_env
set "IP=%~1"

:: Read existing Google credentials
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="GOOGLE_CLIENT_ID" set "EXISTING_CLIENT_ID=%%b"
    if "%%a"=="GOOGLE_CLIENT_SECRET" set "EXISTING_CLIENT_SECRET=%%b"
)

(
echo # VRecommendation Environment Configuration
echo # Generated for LAN access - IP: %IP%
echo # Date: %date% %time%
echo.
echo HOST_IP=%IP%
echo FRONTEND_PORT=5173
echo VITE_API_SERVER_URL=http://%IP%:2030
echo VITE_AI_SERVER_URL=http://%IP%:9999
echo.
echo API_SERVER_PORT=2030
echo API_SERVER_HOST=0.0.0.0
echo AI_SERVER_PORT=9999
echo AI_SERVER_HOST=0.0.0.0
echo.
echo REDIS_HOST=redis
echo REDIS_PORT=6379
echo REDIS_PASSWORD=
echo REDIS_DB=0
echo.
echo KAFKA_PORT=9092
echo KAFKA_BOOTSTRAP_SERVERS=kafka:9093
echo KAFKA_UI_PORT=8080
echo PROMETHEUS_PORT=9090
echo.
echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
echo SESSION_SECRET=your-super-secret-session-key-change-in-production
echo.
echo FRONTEND_URL=http://%IP%:5173
echo.
echo # Google OAuth Configuration
if defined EXISTING_CLIENT_ID (
echo GOOGLE_CLIENT_ID=!EXISTING_CLIENT_ID!
) else (
echo GOOGLE_CLIENT_ID=
)
if defined EXISTING_CLIENT_SECRET (
echo GOOGLE_CLIENT_SECRET=!EXISTING_CLIENT_SECRET!
) else (
echo GOOGLE_CLIENT_SECRET=
)
echo GOOGLE_CALLBACK_URL=http://%IP%:2030/api/v1/auth/google/callback
echo.
echo # Admin Portal
echo ADMIN_PORTAL_PORT=3456
echo API_SERVER_URL=http://localhost:2030
) > ".env"

:: Also update api_server .env
(
echo STATUS_DEV=dev
echo HOST_ADDRESS=0.0.0.0
echo HOST_PORT=2030
echo HOST_READ_TIMEOUT=60
echo.
echo # Google OAuth2 credentials
if defined EXISTING_CLIENT_ID (
echo GOOGLE_CLIENT_ID=!EXISTING_CLIENT_ID!
) else (
echo GOOGLE_CLIENT_ID=
)
if defined EXISTING_CLIENT_SECRET (
echo GOOGLE_CLIENT_SECRET=!EXISTING_CLIENT_SECRET!
) else (
echo GOOGLE_CLIENT_SECRET=
)
echo GOOGLE_CALLBACK_URL=http://%IP%:2030/api/v1/auth/google/callback
echo SESSION_SECRET=your_strong_session_secret
echo.
echo FRONTEND_URL=http://%IP%:5173
echo HOST_IP=%IP%
echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
) > "backend\api_server\.env"

goto :eof

:: ========================================
:: Help
:: ========================================
:help
echo %BLUE%========================================================%NC%
echo %BLUE%  VRecommendation - Command Reference                   %NC%
echo %BLUE%========================================================%NC%
echo.
echo %GREEN%Usage:%NC% start.cmd [COMMAND] [OPTIONS]
echo.
echo %GREEN%Docker Commands:%NC%
echo   up, start         Start all Docker services
echo   all               Start Docker services + Admin Portal together
echo   build             Build all Docker images (no cache)
echo   down, stop        Stop all services
echo   restart           Restart all services
echo   logs [service]    Show logs (optionally for specific service)
echo   status            Show status of all services
echo   clean             Remove all containers, volumes, and images
echo.
echo %GREEN%Admin Commands:%NC%
echo   admin             Start Admin Portal (SuperAdmin management)
echo   admin-portal      Same as 'admin'
echo.
echo %GREEN%Configuration:%NC%
echo   setup             Interactive LAN access configuration
echo   setup-lan         Same as 'setup'
echo.
echo %GREEN%Examples:%NC%
echo   start.cmd                    Start all services
echo   start.cmd up                 Start all services
echo   start.cmd all                Start everything (Docker + Admin Portal)
echo   start.cmd build              Rebuild all images
echo   start.cmd logs               Show all logs
echo   start.cmd logs api_server    Show API server logs
echo   start.cmd admin              Start Admin Portal
echo   start.cmd setup              Configure LAN access
echo   start.cmd status             Show service status
echo   start.cmd clean              Clean everything
echo.
echo %YELLOW%Note:%NC% Admin Portal runs on http://127.0.0.1:3456 (localhost only)
echo       Use it to manage Email Whitelist for user registration.
echo.

:end
echo.
pause
