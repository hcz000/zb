from typing import Any

from fastapi import APIRouter, Body

from .. import store
from ..models import DebateUpdateReq
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api", tags=["debate"])


@router.get("/debate-topic")
async def get_topic(stream_id: str | None = None):
    d = store.get_stream_debate(stream_id) if stream_id else None
    if d is None:
        d = store.debate_topic
    return ok({**d, "streamId": stream_id})


@router.get("/admin/debate")
async def get_debate(stream_id: str | None = None):
    d = store.get_stream_debate(stream_id) if stream_id else None
    if d is None:
        d = store.debate_topic
    return ok({**d, "streamId": stream_id})


@router.put("/admin/debate")
async def update_debate(req: DebateUpdateReq):
    if req.title is not None:
        store.debate_topic["title"] = req.title
    if req.description is not None:
        store.debate_topic["description"] = req.description
    if req.leftPosition is not None:
        store.debate_topic["leftPosition"] = req.leftPosition
    if req.rightPosition is not None:
        store.debate_topic["rightPosition"] = req.rightPosition
    await manager.broadcast(
        "debate-updated",
        {"debate": store.debate_topic, "streamId": req.streamId, "timestamp": store.now_ms()},
    )
    return ok(store.debate_topic)


@router.get("/admin/streams/{stream_id}/debate")
async def get_stream_debate_endpoint(stream_id: str):
    return ok(store.get_stream_debate(stream_id))


@router.put("/admin/streams/{stream_id}/debate")
async def associate_stream_debate_endpoint(stream_id: str, req: dict[str, Any] = Body(default={})):
    did = req.get("debate_id") or req.get("debateId")
    if not did:
        return fail("缺少 debate_id", 400)
    d = store.associate_stream_debate(stream_id, did)
    if not d:
        return fail("辩题不存在", 404)
    await manager.broadcast("debate-updated", {"debate": d, "streamId": stream_id, "timestamp": store.now_ms()})
    return ok(d)


@router.delete("/admin/streams/{stream_id}/debate")
async def delete_stream_debate_endpoint(stream_id: str):
    store.disassociate_stream_debate(stream_id)
    return ok({"streamId": stream_id, "deleted": True})


@router.get("/admin/debates")
async def list_debates_endpoint():
    return ok(store.list_debates())


@router.post("/admin/debates")
async def create_debate_endpoint(req: dict[str, Any] = Body(default={})):
    d = store.create_debate(req)
    return ok(d, message="辩题已创建")


@router.get("/admin/debates/{debate_id}")
async def get_debate_endpoint(debate_id: str):
    d = store.get_debate(debate_id)
    if not d:
        return fail("辩题不存在", 404)
    return ok(d)


@router.put("/admin/debates/{debate_id}")
async def update_debate_endpoint(debate_id: str, req: dict[str, Any] = Body(default={})):
    d = store.update_debate(debate_id, req)
    if not d:
        return fail("辩题不存在", 404)
    await manager.broadcast("debate-updated", {"debate": d, "timestamp": store.now_ms()})
    return ok(d, message="辩题已更新")
