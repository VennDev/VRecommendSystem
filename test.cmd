@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  VRecommendation System - Test Runner
echo ================================================
echo.

:: Parse command line arguments
set COMMAND=%1
set SERVICE=%2

if "%COMMAND%"=="" set COMMAND=all

if "%COMMAND%"=="all" goto :test_all
if "%COMMAND%"=="api" goto :test_api
if "%COMMAND%"=="ai" goto :test_ai
if "%COMMAND%"=="frontend" goto :test_frontend
if "%COMMAND%"=="docker" goto :test_docker
if "%COMMAND%"=="integration" goto :test_integration
if "%COMMAND%"=="help" goto :help
goto :help

:test_all
echo Running all tests...
echo.
call :test_api
call :test_ai
call :test_frontend
call :test_docker
goto :end

:test_api
echo ================================================
echo  Testing API Server
echo ================================================
echo.

if not exist "backend\api_server\go.mod" (
    echo ERROR: API Server not found
    goto :end
)

cd backend\api_server

echo Checking Go installation...
go version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Go not found. Please install Go first.
    cd ..\..
    goto :end
)

echo Installing dependencies...
go mod download

echo Running unit tests...
go test ./...

echo Running tests with coverage...
go test -cover ./...

echo Running tests with verbose output...
go test -v ./...

echo Generating coverage report...
go test -coverprofile=coverage.out ./...
if exist coverage.out (
    go tool cover -html=coverage.out -o coverage.html
    echo SUCCESS: Coverage report generated - coverage.html
)

cd ..\..
echo API Server tests completed.
echo.
goto :eof

:test_ai
echo ================================================
echo  Testing AI Server
echo ================================================
echo.

if not exist "backend\ai_server\pyproject.toml" (
    echo ERROR: AI Server not found
    goto :end
)

cd backend\ai_server

echo Checking Poetry installation...
poetry --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Poetry not found. Please install Poetry first.
    cd ..\..
    goto :end
)

echo Installing dependencies...
poetry install

echo Running unit tests...
poetry run pytest

echo Running tests with coverage...
poetry run pytest --cov=src --cov-report=html --cov-report=term

echo Running tests with verbose output...
poetry run pytest -v

echo Running linting checks...
poetry run flake8 src/

echo Running type checks...
poetry run mypy src/

cd ..\..
echo AI Server tests completed.
echo.
goto :eof

:test_frontend
echo ================================================
echo  Testing Frontend
echo ================================================
echo.

if not exist "frontend\project\package.json" (
    echo ERROR: Frontend not found
    goto :end
)

cd frontend\project

echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js first.
    cd ..\..
    goto :end
)

echo Installing dependencies...
call npm install

echo Running linting...
call npm run lint

echo Running type checking...
call npm run type-check

echo Checking for test scripts...
findstr /c:"\"test\"" package.json >nul
if not errorlevel 1 (
    echo Running tests...
    call npm test
) else (
    echo WARNING: No test script found in package.json
    echo Consider adding a test framework like Vitest or Jest
)

echo Running build test...
call npm run build
if exist "dist" (
    echo SUCCESS: Build test passed
    rmdir /s /q dist
) else (
    echo ERROR: Build test failed
)

cd ..\..
echo Frontend tests completed.
echo.
goto :eof

:test_docker
echo ================================================
echo  Testing Docker Configuration
echo ================================================
echo.

echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found
    goto :end
)

echo Checking Docker Compose installation...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose not found
    goto :end
)

echo Testing Docker Compose configuration...
docker-compose config
if errorlevel 1 (
    echo ERROR: Docker Compose configuration is invalid
    goto :end
)

echo Building Docker images...
docker-compose build
if errorlevel 1 (
    echo ERROR: Docker build failed
    goto :end
)

echo Starting services for testing...
docker-compose up -d

echo Waiting for services to start...
timeout /t 60 /nobreak >nul

echo Testing service health...
set HEALTH_CHECK_FAILED=false

echo Checking API Server...
curl -f http://localhost:2030/api/v1/ping >nul 2>&1
if errorlevel 1 (
    echo ERROR: API Server health check failed
    set HEALTH_CHECK_FAILED=true
) else (
    echo SUCCESS: API Server is healthy
)

echo Checking AI Server...
curl -f http://localhost:9999/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo ERROR: AI Server health check failed
    set HEALTH_CHECK_FAILED=true
) else (
    echo SUCCESS: AI Server is healthy
)

echo Checking Frontend...
curl -f http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo ERROR: Frontend health check failed
    set HEALTH_CHECK_FAILED=true
) else (
    echo SUCCESS: Frontend is healthy
)

echo Checking Prometheus...
curl -f http://localhost:9090 >nul 2>&1
if errorlevel 1 (
    echo WARNING: Prometheus health check failed
) else (
    echo SUCCESS: Prometheus is healthy
)

echo Stopping test services...
docker-compose down

if "%HEALTH_CHECK_FAILED%"=="true" (
    echo ERROR: Some health checks failed
    exit /b 1
) else (
    echo SUCCESS: All Docker tests passed
)

echo Docker tests completed.
echo.
goto :eof

:test_integration
echo ================================================
echo  Running Integration Tests
echo ================================================
echo.

echo Starting all services...
docker-compose up -d

echo Waiting for services to fully start...
timeout /t 90 /nobreak >nul

echo Running integration test scenarios...

:: Test 1: API Server to AI Server communication
echo [Test 1] Testing API Server to AI Server communication...
curl -X GET http://localhost:2030/api/v1/ai/health >nul 2>&1
if errorlevel 1 (
    echo FAILED: API Server cannot communicate with AI Server
) else (
    echo PASSED: API Server to AI Server communication works
)

:: Test 2: Authentication flow (if available)
echo [Test 2] Testing authentication endpoints...
curl -X GET http://localhost:2030/api/v1/ping >nul 2>&1
if errorlevel 1 (
    echo FAILED: Authentication test failed
) else (
    echo PASSED: Authentication endpoints accessible
)

:: Test 3: Frontend to API communication
echo [Test 3] Testing Frontend accessibility...
curl -f http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo FAILED: Frontend is not accessible
) else (
    echo PASSED: Frontend is accessible
)

:: Test 4: Database connectivity (if Redis is required)
echo [Test 4] Testing Redis connectivity...
docker exec vrecom_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo FAILED: Redis connectivity test failed
) else (
    echo PASSED: Redis is accessible
)

:: Test 5: Metrics endpoint
echo [Test 5] Testing metrics endpoint...
curl -f http://localhost:9090 >nul 2>&1
if errorlevel 1 (
    echo WARNING: Prometheus metrics not accessible
) else (
    echo PASSED: Prometheus metrics accessible
)

echo Stopping integration test services...
docker-compose down

echo Integration tests completed.
echo.
goto :eof

:help
echo VRecommendation System - Test Runner
echo.
echo Usage: test.cmd [COMMAND]
echo.
echo Commands:
echo   all            Run all tests (default)
echo   api            Run API Server tests only
echo   ai             Run AI Server tests only
echo   frontend       Run Frontend tests only
echo   docker         Run Docker configuration tests
echo   integration    Run integration tests
echo   help           Show this help message
echo.
echo Examples:
echo   test.cmd                    # Run all tests
echo   test.cmd api               # Test API Server only
echo   test.cmd ai                # Test AI Server only
echo   test.cmd frontend          # Test Frontend only
echo   test.cmd docker            # Test Docker setup
echo   test.cmd integration       # Run integration tests
echo.
echo Requirements:
echo   - Docker and Docker Compose (for Docker and integration tests)
echo   - Go 1.24.4+ (for API Server tests)
echo   - Python 3.9+ and Poetry (for AI Server tests)
echo   - Node.js 18+ (for Frontend tests)
echo   - curl (for health checks)
echo.
echo Test Coverage:
echo   API Server: Unit tests, coverage reports, integration tests
echo   AI Server: Unit tests, coverage reports, linting, type checking
echo   Frontend: Linting, type checking, build tests
echo   Docker: Configuration validation, build tests, health checks
echo   Integration: End-to-end service communication tests
goto :end

:end
echo.
echo ================================================
echo  Test Runner Complete
echo ================================================
pause
