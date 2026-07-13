from fastapi import APIRouter, Body
from typing import Any

from .. import store
from ..models import CommentReq, LikeReq
from ..responses import ok, fail

router = APIRouter(prefix="/api", tags=["interaction"])


@router.post("/comment")
async def add_comment(req: CommentReq):
    c = store.find_ai_content(req.contentId)
    if not c:
        return fail("内容不存在", 404)
    new = {
        "id": store.uid(),
        "user": req.user or "匿名用户",
        "text": req.text.strip(),
        "time": "刚刚",
        "avatar": req.avatar or "👤",
        "likes": 0,
    }
    c.setdefault("comments", []).append(new)
    return ok(new)


@router.delete("/comment/{comment_id}")
async def delete_comment(comment_id: str, body: dict[str, Any] = Body(default={})):
    cid = body.get("contentId")
    if not cid:
        return fail("缺少必要参数: contentId", 400)
    c = store.find_ai_content(cid)
    if not c:
        return fail("内容不存在", 404)
    comments = c.get("comments", [])
    idx = next((i for i, cm in enumerate(comments) if str(cm.get("id")) == str(comment_id)), -1)
    if idx == -1:
        return fail("评论不存在", 404)
    deleted = comments.pop(idx)
    return ok({"message": "评论删除成功", "deletedComment": deleted})


@router.post("/like")
async def like(req: LikeReq):
    c = store.find_ai_content(req.contentId)
    if not c:
        return fail("内容不存在", 404)
    if req.commentId is not None:
        cm = next((x for x in c.get("comments", []) if str(x.get("id")) == str(req.commentId)), None)
        if not cm:
            return fail("评论不存在", 404)
        cm["likes"] = cm.get("likes", 0) + 1
        return ok({"likes": cm["likes"]})
    c["likes"] = c.get("likes", 0) + 1
    return ok({"likes": c["likes"]})
