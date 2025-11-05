#!/bin/bash
# 掼蛋游戏服务器启动脚本（Linux/Mac）

echo "掼蛋游戏服务器启动中..."
echo "======================================"

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "错误: 虚拟环境不存在，请先运行: uv venv"
    exit 1
fi

# 启动服务器
echo ""
echo "启动Flask服务器..."
echo ""
echo "游戏地址: http://localhost:5000"
echo "API文档: http://localhost:5000/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "======================================"

python server.py
