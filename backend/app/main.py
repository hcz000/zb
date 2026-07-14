import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app import store
from app.config import PORT
from app.routers import auth, debate, votes, ai_content, interaction, live, streams, ai, statistics, judges, debate_flow
from app.simulator import vote_loop, ai_loop
from app.ws_manager import manager


def state_snapshot() -> dict:
    from app.routers.statistics import dashboard_data

    return {
        "votes": store.votes_dict(),
        "debate": store.debate_topic,
        "dashboard": dashboard_data(),
        "liveStatus": store.live_status["isLive"],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    t1 = asyncio.create_task(vote_loop())
    t2 = asyncio.create_task(ai_loop())
    yield
    t1.cancel()
    t2.cancel()


app = FastAPI(title="直播辩论系统后端 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ---- 管理员认证中间件 ----
# 无需认证的只读公开接口（观众观看页需要）
_PUBLIC_READONLY_PATHS = {
    "/api/admin/dashboard",
    "/api/v1/admin/dashboard",
    "/api/admin/dashboard/",
    "/api/v1/admin/dashboard/",
}
_PUBLIC_PREFIXES = (
    "/api/admin/dashboard",
    "/api/v1/admin/dashboard",
)


@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(("/api/admin", "/api/v1/admin")):
        # 放行登录接口
        if path == "/api/admin/login":
            return await call_next(request)
        # 放行 dashboard（观众观看页需要读取直播状态、流地址、票数）
        if path in _PUBLIC_READONLY_PATHS or path.startswith(_PUBLIC_PREFIXES):
            return await call_next(request)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"success": False, "detail": "未授权，请先登录"})
        token = auth_header.removeprefix("Bearer ")
        if token not in store.admin_tokens:
            return JSONResponse(status_code=401, content={"success": False, "detail": "登录已过期，请重新登录"})
    return await call_next(request)


for r in (
    auth.router,
    debate.router,
    votes.router,
    ai_content.router,
    interaction.router,
    live.router,
    streams.router,
    ai.router,
    statistics.router,
    judges.router,
    debate_flow.router,
):
    app.include_router(r)


# ---------------- /api/v1/admin/* 别名（兼容 admin-api.js 使用的前缀） ----------------
# 直接复用现有 handler，逻辑与广播行为完全统一，不重复实现。
from app.routers import statistics as _statistics, live as _live, votes as _votes
from app.routers import streams as _streams, ai as _ai, auth as _auth, debate as _debate, judges as _judges

_V1_ALIASES = [
    ("/api/v1/admin/dashboard", ["GET"], _statistics.dashboard),
    ("/api/v1/admin/live/start", ["POST"], _live.live_start),
    ("/api/v1/admin/live/stop", ["POST"], _live.live_stop),
    ("/api/v1/admin/live/update-votes", ["POST"], _votes.live_update_votes),
    ("/api/v1/admin/live/reset-votes", ["POST"], _votes.live_reset_votes),
    ("/api/v1/admin/live/viewers", ["GET"], _live.get_viewers),
    ("/api/v1/admin/live/broadcast-viewers", ["POST"], _live.broadcast_viewers),
    ("/api/v1/admin/streams", ["GET"], _streams.list_streams),
    ("/api/v1/admin/streams", ["POST"], _streams.create_stream),
    ("/api/v1/admin/ai/start", ["POST"], _ai.ai_start),
    ("/api/v1/admin/ai/stop", ["POST"], _ai.ai_stop),
    ("/api/v1/admin/ai/toggle", ["POST"], _ai.ai_toggle),
    ("/api/v1/admin/users", ["GET"], _auth.list_users),
    ("/api/v1/user-vote", ["POST"], _votes.user_vote),
    ("/api/v1/admin/streams/{stream_id}/debate", ["GET"], _debate.get_stream_debate_endpoint),
    ("/api/v1/admin/streams/{stream_id}/debate", ["PUT"], _debate.associate_stream_debate_endpoint),
    ("/api/v1/admin/streams/{stream_id}/debate", ["DELETE"], _debate.delete_stream_debate_endpoint),
    ("/api/v1/admin/debates", ["GET"], _debate.list_debates_endpoint),
    ("/api/v1/admin/debates", ["POST"], _debate.create_debate_endpoint),
    ("/api/v1/admin/debates/{debate_id}", ["GET"], _debate.get_debate_endpoint),
    ("/api/v1/admin/debates/{debate_id}", ["PUT"], _debate.update_debate_endpoint),
    ("/api/v1/admin/judges", ["GET"], _judges.get_judges),
    ("/api/v1/admin/judges", ["POST"], _judges.save_judges),
]
for _path, _methods, _ep in _V1_ALIASES:
    app.add_api_route(_path, _ep, methods=_methods, include_in_schema=False)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await manager.send(ws, {"type": "connected", "message": "已连接到实时数据服务"})
    await manager.send(ws, {"type": "state", "data": state_snapshot(), "timestamp": store.now_ms()})
    try:
        while True:
            data = await ws.receive_json()
            t = data.get("type")
            if t == "ping":
                await manager.send(ws, {"type": "pong", "timestamp": store.now_ms()})
            elif t == "control-live":
                action = data.get("action")
                sid = data.get("streamId")
                if action == "start":
                    try:
                        info = store.start_live(sid)
                        await manager.broadcast(
                            "live-status-changed",
                            {"status": "started", "streamId": info["streamId"], "streamUrl": info["streamUrl"], "timestamp": store.now_ms(), "scheduled": False},
                        )
                        await manager.broadcast(
                            "liveStatus",
                            {"isLive": True, "streamId": info["streamId"], "liveId": info["liveId"], "streamUrl": info["streamUrl"], "startTime": info["startTime"]},
                        )
                    except ValueError as e:
                        await manager.send(ws, {"type": "error", "message": str(e)})
                elif action == "stop":
                    info = store.stop_live(sid)
                    await manager.broadcast("live-status-changed", {"status": "stopped", "streamId": info.get("streamId"), "timestamp": store.now_ms()})
                    await manager.broadcast("liveStatus", {"isLive": False, "streamId": info.get("streamId"), "timestamp": store.now_ms()})
            elif t == "update-debate":
                d = data.get("debate")
                if d:
                    store.debate_topic.update(
                        {k: v for k, v in d.items() if k in ("title", "description", "leftPosition", "rightPosition")}
                    )
                    await manager.broadcast("debate-updated", {"debate": store.debate_topic, "timestamp": store.now_ms()})
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)
