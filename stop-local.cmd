@echo off
setlocal enabledelayedexpansion

title VRecommendation System - Stop Local Services

:: Colors
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "NC=[0m"

echo.
echo %BLUE%========================================================%NC%
echo %BLUE%   VRecommendation System - Stop Local Services         %NC%
echo %BLUE%========================================================%NC%
echo.

:: Get script directory
cd /d "%~dp0"

:: Parse command line arguments
set COMPONENT=%1
if "%COMPONENT%"=="" goto :stop_all
if "%COMPONENT%"=="all" goto :stop_all
if "%COMPONENT%"=="ai" goto :stop_ai
if "%COMPONENT%"=="api" goto :stop_api
if "%COMPONENT%"=="frontend" goto :stop_frontend
if "%COMPONENT%"=="status" goto :status
if "%COMPONENT%"=="help" goto :help
goto :help

:: ========================================
:: Stop All Services
:: ========================================
:stop_all
echo %BLUE%[INFO]%NC% Stopping all local services...
echo.

call :do_stop_ai
call :do_stop_api
call :do_stop_frontend

:: Also try to kill by window title
taskkill /FI "WINDOWTITLE eq VRecommendation - AI Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq VRecommendation - API Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq VRecommendation - Frontend*" /F >nul 2>&1

echo.
echo %GREEN%========================================================%NC%
echo %GREEN%   All services stopped                                 %NC%
echo %GREEN%========================================================%NC%
echo.
goto :end

:: ========================================
:: Stop AI Server
:: ========================================
:stop_ai
echo %BLUE%[INFO]%NC% Stopping AI Server...
call :do_stop_ai
taskkill /FI "WINDOWTITLE eq VRecommendation - AI Server*" /F >nul 2>&1
echo.
goto :end

:do_stop_ai
echo Stopping AI Server (port 9999)...
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":9999" ^| findstr "LISTENING"') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        taskkill /PID !PID! /F >nul 2>&1
        if not errorlevel 1 (
            echo   %GREEN%[OK]%NC% Killed process PID: !PID!
            set "FOUND=1"
        )
    )
)
if "%FOUND%"=="0" (
    echo   %YELLOW%[INFO]%NC% AI Server was not running
)
goto :eof

:: ========================================
:: Stop API Server
:: ========================================
:stop_api
echo %BLUE%[INFO]%NC% Stopping API Server...
call :do_stop_api
taskkill /FI "WINDOWTITLE eq VRecommendation - API Server*" /F >nul 2>&1
echo.
goto :end

:do_stop_api
echo Stopping API Server (port 2030)...
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":2030" ^| findstr "LISTENING"') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        taskkill /PID !PID! /F >nul 2>&1
        if not errorlevel 1 (
            echo   %GREEN%[OK]%NC% Killed process PID: !PID!
            set "FOUND=1"
        )
    )
)
if "%FOUND%"=="0" (
    echo   %YELLOW%[INFO]%NC% API Server was not running
)
goto :eof

:: ========================================
:: Stop Frontend
:: ========================================
:stop_frontend
echo %BLUE%[INFO]%NC% Stopping Frontend...
call :do_stop_frontend
taskkill /FI "WINDOWTITLE eq VRecommendation - Frontend*" /F >nul 2>&1
echo.
goto :end

:do_stop_frontend
echo Stopping Frontend (port 5173)...
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173" ^| findstr "LISTENING"') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        taskkill /PID !PID! /F >nul 2>&1
        if not errorlevel 1 (
            echo   %GREEN%[OK]%NC% Killed process PID: !PID!
            set "FOUND=1"
        )
    )
)
if "%FOUND%"=="0" (
    echo   %YELLOW%[INFO]%NC% Frontend was not running
)
goto :eof

:: ========================================
:: Check Status
:: ========================================
:status
echo %BLUE%[INFO]%NC% Checking service status...
echo.

:: Check AI Server
echo AI Server (port 9999):
netstat -aon 2>nul | findstr ":9999" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[STOPPED]%NC% Not running
) else (
    echo   %GREEN%[RUNNING]%NC% http://localhost:9999
)

:: Check API Server
echo API Server (port 2030):
netstat -aon 2>nul | findstr ":2030" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[STOPPED]%NC% Not running
) else (
    echo   %GREEN%[RUNNING]%NC% http://localhost:2030
)

:: Check Frontend
echo Frontend (port 5173):
netstat -aon 2>nul | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[STOPPED]%NC% Not running
) else (
    echo   %GREEN%[RUNNING]%NC% http://localhost:5173
)

echo.
goto :end

:: ========================================
:: Help
:: ========================================
:help
echo %CYAN%VRecommendation System - Stop Local Services%NC%
echo.
echo Usage: stop-local.cmd [COMPONENT]
echo.
echo Components:
echo   all             Stop all services (default)
echo   ai              Stop only AI Server (port 9999)
echo   api             Stop only API Server (port 2030)
echo   frontend        Stop only Frontend (port 5173)
echo   status          Check status of all services
echo   help            Show this help message
echo.
echo Examples:
echo   stop-local.cmd                Stop all services
echo   stop-local.cmd all            Stop all services
echo   stop-local.cmd ai             Stop only AI Server
echo   stop-local.cmd status         Check service status
echo.
echo Service Ports:
echo   - AI Server:   9999
echo   - API Server:  2030
echo   - Frontend:    5173
echo.
goto :end

:end
endlocal
