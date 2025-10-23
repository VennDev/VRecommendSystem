@echo off
setlocal enabledelayedexpansion

:: Colors for output (Windows CMD doesn't support colors by default, but we'll use echo with formatting)
echo.
echo ================================================
echo  VRecommendation System - Windows Stop Script
echo ================================================
echo.

:: Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=down

if "%COMMAND%"=="down" goto :stop
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="kill" goto :force_stop
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="prune" goto :prune
if "%COMMAND%"=="help" goto :help
goto :help

:stop
echo Stopping all VRecommendation services...
docker-compose down
if %errorlevel% equ 0 (
    echo SUCCESS: All services stopped successfully!
) else (
    echo ERROR: Failed to stop some services
)
goto :end

:force_stop
echo Force stopping all VRecommendation containers...
docker-compose kill
docker-compose down
if %errorlevel% equ 0 (
    echo SUCCESS: All services force stopped!
) else (
    echo ERROR: Failed to force stop services
)
goto :end

:clean
echo.
echo WARNING: This will stop and remove all containers, networks, and volumes
set /p REPLY="Are you sure? (y/N) "
if /i "%REPLY%"=="y" (
    echo Stopping and cleaning up all VRecommendation services...
    docker-compose down -v --remove-orphans
    echo SUCCESS: All services stopped and cleaned up!
) else (
    echo Cleanup cancelled
)
goto :end

:prune
echo.
echo WARNING: This will remove ALL unused Docker resources (images, containers, volumes, networks)
set /p REPLY="Are you sure? (y/N) "
if /i "%REPLY%"=="y" (
    echo Stopping VRecommendation services...
    docker-compose down
    echo Pruning Docker system...
    docker system prune -a -f --volumes
    echo SUCCESS: Docker system pruned!
) else (
    echo Prune cancelled
)
goto :end

:help
echo VRecommendation System - Windows Stop Script
echo.
echo Usage: stop.cmd [COMMAND]
echo.
echo Commands:
echo   down, stop      Stop all services (default)
echo   kill            Force stop all services
echo   clean           Stop and remove containers, networks, volumes
echo   prune           Stop services and prune entire Docker system
echo   help            Show this help message
echo.
echo Examples:
echo   stop.cmd                # Stop all services
echo   stop.cmd kill           # Force stop all services
echo   stop.cmd clean          # Stop and clean up everything
echo   stop.cmd prune          # Full Docker cleanup
goto :end

:end
echo.
echo ================================================
echo  Stop Script Completed
echo ================================================
echo.
pause
