#!/bin/bash

echo "========================================"
echo "启动图书管理员 Flask 应用"
echo "========================================"
echo ""

# 设置编码环境
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 检查并清理端口占用
echo "[1/3] 检查端口占用情况..."

# 检查 lsof 命令是否可用
if ! command -v lsof &> /dev/null; then
    echo "警告: lsof 命令不可用，将跳过端口清理步骤"
    echo "如果遇到端口占用问题，请手动终止相关进程"
else
    # 清理 Flask 应用端口 (5000)
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "检测到端口 5000 被占用，正在清理..."
        lsof -ti :5000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # 清理 Streamlit 应用端口
    echo "[2/3] 清理 Streamlit 应用端口..."
    for port in 8501 8502 8503; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            echo "清理端口 $port..."
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
        fi
    done
    sleep 1
fi

# 启动 Flask 应用
echo "[3/3] 启动 Flask 应用..."
echo ""
python app.py

