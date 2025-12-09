@echo off
setlocal enabledelayedexpansion

title VRecommendation - LAN Access Setup
color 0A

echo.
echo ====================================================================
echo    VRecommendation - LAN Access Configuration Setup
echo ====================================================================
echo.

REM Get the script directory
cd /d "%~dp0"

echo [INFO] Detecting network configuration...
echo.

REM Get all IPv4 addresses
set "IP_COUNT=0"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set /a IP_COUNT+=1
    set "IP_!IP_COUNT!=%%a"
    REM Remove leading space
    for /f "tokens=* delims= " %%b in ("%%a") do set "IP_!IP_COUNT!=%%b"
)

if %IP_COUNT% EQU 0 (
    echo [ERROR] No IPv4 address found. Please check your network connection.
    pause
    exit /b 1
)

echo Found %IP_COUNT% IPv4 address(es):
echo.

REM Display all IPs
for /l %%i in (1,1,%IP_COUNT%) do (
    echo   [%%i] !IP_%%i!
)
echo.

REM Auto-select if only one IP, otherwise ask user
if %IP_COUNT% EQU 1 (
    set "SELECTED_IP=!IP_1!"
    echo [INFO] Auto-selected: !SELECTED_IP!
) else (
    set /p "IP_CHOICE=Select IP address number [1-%IP_COUNT%] or enter custom IP: "

    REM Check if it's a number within range
    set "VALID_CHOICE=0"
    for /l %%i in (1,1,%IP_COUNT%) do (
        if "!IP_CHOICE!"=="%%i" (
            set "SELECTED_IP=!IP_%%i!"
            set "VALID_CHOICE=1"
        )
    )

    if "!VALID_CHOICE!"=="0" (
        REM Assume user entered custom IP
        set "SELECTED_IP=!IP_CHOICE!"
    )
)

echo.
echo [INFO] Using IP address: %SELECTED_IP%
echo.

REM Confirm with user
set /p "CONFIRM=Continue with this IP? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo [CANCELLED] Setup cancelled by user.
    pause
    exit /b 0
)

echo.
echo [INFO] Updating .env file for LAN access...

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file first:
    echo   - Copy from .env.example or example-env
    echo   - Or run dev-setup.cmd
    echo.
    pause
    exit /b 1
)

REM Backup existing .env
echo [INFO] Backing up existing .env to .env.backup
copy /y ".env" ".env.backup" >nul

REM Update HOST_IP using PowerShell
echo [INFO] Updating HOST_IP to %SELECTED_IP%
powershell -Command "(Get-Content .env) -replace '^HOST_IP=.*', 'HOST_IP=%SELECTED_IP%' | Set-Content .env" 2>nul

REM Update VITE_API_SERVER_URL
echo [INFO] Updating VITE_API_SERVER_URL
powershell -Command "(Get-Content .env) -replace '^VITE_API_SERVER_URL=.*', 'VITE_API_SERVER_URL=http://%SELECTED_IP%:2030' | Set-Content .env" 2>nul

REM Update VITE_AI_SERVER_URL
echo [INFO] Updating VITE_AI_SERVER_URL
powershell -Command "(Get-Content .env) -replace '^VITE_AI_SERVER_URL=.*', 'VITE_AI_SERVER_URL=http://%SELECTED_IP%:9999' | Set-Content .env" 2>nul

echo [SUCCESS] .env file updated successfully for LAN access!
echo.

REM Ask if user wants to rebuild Docker
echo ====================================================================
echo    Next Steps
echo ====================================================================
echo.
echo To apply changes, you need to rebuild the Docker containers:
echo.
echo   docker-compose down
echo   docker-compose build --no-cache frontend
echo   docker-compose up -d
echo.

set /p "REBUILD=Do you want to rebuild Docker now? (Y/N): "
if /i "%REBUILD%"=="Y" (
    echo.
    echo [INFO] Stopping containers...
    docker-compose down

    echo.
    echo [INFO] Rebuilding frontend...
    docker-compose build --no-cache frontend

    echo.
    echo [INFO] Starting containers...
    docker-compose up -d

    echo.
    echo [SUCCESS] Docker containers rebuilt and started!
)

echo.
echo ====================================================================
echo    Configuration Complete!
echo ====================================================================
echo.
echo Your VRecommendation system is now configured for LAN access.
echo.
echo Access URLs:
echo   Frontend:    http://%SELECTED_IP%:5173
echo   API Server:  http://%SELECTED_IP%:2030
echo   AI Server:   http://%SELECTED_IP%:9999
echo   Kafka UI:    http://%SELECTED_IP%:8080
echo.
echo NOTE: SuperAdmin features are ONLY accessible from localhost!
echo       Use Admin Portal (admin-portal/start.cmd) on this machine.
echo.
echo ====================================================================
echo.

REM Open firewall ports
set /p "FIREWALL=Do you want to open firewall ports? (Y/N): "
if /i "%FIREWALL%"=="Y" (
    echo.
    echo [INFO] Opening firewall ports...

    netsh advfirewall firewall add rule name="VRecom Frontend" dir=in action=allow protocol=tcp localport=5173 >nul 2>&1
    netsh advfirewall firewall add rule name="VRecom API" dir=in action=allow protocol=tcp localport=2030 >nul 2>&1
    netsh advfirewall firewall add rule name="VRecom AI" dir=in action=allow protocol=tcp localport=9999 >nul 2>&1
    netsh advfirewall firewall add rule name="VRecom Kafka UI" dir=in action=allow protocol=tcp localport=8080 >nul 2>&1

    echo [SUCCESS] Firewall rules added!
)

echo.
echo Setup complete! Press any key to exit.
pause >nul
