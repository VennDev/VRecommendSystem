@echo off
setlocal enabledelayedexpansion

title VRecommendation System - Stop Script

:: Colors
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo.
echo %BLUE%========================================================%NC%
echo %BLUE%  VRecommendation System - Stop Script                  %NC%
echo %BLUE%========================================================%NC%
echo.

:: Get script directory
cd /d "%~dp0"

:: Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=down

if "%COMMAND%"=="down" goto :stop
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="all" goto :stop_all
if "%COMMAND%"=="kill" goto :force_stop
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="prune" goto :prune
if "%COMMAND%"=="admin" goto :stop_admin
if "%COMMAND%"=="help" goto :help
goto :help

:stop
echo %BLUE%[INFO]%NC% Stopping all Docker services...
docker-compose down
if %errorlevel% equ 0 (
    echo %GREEN%[OK]%NC% All Docker services stopped successfully!
) else (
    echo %RED%[ERROR]%NC% Failed to stop some services
)

:: Check if Admin Portal is running and notify user
tasklist /fi "WINDOWTITLE eq VRecommendation Admin Portal*" 2>nul | find "node.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo %YELLOW%[NOTE]%NC% Admin Portal is still running.
    echo        Use 'stop.cmd all' to stop everything including Admin Portal.
)
goto :end

:stop_all
echo %BLUE%[INFO]%NC% Stopping ALL services (Docker + Admin Portal)...
echo.

:: Stop Admin Portal first
call :stop_admin_silent

:: Stop Docker services
echo %BLUE%[INFO]%NC% Stopping Docker services...
docker-compose down
if %errorlevel% equ 0 (
    echo %GREEN%[OK]%NC% All services stopped successfully!
) else (
    echo %RED%[ERROR]%NC% Failed to stop some Docker services
)
goto :end

:stop_admin
echo %BLUE%[INFO]%NC% Stopping Admin Portal...

:: Find and kill node processes running admin portal
for /f "tokens=2" %%a in ('tasklist /fi "WINDOWTITLE eq VRecommendation Admin Portal*" /fo list 2^>nul ^| findstr "PID:"') do (
    echo %YELLOW%[INFO]%NC% Terminating Admin Portal process (PID: %%a)
    taskkill /pid %%a /f >nul 2>&1
)

:: Also try to kill by port 3456
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3456" ^| findstr "LISTENING" 2^>nul') do (
    echo %YELLOW%[INFO]%NC% Terminating process on port 3456 (PID: %%a)
    taskkill /pid %%a /f >nul 2>&1
)

echo %GREEN%[OK]%NC% Admin Portal stopped
goto :end

:stop_admin_silent
:: Silent version for internal use
for /f "tokens=2" %%a in ('tasklist /fi "WINDOWTITLE eq VRecommendation Admin Portal*" /fo list 2^>nul ^| findstr "PID:"') do (
    taskkill /pid %%a /f >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3456" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /pid %%a /f >nul 2>&1
)
echo %GREEN%[OK]%NC% Admin Portal stopped
goto :eof

:force_stop
echo %BLUE%[INFO]%NC% Force stopping all services...

:: Force stop Admin Portal
call :stop_admin_silent

:: Force stop Docker
echo %BLUE%[INFO]%NC% Force stopping Docker containers...
docker-compose kill
docker-compose down
if %errorlevel% equ 0 (
    echo %GREEN%[OK]%NC% All services force stopped!
) else (
    echo %RED%[ERROR]%NC% Failed to force stop services
)
goto :end

:clean
echo.
echo %RED%WARNING: This will stop and remove all containers, networks, and volumes%NC%
set /p REPLY="Are you sure? (y/N): "
if /i "%REPLY%"=="y" (
    echo.
    echo %BLUE%[INFO]%NC% Stopping Admin Portal...
    call :stop_admin_silent

    echo %BLUE%[INFO]%NC% Stopping and cleaning up Docker services...
    docker-compose down -v --remove-orphans
    echo %GREEN%[OK]%NC% All services stopped and cleaned up!
) else (
    echo %YELLOW%[INFO]%NC% Cleanup cancelled
)
goto :end

:prune
echo.
echo %RED%WARNING: This will remove ALL unused Docker resources!%NC%
echo         (images, containers, volumes, networks)
set /p REPLY="Are you sure? (y/N): "
if /i "%REPLY%"=="y" (
    echo.
    echo %BLUE%[INFO]%NC% Stopping Admin Portal...
    call :stop_admin_silent

    echo %BLUE%[INFO]%NC% Stopping Docker services...
    docker-compose down

    echo %BLUE%[INFO]%NC% Pruning Docker system...
    docker system prune -a -f --volumes

    echo %GREEN%[OK]%NC% Docker system pruned!
) else (
    echo %YELLOW%[INFO]%NC% Prune cancelled
)
goto :end

:help
echo %BLUE%========================================================%NC%
echo %BLUE%  VRecommendation - Stop Command Reference              %NC%
echo %BLUE%========================================================%NC%
echo.
echo %GREEN%Usage:%NC% stop.cmd [COMMAND]
echo.
echo %GREEN%Commands:%NC%
echo   down, stop      Stop Docker services (default)
echo   all             Stop everything (Docker + Admin Portal)
echo   admin           Stop only Admin Portal
echo   kill            Force stop all services
echo   clean           Stop and remove containers, networks, volumes
echo   prune           Stop services and prune entire Docker system
echo   help            Show this help message
echo.
echo %GREEN%Examples:%NC%
echo   stop.cmd              Stop Docker services
echo   stop.cmd all          Stop everything
echo   stop.cmd admin        Stop only Admin Portal
echo   stop.cmd kill         Force stop all services
echo   stop.cmd clean        Stop and clean up everything
echo   stop.cmd prune        Full Docker cleanup
echo.
goto :end

:end
echo.
echo %BLUE%========================================================%NC%
echo %BLUE%  Stop Script Completed                                 %NC%
echo %BLUE%========================================================%NC%
echo.
pause
