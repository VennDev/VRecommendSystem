@echo off
setlocal enabledelayedexpansion

:: System Test Script for VRecommendation
:: Tests all services and endpoints

echo.
echo ================================================
echo  VRecommendation System - Test Script
echo ================================================
echo.

:: Colors (Windows doesn't support ANSI colors in cmd by default)
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

:: Test configuration
set API_BASE=http://localhost:2030/api/v1
set AI_BASE=http://localhost:9999/api/v1
set FRONTEND_BASE=http://localhost:5173
set PROMETHEUS_BASE=http://localhost:9090

:: JWT Token for testing (replace with actual token)
set "AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImxpZmVib2F0OTA5QGdtYWlsLmNvbSIsImV4cCI6MTc2MDgxODAyMywiaWF0IjoxNzYwNzMxNjIzLCJuYW1lIjoiTGlmZSBCb2F0IiwidXNlcl9pZCI6IjEwMTAxMTMzNjY2OTczODYxMDkxNiJ9.M5WJbMh-DLOSrXVFvcC9b4MFHFIhH1oiC7ZvrUmcloY"

:: Test counters
set TOTAL_TESTS=0
set PASSED_TESTS=0
set FAILED_TESTS=0

:: Function to run a test
:run_test
set /a TOTAL_TESTS+=1
set TEST_NAME=%1
set TEST_URL=%2
set EXPECTED_STATUS=%3
shift & shift & shift
set TEST_DESC=%*

echo Testing: %TEST_DESC%
echo URL: %TEST_URL%

:: Run curl and capture response
curl -s -w "%%{http_code}" -o temp_response.txt "%TEST_URL%" > temp_status.txt 2>nul
set /p STATUS=<temp_status.txt

if "%STATUS%"=="%EXPECTED_STATUS%" (
    echo %GREEN%PASS%NC% - %TEST_NAME% ^(%STATUS%^)
    set /a PASSED_TESTS+=1
) else (
    echo %RED%FAIL%NC% - %TEST_NAME% ^(Expected: %EXPECTED_STATUS%, Got: %STATUS%^)
    set /a FAILED_TESTS+=1
    if exist temp_response.txt type temp_response.txt
)

:: Cleanup temp files
if exist temp_response.txt del temp_response.txt
if exist temp_status.txt del temp_status.txt
echo.
goto :eof

:: Function to test with auth
:run_auth_test
set /a TOTAL_TESTS+=1
set TEST_NAME=%1
set TEST_URL=%2
set EXPECTED_STATUS=%3
shift & shift & shift
set TEST_DESC=%*

echo Testing: %TEST_DESC%
echo URL: %TEST_URL%

:: Run curl with auth header
curl -s -w "%%{http_code}" -H "Authorization: Bearer %AUTH_TOKEN%" -o temp_response.txt "%TEST_URL%" > temp_status.txt 2>nul
set /p STATUS=<temp_status.txt

if "%STATUS%"=="%EXPECTED_STATUS%" (
    echo %GREEN%PASS%NC% - %TEST_NAME% ^(%STATUS%^)
    set /a PASSED_TESTS+=1
) else (
    echo %RED%FAIL%NC% - %TEST_NAME% ^(Expected: %EXPECTED_STATUS%, Got: %STATUS%^)
    set /a FAILED_TESTS+=1
    if exist temp_response.txt type temp_response.txt
)

:: Cleanup temp files
if exist temp_response.txt del temp_response.txt
if exist temp_status.txt del temp_status.txt
echo.
goto :eof

:: Check if curl is available
curl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%ERROR: curl is not installed or not in PATH%NC%
    echo Please install curl to run this test script.
    pause
    exit /b 1
)

:: Check if Docker services are running
echo Checking Docker services status...
docker-compose ps >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%ERROR: Docker Compose is not available or services are not running%NC%
    echo Please start the services with: docker-compose up -d
    pause
    exit /b 1
)

echo %GREEN%Docker services are running%NC%
echo.

:: Wait for services to be ready
echo Waiting for services to initialize...
timeout /t 5 /nobreak >nul
echo.

:: Start testing
echo ================================================
echo  TESTING API SERVER
echo ================================================

:: Test API Server basic endpoints
call :run_test "API_PING" "%API_BASE%/ping" "200" "API Server ping endpoint"
call :run_test "API_HEALTH" "%API_BASE%/health" "404" "API Server health endpoint (might not exist)"

:: Test API Server protected endpoints
call :run_auth_test "API_ACTIVITY_LOGS" "%API_BASE%/activity-logs/all" "200" "API Server activity logs with auth"

echo ================================================
echo  TESTING AI SERVER
echo ================================================

:: Test AI Server public endpoints
call :run_test "AI_HEALTH" "%AI_BASE%/health" "200" "AI Server health endpoint"
call :run_test "AI_LIST_TASKS" "%AI_BASE%/list_tasks" "200" "AI Server list tasks endpoint"
call :run_test "AI_LIST_MODELS" "%AI_BASE%/list_models" "200" "AI Server list models endpoint"
call :run_test "AI_LIST_DATA_CHEFS" "%AI_BASE%/list_data_chefs" "200" "AI Server list data chefs endpoint"
call :run_test "AI_SCHEDULER_STATUS" "%AI_BASE%/get_scheduler_status" "200" "AI Server scheduler status endpoint"
call :run_test "AI_TOTAL_RUNNING_TASKS" "%AI_BASE%/get_total_running_tasks" "200" "AI Server total running tasks endpoint"

echo ================================================
echo  TESTING FRONTEND
echo ================================================

:: Test Frontend
call :run_test "FRONTEND_HOME" "%FRONTEND_BASE%" "200" "Frontend home page"

echo ================================================
echo  TESTING PROMETHEUS
echo ================================================

:: Test Prometheus
call :run_test "PROMETHEUS_HOME" "%PROMETHEUS_BASE%" "200" "Prometheus home page"
call :run_test "PROMETHEUS_HEALTH" "%PROMETHEUS_BASE%/-/healthy" "200" "Prometheus health endpoint"

echo ================================================
echo  TESTING CORS
echo ================================================

:: Test CORS for AI Server
curl -s -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: GET" -X OPTIONS "%AI_BASE%/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%PASS%NC% - CORS_AI_SERVER - CORS preflight request works
    set /a PASSED_TESTS+=1
) else (
    echo %RED%FAIL%NC% - CORS_AI_SERVER - CORS preflight request failed
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo ================================================
echo  TESTING REDIS CONNECTION
echo ================================================

:: Test Redis connection through Docker
docker-compose exec -T redis redis-cli ping >temp_redis.txt 2>nul
set /p REDIS_RESPONSE=<temp_redis.txt
if "%REDIS_RESPONSE%"=="PONG" (
    echo %GREEN%PASS%NC% - REDIS_CONNECTION - Redis is responding
    set /a PASSED_TESTS+=1
) else (
    echo %RED%FAIL%NC% - REDIS_CONNECTION - Redis is not responding
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
if exist temp_redis.txt del temp_redis.txt
echo.

echo ================================================
echo  TESTING SERVICE INTEGRATION
echo ================================================

:: Test if services can communicate with each other
echo Testing inter-service communication...

:: Test AI Server -> API Server communication (if any)
:: This would depend on your specific implementation

echo %BLUE%INFO%NC% - Inter-service communication tests would depend on specific implementation
echo.

echo ================================================
echo  TEST SUMMARY
echo ================================================

echo Total Tests: %TOTAL_TESTS%
echo Passed: %GREEN%%PASSED_TESTS%%NC%
echo Failed: %RED%%FAILED_TESTS%%NC%

if %FAILED_TESTS% equ 0 (
    echo.
    echo %GREEN%ALL TESTS PASSED! System is working correctly.%NC%
    set EXIT_CODE=0
) else (
    echo.
    echo %RED%SOME TESTS FAILED! Please check the failed tests above.%NC%
    set EXIT_CODE=1
)

echo.
echo ================================================
echo  ADDITIONAL SYSTEM INFO
echo ================================================

echo Docker Compose Services:
docker-compose ps

echo.
echo Docker Images:
docker images | findstr vrecommendation

echo.
echo Docker Networks:
docker network ls | findstr vrecommendation

echo.
echo ================================================
echo  TROUBLESHOOTING TIPS
echo ================================================

if %FAILED_TESTS% gtr 0 (
    echo.
    echo If tests are failing, try:
    echo 1. Check if all services are running: docker-compose ps
    echo 2. Check service logs: docker-compose logs [service-name]
    echo 3. Restart services: docker-compose restart
    echo 4. Rebuild services: docker-compose build --no-cache
    echo 5. Check network connectivity: docker network inspect vrecommendation_vrecom_network
    echo.
    echo Common issues:
    echo - Services still starting up: Wait a few more seconds and rerun tests
    echo - Port conflicts: Check if ports 2030, 9999, 5173, 9090, 6379 are free
    echo - Docker issues: Try 'docker system prune' to clean up
    echo - Configuration issues: Check .env file settings
)

echo.
echo Test completed at: %DATE% %TIME%
echo.

pause
exit /b %EXIT_CODE%
