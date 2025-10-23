@echo off
setlocal enabledelayedexpansion

:: VRecommendation Auth Test & Fix Script
:: Tests authentication flow and provides fixes for common issues

echo.
echo ================================================
echo  VRecommendation - Authentication Test & Fix
echo ================================================
echo.

:: Colors
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

:: Configuration
set API_BASE=http://localhost:2030/api/v1
set FRONTEND_BASE=http://localhost:5173

echo %BLUE%Testing authentication system...%NC%
echo.

:menu
echo Please select an option:
echo.
echo 1. Test authentication endpoints
echo 2. Clear browser data and restart services
echo 3. Reset authentication completely
echo 4. Check JWT token storage
echo 5. Fix reload authentication issue
echo 6. View authentication logs
echo 7. Full system restart
echo 8. Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto :test_auth
if "%choice%"=="2" goto :clear_and_restart
if "%choice%"=="3" goto :reset_auth
if "%choice%"=="4" goto :check_jwt
if "%choice%"=="5" goto :fix_reload
if "%choice%"=="6" goto :view_logs
if "%choice%"=="7" goto :full_restart
if "%choice%"=="8" goto :exit
goto :invalid_choice

:test_auth
echo.
echo %BLUE%Testing authentication endpoints...%NC%
echo.

echo 1. Testing API server ping...
curl -s %API_BASE%/ping && echo %GREEN%OK%NC% || echo %RED%FAILED%NC%
echo.

echo 2. Testing auth user endpoint (should return 401)...
curl -s -w "Status: %%{http_code}" %API_BASE%/auth/user
echo.

echo 3. Testing Google auth redirect...
curl -s -I %API_BASE%/auth/google | findstr Location
if %errorlevel% equ 0 (
    echo %GREEN%Auth redirect is working%NC%
) else (
    echo %RED%Auth redirect failed%NC%
)
echo.

echo 4. Testing frontend access...
curl -s -I %FRONTEND_BASE% | findstr "200 OK"
if %errorlevel% equ 0 (
    echo %GREEN%Frontend is accessible%NC%
) else (
    echo %RED%Frontend is not accessible%NC%
)
echo.

echo %YELLOW%Authentication endpoints test completed%NC%
goto :menu

:clear_and_restart
echo.
echo %YELLOW%Clearing browser data and restarting services...%NC%
echo.

echo %BLUE%Step 1: Instructions for clearing browser data%NC%
echo Please manually clear your browser data:
echo 1. Open Developer Tools (F12)
echo 2. Right-click Refresh button → Empty Cache and Hard Reload
echo 3. Or go to Application tab → Storage → Clear site data
echo 4. Or use Ctrl+Shift+Delete to clear browsing data
echo.
echo Press any key after clearing browser data...
pause >nul

echo %BLUE%Step 2: Restarting API server...%NC%
docker-compose restart api_server
if %errorlevel% equ 0 (
    echo %GREEN%API server restarted successfully%NC%
) else (
    echo %RED%Failed to restart API server%NC%
)

echo %BLUE%Step 3: Restarting frontend...%NC%
docker-compose restart frontend
if %errorlevel% equ 0 (
    echo %GREEN%Frontend restarted successfully%NC%
) else (
    echo %RED%Failed to restart frontend%NC%
)
echo.

echo %GREEN%Services restarted. Please try logging in again.%NC%
goto :menu

:reset_auth
echo.
echo %RED%WARNING: This will reset all authentication data%NC%
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto :menu

echo %YELLOW%Resetting authentication system...%NC%

echo 1. Clearing Redis database...
docker-compose exec -T redis redis-cli FLUSHALL
if %errorlevel% equ 0 (
    echo %GREEN%Redis cleared%NC%
) else (
    echo %RED%Failed to clear Redis%NC%
)

echo 2. Restarting API server...
docker-compose restart api_server

echo 3. Restarting frontend...
docker-compose restart frontend

echo.
echo %GREEN%Authentication system reset complete%NC%
echo %YELLOW%Please clear your browser data and try logging in again%NC%
goto :menu

:check_jwt
echo.
echo %BLUE%Checking JWT token configuration...%NC%
echo.

echo Environment variables in API server:
docker-compose exec api_server printenv | findstr SECRET
echo.

echo Environment variables in AI server:
docker-compose exec ai_server printenv | findstr SECRET
echo.

echo %YELLOW%If secrets are not set or different, authentication will fail%NC%
echo %YELLOW%Both servers should have the same JWT_SECRET_KEY%NC%
goto :menu

:fix_reload
echo.
echo %BLUE%Fixing reload authentication issue...%NC%
echo.

echo This issue occurs when JWT tokens are not persisted properly.
echo.

echo %YELLOW%Current fixes applied:%NC%
echo - JWT tokens are stored in localStorage
echo - Auth status is checked on page reload
echo - Both session cookies and JWT tokens are supported
echo - Token verification with server on app start
echo.

echo %BLUE%Manual steps to test:%NC%
echo 1. Login to the application
echo 2. Open browser Developer Tools (F12)
echo 3. Go to Application → Local Storage → http://localhost:5173
echo 4. Check if 'auth_token' and 'user' are stored
echo 5. Reload the page - you should stay logged in
echo.

echo %BLUE%If still not working:%NC%
echo 1. Clear browser data completely
echo 2. Login again
echo 3. Check browser console for any errors
echo 4. Check that localStorage has the tokens
echo.

goto :menu

:view_logs
echo.
echo %BLUE%Viewing authentication logs...%NC%
echo.

echo API Server logs (last 20 lines):
echo ====================================
docker-compose logs api_server --tail=20
echo.

echo Frontend logs (last 10 lines):
echo =================================
docker-compose logs frontend --tail=10
echo.

goto :menu

:full_restart
echo.
echo %YELLOW%Performing full system restart...%NC%
echo.

echo 1. Stopping all services...
docker-compose down

echo 2. Starting all services...
docker-compose up -d

echo 3. Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo 4. Checking service status...
docker-compose ps

echo.
echo %GREEN%Full restart completed%NC%
echo %YELLOW%Please clear browser data and try logging in again%NC%
goto :menu

:invalid_choice
echo.
echo %RED%Invalid choice. Please select 1-8.%NC%
goto :menu

:exit
echo.
echo %BLUE%Exiting...%NC%
goto :end

:end
echo.
echo ================================================
echo  Authentication Troubleshooting Guide
echo ================================================
echo.
echo %YELLOW%Common Issues and Solutions:%NC%
echo.
echo %BLUE%1. Session expires on reload:%NC%
echo   - Clear browser cache and cookies
echo   - Ensure localStorage contains auth_token
echo   - Check JWT_SECRET_KEY is consistent
echo.
echo %BLUE%2. Login redirect loop:%NC%
echo   - Clear all browser data
echo   - Reset Redis database
echo   - Restart API server
echo.
echo %BLUE%3. CORS errors:%NC%
echo   - Check AI server is running
echo   - Verify CORS origins are set correctly
echo   - Restart services if needed
echo.
echo %BLUE%4. JWT token invalid:%NC%
echo   - Check JWT_SECRET_KEY in both servers
echo   - Clear localStorage and login again
echo   - Verify token is not expired
echo.
echo %BLUE%5. Still having issues?%NC%
echo   - Run: docker-compose logs api_server
echo   - Check browser console for errors
echo   - Verify all services are running
echo   - Try incognito/private browsing mode
echo.
echo %GREEN%For persistent issues, check the logs and verify all services are running properly.%NC%
echo.
pause
