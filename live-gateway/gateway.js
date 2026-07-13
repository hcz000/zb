const express = require('express');
const cors = require('cors');
const http = require('http');
const httpProxy = require('http-proxy');
const path = require('path');

// ==================== 后端目标地址 ====================
// 网关把 /api 与 /ws 反向代理到真实 Python 后端。
// 部署时通过环境变量 BACKEND_URL 指定（默认本机 8000）。
const BACKEND_TARGET = process.env.BACKEND_URL || 'http://localhost:8000';

const serverCfg = require('./config/server-mode.node.js');
const { getCurrentServerConfig, printConfig } = serverCfg;
const currentConfig = getCurrentServerConfig();
const port = currentConfig.port; // 8080

const app = express();

// CORS：允许所有来源（前端可能从任意源访问网关）
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    credentials: true
}));

// 注意：不要在此使用 express.json()，否则会消费请求体，
// 导致反向代理转发 POST/PUT 时 body 为空。后端自己解析 JSON。

// ==================== 静态托管前端（管理后台页面） ====================
// 把 Live/ 作为站点根：/admin/*、/static/* 均从 Live 解析；
// 访问网关根路径 / 直接打开管理后台，实现同源调用，避免跨域。
const SITE_ROOT = process.env.SITE_ROOT || path.resolve(__dirname, '..', 'Live');
// 注意：禁用 index 自动服务，否则访问 / 时 static 会直接返回 Live/ 根目录下的
// index.html（小程序 uniapp 构建产物），而不是后台管理页。/ 交给下面显式的
// app.get('/') 返回 admin/index.html；/admin/* 与 /static/* 仍由 static 提供。
app.use(express.static(SITE_ROOT, { index: false }));
app.get('/', (req, res) => {
    res.sendFile(path.join(SITE_ROOT, 'admin', 'index.html'));
});

// ==================== 反向代理 ====================
const proxy = httpProxy.createProxyServer({
    target: BACKEND_TARGET,
    changeOrigin: true,
    ws: true,
    proxyTimeout: 30000,
    timeout: 30000
});

proxy.on('error', (err, req, res) => {
    console.error('❌ 代理错误:', err.message);
    if (res && typeof res.writeHead === 'function' && !res.headersSent) {
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, message: '网关无法连接后端: ' + BACKEND_TARGET }));
    } else if (res && res.socket) {
        res.socket.destroy();
    }
});

// 健康检查
app.get('/health', (req, res) => res.json({ status: 'ok', backend: BACKEND_TARGET }));

// REST 代理：所有 /api/* 转发到后端
// 注意：不能用 app.use('/api', ...) 挂载，否则 Express 会剥离 /api 前缀，
// 导致转发到后端的路径变成 /v1/... 而 404。这里用不带路径的中间件 + 手动判断，
// 保留完整的 req.url（含 /api 前缀）再代理。
app.use((req, res, next) => {
    if (req.url.startsWith('/api')) {
        console.log(`🔀 代理 ${req.method} ${req.url} -> ${BACKEND_TARGET}`);
        proxy.web(req, res, { target: BACKEND_TARGET, changeOrigin: true });
        return;
    }
    next();
});

// WebSocket 代理：/ws 升级到后端
const server = http.createServer(app);
server.on('upgrade', (req, socket, head) => {
    if (req.url && req.url.startsWith('/ws')) {
        console.log(`🔌 代理 WS ${req.url} -> ${BACKEND_TARGET}`);
        proxy.ws(req, socket, head);
    } else {
        socket.destroy();
    }
});

server.listen(port, '0.0.0.0', () => {
    console.log('');
    printConfig();
    console.log(`🌉 反向代理模式: /api 与 /ws -> ${BACKEND_TARGET}`);
    console.log(`🖥️  前端页面: http://localhost:${port}/`);
    console.log(`状态: ✅ 网关运行中`);
    console.log('═══════════════════════════════════════');
});

module.exports = app;
