#!/bin/bash
# 一键启动 / 重启所有服务
set -e

PROJ_DIR="/opt/zy"

echo "======================================"
echo "  停止旧进程..."
echo "======================================"

# 杀掉 uvicorn 和 gateway 进程
pkill -f "uvicorn app.main" 2>/dev/null && echo "✓ 已停止后端" || echo "- 后端未运行"
pkill -f "node gateway.js" 2>/dev/null && echo "✓ 已停止网关" || echo "- 网关未运行"

sleep 1

echo ""
echo "======================================"
echo "  拉取最新代码..."
echo "======================================"
cd "$PROJ_DIR"
git pull

echo ""
echo "======================================"
echo "  启动后端 (port 8000)..."
echo "======================================"
cd "$PROJ_DIR/backend"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
echo "✓ 后端已启动, PID: $!"

echo ""
echo "======================================"
echo "  启动网关 (port 8080)..."
echo "======================================"
cd "$PROJ_DIR/live-gateway"
nohup node gateway.js > /tmp/gateway.log 2>&1 &
echo "✓ 网关已启动, PID: $!"

sleep 2

echo ""
echo "======================================"
echo "  服务状态"
echo "======================================"
ps aux | grep -E "uvicorn|gateway" | grep -v grep

echo ""
echo "======================================"
echo "  访问地址"
echo "======================================"
echo "  后台管理: http://125.208.17.114:8080/"
echo "  观众观看: http://125.208.17.114:8080/viewer/"
