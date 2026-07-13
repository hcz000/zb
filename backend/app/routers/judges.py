from fastapi import APIRouter

from .. import store
from ..models import JudgesSaveReq
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api/admin", tags=["judges"])


@router.get("/judges")
async def get_judges(stream_id: str | None = None):
    if not stream_id:
        return ok({sid: store.get_judges(sid) for sid in store.judges})
    return ok({"streamId": stream_id, "judges": store.get_judges(stream_id)})


@router.post("/judges")
async def save_judges(req: JudgesSaveReq):
    store.save_judges(req.streamId, req.judges)
    data = {"streamId": req.streamId, "judges": store.get_judges(req.streamId)}
    await manager.broadcast("judges-updated", data)
    return ok(data, message="评委配置已保存")
