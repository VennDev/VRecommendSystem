@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     VRecommendation - Ngrok OAuth Setup Script               ║
echo ║     Tạo public URL để bypass Google OAuth private IP issue   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if ngrok is installed
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ngrok chưa được cài đặt!
    echo.
    echo Cách cài đặt:
    echo   1. Tải từ: https://ngrok.com/download
    echo   2. Hoặc dùng Scoop: scoop install ngrok
    echo   3. Hoặc dùng Chocolatey: choco install ngrok
    echo.
    echo Sau khi cài đặt, đăng ký tài khoản tại https://ngrok.com
    echo và chạy: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

:: Check if Docker containers are running
docker ps | findstr vrecom_api_server >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] API Server chưa chạy. Đang khởi động Docker...
    docker-compose up -d api_server
    timeout /t 5 >nul
)

echo [INFO] Đang tạo ngrok tunnel cho API Server (port 2030)...
echo.
echo ════════════════════════════════════════════════════════════════
echo.

:: Start ngrok in background and capture URL
start /b ngrok http 2030 --log=stdout > ngrok_temp.log 2>&1

:: Wait for ngrok to start
echo [INFO] Đợi ngrok khởi động...
timeout /t 3 >nul

:: Get the public URL from ngrok API
for /f "tokens=*" %%a in ('curl -s http://127.0.0.1:4040/api/tunnels 2^>nul ^| findstr /r "https://[^\"]*\.ngrok"') do (
    set "NGROK_OUTPUT=%%a"
)

:: Try to extract URL using PowerShell (more reliable)
for /f "delims=" %%i in ('powershell -Command "(Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels').tunnels[0].public_url" 2^>nul') do (
    set "NGROK_URL=%%i"
)

if not defined NGROK_URL (
    echo [ERROR] Không thể lấy ngrok URL. Đang thử lại...
    timeout /t 3 >nul
    for /f "delims=" %%i in ('powershell -Command "(Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels').tunnels[0].public_url" 2^>nul') do (
        set "NGROK_URL=%%i"
    )
)

if not defined NGROK_URL (
    echo [ERROR] Không thể khởi động ngrok tunnel.
    echo Vui lòng chạy thủ công: ngrok http 2030
    del ngrok_temp.log 2>nul
    pause
    exit /b 1
)

:: Clean up temp file
del ngrok_temp.log 2>nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    NGROK TUNNEL ACTIVE                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo   Public URL: %NGROK_URL%
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo [BƯỚC 1] Cập nhật Google Cloud Console:
echo.
echo   1. Truy cập: https://console.cloud.google.com/
echo   2. Vào: APIs ^& Services ^> Credentials
echo   3. Chọn OAuth 2.0 Client ID của bạn
echo   4. Thêm vào "Authorized redirect URIs":
echo.
echo      %NGROK_URL%/api/v1/auth/google/callback
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo [BƯỚC 2] Cập nhật file .env:
echo.
echo   Thay đổi dòng GOOGLE_CALLBACK_URL thành:
echo.
echo      GOOGLE_CALLBACK_URL=%NGROK_URL%/api/v1/auth/google/callback
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo [BƯỚC 3] Restart API Server:
echo.
echo      docker-compose restart api_server
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo [BƯỚC 4] Truy cập Frontend:
echo.
echo   - Từ máy chủ: http://localhost:5173
echo   - Từ LAN: http://192.168.x.x:5173
echo.
echo   Đăng nhập Google sẽ hoạt động trên cả hai!
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo [INFO] Ngrok Dashboard: http://127.0.0.1:4040
echo [INFO] Nhấn Ctrl+C để dừng ngrok tunnel
echo.
echo ════════════════════════════════════════════════════════════════

:: Keep the script running to maintain ngrok
echo.
echo Đang giữ ngrok tunnel hoạt động... (Ctrl+C để dừng)
echo.

:loop
timeout /t 60 >nul
:: Check if ngrok is still running
tasklist | findstr ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ngrok đã dừng. Đang khởi động lại...
    start /b ngrok http 2030 --log=stdout > nul 2>&1
    timeout /t 3 >nul
)
goto loop
