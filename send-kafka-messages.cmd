@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ========================================
echo   Send Test Messages to Kafka
echo ========================================
echo.

set /p num_messages="How many messages to send? (default: 100): "
if "%num_messages%"=="" set num_messages=100

set /p topic="Topic name (default: test_connection_topic): "
if "%topic%"=="" set topic=test_connection_topic

echo.
echo Sending %num_messages% messages to topic '%topic%'...
echo.

set count=0
for /L %%i in (1,1,%num_messages%) do (
    set /a user_id=!random! %% 20 + 1
    set /a item_id=!random! %% 50 + 1
    set /a rating_raw=!random! %% 50 + 10
    set /a rating=!rating_raw! / 10

    echo {"user_id":"user_!user_id!","item_id":"item_!item_id!","rating":!rating!.0,"timestamp":"2025-11-23T10:00:00Z"} | docker exec -i vrecom_kafka kafka-console-producer --bootstrap-server localhost:9092 --topic %topic% 2>nul

    set /a count+=1
    if !count! EQU 10 (
        echo Sent !count! messages...
        set count=0
    )
)

echo.
echo ✓ Successfully sent %num_messages% messages to topic '%topic%'
echo.
echo Verify messages:
echo   docker exec vrecom_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic %topic% --from-beginning --max-messages 5
echo.
pause
