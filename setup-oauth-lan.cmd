@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║       VRecommendation - OAuth LAN Access Setup                   ║
echo ║       Cấu hình Google OAuth để truy cập từ mạng LAN              ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: Check if .env exists
if not exist ".env" (
    echo [ERROR] File .env không tồn tại!
    echo Vui lòng copy từ docker-env-example hoặc example-env
    pause
    exit /b 1
)

echo ════════════════════════════════════════════════════════════════════
echo                         HƯỚNG DẪN
echo ════════════════════════════════════════════════════════════════════
echo.
echo Google OAuth KHÔNG cho phép Private IP (192.168.x.x) làm callback URL.
echo.
echo Bạn có 2 lựa chọn:
echo.
echo   [1] Sử dụng NGROK (Tạo public URL miễn phí)
echo       - Cần cài đặt ngrok và đăng ký tài khoản
echo       - URL thay đổi mỗi lần restart (bản miễn phí)
echo.
echo   [2] Chỉ dùng localhost (Đăng nhập trên máy chủ)
echo       - Đăng nhập Google trên máy đang chạy Docker
echo       - Thiết bị LAN dùng được sau khi đăng nhập
echo.
echo   [3] Thoát
echo.
echo ════════════════════════════════════════════════════════════════════
echo.

set /p CHOICE="Chọn phương án (1/2/3): "

if "%CHOICE%"=="1" goto SETUP_NGROK
if "%CHOICE%"=="2" goto SETUP_LOCALHOST
if "%CHOICE%"=="3" goto END
goto INVALID_CHOICE

:INVALID_CHOICE
echo [ERROR] Lựa chọn không hợp lệ!
pause
exit /b 1

:: ============================================================
:: SETUP NGROK
:: ============================================================
:SETUP_NGROK
echo.
echo ════════════════════════════════════════════════════════════════════
echo                      THIẾT LẬP NGROK
echo ════════════════════════════════════════════════════════════════════
echo.

:: Check if ngrok is installed
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ngrok chưa được cài đặt!
    echo.
    echo Cách cài đặt:
    echo   1. Tải từ: https://ngrok.com/download
    echo   2. Hoặc dùng Scoop: scoop install ngrok
    echo   3. Hoặc dùng Chocolatey: choco install ngrok
    echo.
    echo Sau khi cài đặt:
    echo   1. Đăng ký tài khoản tại https://ngrok.com
    echo   2. Lấy authtoken từ Dashboard
    echo   3. Chạy: ngrok config add-authtoken YOUR_TOKEN
    echo.
    set /p CONTINUE="Bạn đã cài đặt ngrok chưa? (y/n): "
    if /i not "!CONTINUE!"=="y" goto END
)

echo.
echo [INFO] Đang khởi động ngrok tunnel cho port 2030...
echo.

:: Start ngrok in a new window
start "Ngrok Tunnel" cmd /c "ngrok http 2030"

echo [INFO] Đợi ngrok khởi động (5 giây)...
timeout /t 5 /nobreak >nul

:: Get ngrok URL using PowerShell
echo [INFO] Đang lấy ngrok public URL...
for /f "delims=" %%i in ('powershell -Command "try { (Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels' -ErrorAction Stop).tunnels[0].public_url } catch { '' }"') do set NGROK_URL=%%i

if "%NGROK_URL%"=="" (
    echo.
    echo [ERROR] Không thể lấy ngrok URL tự động.
    echo.
    echo Vui lòng:
    echo   1. Mở http://127.0.0.1:4040 trong trình duyệt
    echo   2. Copy URL https://xxxx.ngrok-free.app
    echo.
    set /p NGROK_URL="Nhập ngrok URL (hoặc Enter để bỏ qua): "
)

if "%NGROK_URL%"=="" (
    echo [ERROR] Không có ngrok URL. Đang chuyển sang chế độ localhost...
    goto SETUP_LOCALHOST
)

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║  NGROK URL: %NGROK_URL%
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

set CALLBACK_URL_PUBLIC=%NGROK_URL%/api/v1/auth/google/callback

echo [BƯỚC 1] Cập nhật Google Cloud Console
echo ════════════════════════════════════════════════════════════════════
echo.
echo   1. Truy cập: https://console.cloud.google.com/apis/credentials
echo   2. Chọn OAuth 2.0 Client ID của bạn
echo   3. Trong "Authorized redirect URIs", thêm:
echo.
echo      %CALLBACK_URL_PUBLIC%
echo.
echo   4. Nhấn "Save"
echo.
echo ════════════════════════════════════════════════════════════════════
echo.
set /p DONE1="Đã thêm URI vào Google Console? (y/n): "
if /i not "%DONE1%"=="y" (
    echo [INFO] Vui lòng hoàn thành bước này trước khi tiếp tục.
    pause
)

echo.
echo [BƯỚC 2] Cập nhật file .env
echo ════════════════════════════════════════════════════════════════════
echo.

:: Backup .env
copy /y .env .env.backup >nul 2>&1
echo [INFO] Đã backup .env thành .env.backup

:: Check if GOOGLE_CALLBACK_URL_PUBLIC exists in .env
findstr /C:"GOOGLE_CALLBACK_URL_PUBLIC" .env >nul 2>&1
if %errorlevel% neq 0 (
    echo.>> .env
    echo # Public callback URL for LAN/ngrok access>> .env
    echo GOOGLE_CALLBACK_URL_PUBLIC=%CALLBACK_URL_PUBLIC%>> .env
    echo [INFO] Đã thêm GOOGLE_CALLBACK_URL_PUBLIC vào .env
) else (
    :: Update existing value using PowerShell
    powershell -Command "(Get-Content .env) -replace 'GOOGLE_CALLBACK_URL_PUBLIC=.*', 'GOOGLE_CALLBACK_URL_PUBLIC=%CALLBACK_URL_PUBLIC%' | Set-Content .env"
    echo [INFO] Đã cập nhật GOOGLE_CALLBACK_URL_PUBLIC trong .env
)

:: Ensure GOOGLE_CALLBACK_URL is localhost
findstr /C:"GOOGLE_CALLBACK_URL=" .env | findstr /C:"localhost" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] GOOGLE_CALLBACK_URL không phải localhost!
    echo Đang cập nhật...
    powershell -Command "(Get-Content .env) -replace 'GOOGLE_CALLBACK_URL=http://[0-9\.]+:2030', 'GOOGLE_CALLBACK_URL=http://localhost:2030' | Set-Content .env"
    echo [INFO] Đã cập nhật GOOGLE_CALLBACK_URL về localhost
)

echo.
echo [BƯỚC 3] Restart API Server
echo ════════════════════════════════════════════════════════════════════
echo.

docker-compose restart api_server
if %errorlevel% neq 0 (
    echo [ERROR] Không thể restart API server
    echo Vui lòng chạy: docker-compose restart api_server
) else (
    echo [INFO] API Server đã được restart
)

:: Wait for API server to be ready
echo [INFO] Đợi API Server khởi động...
timeout /t 5 /nobreak >nul

:: Verify configuration
echo.
echo [BƯỚC 4] Kiểm tra cấu hình
echo ════════════════════════════════════════════════════════════════════
echo.
curl -s http://localhost:2030/api/v1/debug/oauth-config 2>nul
echo.

goto SUCCESS

:: ============================================================
:: SETUP LOCALHOST ONLY
:: ============================================================
:SETUP_LOCALHOST
echo.
echo ════════════════════════════════════════════════════════════════════
echo                   CHẾ ĐỘ LOCALHOST
echo ════════════════════════════════════════════════════════════════════
echo.
echo Cấu hình sẽ được đặt để chỉ sử dụng localhost.
echo.
echo Quy trình đăng nhập:
echo   1. Mở trình duyệt trên MÁY ĐANG CHẠY DOCKER
echo   2. Truy cập http://localhost:5173
echo   3. Đăng nhập bằng Google
echo   4. Sau đó, các thiết bị LAN có thể sử dụng app
echo.

:: Backup .env
copy /y .env .env.backup >nul 2>&1
echo [INFO] Đã backup .env thành .env.backup

:: Update GOOGLE_CALLBACK_URL to localhost
powershell -Command "(Get-Content .env) -replace 'GOOGLE_CALLBACK_URL=http://[0-9\.]+:2030', 'GOOGLE_CALLBACK_URL=http://localhost:2030' | Set-Content .env" 2>nul

:: Remove or comment out GOOGLE_CALLBACK_URL_PUBLIC
powershell -Command "(Get-Content .env) -replace '^GOOGLE_CALLBACK_URL_PUBLIC=.*', '# GOOGLE_CALLBACK_URL_PUBLIC=' | Set-Content .env" 2>nul

echo [INFO] Đã cập nhật .env cho chế độ localhost
echo.

echo [BƯỚC] Kiểm tra Google Cloud Console
echo ════════════════════════════════════════════════════════════════════
echo.
echo Đảm bảo trong Google Cloud Console có redirect URI:
echo.
echo   http://localhost:2030/api/v1/auth/google/callback
echo.
echo ════════════════════════════════════════════════════════════════════
echo.

set /p RESTART="Restart API Server? (y/n): "
if /i "%RESTART%"=="y" (
    docker-compose restart api_server
    echo [INFO] API Server đã được restart
    timeout /t 5 /nobreak >nul
)

goto SUCCESS

:: ============================================================
:: SUCCESS
:: ============================================================
:SUCCESS
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    HOÀN TẤT CẤU HÌNH!                            ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo Bạn có thể test OAuth bằng cách:
echo.
echo   1. Mở http://localhost:5173 (hoặc http://LAN_IP:5173)
echo   2. Click "Đăng nhập bằng Google"
echo   3. Hoàn tất đăng nhập
echo.

if defined NGROK_URL (
    echo LƯU Ý VỚI NGROK:
    echo   - Ngrok URL thay đổi mỗi lần restart
    echo   - Phải cập nhật lại Google Console khi URL đổi
    echo   - Ngrok Dashboard: http://127.0.0.1:4040
    echo.
)

echo Xem logs: docker logs -f vrecom_api_server
echo.
goto END

:: ============================================================
:: END
:: ============================================================
:END
echo.
pause
endlocal
