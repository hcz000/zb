import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body

from .. import store
from ..models import AIContentCreate, AIContentUpdate
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api", tags=["ai-content"])


def _parse(s):
    if s is None:
        return 0
    try:
        return int(s)
    except Exception:
        try:
            return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            return 0


def _cts(cm):
    t = cm.get("timestamp") or cm.get("time")
    if isinstance(t, (int, float)):
        return t
    return int(time.time() * 1000)


def _content_to_doc(item: dict) -> dict:
    comment_count = len(item.get("comments", [])) if isinstance(item.get("comments"), list) else 0
    ts = item.get("timestamp")
    ts_iso = (
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts / 1000))
        if isinstance(ts, (int, float))
        else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    return {
        "id": item["id"],
        "content": item.get("text", ""),
        "type": "summary",
        "timestamp": ts_iso,
        "position": item.get("side", "left"),
        "confidence": 0.95,
        "statistics": {"views": item.get("views", 0), "likes": item.get("likes", 0), "comments": comment_count},
    }


@router.get("/ai-content")
async def list_ai(stream_id: str | None = None):
    items = store.ai_contents
    if stream_id:
        items = [c for c in items if c.get("streamId") == stream_id]
    return ok(items)


@router.get("/admin/ai-content")
async def admin_list_ai(stream_id: str | None = None):
    items = store.ai_contents
    if stream_id:
        items = [c for c in items if c.get("streamId") == stream_id]
    return ok(items)


@router.get("/admin/ai-content/list")
async def admin_ai_list(page: int = 1, pageSize: int = 20, startTime: str | None = None, endTime: str | None = None):
    items = list(store.ai_contents)
    if startTime:
        items = [i for i in items if (i.get("timestamp") or 0) >= _parse(startTime)]
    if endTime:
        items = [i for i in items if (i.get("timestamp") or 0) <= _parse(endTime)]
    total = len(items)
    start = (page - 1) * pageSize
    end = start + pageSize
    return ok({"total": total, "page": page, "pageSize": pageSize, "items": items[start:end]})


@router.get("/v1/admin/ai-content/list")
async def v1_admin_ai_list(page: int = 1, pageSize: int = 20, startTime: str | None = None, endTime: str | None = None):
    if pageSize > 100:
        return fail("pageSize最大值为100", 400)
    items = list(store.ai_contents)
    if startTime:
        items = [i for i in items if (i.get("timestamp") or 0) >= _parse(startTime)]
    if endTime:
        items = [i for i in items if (i.get("timestamp") or 0) <= _parse(endTime)]
    total = len(items)
    start = (page - 1) * pageSize
    end = start + pageSize
    return ok({"total": total, "page": page, "items": [_content_to_doc(i) for i in items[start:end]]})


@router.get("/admin/ai-content/{content_id}")
async def get_ai(content_id: str):
    c = store.find_ai_content(content_id)
    if not c:
        return fail("内容不存在", 404)
    return ok(c)


@router.get("/admin/ai-content/{content_id}/comments")
async def get_comments(content_id: str, page: int = 1, pageSize: int = 20):
    c = store.find_ai_content(content_id)
    if not c:
        return fail("AI内容不存在", 404)
    comments = c.get("comments", [])
    total = len(comments)
    start = (page - 1) * pageSize
    end = start + pageSize
    return ok(
        {
            "contentId": content_id,
            "contentText": c.get("text", ""),
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "comments": comments[start:end],
        }
    )


@router.get("/v1/admin/ai-content/{content_id}/comments")
async def v1_get_comments(content_id: str, page: int = 1, pageSize: int = 20):
    if pageSize > 100:
        return fail("pageSize最大值为100", 400)
    c = store.find_ai_content(content_id)
    if not c:
        return fail("AI内容不存在", 404)
    comments = sorted(c.get("comments", []), key=_cts, reverse=True)
    total = len(comments)
    start = (page - 1) * pageSize
    end = start + pageSize
    fmt = [
        {
            "commentId": cm.get("id"),
            "userId": "anonymous",
            "nickname": cm.get("user", "匿名用户"),
            "avatar": cm.get("avatar", "👤"),
            "content": cm.get("text", ""),
            "likes": cm.get("likes", 0),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_cts(cm) / 1000)),
        }
        for cm in comments[start:end]
    ]
    return ok(
        {
            "contentId": content_id,
            "contentText": c.get("text", ""),
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "comments": fmt,
        }
    )


@router.delete("/admin/ai-content/{content_id}/comments/{comment_id}")
async def del_comment(content_id: str, comment_id: str, body: dict[str, Any] = Body(default={})):
    c = store.find_ai_content(content_id)
    if not c:
        return fail("AI内容不存在", 404)
    comments = c.get("comments", [])
    idx = next((i for i, cm in enumerate(comments) if str(cm.get("id")) == str(comment_id)), -1)
    if idx == -1:
        return fail("评论不存在", 404)
    comments.pop(idx)
    if isinstance(c.get("statistics"), dict):
        c["statistics"]["comments"] = len(comments)
    return ok({"contentId": content_id, "commentId": comment_id, "deleted": True}, message="评论已删除")


@router.delete("/v1/admin/ai-content/{content_id}/comments/{comment_id}")
async def v1_del_comment(content_id: str, comment_id: str, body: dict[str, Any] = Body(default={})):
    c = store.find_ai_content(content_id)
    if not c:
        return fail("AI内容不存在", 404)
    comments = c.get("comments", [])
    idx = next((i for i, cm in enumerate(comments) if str(cm.get("id")) == str(comment_id)), -1)
    if idx == -1:
        return fail(f"评论ID {comment_id} 不存在", 404)
    comments.pop(idx)
    if isinstance(c.get("statistics"), dict):
        c["statistics"]["comments"] = len(comments)
    await manager.broadcast("comment-deleted", {"contentId": content_id, "commentId": comment_id, "streamId": None, "timestamp": store.now_ms()})
    return ok({"commentId": comment_id, "contentId": content_id, "deleteTime": None}, message="评论已删除")


@router.post("/admin/ai-content")
async def create_ai(req: AIContentCreate):
    content = {
        "id": store.uid(),
        "debate_id": req.debate_id or store.debate_topic["id"],
        "streamId": req.streamId,
        "text": req.text.strip(),
        "side": req.side,
        "timestamp": store.now_ms(),
        "comments": [],
        "likes": 0,
    }
    store.ai_contents.append(content)
    await manager.broadcast("newAIContent", {**content, "streamId": req.streamId, "updatedBy": "admin"})
    return ok(content)


@router.put("/admin/ai-content/{content_id}")
async def update_ai(content_id: str, req: AIContentUpdate):
    c = store.find_ai_content(content_id)
    if not c:
        return fail("内容不存在", 404)
    if req.text is not None:
        c["text"] = req.text.strip()
    if req.side is not None:
        c["side"] = req.side
    if req.debate_id is not None:
        c["debate_id"] = req.debate_id
    await manager.broadcast("ai-content-updated", {"content": c, "updatedBy": "admin"})
    return ok(c)


@router.delete("/admin/ai-content/{content_id}")
async def delete_ai(content_id: str):
    c = store.find_ai_content(content_id)
    if not c:
        return fail("内容不存在", 404)
    store.ai_contents.remove(c)
    await manager.broadcast("aiContentDeleted", {"contentId": content_id, "streamId": c.get("streamId"), "updatedBy": "admin"})
    return ok({"contentId": content_id, "deleted": True}, message="删除成功")

