@echo off
chcp 65001 >nul
echo ========================================
echo       小说分析器 - 启动程序
echo ========================================

cd /d "%~dp0"

echo [1/2] 检查依赖...
pip install -q -r requirements.txt 2>nul

echo [2/2] 启动服务...
echo.
echo 服务启动后，请访问: http://localhost:8000
echo 按 Ctrl+C 停止服务
echo ========================================

python backend.py

pause
