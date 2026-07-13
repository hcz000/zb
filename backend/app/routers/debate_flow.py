from fastapi import APIRouter

from .. import store
from ..models import DebateFlowSaveReq, DebateFlowControlReq
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api/admin", tags=["debate-flow"])


@router.get("/debate-flow")
async def get_flow(stream_id: str | None = None):
    if not stream_id:
        return ok({sid: store.get_debate_flow(sid) for sid in store.debate_flows})
    return ok({"streamId": stream_id, "flow": store.get_debate_flow(stream_id)})


@router.post("/debate-flow")
async def save_flow(req: DebateFlowSaveReq):
    store.save_debate_flow(req.streamId, req.flow)
    data = {"streamId": req.streamId, "flow": store.get_debate_flow(req.streamId)}
    await manager.broadcast("debate-flow-updated", data)
    return ok(data, message="流程配置已保存")


@router.post("/debate-flow/control")
async def control_flow(req: DebateFlowControlReq):
    store.control_debate_flow(req.streamId, req.action, req.segmentIndex or 0)
    data = {"streamId": req.streamId, "action": req.action, "segmentIndex": req.segmentIndex or 0}
    await manager.broadcast("debate-flow-control", data)
    return ok(data, message="流程控制命令已发送")
