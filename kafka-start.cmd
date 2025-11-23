@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   VRecommendation - Kafka Manager
echo ========================================
echo.

:MENU
echo.
echo Chọn hành động:
echo [1] Start Kafka (Test Server)
echo [2] Stop Kafka (Test Server)
echo [3] Restart Kafka (Test Server)
echo [4] View Kafka Logs
echo [5] Check Kafka Status
echo [6] List Topics
echo [7] Create Topic
echo [8] Start Kafka UI
echo [9] Clean Kafka Data
echo [0] Exit
echo.
set /p choice="Nhập lựa chọn (0-9): "

if "%choice%"=="1" goto START_KAFKA
if "%choice%"=="2" goto STOP_KAFKA
if "%choice%"=="3" goto RESTART_KAFKA
if "%choice%"=="4" goto VIEW_LOGS
if "%choice%"=="5" goto CHECK_STATUS
if "%choice%"=="6" goto LIST_TOPICS
if "%choice%"=="7" goto CREATE_TOPIC
if "%choice%"=="8" goto START_UI
if "%choice%"=="9" goto CLEAN_DATA
if "%choice%"=="0" goto END

echo Invalid choice. Please try again.
goto MENU

:START_KAFKA
echo.
echo Starting Kafka Test Server...
echo.
cd tests\kafka-server
docker-compose up -d
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Kafka started successfully!
    echo ✓ Kafka Broker: localhost:9092
    echo ✓ Kafka UI: http://localhost:8080
    echo.
    echo Waiting for Kafka to be ready...
    timeout /t 10 /nobreak >nul
    docker exec test_kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo ✓ Kafka is ready!
    ) else (
        echo ⚠ Kafka is starting... Please wait a moment.
    )
) else (
    echo ✗ Failed to start Kafka!
)
cd ..\..
pause
goto MENU

:STOP_KAFKA
echo.
echo Stopping Kafka Test Server...
echo.
cd tests\kafka-server
docker-compose down
if %ERRORLEVEL% EQU 0 (
    echo ✓ Kafka stopped successfully!
) else (
    echo ✗ Failed to stop Kafka!
)
cd ..\..
pause
goto MENU

:RESTART_KAFKA
echo.
echo Restarting Kafka Test Server...
echo.
cd tests\kafka-server
docker-compose restart
if %ERRORLEVEL% EQU 0 (
    echo ✓ Kafka restarted successfully!
    echo.
    echo Waiting for Kafka to be ready...
    timeout /t 10 /nobreak >nul
) else (
    echo ✗ Failed to restart Kafka!
)
cd ..\..
pause
goto MENU

:VIEW_LOGS
echo.
echo Viewing Kafka Logs (Press Ctrl+C to exit)...
echo.
cd tests\kafka-server
docker-compose logs -f kafka
cd ..\..
goto MENU

:CHECK_STATUS
echo.
echo Checking Kafka Status...
echo.
cd tests\kafka-server
docker-compose ps
echo.
echo Checking Kafka connectivity...
docker exec test_kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Kafka is running and accessible!
) else (
    echo ✗ Kafka is not running or not accessible!
)
cd ..\..
pause
goto MENU

:LIST_TOPICS
echo.
echo Listing Kafka Topics...
echo.
docker exec test_kafka kafka-topics --list --bootstrap-server localhost:9092
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Failed to list topics. Is Kafka running?
)
echo.
pause
goto MENU

:CREATE_TOPIC
echo.
set /p topic_name="Enter topic name: "
set /p partitions="Enter number of partitions (default: 3): "
set /p replication="Enter replication factor (default: 1): "

if "%partitions%"=="" set partitions=3
if "%replication%"=="" set replication=1

echo.
echo Creating topic '%topic_name%' with %partitions% partitions and replication factor %replication%...
echo.
docker exec test_kafka kafka-topics --create --topic %topic_name% --partitions %partitions% --replication-factor %replication% --bootstrap-server localhost:9092
if %ERRORLEVEL% EQU 0 (
    echo ✓ Topic created successfully!
) else (
    echo ✗ Failed to create topic!
)
echo.
pause
goto MENU

:START_UI
echo.
echo Opening Kafka UI...
echo URL: http://localhost:8080
start http://localhost:8080
echo.
pause
goto MENU

:CLEAN_DATA
echo.
echo ⚠ WARNING: This will delete all Kafka data and topics!
set /p confirm="Are you sure? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo Cancelled.
    pause
    goto MENU
)
echo.
echo Stopping and cleaning Kafka data...
cd tests\kafka-server
docker-compose down -v
if %ERRORLEVEL% EQU 0 (
    echo ✓ Kafka data cleaned successfully!
) else (
    echo ✗ Failed to clean Kafka data!
)
cd ..\..
pause
goto MENU

:END
echo.
echo Goodbye!
exit /b 0
