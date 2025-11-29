@echo off
REM Docker Networking Test Script for Windows
REM Script này kiểm tra xem các container có thể giao tiếp với nhau không

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo Docker Networking Test
echo ==========================================
echo.

REM Test 1: Check if containers are running
echo Test 1: Checking if containers are running...
echo ---

set containers=vrecom_api_server vrecom_ai_server vrecom_frontend vrecom_redis vrecom_kafka

for %%C in (%containers%) do (
    docker ps | findstr "%%C" >nul
    if !errorlevel! equ 0 (
        echo [PASS] Container %%C is running
    ) else (
        echo [FAIL] Container %%C is NOT running
    )
)

echo.

REM Test 2: Check container-to-container communication
echo Test 2: Checking container-to-container communication...
echo ---

REM Test API Server from Frontend
echo Testing API Server connectivity from Frontend...
docker exec vrecom_frontend curl -s http://api_server:2030/api/v1/ping >nul 2>&1
if !errorlevel! equ 0 (
    echo [PASS] Frontend ^-^> API Server (http://api_server:2030)
) else (
    echo [FAIL] Frontend ^-^> API Server (http://api_server:2030)
)

REM Test AI Server from Frontend
echo Testing AI Server connectivity from Frontend...
docker exec vrecom_frontend curl -s http://ai_server:9999/api/v1/health >nul 2>&1
if !errorlevel! equ 0 (
    echo [PASS] Frontend ^-^> AI Server (http://ai_server:9999)
) else (
    echo [FAIL] Frontend ^-^> AI Server (http://ai_server:9999)
)

REM Test Redis from API Server
echo Testing Redis connectivity from API Server...
docker exec vrecom_api_server curl -s http://redis:6379 >nul 2>&1
if !errorlevel! equ 0 (
    echo [PASS] API Server ^-^> Redis (http://redis:6379)
) else (
    echo [FAIL] API Server ^-^> Redis (http://redis:6379)
)

echo.

REM Test 3: Check SuperAdmin Security
echo Test 3: Checking SuperAdmin Security...
echo ---

REM Test from localhost (should succeed)
echo Testing SuperAdmin access from localhost...
docker exec vrecom_api_server curl -s -H "Host: localhost" http://localhost:2030/api/v1/local/whitelist/list >nul 2>&1
if !errorlevel! equ 0 (
    echo [PASS] SuperAdmin access from localhost
) else (
    echo [FAIL] SuperAdmin access from localhost
)

REM Test from external IP (should fail with 403)
echo Testing SuperAdmin access from external IP (should be denied)...
for /f %%A in ('docker exec vrecom_api_server curl -s -w "%%{http_code}" http://api_server:2030/api/v1/local/whitelist/list') do set http_code=%%A

if "%http_code:~-3%" equ "403" (
    echo [PASS] SuperAdmin correctly denies external access (HTTP 403)
) else (
    echo [FAIL] SuperAdmin should deny external access but got HTTP %http_code:~-3%
)

echo.

REM Test 4: Check port mappings
echo Test 4: Checking port mappings...
echo ---

docker ps --format "table {{.Ports}}" | findstr "2030" >nul
if !errorlevel! equ 0 (
    echo [PASS] Port 2030 is mapped
) else (
    echo [FAIL] Port 2030 is NOT mapped
)

docker ps --format "table {{.Ports}}" | findstr "9999" >nul
if !errorlevel! equ 0 (
    echo [PASS] Port 9999 is mapped
) else (
    echo [FAIL] Port 9999 is NOT mapped
)

docker ps --format "table {{.Ports}}" | findstr "5173" >nul
if !errorlevel! equ 0 (
    echo [PASS] Port 5173 is mapped
) else (
    echo [FAIL] Port 5173 is NOT mapped
)

echo.

REM Test 5: Check network
echo Test 5: Checking Docker network...
echo ---

docker network ls | findstr "vrecom_network" >nul
if !errorlevel! equ 0 (
    echo [PASS] Network 'vrecom_network' exists
    echo.
    echo Containers in vrecom_network:
    docker network inspect vrecom_network --format="{{range .Containers}}{{.Name}} ({{.IPv4Address}}){{println}}{{end}}"
) else (
    echo [FAIL] Network 'vrecom_network' does NOT exist
)

echo.
echo ==========================================
echo Test Complete
echo ==========================================
echo.

pause
