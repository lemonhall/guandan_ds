# 掼蛋游戏服务器启动脚本（PowerShell）

Write-Host "掼蛋游戏服务器启动中..." -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

# 激活虚拟环境
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "错误: 虚拟环境不存在，请先运行: uv venv" -ForegroundColor Red
    exit 1
}

# 启动服务器
Write-Host ""
Write-Host "启动Flask服务器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "游戏地址: http://localhost:5000" -ForegroundColor Green
Write-Host "API文档: http://localhost:5000/health" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan

python server.py
