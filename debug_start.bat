@echo off
chcp 65001 >nul
title LitManager 诊断
echo ==========================================
echo    LitManager 启动诊断
echo ==========================================
echo.

echo [1] 检查 Python...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] Python 不在 PATH 中！
    echo 请确保 Python 已安装并添加到系统 PATH。
    goto :end
)
python --version
echo.

echo [2] 检查后端依赖...
cd /d "%~dp0backend"
python -c "import app.main; print('  后端导入: OK')" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 后端导入失败！
    goto :end
)
echo.

echo [3] 检查前端依赖...
cd /d "%~dp0"
python -c "import modern_gui; print('  前端导入: OK')" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 前端导入失败！
    goto :end
)
echo.

echo [4] 尝试启动后端...
cd /d "%~dp0backend"
start "LitManager-Backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo  后端已在新窗口启动。
echo.

echo [5] 等待 5 秒...
timeout /t 5 /nobreak >nul
echo.

echo [6] 尝试启动前端...
cd /d "%~dp0"
python modern_gui.py 2>&1
echo.
echo 前端已关闭（退出码: %ERRORLEVEL%）

:end
echo.
echo ==========================================
pause
