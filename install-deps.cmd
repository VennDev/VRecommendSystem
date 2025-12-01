@echo off
setlocal enabledelayedexpansion

title VRecommendation System - Dependency Installation

:: Colors
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "NC=[0m"

echo.
echo %BLUE%========================================================%NC%
echo %BLUE%   VRecommendation System - Dependency Installation     %NC%
echo %BLUE%========================================================%NC%
echo.

:: Get script directory
cd /d "%~dp0"

:: Parse command line arguments
set COMPONENT=%1
if "%COMPONENT%"=="" goto :install_all
if "%COMPONENT%"=="all" goto :install_all
if "%COMPONENT%"=="ai" goto :install_ai
if "%COMPONENT%"=="api" goto :install_api
if "%COMPONENT%"=="frontend" goto :install_frontend
if "%COMPONENT%"=="check" goto :check_deps
if "%COMPONENT%"=="help" goto :help
goto :help

:: ========================================
:: Check Dependencies
:: ========================================
:check_deps
echo %BLUE%[INFO]%NC% Checking system dependencies...
echo.

set "ALL_OK=1"

:: Check Go
echo Checking Go...
go version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Go is not installed
    echo   Download from: https://golang.org/dl/
    set "ALL_OK=0"
) else (
    for /f "tokens=3" %%v in ('go version') do echo   %GREEN%[OK]%NC% Go %%v
)

:: Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Python is not installed
    echo   Download from: https://python.org/downloads/
    set "ALL_OK=0"
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   %GREEN%[OK]%NC% Python %%v
)

:: Check Poetry
echo Checking Poetry...
poetry --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Poetry is not installed
    echo   Install with: pip install poetry
    echo   Or visit: https://python-poetry.org/docs/
    set "ALL_OK=0"
) else (
    for /f "tokens=1-3" %%a in ('poetry --version 2^>^&1') do echo   %GREEN%[OK]%NC% %%a %%b %%c
)

:: Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% Node.js is not installed
    echo   Download from: https://nodejs.org/
    set "ALL_OK=0"
) else (
    for /f %%v in ('node --version') do echo   %GREEN%[OK]%NC% Node.js %%v
)

:: Check npm
echo Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo   %RED%[MISSING]%NC% npm is not installed
    set "ALL_OK=0"
) else (
    for /f %%v in ('npm --version') do echo   %GREEN%[OK]%NC% npm %%v
)

echo.
if "%ALL_OK%"=="1" (
    echo %GREEN%[SUCCESS]%NC% All system dependencies are installed!
) else (
    echo %RED%[WARNING]%NC% Some dependencies are missing. Please install them.
)
echo.
goto :end

:: ========================================
:: Install All
:: ========================================
:install_all
echo %BLUE%[INFO]%NC% Installing all project dependencies...
echo.

:: Check system dependencies first
call :check_system_deps
if "%DEPS_OK%"=="0" (
    echo %RED%[ERROR]%NC% Missing system dependencies. Please install them first.
    echo Run: install-deps.cmd check
    goto :end
)

:: Install AI Server
echo.
echo %CYAN%========================================%NC%
echo %CYAN%[1/3] AI Server (Python/Poetry)%NC%
echo %CYAN%========================================%NC%
call :do_install_ai

:: Install API Server
echo.
echo %CYAN%========================================%NC%
echo %CYAN%[2/3] API Server (Go)%NC%
echo %CYAN%========================================%NC%
call :do_install_api

:: Install Frontend
echo.
echo %CYAN%========================================%NC%
echo %CYAN%[3/3] Frontend (Node.js/npm)%NC%
echo %CYAN%========================================%NC%
call :do_install_frontend

echo.
echo %GREEN%========================================================%NC%
echo %GREEN%   All dependencies installed successfully!             %NC%
echo %GREEN%========================================================%NC%
echo.
echo %YELLOW%Next steps:%NC%
echo   1. Configure your .env files (run: start-local.cmd)
echo   2. Start the services: start-local.cmd start
echo.
goto :end

:: ========================================
:: Install AI Server
:: ========================================
:install_ai
echo %BLUE%[INFO]%NC% Installing AI Server dependencies...
echo.
call :do_install_ai
goto :end

:do_install_ai
if not exist "backend\ai_server\pyproject.toml" (
    echo %RED%[ERROR]%NC% pyproject.toml not found in backend\ai_server
    goto :eof
)

echo Checking Poetry...
poetry --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Poetry is not installed
    echo Install with: pip install poetry
    goto :eof
)

cd backend\ai_server
echo Installing Python dependencies with Poetry...
echo This may take a few minutes...
echo.

poetry install
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Failed to install AI Server dependencies
    cd ..\..
    goto :eof
)

echo.
echo %GREEN%[OK]%NC% AI Server dependencies installed successfully
cd ..\..
goto :eof

:: ========================================
:: Install API Server
:: ========================================
:install_api
echo %BLUE%[INFO]%NC% Installing API Server dependencies...
echo.
call :do_install_api
goto :end

:do_install_api
if not exist "backend\api_server\go.mod" (
    echo %RED%[ERROR]%NC% go.mod not found in backend\api_server
    goto :eof
)

echo Checking Go...
go version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Go is not installed
    echo Download from: https://golang.org/dl/
    goto :eof
)

cd backend\api_server
echo Downloading Go modules...
echo.

go mod download
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Failed to download Go modules
    cd ..\..
    goto :eof
)

echo Tidying Go modules...
go mod tidy
if errorlevel 1 (
    echo %YELLOW%[WARN]%NC% go mod tidy returned warnings
)

echo.
echo %GREEN%[OK]%NC% API Server dependencies installed successfully
cd ..\..
goto :eof

:: ========================================
:: Install Frontend
:: ========================================
:install_frontend
echo %BLUE%[INFO]%NC% Installing Frontend dependencies...
echo.
call :do_install_frontend
goto :end

:do_install_frontend
if not exist "frontend\project\package.json" (
    echo %RED%[ERROR]%NC% package.json not found in frontend\project
    goto :eof
)

echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Node.js is not installed
    echo Download from: https://nodejs.org/
    goto :eof
)

cd frontend\project
echo Installing npm packages...
echo This may take a few minutes...
echo.

call npm install
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Failed to install Frontend dependencies
    cd ..\..
    goto :eof
)

echo.
echo %GREEN%[OK]%NC% Frontend dependencies installed successfully
cd ..\..
goto :eof

:: ========================================
:: Silent System Dependency Check
:: ========================================
:check_system_deps
set "DEPS_OK=1"
go version >nul 2>&1
if errorlevel 1 set "DEPS_OK=0"
poetry --version >nul 2>&1
if errorlevel 1 set "DEPS_OK=0"
node --version >nul 2>&1
if errorlevel 1 set "DEPS_OK=0"
goto :eof

:: ========================================
:: Help
:: ========================================
:help
echo %CYAN%VRecommendation System - Dependency Installation%NC%
echo.
echo Usage: install-deps.cmd [COMPONENT]
echo.
echo Components:
echo   all             Install all dependencies (default)
echo   ai              Install AI Server dependencies (Python/Poetry)
echo   api             Install API Server dependencies (Go)
echo   frontend        Install Frontend dependencies (Node.js/npm)
echo   check           Check if system dependencies are installed
echo   help            Show this help message
echo.
echo Examples:
echo   install-deps.cmd                Install all dependencies
echo   install-deps.cmd all            Install all dependencies
echo   install-deps.cmd ai             Install only AI Server dependencies
echo   install-deps.cmd api            Install only API Server dependencies
echo   install-deps.cmd frontend       Install only Frontend dependencies
echo   install-deps.cmd check          Check system dependencies
echo.
echo System Requirements:
echo   - Go 1.24+      (for API Server)
echo   - Python 3.9+   (for AI Server)
echo   - Poetry        (for AI Server dependency management)
echo   - Node.js 18+   (for Frontend)
echo   - npm           (for Frontend)
echo.
echo Installation Links:
echo   - Go:       https://golang.org/dl/
echo   - Python:   https://python.org/downloads/
echo   - Poetry:   https://python-poetry.org/docs/ (or: pip install poetry)
echo   - Node.js:  https://nodejs.org/
echo.
goto :end

:end
echo.
endlocal
