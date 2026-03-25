@echo off
echo ========================================
echo   停止所有 Python 进程
echo ========================================
echo.

taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo ✓ 成功停止所有 Python 进程
) else (
    echo × 没有 Python 进程正在运行
)

echo.
echo 按任意键退出...
pause >nul
