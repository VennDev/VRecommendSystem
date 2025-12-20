@echo off
setlocal enabledelayedexpansion

title VRecommendation - Quick Setup

:: Colors
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "NC=[0m"

cls
echo.
echo %CYAN%========================================================%NC%
echo %CYAN%                                                        %NC%
echo %CYAN%   VRecommendation - Quick Setup Wizard                 %NC%
echo %CYAN%                                                        %NC%
echo %CYAN%   First-time setup for new users                       %NC%
echo %CYAN%                                                        %NC%
echo %CYAN%========================================================%NC%
echo.

:: Get script directory
cd /d "%~dp0"

:: ========================================
:: Step 1: Check Prerequisites
:: ========================================
echo %BLUE%[Step 1/6]%NC% Checking prerequisites...
echo.

:: Check Docker
echo   Checking Docker...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   %RED%[X] Docker is NOT installed%NC%
    echo.
    echo   Please install Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%a in ('docker --version') do echo   %GREEN%[OK]%NC% %%a

:: Check Docker Compose
echo   Checking Docker Compose...
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker compose version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo   %RED%[X] Docker Compose is NOT installed%NC%
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%a in ('docker-compose --version 2^>nul') do echo   %GREEN%[OK]%NC% %%a

:: Check if Docker is running
echo   Checking if Docker is running...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   %RED%[X] Docker is not running!%NC%
    echo.
    echo   Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo   %GREEN%[OK]%NC% Docker is running

:: Check Node.js (optional, for Admin Portal)
echo   Checking Node.js (for Admin Portal)...
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   %YELLOW%[!] Node.js not found (optional - needed for Admin Portal)%NC%
    set "NODE_INSTALLED=0"
) else (
    for /f "tokens=*" %%a in ('node --version') do echo   %GREEN%[OK]%NC% Node.js %%a
    set "NODE_INSTALLED=1"
)

echo.
echo   %GREEN%Prerequisites check completed!%NC%
echo.

:: ========================================
:: Step 2: Network Configuration
:: ========================================
echo %BLUE%[Step 2/6]%NC% Network Configuration
echo.
echo   Do you want to enable LAN access?
echo   (Allow other devices on your network to access the system)
echo.
echo   [1] Yes - Configure for LAN access
echo   [2] No  - Localhost only (default)
echo.
set /p "LAN_CHOICE=Select option [1/2]: "

if "%LAN_CHOICE%"=="1" (
    set "ENABLE_LAN=1"
    echo.
    echo   %YELLOW%[INFO]%NC% Detecting network interfaces...
    echo.

    set "IP_COUNT=0"
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
        set /a IP_COUNT+=1
        for /f "tokens=* delims= " %%b in ("%%a") do (
            set "IP_!IP_COUNT!=%%b"
            echo     [!IP_COUNT!] %%b
        )
    )

    if !IP_COUNT! EQU 0 (
        echo   %RED%[ERROR]%NC% No IPv4 address found!
        set "HOST_IP=localhost"
    ) else if !IP_COUNT! EQU 1 (
        set "HOST_IP=!IP_1!"
        echo.
        echo   %GREEN%[INFO]%NC% Auto-selected: !HOST_IP!
    ) else (
        echo.
        set /p "IP_CHOICE=   Select IP number [1-!IP_COUNT!]: "
        set "HOST_IP=!IP_%IP_CHOICE%!"
        if not defined HOST_IP set "HOST_IP=!IP_1!"
    )
) else (
    set "ENABLE_LAN=0"
    set "HOST_IP=localhost"
    echo.
    echo   %GREEN%[OK]%NC% Using localhost only
)

echo.

:: ========================================
:: Step 3: Google OAuth Configuration
:: ========================================
echo %BLUE%[Step 3/6]%NC% Google OAuth Configuration
echo.
echo   Google OAuth is required for user login.
echo   Get credentials from: https://console.cloud.google.com/apis/credentials
echo.

set /p "GOOGLE_CLIENT_ID=Enter Google Client ID (or press Enter to skip): "
if "%GOOGLE_CLIENT_ID%"=="" (
    echo   %YELLOW%[!] Skipped - OAuth login will not work until configured%NC%
    set "GOOGLE_CLIENT_ID="
    set "GOOGLE_CLIENT_SECRET="
) else (
    set /p "GOOGLE_CLIENT_SECRET=Enter Google Client Secret: "
    echo   %GREEN%[OK]%NC% OAuth credentials configured
)

echo.

:: ========================================
:: Step 4: Check Environment Files
:: ========================================
echo %BLUE%[Step 4/6]%NC% Checking environment files...
echo.

:: Check for required .env files
set "ENV_MISSING=0"

if not exist ".env" (
    echo   %RED%[X] Root .env file not found%NC%
    set "ENV_MISSING=1"
) else (
    echo   %GREEN%[OK]%NC% Root .env file exists
)

if not exist "backend\api_server\.env" (
    echo   %RED%[X] API Server .env file not found%NC%
    set "ENV_MISSING=1"
) else (
    echo   %GREEN%[OK]%NC% API Server .env file exists
)

if not exist "backend\ai_server\.env" (
    echo   %RED%[X] AI Server .env file not found%NC%
    set "ENV_MISSING=1"
) else (
    echo   %GREEN%[OK]%NC% AI Server .env file exists
)

if not exist "frontend\project\.env" (
    echo   %RED%[X] Frontend .env file not found%NC%
    set "ENV_MISSING=1"
) else (
    echo   %GREEN%[OK]%NC% Frontend .env file exists
)

if "%ENV_MISSING%"=="1" (
    echo.
    echo   %RED%[ERROR] Missing required .env files!%NC%
    echo.
    echo   Please create the following .env files manually:
    echo.
    echo   1. Root .env:
    echo      Copy .env.example to .env
    echo      Update HOST_IP=%HOST_IP%
    if not "%GOOGLE_CLIENT_ID%"=="" (
        echo      Update GOOGLE_CLIENT_ID=%GOOGLE_CLIENT_ID%
        echo      Update GOOGLE_CLIENT_SECRET=%GOOGLE_CLIENT_SECRET%
    )
    echo.
    echo   2. API Server .env:
    echo      Copy backend\api_server\example-env to backend\api_server\.env
    if not "%GOOGLE_CLIENT_ID%"=="" (
        echo      Update Google OAuth settings
    )
    echo.
    echo   3. AI Server .env:
    echo      Copy backend\ai_server\example-env to backend\ai_server\.env
    echo.
    echo   4. Frontend .env:
    echo      Copy frontend\project\.env.example to frontend\project\.env
    echo.
    pause
    exit /b 1
)

echo.

:: ========================================
:: Step 5: Build and Start Services
:: ========================================
echo %BLUE%[Step 5/6]%NC% Building and starting Docker services...
echo.
echo   This may take several minutes on first run...
echo.

:: Pull base images first
echo   %YELLOW%[INFO]%NC% Pulling base images...
docker-compose pull redis zookeeper 2>nul

:: Build all services
echo   %YELLOW%[INFO]%NC% Building services...
docker-compose build
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   %RED%[ERROR]%NC% Build failed! Check the errors above.
    pause
    exit /b 1
)

:: Start services
echo.
echo   %YELLOW%[INFO]%NC% Starting services...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   %RED%[ERROR]%NC% Failed to start services!
    pause
    exit /b 1
)

echo.
echo   %GREEN%[OK]%NC% All Docker services started!
echo.

:: ========================================
:: Step 6: Setup Admin Portal
:: ========================================
echo %BLUE%[Step 6/6]%NC% Setting up Admin Portal...
echo.

if "%NODE_INSTALLED%"=="1" (
    if exist "admin-portal\package.json" (
        echo   %YELLOW%[INFO]%NC% Installing Admin Portal dependencies...
        cd admin-portal
        call npm install >nul 2>&1
        cd ..
        echo   %GREEN%[OK]%NC% Admin Portal ready
    ) else (
        echo   %YELLOW%[!]%NC% Admin Portal not found
    )
) else (
    echo   %YELLOW%[!]%NC% Skipped - Node.js not installed
    echo       Install Node.js to use Admin Portal for email whitelist management
)

echo.

:: ========================================
:: Setup Complete!
:: ========================================
echo.
echo %GREEN%========================================================%NC%
echo %GREEN%                                                        %NC%
echo %GREEN%   Setup Complete!                                      %NC%
echo %GREEN%                                                        %NC%
echo %GREEN%========================================================%NC%
echo.

:: Wait for services to be ready
echo %YELLOW%[INFO]%NC% Waiting for services to be ready...
timeout /t 10 /nobreak >nul

:: Show status
echo.
docker-compose ps
echo.

:: Show access URLs
echo %BLUE%========================================================%NC%
echo %BLUE%  Access URLs                                           %NC%
echo %BLUE%========================================================%NC%
echo.
echo   %GREEN%Frontend:%NC%
echo     http://localhost:5173
if "%ENABLE_LAN%"=="1" (
    echo     http://%HOST_IP%:5173  (LAN)
)
echo.
echo   %GREEN%API Server:%NC%
echo     http://localhost:2030
if "%ENABLE_LAN%"=="1" (
    echo     http://%HOST_IP%:2030  (LAN)
)
echo.
echo   %GREEN%Kafka UI:%NC%
echo     http://localhost:8080
echo.
echo   %GREEN%Admin Portal:%NC% (for email whitelist management)
echo     Run: start.cmd admin
echo     URL: http://127.0.0.1:3456
echo.

:: Show next steps
echo %YELLOW%========================================================%NC%
echo %YELLOW%  Next Steps                                           %NC%
echo %YELLOW%========================================================%NC%
echo.

if "%GOOGLE_CLIENT_ID%"=="" (
    echo   1. Configure Google OAuth:
    echo      - Go to https://console.cloud.google.com/apis/credentials
    echo      - Create OAuth 2.0 Client ID
    echo      - Add redirect URI: http://%HOST_IP%:2030/api/v1/auth/google/callback
    echo      - Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
    echo      - Restart: start.cmd restart
    echo.
)

if "%ENABLE_LAN%"=="1" (
    echo   2. Open Windows Firewall (run as Administrator):
    echo      netsh advfirewall firewall add rule name="VRecom" dir=in action=allow protocol=tcp localport=5173,2030,9999
    echo.
)

echo   3. Access the dashboard:
echo      Open http://localhost:5173 in your browser
echo.
echo   4. Manage email whitelist:
echo      Run: start.cmd admin
echo.

echo %BLUE%========================================================%NC%
echo %BLUE%  Useful Commands                                       %NC%
echo %BLUE%========================================================%NC%
echo.
echo   start.cmd           Start all services
echo   start.cmd admin     Start Admin Portal
echo   start.cmd status    Check service status
echo   start.cmd logs      View logs
echo   stop.cmd            Stop all services
echo.

pause
