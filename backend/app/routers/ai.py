import time
from typing import Any

from fastapi import APIRouter, Body

from .. import store
from ..models import AIStartReq, AIToggleReq
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api/admin", tags=["ai"])


def _ai_stream_id(req) -> str | None:
    sid = getattr(req, "streamId", None) if req else None
    return sid or store.live_status.get("streamId")


@router.post("/ai/start")
async def ai_start(req: AIStartReq | None = Body(default=None)):
    if store.ai_status["status"] == "running":
        return fail("AI识别已在运行中", 409)
    if req and req.settings:
        store.ai_status["settings"].update(req.settings)
    store.ai_status["status"] = "running"
    store.ai_status["aiSessionId"] = store.uid()
    store.ai_status["startTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    store.ai_status["statistics"] = {"totalContents": 0, "totalWords": 0, "averageConfidence": 0}
    if not req or req.notifyUsers:
        await manager.broadcast("aiStatus", {"status": "running", "streamId": _ai_stream_id(req), "aiSessionId": store.ai_status["aiSessionId"]})
    return ok(
        {
            "aiSessionId": store.ai_status["aiSessionId"],
            "status": "running",
            "streamId": _ai_stream_id(req),
            "startTime": store.ai_status["startTime"],
            "settings": store.ai_status["settings"],
        },
        message="AI识别已启动",
    )


@router.post("/ai/stop")
async def ai_stop(req: dict[str, Any] = Body(default={})):
    if store.ai_status["status"] == "stopped":
        return fail("AI识别未运行", 400)
    stop = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    start = store.ai_status.get("startTime")
    duration = max(0, int((store.now_ms() - store._parse_dt(start)) / 1000)) if start else 0
    sid = store.ai_status["aiSessionId"]
    summary = dict(store.ai_status["statistics"])
    store.ai_status.update(status="stopped", aiSessionId=None, startTime=None)
    if req.get("notifyUsers", True):
        await manager.broadcast("aiStatus", {"status": "stopped", "streamId": store.live_status.get("streamId"), "aiSessionId": sid})
    return ok(
        {"aiSessionId": sid, "status": "stopped", "stopTime": stop, "duration": duration, "summary": summary},
        message="AI识别已停止",
    )


@router.post("/ai/toggle")
async def ai_toggle(req: AIToggleReq):
    if req.action == "pause":
        if store.ai_status["status"] != "running":
            return fail("AI识别未运行，无法暂停", 400)
        store.ai_status["status"] = "paused"
    else:
        if store.ai_status["status"] != "paused":
            return fail("AI识别未暂停，无法恢复", 400)
        store.ai_status["status"] = "running"
    if req.notifyUsers:
        await manager.broadcast("aiStatus", {"status": store.ai_status["status"], "streamId": store.live_status.get("streamId")})
    return ok(
        {
            "aiSessionId": store.ai_status["aiSessionId"],
            "status": store.ai_status["status"],
            "actionTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        message="已暂停" if req.action == "pause" else "已恢复",
    )


@router.delete("/ai/content/{content_id}")
async def delete_ai_content(content_id: str, body: dict[str, Any] = Body(default={})):
    await manager.broadcast("aiContentDeleted", {"contentId": content_id, "streamId": None})
    return ok(
        {
            "contentId": content_id,
            "deleteTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "reason": body.get("reason", "管理员删除"),
        },
        message="内容已删除",
    )
