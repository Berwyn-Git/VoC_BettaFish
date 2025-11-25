@echo off
chcp 65001 >nul
echo ========================================
echo 启动图书管理员 Flask 应用
echo ========================================
echo.

REM 设置编码环境
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM 检查并清理端口占用
echo [1/3] 检查端口占用情况...
netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel% == 0 (
    echo 检测到端口 5000 被占用，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
        echo 终止进程 PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

REM 清理 Streamlit 应用端口
echo [2/3] 清理 Streamlit 应用端口...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501 :8502 :8503" ^| findstr "LISTENING"') do (
    echo 终止进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM 启动 Flask 应用
echo [3/3] 启动 Flask 应用...
echo.
python app.py

pause

