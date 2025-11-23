@echo off
REM Kafka Test Runner Script for Windows
REM ======================================
REM Script để chạy các Kafka tests một cách dễ dàng trên Windows

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set KAFKA_BROKER=localhost:9092

:main
cls
call :print_header "VRecommendation - Kafka Test Runner"
echo.
echo 1. Start Kafka Server
echo 2. Stop Kafka Server
echo 3. Show Kafka Status
echo 4. Show Kafka Logs
echo.
echo 5. Run Connection Test (Full Test Suite)
echo 6. Run Producer Test
echo 7. Run Consumer Test
echo.
echo 8. Open Kafka UI
echo 9. Exit
echo.

set /p choice="Enter your choice (1-9): "
echo.

if "%choice%"=="1" goto start_kafka
if "%choice%"=="2" goto stop_kafka
if "%choice%"=="3" goto show_status
if "%choice%"=="4" goto show_logs
if "%choice%"=="5" goto run_connection_test
if "%choice%"=="6" goto run_producer
if "%choice%"=="7" goto run_consumer
if "%choice%"=="8" goto open_ui
if "%choice%"=="9" goto exit_script

echo [91mInvalid choice. Please try again.[0m
pause
goto main

:start_kafka
call :print_header "Starting Kafka Server"
cd /d "%SCRIPT_DIR%"
docker-compose up -d
if errorlevel 1 (
    echo [91m✗ Failed to start Kafka[0m
    pause
    goto main
)

echo.
echo [93mℹ Waiting for Kafka to be ready...[0m
timeout /t 5 /nobreak >nul

call :check_kafka_running
if errorlevel 1 (
    echo [91m✗ Kafka failed to start properly[0m
    pause
    goto main
)

echo [92m✓ Kafka started successfully[0m
echo [93mℹ Kafka UI: http://localhost:8080[0m
pause
goto main

:stop_kafka
call :print_header "Stopping Kafka Server"
cd /d "%SCRIPT_DIR%"
docker-compose down
echo [92m✓ Kafka stopped[0m
pause
goto main

:show_status
call :print_header "Kafka Server Status"
echo.
echo Docker Containers:
docker ps --filter "name=kafka" --filter "name=zookeeper" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Connection Info:
echo   Kafka Broker: %KAFKA_BROKER%
echo   Kafka UI: http://localhost:8080
echo   Zookeeper: localhost:2181
echo.
pause
goto main

:show_logs
call :print_header "Kafka Logs"
cd /d "%SCRIPT_DIR%"
echo [93mPress Ctrl+C to stop viewing logs[0m
echo.
docker-compose logs -f kafka
pause
goto main

:run_connection_test
call :print_header "Running Full Connection Test"

call :check_kafka_running
if errorlevel 1 (
    echo [91m✗ Kafka is not running. Please start Kafka first.[0m
    pause
    goto main
)

call :check_python_dependencies
if errorlevel 1 (
    echo [91m✗ Python dependencies not installed[0m
    echo [93m⚠ Please run: pip install -r requirements.txt[0m
    pause
    goto main
)

echo [93mℹ This will test both Producer and Consumer[0m
echo [93mℹ Verifying that group.id is required for Consumer[0m
echo.

cd /d "%SCRIPT_DIR%"
python test_kafka_connection.py
echo.
pause
goto main

:run_producer
call :print_header "Running Kafka Producer Test"

call :check_kafka_running
if errorlevel 1 (
    echo [91m✗ Kafka is not running. Please start Kafka first.[0m
    pause
    goto main
)

call :check_python_dependencies
if errorlevel 1 (
    echo [91m✗ Python dependencies not installed[0m
    echo [93m⚠ Please run: pip install -r requirements.txt[0m
    pause
    goto main
)

echo [93mℹ Producer Script: kafka_producer.py[0m
echo [93mℹ Note: Producer does NOT require group.id[0m
echo.

cd /d "%SCRIPT_DIR%"
python kafka_producer.py
echo.
pause
goto main

:run_consumer
call :print_header "Running Kafka Consumer Test"

call :check_kafka_running
if errorlevel 1 (
    echo [91m✗ Kafka is not running. Please start Kafka first.[0m
    pause
    goto main
)

call :check_python_dependencies
if errorlevel 1 (
    echo [91m✗ Python dependencies not installed[0m
    echo [93m⚠ Please run: pip install -r requirements.txt[0m
    pause
    goto main
)

echo [93mℹ Consumer Script: kafka_consumer_test.py[0m
echo [93mℹ Note: Consumer REQUIRES group.id[0m
echo.

cd /d "%SCRIPT_DIR%"
python kafka_consumer_test.py
echo.
pause
goto main

:open_ui
echo [93mℹ Opening Kafka UI in browser...[0m
start http://localhost:8080
pause
goto main

:exit_script
echo [92m✓ Goodbye![0m
exit /b 0

REM ==================== Functions ====================

:print_header
echo [94m======================================================================[0m
echo   %~1
echo [94m======================================================================[0m
exit /b 0

:check_kafka_running
echo [93mℹ Checking if Kafka is running...[0m
docker ps | findstr /i "kafka" >nul 2>&1
if errorlevel 1 (
    echo [91m✗ Kafka container is not running[0m
    echo [93m⚠ Please start Kafka first:[0m
    echo   cd %SCRIPT_DIR%
    echo   docker-compose up -d
    exit /b 1
)
echo [92m✓ Kafka container is running[0m
exit /b 0

:check_python_dependencies
echo [93mℹ Checking Python dependencies...[0m
python -c "import confluent_kafka" 2>nul
if errorlevel 1 (
    echo [91m✗ confluent-kafka is not installed[0m
    exit /b 1
)
echo [92m✓ confluent-kafka is installed[0m
exit /b 0
