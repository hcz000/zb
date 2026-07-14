# 直播辩论实时互动系统（Live Debate）

> 基于 FastAPI 的后端服务 + Node.js 网关 + Live 前端（后台管理 Web + 微信小程序），使用 Mock 数据完整模拟直播辩论业务。

---

## 📌 基本信息

- **项目名称**：直播辩论实时互动系统
- **一句话简介**：为直播辩论场景提供实时投票、评委配置、辩论流程控制、AI 观点推送与数据大屏联动的后端服务，支持多直播流独立隔离。

---

## 🚀 演示地址

- **前端访问地址（公网可访问）**：`[请填写：部署后的后台管理 / 数据大屏地址，例如 https://xxx/]`
- **后端 API 地址**：`[请填写：例如 https://xxx/api 或 https://xxx/docs（Swagger）]`

> 部署后请将上面两处替换为真实公网链接，否则不满足"前端页面可通过公网访问"的验收要求。

---

## 🧱 技术栈说明

- **后端框架**：Python 3.10+ / FastAPI / Uvicorn
- **Mock 数据生成方案**：进程内存 Mock（`backend/app/store.py`），无需数据库；`simulator.py` 模拟直播中票数与 AI 观点的实时变化
- **实时通信**：原生 WebSocket（`/ws`）广播票数、直播状态、辩题、评委、流程等事件，所有事件携带 `streamId` 支持多流隔离
- **网关**：Node.js `live-gateway` 将 `/api/*` 与 `/ws` 反向代理到后端
- **前端**：`Live` 仓库（后台管理 `admin/` 为 Web 页面，小程序 `pages/` 为微信小程序）
- **部署平台与方式**：`[请填写：例如 Railway / Render / VPS，端口由环境变量 $PORT 指定]`

---

## 🔗 项目结构与接口说明

### 目录结构

```
zy/
├── backend/            # 你编写的后端服务（FastAPI）
│   └── app/
│       ├── main.py            # 入口：CORS、路由挂载、/ws、健康检查、启动模拟
│       ├── store.py           # 内存 Mock 数据 + 业务函数（多流隔离）
│       ├── ws_manager.py      # WebSocket 连接管理 + 广播
│       ├── simulator.py       # 票数/AI 内容模拟生成
│       └── routers/           # 各业务路由（votes/judges/debate_flow/live/...）
├── live-gateway/       # 网关：/api 与 /ws 转发到后端
├── Live/               # 前端项目（后台管理 Web + 微信小程序）
└── 需求文档.md
```

### 主要接口（全部支持 `stream_id` 多流隔离）

| 功能 | 方法 | 路径 |
| --- | --- | --- |
| 实时票数（按流） | GET | `/api/votes?stream_id=` |
| 辩题 | GET | `/api/debate-topic?stream_id=` |
| AI 观点 | GET | `/api/ai-content?stream_id=` |
| 用户投票（兼容 `request` 包装） | POST | `/api/user-vote` |
| 微信登录(mock) | POST | `/api/wechat-login` |
| 评论/点赞 | POST | `/api/comment`、`/api/like` |
| 直播控制 | POST | `/api/admin/live/start`、`/stop` |
| 直播流管理 | GET/POST/PUT/DELETE | `/api/admin/streams` |
| 评委配置 | GET/POST | `/api/admin/judges?stream_id=` |
| 辩论流程 | GET/POST | `/api/admin/debate-flow?stream_id=` |
| 流程控制命令 | POST | `/api/admin/debate-flow/control` |
| 后台仪表盘 | GET | `/api/admin/dashboard?stream_id=` |

> 管理后台前端（`Live/admin/admin-api.js`）统一使用 `/api/v1/admin/*` 前缀，后端已通过别名复用同一套 handler（详见 `backend/README.md`）。
> 完整接口契约见仓库内接口文档；WebSocket 事件：`votes-updated`、`liveStatus`、`debate-updated`、`judges-updated`、`debate-flow-updated`、`debate-flow-control`、`viewers-updated` 等。

---

## 🧠 项目开发过程笔记

### 实现思路
- 用 FastAPI 提供 REST + WebSocket；业务数据全部放在内存（`store.py`），按 `streamId` 做多直播流隔离，每个流有独立的票数、评委、流程与计时状态。
- 网关只做反向代理，把前端 `/api/*` 与 `/ws` 转发到后端，前端无需关心后端地址。

### 遇到的问题与解决方案
- **WebSocket 活跃用户数 ≠ 真实人数**：`activeUsers` 取自当前 `/ws` 连接数（`len(manager.active)`），同一用户多开标签页会重复计数；按需求用 Mock 即可，未做按用户去重。
- **网关代理不能剥离 `/api` 前缀**：Express 挂载 `/api` 会丢失前缀导致后端 404，改为手动 `proxy.web` 并保留完整 `req.url` 解决。
- **前端混用 `/api/v1/admin/*` 与非 v1 路径**：后端为非 v1 路由注册了 v1 别名，保证管理后台与数据大屏都能调通。

### 本地联调经验
- 同时启动后端（`:3000`）、网关（`:8080`）、前端；浏览器访问网关地址即可打开后台管理与数据大屏，所有 API 与 WS 经网关转发。
- 用浏览器 F12 → Network 看 `/api` 请求是否 200，可确认前后端是否真正对接。

### 部署步骤与踩坑记录
- 常驻进程（Railway / Render / VPS）：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
- Serverless（Vercel / Cloudflare）：WebSocket 不支持长连接，需降级为前端轮询 `/api/votes`、`/api/ai-content`。
- 网关的 `BACKEND_TARGET` 指向后端公网地址即可完成转发。

---

## 🧍 个人介绍

`[请填写：你的主语言、擅长方向、学习目标等，例如：主语言 Python/JavaScript，擅长 Web 后端与实时通信，希望通过本项目练习 FastAPI + WebSocket 全栈联调。]`

---

## ⚠️ 说明（Mock 范围内的取舍）

- 数据大屏票数趋势图为 Mock 历史（非真实逐条记录），符合需求"使用 Mock 数据"的要求。
- 数据大屏在后端无数据时使用内置默认流程/评委兜底展示，属前端自带行为，不影响接口对接。
