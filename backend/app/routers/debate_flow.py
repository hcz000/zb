from typing import Any

from fastapi import APIRouter, Body

from .. import store
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api/admin", tags=["debate-flow"])


@router.get("/debate-flow")
async def get_flow(stream_id: str | None = None):
    if not stream_id:
        return ok({sid: store.get_debate_flow(sid) for sid in store.debate_flows})
    return ok({"streamId": stream_id, "flow": store.get_debate_flow(stream_id)})


@router.post("/debate-flow")
async def save_flow(req: dict[str, Any] = Body(default={})):
    stream_id = req.get("streamId") or req.get("stream_id")
    flow = req.get("flow") or req.get("segments")
    if not stream_id:
        return fail("缺少 streamId", 400)
    if not isinstance(flow, list):
        return fail("缺少流程配置 flow", 400)
    store.save_debate_flow(stream_id, flow)
    data = {"streamId": stream_id, "flow": store.get_debate_flow(stream_id)}
    await manager.broadcast("debate-flow-updated", data)
    return ok(data, message="流程配置已保存")


@router.post("/debate-flow/control")
async def control_flow(req: dict[str, Any] = Body(default={})):
    stream_id = req.get("streamId") or req.get("stream_id")
    action = req.get("action")
    segment_index = req.get("segmentIndex", req.get("segment_index", 0)) or 0
    if not stream_id:
        return fail("缺少 streamId", 400)
    if action not in ("start", "pause", "resume", "reset", "next", "prev"):
        return fail("无效的流程控制命令", 400)
    store.control_debate_flow(stream_id, action, segment_index)
    data = {"streamId": stream_id, "action": action, "segmentIndex": segment_index}
    await manager.broadcast("debate-flow-control", data)
    return ok(data, message="流程控制命令已发送")
