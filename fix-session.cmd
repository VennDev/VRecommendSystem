@echo off
setlocal enabledelayedexpansion

:: Quick Session Fix Script for VRecommendation
:: This script helps fix common session-related issues

echo.
echo ================================================
echo  VRecommendation - Session Fix Script
echo ================================================
echo.

:: Colors
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

echo %YELLOW%This script will help fix session-related issues%NC%
echo.

:: Menu
echo Please select an option:
echo.
echo 1. Clear browser cookies and restart services
echo 2. Reset Redis database (clears all sessions)
echo 3. Restart API server only
echo 4. Check session configuration
echo 5. Test authentication endpoints
echo 6. Full system restart
echo 7. Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto :clear_cookies
if "%choice%"=="2" goto :reset_redis
if "%choice%"=="3" goto :restart_api
if "%choice%"=="4" goto :check_config
if "%choice%"=="5" goto :test_auth
if "%choice%"=="6" goto :full_restart
if "%choice%"=="7" goto :exit
goto :invalid_choice

:clear_cookies
echo.
echo %YELLOW%Step 1: Clearing browser data...%NC%
echo.
echo Please manually clear your browser cookies for localhost:
echo 1. Open browser developer tools (F12)
echo 2. Go to Application/Storage tab
echo 3. Clear cookies for localhost:5173, localhost:2030
echo 4. Or use Ctrl+Shift+Delete and clear browsing data
echo.
echo %YELLOW%Step 2: Restarting services...%NC%
docker-compose restart api_server
if %errorlevel% equ 0 (
    echo %GREEN%API server restarted successfully%NC%
) else (
    echo %RED%Failed to restart API server%NC%
)
echo.
echo %GREEN%Please try logging in again%NC%
goto :end

:reset_redis
echo.
echo %RED%WARNING: This will clear ALL data in Redis including sessions%NC%
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto :end

echo %YELLOW%Resetting Redis database...%NC%
docker-compose exec redis redis-cli FLUSHALL
if %errorlevel% equ 0 (
    echo %GREEN%Redis database reset successfully%NC%
    echo %YELLOW%Restarting API server...%NC%
    docker-compose restart api_server
    echo %GREEN%Please try logging in again%NC%
) else (
    echo %RED%Failed to reset Redis database%NC%
)
goto :end

:restart_api
echo.
echo %YELLOW%Restarting API server...%NC%
docker-compose restart api_server
if %errorlevel% equ 0 (
    echo %GREEN%API server restarted successfully%NC%
    echo %GREEN%Please try logging in again%NC%
) else (
    echo %RED%Failed to restart API server%NC%
)
goto :end

:check_config
echo.
echo %BLUE%Checking session configuration...%NC%
echo.
echo Environment Variables:
echo SESSION_SECRET: %SESSION_SECRET%
echo JWT_SECRET_KEY: %JWT_SECRET_KEY%
echo.
echo Checking Docker environment...
docker-compose exec api_server printenv | findstr SECRET
echo.
echo Checking Redis connection...
docker-compose exec redis redis-cli ping
echo.
echo API Server logs (last 10 lines):
docker-compose logs api_server --tail=10
goto :end

:test_auth
echo.
echo %BLUE%Testing authentication endpoints...%NC%
echo.

echo Testing API server ping...
curl -s http://localhost:2030/api/v1/ping
echo.

echo.
echo Testing auth user endpoint (should return 401)...
curl -s http://localhost:2030/api/v1/auth/user
echo.

echo.
echo Testing Google auth redirect...
curl -s -I http://localhost:2030/api/v1/auth/google | findstr Location
echo.

echo.
echo If Google auth returns a Location header, the auth system is working.
echo The session error occurs after successful authentication.
goto :end

:full_restart
echo.
echo %YELLOW%Performing full system restart...%NC%
echo.
echo Stopping all services...
docker-compose down
echo.
echo Starting all services...
docker-compose up -d
echo.
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul
echo.
echo Checking service status...
docker-compose ps
echo.
echo %GREEN%Full restart completed. Please try logging in again.%NC%
goto :end

:invalid_choice
echo.
echo %RED%Invalid choice. Please select 1-7.%NC%
timeout /t 2 /nobreak >nul
goto :clear_cookies

:exit
echo.
echo %BLUE%Goodbye!%NC%
goto :end

:end
echo.
echo ================================================
echo  Additional Troubleshooting Tips
echo ================================================
echo.
echo If you're still having issues:
echo.
echo 1. Check browser console for JavaScript errors
echo 2. Verify you're accessing http://localhost:5173 (not 127.0.0.1)
echo 3. Ensure no firewall is blocking the ports
echo 4. Try incognito/private browsing mode
echo 5. Check if antivirus is interfering
echo.
echo For persistent issues, run: docker-compose logs api_server
echo.
pause
