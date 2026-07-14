import time

from fastapi import APIRouter

from .. import store
from ..responses import ok
from ..ws_manager import manager

router = APIRouter(prefix="/api/admin", tags=["statistics"])


def dashboard_data(stream_id: str | None = None) -> dict:
    v = store.votes_dict(stream_id)
    sid = v["streamId"]
    active = store.get_active_stream()
    ls = store.live_status_dict(sid)
    live_duration = 0
    if ls["isLive"] and ls.get("startTime"):
        live_duration = max(0, int((store.now_ms() - store._parse_dt(ls["startTime"])) / 1000))
    return {
        "streamId": sid,
        "totalUsers": len(store.users),
        "activeUsers": len(manager.active),
        "isLive": ls["isLive"],
        "liveStreamUrl": ls["streamUrl"],
        "activeStreamUrl": active["url"] if active else None,
        "activeStreamId": active["id"] if active else None,
        "activeStreamName": active["name"] if active else None,
        "totalVotes": v["totalVotes"],
        "leftVotes": v["leftVotes"],
        "rightVotes": v["rightVotes"],
        "leftPercentage": v["leftPercentage"],
        "rightPercentage": v["rightPercentage"],
        "totalComments": 0,
        "totalLikes": 0,
        "aiStatus": store.ai_status["status"],
        "debateTopic": {
            "title": store.debate_topic["title"],
            "leftSide": store.debate_topic["leftPosition"],
            "rightSide": store.debate_topic["rightPosition"],
            "description": store.debate_topic["description"],
        },
        "liveStartTime": ls.get("startTime"),
        "liveDuration": live_duration,
        "judges": store.get_judges(sid),
        "debateFlow": {"flow": store.get_debate_flow(sid)},
    }


@router.get("/dashboard")
async def dashboard(stream_id: str | None = None):
    return ok(dashboard_data(stream_id))


@router.get("/statistics/summary")
async def summary(stream_id: str | None = None):
    if stream_id:
        total_votes = store.votes_dict(stream_id)["totalVotes"]
    else:
        total_votes = sum(sv["leftVotes"] + sv["rightVotes"] for sv in store.stream_votes.values())
    return ok(
        {
            "totalVotes": total_votes,
            "totalUsers": len(store.users),
            "totalStreams": len(store.streams),
            "totalLiveDays": 0,
        }
    )


@router.get("/statistics/daily")
async def daily(stream_id: str | None = None):
    return ok([])
