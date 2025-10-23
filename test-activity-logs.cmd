@echo off
setlocal enabledelayedexpansion

:: VRecommendation Activity Logs Test & Seed Script
:: Tests activity logging functionality and creates sample data

echo.
echo ================================================
echo  VRecommendation - Activity Logs Test & Seed
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
set SAMPLE_USER_ID=10101133666973861091
set SAMPLE_EMAIL=lifeboat909@gmail.com

echo %BLUE%Testing and seeding activity logs...%NC%
echo.

:menu
echo Please select an option:
echo.
echo 1. Test activity logs API endpoints
echo 2. Create sample activity data
echo 3. View recent activity logs
echo 4. Clear all activity logs
echo 5. Test frontend activity logging
echo 6. Debug activity logs issue
echo 7. Full activity logs reset
echo 8. Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto :test_api
if "%choice%"=="2" goto :create_samples
if "%choice%"=="3" goto :view_logs
if "%choice%"=="4" goto :clear_logs
if "%choice%"=="5" goto :test_frontend
if "%choice%"=="6" goto :debug_logs
if "%choice%"=="7" goto :reset_logs
if "%choice%"=="8" goto :exit
goto :invalid_choice

:test_api
echo.
echo %BLUE%Testing Activity Logs API endpoints...%NC%
echo.

echo 1. Testing Create Activity Log...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"api_test\",\"details\":{\"test_type\":\"endpoint_test\"}}"
echo.

echo 2. Testing Get All Recent Logs...
curl -s "%API_BASE%/activity-logs/all?limit=5"
echo.

echo 3. Testing Get User Logs...
curl -s "%API_BASE%/activity-logs/user?user_id=%SAMPLE_USER_ID%&limit=5"
echo.

echo %YELLOW%API endpoints test completed%NC%
goto :menu

:create_samples
echo.
echo %BLUE%Creating sample activity data...%NC%
echo.

echo Creating login activity...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"login\",\"details\":{\"provider\":\"google\",\"timestamp\":\"%date% %time%\"}}" >nul

echo Creating model creation activity...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"create\",\"resource_type\":\"model\",\"resource_id\":\"sample_model_1\",\"details\":{\"model_name\":\"Sample Model\",\"algorithm\":\"svd\"}}" >nul

echo Creating task creation activity...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"create\",\"resource_type\":\"task\",\"resource_id\":\"sample_task_1\",\"details\":{\"interval\":60,\"status\":\"active\"}}" >nul

echo Creating data chef activity...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"create\",\"resource_type\":\"data_chef\",\"resource_id\":\"sample_chef_1\",\"details\":{\"type\":\"csv\",\"source\":\"sample.csv\"}}" >nul

echo Creating update activity...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"update\",\"resource_type\":\"task\",\"resource_id\":\"sample_task_1\",\"details\":{\"field\":\"interval\",\"old_value\":60,\"new_value\":120}}" >nul

echo Creating scheduler activity...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"restart\",\"resource_type\":\"scheduler\",\"resource_id\":\"main_scheduler\",\"details\":{\"reason\":\"user_request\"}}" >nul

echo Creating delete activity...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"delete\",\"resource_type\":\"model\",\"resource_id\":\"old_model_1\",\"details\":{\"reason\":\"cleanup\"}}" >nul

echo.
echo %GREEN%Sample activity data created successfully!%NC%
echo %YELLOW%Check the dashboard to see the activities%NC%
goto :menu

:view_logs
echo.
echo %BLUE%Viewing recent activity logs...%NC%
echo.

echo Recent Activity Logs (Last 10):
echo =================================
curl -s "%API_BASE%/activity-logs/all?limit=10" | findstr /C:"action" /C:"user_email" /C:"created_at" /C:"resource_type"
echo.

echo User-specific Activity Logs:
echo =============================
curl -s "%API_BASE%/activity-logs/user?user_id=%SAMPLE_USER_ID%&limit=10" | findstr /C:"action" /C:"user_email" /C:"created_at" /C:"resource_type"
echo.

goto :menu

:clear_logs
echo.
echo %RED%WARNING: This will delete all activity log files%NC%
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto :menu

echo %YELLOW%Clearing activity logs...%NC%

docker-compose exec -T api_server sh -c "rm -rf /app/user_logs/*"
if %errorlevel% equ 0 (
    echo %GREEN%Activity logs cleared successfully%NC%
) else (
    echo %RED%Failed to clear activity logs%NC%
)

goto :menu

:test_frontend
echo.
echo %BLUE%Testing frontend activity logging integration...%NC%
echo.

echo %YELLOW%Frontend Activity Logging Test Instructions:%NC%
echo.
echo 1. Open browser and go to: http://localhost:5173
echo 2. Login to the application
echo 3. Perform the following actions:
echo    - Create a new model
echo    - Create a new task
echo    - Create a new data chef
echo    - Update a task
echo    - Delete something
echo 4. Check the Dashboard "Recent Activity" section
echo 5. Go to the Logs page to see all activities
echo.

echo %BLUE%Checking current frontend activity...%NC%
curl -s "%API_BASE%/activity-logs/all?limit=5"
echo.

echo %YELLOW%If no activities appear after performing actions,%NC%
echo %YELLOW%there might be an issue with frontend integration.%NC%
goto :menu

:debug_logs
echo.
echo %BLUE%Debugging activity logs issues...%NC%
echo.

echo 1. Checking API server logs for activity-related errors...
docker-compose logs api_server --tail=20 | findstr -i activity

echo.
echo 2. Checking user_logs directory structure...
docker-compose exec -T api_server sh -c "find /app/user_logs -type f -name '*.json' | head -10"

echo.
echo 3. Checking user_logs directory permissions...
docker-compose exec -T api_server sh -c "ls -la /app/user_logs"

echo.
echo 4. Testing activity log creation manually...
curl -s -w "HTTP Status: %%{http_code}\n" -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"debug_test\",\"user_email\":\"debug@test.com\",\"action\":\"debug_test\",\"details\":{}}"

echo.
echo 5. Checking if log file was created...
docker-compose exec -T api_server sh -c "ls -la /app/user_logs/debug_test/ 2>/dev/null || echo 'No debug_test directory found'"

echo.
echo %YELLOW%Debug information completed%NC%
goto :menu

:reset_logs
echo.
echo %RED%WARNING: This will completely reset the activity logs system%NC%
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto :menu

echo %YELLOW%Resetting activity logs system...%NC%

echo 1. Stopping API server...
docker-compose stop api_server

echo 2. Clearing all log files...
docker-compose run --rm api_server sh -c "rm -rf /app/user_logs/*"

echo 3. Recreating user_logs directory...
docker-compose run --rm api_server sh -c "mkdir -p /app/user_logs && chown -R appuser:appgroup /app/user_logs"

echo 4. Starting API server...
docker-compose up -d api_server

echo 5. Waiting for server to initialize...
timeout /t 5 /nobreak >nul

echo 6. Testing with fresh log entry...
curl -s -X POST %API_BASE%/activity-logs ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"%SAMPLE_USER_ID%\",\"user_email\":\"%SAMPLE_EMAIL%\",\"action\":\"system_reset\",\"details\":{\"reset_time\":\"%date% %time%\"}}"

echo.
echo %GREEN%Activity logs system reset completed%NC%
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
echo  Activity Logs Troubleshooting Guide
echo ================================================
echo.
echo %YELLOW%Common Issues and Solutions:%NC%
echo.
echo %BLUE%1. No activities showing in dashboard:%NC%
echo   - Check if API endpoints are working (option 1)
echo   - Create sample data to test (option 2)
echo   - Check frontend console for errors
echo   - Verify user ID matches between frontend and backend
echo.
echo %BLUE%2. Permission denied errors:%NC%
echo   - Check user_logs directory permissions
echo   - Rebuild API server container
echo   - Ensure appuser has write access to /app/user_logs
echo.
echo %BLUE%3. Activities not persisting:%NC%
echo   - Check if log files are being created
echo   - Verify JSON structure of log files
echo   - Check disk space in container
echo.
echo %BLUE%4. Frontend not logging activities:%NC%
echo   - Check browser console for errors
echo   - Verify activityLogger.log calls in components
echo   - Check if user object is available
echo   - Verify API endpoints are reachable
echo.
echo %BLUE%5. Sample Activities for Testing:%NC%
echo   - login, logout
echo   - create, update, delete (models, tasks, data_chefs)
echo   - restart, stop (scheduler)
echo.
echo %GREEN%For detailed debugging, use option 6 from the menu.%NC%
echo %GREEN%To reset everything, use option 7 from the menu.%NC%
echo.
pause
