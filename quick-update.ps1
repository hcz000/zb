# 快速更新已部署的服务器代码 (PowerShell 版)
# 服务器信息
$SERVER_HOST = "192.140.160.119"
$SERVER_PORT = "13621"
$SERVER_USER = "root"
$SERVER_PASS = "ifcqTXOR1880"

# 服务器上的项目路径（根据实际情况修改）
$GATEWAY_PATH = "/opt/live-admin/live-gateway"
$LIVE_PATH = "/opt/live-admin/Live"
$BACKEND_PATH = "/opt/live-admin/backend"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " 快速更新部署文件到服务器" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 检查 sshpass (Git Bash 自带) 或直接用 scp
$hasSshpass = Get-Command sshpass -ErrorAction SilentlyContinue
$hasScp = Get-Command scp -ErrorAction SilentlyContinue

if (-not $hasScp) {
    Write-Host "请先安装 Git for Windows (自带 scp): https://git-scm.com/" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "将更新以下文件:" -ForegroundColor Yellow
Write-Host "  1. Live/viewer/index.html  (新文件，观众观看页)"
Write-Host "  2. live-gateway/gateway.js  (新路由)"
Write-Host "  3. backend/app/main.py      (中间件白名单)"

Write-Host ""
$confirm = Read-Host "确认上传? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "已取消" -ForegroundColor Gray
    exit 0
}

# 上传 viewer 目录
Write-Host ""
Write-Host "[1/3] 上传 viewer 目录..." -ForegroundColor Green
$cmd = "sshpass -p '$SERVER_PASS' scp -P $SERVER_PORT -o StrictHostKeyChecking=no -r Live/viewer/ $SERVER_USER@$SERVER_HOST:$LIVE_PATH/viewer/"
if ($hasSshpass) {
    Invoke-Expression $cmd
} else {
    Write-Host "手动执行: $cmd" -ForegroundColor Yellow
    Write-Host "密码: $SERVER_PASS" -ForegroundColor Yellow
}

# 上传 gateway.js
Write-Host ""
Write-Host "[2/3] 上传 gateway.js..." -ForegroundColor Green
$cmd2 = "sshpass -p '$SERVER_PASS' scp -P $SERVER_PORT -o StrictHostKeyChecking=no live-gateway/gateway.js $SERVER_USER@$SERVER_HOST:$GATEWAY_PATH/gateway.js"
if ($hasSshpass) {
    Invoke-Expression $cmd2
} else {
    Write-Host "手动执行: $cmd2" -ForegroundColor Yellow
    Write-Host "密码: $SERVER_PASS" -ForegroundColor Yellow
}

# 上传 main.py
Write-Host ""
Write-Host "[3/3] 上传 main.py..." -ForegroundColor Green
$cmd3 = "sshpass -p '$SERVER_PASS' scp -P $SERVER_PORT -o StrictHostKeyChecking=no backend/app/main.py $SERVER_USER@$SERVER_HOST:$BACKEND_PATH/app/main.py"
if ($hasSshpass) {
    Invoke-Expression $cmd3
} else {
    Write-Host "手动执行: $cmd3" -ForegroundColor Yellow
    Write-Host "密码: $SERVER_PASS" -ForegroundColor Yellow
}

# 重启服务
Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " 重启服务器上的服务" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$restartCmd = "sshpass -p '$SERVER_PASS' ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST 'pm2 restart all'"

if ($hasSshpass) {
    Write-Host "正在重启所有 PM2 服务..." -ForegroundColor Yellow
    Invoke-Expression $restartCmd
    Write-Host "服务重启完成!" -ForegroundColor Green
} else {
    Write-Host "手动SSH连接服务器并重启:" -ForegroundColor Yellow
    Write-Host "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST" -ForegroundColor White
    Write-Host "  pm2 restart all" -ForegroundColor White
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " 更新完成!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "验证:" -ForegroundColor Yellow
Write-Host "  后台管理:  http://125.208.17.114:8080/"
Write-Host "  观众观看:  http://125.208.17.114:8080/viewer/"
Write-Host "  票数大屏:  http://125.208.17.114:8080/admin/vote-display.html"
