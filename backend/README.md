# 直播辩论系统 · 后端服务（FastAPI）

基于 **FastAPI** 实现的直播辩论系统后端，使用内存 **Mock 数据** 模拟全部业务逻辑，对外提供 REST API 与 WebSocket 实时通信。网关（`live-gateway`）将 `/api/*` 与 `/ws` 转发到此服务。

> 全面支持**多直播流独立隔离**（`streamId`），评委、辩论流程、按流票数、WS 事件统一携带 `streamId`。

## 技术栈

- Python 3.10+ / FastAPI / Uvicorn
- 内存 Mock 数据（无需数据库）
- 原生 WebSocket 实时推送
- 响应统一格式：`{ success, code, data, message, timestamp }`（成功 `code=0`，失败 `code` 取 400/404/409/500）

## 目录结构

```
backend/
├── app/
│   ├── main.py            # 入口：CORS、路由挂载、/ws、健康检查、启动模拟
│   ├── config.py          # 配置（端口、微信 mock 开关）
│   ├── models.py          # Pydantic 请求模型
│   ├── responses.py       # 统一响应 ok() / fail()
│   ├── store.py           # 内存 Mock 数据 + 业务函数
│   ├── ws_manager.py      # WebSocket 连接管理 + 广播
│   ├── simulator.py       # 直播中票数/AI 内容模拟生成
│   └── routers/           # 各业务路由
│       ├── auth.py        # 微信登录(mock)、用户
│       ├── debate.py      # 辩题
│       ├── votes.py       # 投票
│       ├── ai_content.py  # AI 观点 + 评论管理
│       ├── interaction.py # 公开评论/点赞
│       ├── live.py        # 直播控制/计划
│       ├── streams.py     # 直播流管理
│       ├── ai.py          # AI 识别控制
│       ├── judges.py      # 评委配置（多流）
│       ├── debate_flow.py # 辩论流程控制（多流）
│       └── statistics.py  # 仪表盘/统计
├── requirements.txt
└── .env.example
```

## 本地运行

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # 按需修改
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

- API 根地址：`http://localhost:3000`
- 健康检查：`GET /health`
- 自动交互文档（Swagger）：`http://localhost:3000/docs`
- WebSocket：`ws://localhost:3000/ws`

## 主要接口（全部支持 `stream_id`）

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
| 后台仪表盘（含 judges/debateFlow） | GET | `/api/admin/dashboard?stream_id=` |

WebSocket 事件（`/ws`）均携带 `streamId`：`votes-updated`、`liveStatus`、`debate-updated`、`newAIContent`、`aiStatus`、`judges-updated`、`debate-flow-updated`、`debate-flow-control`、`viewers-updated` 等。

## v1 路径别名（兼容管理后台 admin-api.js）

管理后台前端（`Live/admin/admin-api.js`）统一使用 `/api/v1/admin/*` 前缀。后端通过 `app.add_api_route` 为以下接口注册了 v1 别名，**复用同一套 handler（含广播逻辑）**：

| 非 v1 路径 | v1 别名 | 说明 |
| --- | --- | --- |
| `/api/admin/dashboard` | `/api/v1/admin/dashboard` | 仪表盘 |
| `/api/admin/live/start`、`/stop` | `/api/v1/admin/live/start`、`/stop` | 直播控制 |
| `/api/admin/live/update-votes`、`/reset-votes` | `/api/v1/admin/live/update-votes`、`/reset-votes` | 票数增减/重置 |
| `/api/admin/live/viewers`、`/broadcast-viewers` | `/api/v1/admin/live/viewers`、`/broadcast-viewers` | 观看人数（新增） |
| `/api/admin/streams` | `/api/v1/admin/streams` | 直播流列表/创建 |
| `/api/admin/ai/start`、`/stop`、`/toggle` | `/api/v1/admin/ai/start`、`/stop`、`/toggle` | AI 识别控制 |
| `/api/admin/users` | `/api/v1/admin/users` | 用户列表 |
| `/api/user-vote` | `/api/v1/user-vote` | 用户投票 |
| `/api/admin/streams/{id}/debate` | `/api/v1/admin/streams/{id}/debate` | 流关联辩题（GET/PUT/DELETE，新增） |
| `/api/admin/debates` | `/api/v1/admin/debates` | 辩题集合（GET/POST，新增） |
| `/api/admin/debates/{id}` | `/api/v1/admin/debates/{id}` | 辩题详情（GET/PUT，新增） |

## 部署提示

- 常驻进程运行（Railway / Render / VPS）：直接 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
- Serverless（Vercel / Cloudflare）：需将 API 改为函数入口；注意 WebSocket 在 Serverless 不支持长连接，应降级为轮询（前端改轮询 `/api/votes`、`/api/ai-content` 即可）。
- 网关转发：将网关的 `/api/*` 与 `/ws` 指向本服务地址（默认 `http://localhost:3000`）。
