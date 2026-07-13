import time
from typing import Any

from fastapi import APIRouter, Body

from .. import store
from ..models import UserVoteReq, UpdateVotesReq, ResetVotesReq
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api", tags=["votes"])


@router.get("/votes")
async def get_votes(stream_id: str | None = None):
    return ok(store.votes_dict(stream_id))


@router.post("/user-vote")
async def user_vote(req: dict[str, Any] = Body(default={})):
    body = dict(req)
    # 兼容小程序 { request: {...} } 包装格式
    if "request" in body and isinstance(body["request"], dict):
        body = body["request"]
    sid = body.get("streamId")
    try:
        result = store.apply_user_vote(body, sid)
    except ValueError as e:
        return fail(str(e), 400)
    payload = dict(result)
    if "leftVotes" in body and "rightVotes" in body:
        payload["userVote"] = {
            "userId": body.get("userId"),
            "leftVotes": body.get("leftVotes"),
            "rightVotes": body.get("rightVotes"),
            "mode": "100票分配制",
        }
    await manager.broadcast("votes-updated", payload)
    return ok(result, message="投票成功")


@router.get("/admin/votes")
async def admin_votes(stream_id: str | None = None):
    return ok(store.votes_dict(stream_id))


@router.put("/admin/votes")
async def admin_update_votes(req: dict[str, Any] = Body(default={})):
    sid = req.get("streamId") or store._active_stream_id()
    lv = req.get("leftVotes")
    rv = req.get("rightVotes")
    if lv is not None and not isinstance(lv, int):
        return fail("leftVotes 必须是数字", 400)
    if rv is not None and not isinstance(rv, int):
        return fail("rightVotes 必须是数字", 400)
    v = store.stream_votes.setdefault(sid, {"leftVotes": 0, "rightVotes": 0})
    if lv is not None:
        v["leftVotes"] = lv
    if rv is not None:
        v["rightVotes"] = rv
    after = store.votes_dict(sid)
    await manager.broadcast("votes-updated", after)
    return ok(after)


@router.post("/admin/votes/reset")
async def admin_reset_votes(req: dict[str, Any] = Body(default={})):
    sid = req.get("streamId") or store._active_stream_id()
    v = store.stream_votes.setdefault(sid, {"leftVotes": 0, "rightVotes": 0})
    v["leftVotes"] = 0
    v["rightVotes"] = 0
    after = store.votes_dict(sid)
    await manager.broadcast("votes-updated", after)
    return ok(message="票数已重置")


@router.post("/admin/live/update-votes")
async def live_update_votes(req: UpdateVotesReq):
    try:
        after = store.update_votes_action(req.streamId, req.action, req.leftVotes, req.rightVotes)
    except ValueError as e:
        return fail(str(e), 400)
    if req.notifyUsers:
        await manager.broadcast("votes-updated", after)
    return ok(
        {"beforeUpdate": {}, "afterUpdate": after, "updateTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        message="投票数据已更新",
    )


@router.post("/admin/live/reset-votes")
async def live_reset_votes(req: ResetVotesReq):
    sid = req.streamId or store._active_stream_id()
    v = store.stream_votes.setdefault(sid, {"leftVotes": 0, "rightVotes": 0})
    if req.resetTo:
        v["leftVotes"] = req.resetTo.get("leftVotes", 0)
        v["rightVotes"] = req.resetTo.get("rightVotes", 0)
    else:
        v["leftVotes"] = 0
        v["rightVotes"] = 0
    after = store.votes_dict(sid)
    if req.notifyUsers:
        await manager.broadcast("votes-updated", after)
    return ok({"currentVotes": after}, message="投票数据已重置")


@router.get("/admin/votes/statistics")
async def votes_statistics(timeRange: str = "1h", stream_id: str | None = None):
    v = store.votes_dict(stream_id)
    now = store.now_ms()
    timeline = []
    for i in range(10):
        ts = now - i * 60000
        timeline.insert(
            0,
            {
                "timestamp": ts,
                "leftVotes": int(v["leftVotes"] * (10 - i) / 10),
                "rightVotes": int(v["rightVotes"] * (10 - i) / 10),
                "totalVotes": int(v["totalVotes"] * (10 - i) / 10),
                "activeUsers": len(manager.active),
            },
        )
    return ok(
        {
            "summary": {
                "totalVotes": v["totalVotes"],
                "leftVotes": v["leftVotes"],
                "rightVotes": v["rightVotes"],
                "leftPercentage": v["leftPercentage"],
                "rightPercentage": v["rightPercentage"],
                "streamId": v["streamId"],
                "growthRate": 5.2,
            },
            "timeline": timeline,
            "topVoters": [],
        }
    )
