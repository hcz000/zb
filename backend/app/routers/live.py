import time
from typing import Any

from fastapi import APIRouter, Body

from .. import store
from ..models import LiveControlReq, LiveStartReq, LiveStopReq, ScheduleReq
from ..responses import ok, fail
from ..ws_manager import manager

router = APIRouter(prefix="/api", tags=["live"])


@router.post("/live/control")
async def live_control(req: LiveControlReq):
    try:
        if req.action == "start":
            info = store.start_live(req.streamId)
            await manager.broadcast(
                "live-status-changed",
                {"status": "started", "streamId": info["streamId"], "streamUrl": info["streamUrl"], "timestamp": store.now_ms(), "startedBy": "user"},
            )
            return ok(
                {"status": "started", "streamUrl": info["streamUrl"], "streamId": info["streamId"], "streamName": info.get("streamName")},
                message="直播已开始",
            )
        else:
            info = store.stop_live(req.streamId)
            await manager.broadcast("live-status-changed", {"status": "stopped", "streamId": info.get("streamId"), "timestamp": store.now_ms()})
            return ok({"status": "stopped"}, message="直播已停止")
    except ValueError as e:
        return fail(str(e), 400)


@router.post("/admin/live/control")
async def admin_live_control(req: LiveControlReq):
    return await live_control(req)


@router.post("/admin/live/start")
async def live_start(req: LiveStartReq | None = Body(default=None)):
    try:
        info = store.start_live(req.streamId if req else None)
    except ValueError as e:
        return fail(str(e), 400)
    sid = info["streamId"]
    if req and req.autoStartAI and store.ai_status["status"] != "running":
        store.ai_status["status"] = "running"
        store.ai_status["aiSessionId"] = store.uid()
        store.ai_status["startTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        await manager.broadcast("aiStatus", {"status": "running", "streamId": sid, "aiSessionId": store.ai_status["aiSessionId"]})
    if not req or req.notifyUsers:
        await manager.broadcast(
            "liveStatus",
            {"isLive": True, "streamId": sid, "liveId": info["liveId"], "streamUrl": info["streamUrl"], "startTime": info["startTime"]},
        )
    return ok(
        {
            "liveId": info["liveId"],
            "streamUrl": info["streamUrl"],
            "status": "started",
            "streamId": sid,
            "startTime": info["startTime"],
            "notifiedUsers": len(manager.active),
        },
        message="直播已开始",
    )


@router.post("/admin/live/stop")
async def live_stop(req: LiveStopReq | None = Body(default=None)):
    info = store.stop_live(req.streamId if req else None)
    sid = info.get("streamId")
    if not req or req.notifyUsers:
        await manager.broadcast(
            "liveStatus",
            {"streamId": sid, "isLive": False, "liveId": info.get("liveId"), "stopTime": info.get("stopTime")},
        )
    return ok(
        {
            "liveId": info.get("liveId"),
            "status": "stopped",
            "streamId": sid,
            "stopTime": info.get("stopTime"),
            "duration": info.get("duration", 0),
            "summary": info.get("summary", {}),
            "notifiedUsers": len(manager.active),
        },
        message="直播已停止",
    )


@router.post("/admin/live/setup-and-start")
async def setup_start(req: dict[str, Any] = Body(default={})):
    stream_id = req.get("streamId")
    start_now = req.get("startNow")
    try:
        if start_now:
            info = store.start_live(stream_id)
            await manager.broadcast(
                "liveStatus",
                {"isLive": True, "streamId": info["streamId"], "liveId": info["liveId"], "streamUrl": info["streamUrl"], "startTime": info["startTime"]},
            )
            return ok({"isLive": True, "streamUrl": info["streamUrl"], "streamId": info["streamId"]}, message="直播已开始")
        st = req.get("scheduledStartTime")
        if not st:
            return fail("请设置直播开始时间", 400)
        if store._parse_dt(st) <= store.now_ms():
            return fail("开始时间必须晚于当前时间", 400)
        store.set_schedule(st, req.get("scheduledEndTime"), stream_id)
        return ok(store.live_schedule, message="直播计划已设置")
    except ValueError as e:
        return fail(str(e), 400)


@router.get("/admin/live/status")
async def live_status(stream_id: str | None = None):
    active = store.get_active_stream()
    status = store.live_status_dict(stream_id)
    return ok(
        {
            **status,
            "schedule": store.live_schedule,
            "streamId": status.get("streamId") or stream_id,
            "activeStreamUrl": active["url"] if active else None,
            "activeStreamId": active["id"] if active else None,
            "activeStreamName": active["name"] if active else None,
        }
    )


@router.post("/admin/live/schedule")
async def set_schedule(req: ScheduleReq):
    if not req.scheduledStartTime:
        return fail("请设置直播开始时间", 400)
    if store._parse_dt(req.scheduledStartTime) <= store.now_ms():
        return fail("开始时间必须晚于当前时间", 400)
    store.set_schedule(req.scheduledStartTime, req.scheduledEndTime, req.streamId)
    await manager.broadcast("live-schedule-updated", {"streamId": req.streamId, "schedule": store.live_schedule, "timestamp": store.now_ms()})
    return ok(store.live_schedule, message="直播计划已设置")


@router.get("/admin/live/schedule")
async def get_schedule(stream_id: str | None = None):
    return ok({**store.live_schedule, "streamId": store.live_schedule.get("streamId") or stream_id})


@router.post("/admin/live/schedule/cancel")
async def cancel_schedule(req: dict[str, Any] = Body(default={})):
    store.clear_schedule()
    await manager.broadcast("live-schedule-cancelled", {"streamId": req.get("streamId"), "timestamp": store.now_ms()})
    return ok(message="直播计划已取消")


@router.get("/admin/live/viewers")
async def get_viewers(stream_id: str | None = None):
    if stream_id:
        return ok({"streamId": stream_id, "viewers": store.get_viewers(stream_id), "timestamp": store.iso_now()})
    streams_map = {s["id"]: store.get_viewers(s["id"]) for s in store.streams}
    total = sum(streams_map.values())
    return ok({"streams": streams_map, "totalConnections": total, "timestamp": store.iso_now()})


@router.post("/admin/live/broadcast-viewers")
async def broadcast_viewers(req: dict[str, Any] = Body(default={})):
    sid = req.get("streamId")
    count = store.get_viewers(sid) if sid else 0
    data = {"streamId": sid, "viewers": count}
    await manager.broadcast("viewers-updated", data)
    return ok({**data, "message": "观看人数已广播"})
