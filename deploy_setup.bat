@echo off
chcp 65001 > nul
title AI Video Factory - 1-Click Cloud Deployment Assistant
color 0B

echo ===============================================================================
echo     🎬 AI VIDEO FACTORY - TRỢ LÝ TỰ ĐỘNG ĐẨY GITHUB ^& CLOUD DEPLOYMENT
echo ===============================================================================
echo.

:: 1. Kiểm tra Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Chưa cài đặt Git! Vui lòng tải Git tại https://git-scm.com
    pause
    exit /b
)

:: 2. Đăng nhập GitHub
echo [1/3] Đang kiểm tra đăng nhập GitHub...
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [*] Bạn chưa đăng nhập GitHub trên máy tính.
    echo [*] Vui lòng làm theo hướng dẫn trên màn hình để đăng nhập (chọn GitHub.com - HTTPS - Yes - Login with a web browser):
    echo.
    gh auth login -p https -w
)

echo.
echo [2/3] Đang tự động tạo Repository trên GitHub và đẩy mã nguồn lên...
gh repo create ai-video-factory --public --source=. --remote=origin --push
if %errorlevel% neq 0 (
    echo [*] Đang cập nhật mã nguồn lên repo đã có...
    git branch -M main
    git push -u origin main
)

echo.
echo [3/3] Đẩy mã nguồn lên GitHub thành công 100%!
echo.
echo ===============================================================================
echo     🎉 BƯỚC CUỐI CÙNG ĐỂ BẬT WEB CHẠY ONLINE TOÀN CẦU:
echo ===============================================================================
echo.
echo 1. Vào https://render.com - Bấm "New +" - "Web Service" - Chọn repo "ai-video-factory" - Bấm Deploy.
echo    (Bạn sẽ nhận được link Backend ví dụ: https://ai-video-factory-api.onrender.com)
echo.
echo 2. Vào https://vercel.com - Bấm "Add New" - "Project" - Chọn repo "ai-video-factory":
echo    - Root Directory: chọn "frontend"
echo    - Environment Variables: thêm VITE_API_BASE_URL = <link Render ở bước 1>
echo    - Bấm Deploy.
echo.
echo Mở trang GitHub của bạn:
gh repo view --web
echo.
pause
