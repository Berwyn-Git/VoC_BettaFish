@echo off
chcp 65001 >nul
echo ========================================
echo 重启图书管理员 Flask 应用
echo ========================================
echo.

REM 设置编码环境
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM 停止 Flask 应用
echo [1/3] 停止 Flask 应用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo 终止 Flask 进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM 停止 Streamlit 应用
echo [2/3] 停止 Streamlit 应用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501 :8502 :8503" ^| findstr "LISTENING"') do (
    echo 终止 Streamlit 进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

REM 启动 Flask 应用
echo [3/3] 启动 Flask 应用...
echo.
call start_app.bat

