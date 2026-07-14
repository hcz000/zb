import time
from urllib.parse import urlparse

from fastapi import APIRouter

from .. import store
from ..models import StreamCreate, StreamUpdate
from ..responses import ok, fail

router = APIRouter(prefix="/api/admin", tags=["streams"])


@router.get("/streams")
async def list_streams():
    result = []
    for s in store.streams:
        status = store.stream_live_statuses.get(s["id"], {"isLive": False})
        result.append(
            {
                **s,
                "playUrls": store.generate_play_urls(s),
                "liveStatus": {
                    "isLive": status.get("isLive", False),
                    "liveId": status.get("liveId"),
                    "startTime": status.get("startTime"),
                    "stopTime": status.get("stopTime"),
                    "streamUrl": status.get("streamUrl", s["url"]),
                },
            }
        )
    return ok({"streams": result, "total": len(result)})


@router.post("/streams")
async def create_stream(req: StreamCreate):
    p = urlparse(req.url)
    if not p.scheme or not p.netloc:
        return fail("流地址格式不正确，请输入有效的URL", 400)
    new = {
        "id": f"stream-{store.now_ms()}",
        "name": req.name.strip(),
        "url": req.url.strip(),
        "type": req.type,
        "description": req.description or "",
        "enabled": req.enabled,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    store.streams.append(new)
    return ok(new, message="直播流添加成功")


@router.put("/streams/{stream_id}")
async def update_stream(stream_id: str, req: StreamUpdate):
    s = store.get_stream(stream_id)
    if not s:
        return fail("直播流不存在", 404)
    if req.name is not None:
        s["name"] = req.name.strip()
    if req.url is not None:
        s["url"] = req.url.strip()
    if req.type is not None:
        s["type"] = req.type
    if req.description is not None:
        s["description"] = req.description
    if req.enabled is not None:
        s["enabled"] = req.enabled
    s["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return ok(s, message="直播流更新成功")


@router.delete("/streams/{stream_id}")
async def delete_stream(stream_id: str):
    s = store.get_stream(stream_id)
    if not s:
        return fail("直播流不存在", 404)
    if store.live_status.get("streamId") == stream_id:
        return fail("该直播流正在使用中，请先停止直播", 400)
    store.streams.remove(s)
    return ok({"id": stream_id, "name": s["name"]}, message="直播流删除成功")


@router.post("/streams/{stream_id}/toggle")
async def toggle_stream(stream_id: str):
    s = store.get_stream(stream_id)
    if not s:
        return fail("直播流不存在", 404)
    s["enabled"] = not bool(s.get("enabled", True))
    s["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return ok(s, message="直播流状态已更新")
