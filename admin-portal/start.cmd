@echo off
title VRecommendation Admin Portal - Localhost Only

echo.
echo ====================================================
echo   VRecommendation Admin Portal - Starting...
echo ====================================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Navigate to admin-portal directory
cd /d "%~dp0"

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [INFO] Dependencies installed successfully.
    echo.
)

echo [INFO] Starting Admin Portal on http://127.0.0.1:3456
echo [INFO] This portal is ONLY accessible from localhost!
echo.
echo Press Ctrl+C to stop the server.
echo.

npm start

pause
