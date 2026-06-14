@echo off
chcp 65001 >nul
title LitManager 图书馆管理系统
echo ==========================================
echo    LitManager 图书馆管理系统
echo ==========================================
echo.

echo [1/2] 启动后端服务...
set "BACKEND_SCRIPT=%~dp0backend\run_server.bat"
start "" "%BACKEND_SCRIPT%"

echo 等待后端启动（5秒）...
timeout /t 5 /nobreak >nul

echo [2/2] 启动管理端界面...
cd /d "%~dp0"
python modern_gui.py

echo.
echo 管理端已关闭。
pause
