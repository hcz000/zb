from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any


# ---------------- 工具 ----------------
def now_ms() -> int:
    return int(time.time() * 1000)


def uid() -> str:
    return str(uuid.uuid4())


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _parse_dt(s: Any) -> int:
    """将时间字符串/数字解析为毫秒时间戳；失败返回 0。"""
    if isinstance(s, (int, float)):
        return int(s)
    s = str(s).replace("Z", "+00:00")
    try:
        return int(datetime.fromisoformat(s).timestamp() * 1000)
    except Exception:
        try:
            return int(s)
        except Exception:
            return 0


# ---------------- 内存状态 ----------------
# 票数按直播流独立存储：stream_votes[streamId] = {"leftVotes": int, "rightVotes": int}
stream_votes: dict[str, dict[str, int]] = {}

debate_topic: dict[str, str] = {
    "id": "debate-default-001",
    "title": "如果有一个能一键消除痛苦的按钮，你会按吗？",
    "description": "这是一个关于痛苦、成长与人性选择的深度辩论",
    "leftPosition": "正方",
    "rightPosition": "反方",
}

users: list[dict[str, Any]] = [
    {
        "id": "user-demo-001",
        "nickname": "辩论达人",
        "avatar": "👥",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 128, "totalComments": 15, "totalLikes": 42, "currentPosition": "left"},
    },
    {
        "id": "user-demo-002",
        "nickname": "理性思考者",
        "avatar": "🧠",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 96, "totalComments": 22, "totalLikes": 58, "currentPosition": "right"},
    },
    {
        "id": "user-demo-003",
        "nickname": "吃瓜群众",
        "avatar": "🍉",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 34, "totalComments": 5, "totalLikes": 10, "currentPosition": "neutral"},
    },
    {
        "id": "user-demo-004",
        "nickname": "哲学少女",
        "avatar": "🎀",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 210, "totalComments": 31, "totalLikes": 89, "currentPosition": "left"},
    },
    {
        "id": "user-demo-005",
        "nickname": "逻辑狂魔",
        "avatar": "⚡",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 167, "totalComments": 18, "totalLikes": 63, "currentPosition": "right"},
    },
    {
        "id": "user-demo-006",
        "nickname": "夜猫子",
        "avatar": "🦉",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 55, "totalComments": 8, "totalLikes": 25, "currentPosition": "left"},
    },
    {
        "id": "user-demo-007",
        "nickname": "键盘侠",
        "avatar": "⌨️",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 78, "totalComments": 40, "totalLikes": 12, "currentPosition": "right"},
    },
    {
        "id": "user-demo-008",
        "nickname": "安静的美男子",
        "avatar": "🤫",
        "createdAt": iso_now(),
        "statistics": {"totalVotes": 12, "totalComments": 0, "totalLikes": 3, "currentPosition": "neutral"},
    },
]
admin_tokens: dict[str, dict[str, str]] = {}

streams: list[dict[str, Any]] = [
    {
        "id": "stream-default-001",
        "name": "测试直播流",
        "url": "rtmp://localhost/live/test",
        "type": "rtmp",
        "description": "默认测试流（mock）",
        "enabled": True,
        "createdAt": iso_now(),
        "updatedAt": iso_now(),
    }
]

# 默认给每个流建立独立票数（多流隔离）
for _s in streams:
    stream_votes[_s["id"]] = {"leftVotes": 0, "rightVotes": 0}

# 观看人数按流存储（mock 模拟）
stream_viewers: dict[str, int] = {}
for _s in streams:
    stream_viewers[_s["id"]] = 120

# 评委配置按流存储：judges[streamId] = [Judge, ...]
judges: dict[str, list[dict[str, Any]]] = {}

# 辩论流程按流存储：debate_flows[streamId] = [Segment, ...]
debate_flows: dict[str, list[dict[str, Any]]] = {}
DEFAULT_FLOW: list[dict[str, Any]] = [
    {"name": "正方发言", "duration": 180, "side": "left", "order": 1},
    {"name": "反方质问", "duration": 120, "side": "right", "order": 2},
    {"name": "反方发言", "duration": 180, "side": "right", "order": 3},
    {"name": "正方质问", "duration": 120, "side": "left", "order": 4},
    {"name": "自由辩论", "duration": 300, "side": "both", "order": 5},
    {"name": "正方总结", "duration": 120, "side": "left", "order": 6},
    {"name": "反方总结", "duration": 120, "side": "right", "order": 7},
]

# 辩题集合 + 辩题按流关联（多流）
debates: list[dict[str, Any]] = [
    {
        "id": debate_topic["id"],
        "title": debate_topic["title"],
        "description": debate_topic["description"],
        "leftPosition": debate_topic["leftPosition"],
        "rightPosition": debate_topic["rightPosition"],
        "isActive": True,
        "createdAt": iso_now(),
        "updatedAt": iso_now(),
    }
]
stream_debates: dict[str, str] = {s["id"]: debate_topic["id"] for s in streams}

live_status: dict[str, Any] = {
    "isLive": False,
    "streamUrl": None,
    "streamId": None,
    "liveId": None,
    "startTime": None,
    "isScheduled": False,
    "scheduledStartTime": None,
    "scheduledEndTime": None,
}

ai_status: dict[str, Any] = {
    "status": "stopped",
    "aiSessionId": None,
    "startTime": None,
    "settings": {"mode": "realtime", "interval": 5000, "sensitivity": "high", "minConfidence": 0.7},
    "statistics": {"totalContents": 0, "totalWords": 0, "averageConfidence": 0},
}

stream_live_statuses: dict[str, dict[str, Any]] = {}

live_schedule: dict[str, Any] = {"isScheduled": False, "scheduledStartTime": None, "scheduledEndTime": None, "streamId": None}


def _live_status_base() -> dict[str, Any]:
    return {
        "isScheduled": live_status.get("isScheduled", False),
        "scheduledStartTime": live_status.get("scheduledStartTime"),
        "scheduledEndTime": live_status.get("scheduledEndTime"),
    }


def _sync_global_live_status(preferred_stream_id: str | None = None) -> dict[str, Any]:
    preferred = None
    if preferred_stream_id:
        st = stream_live_statuses.get(preferred_stream_id)
        if st and st.get("isLive"):
            preferred = preferred_stream_id
    if not preferred and live_status.get("streamId"):
        st = stream_live_statuses.get(live_status["streamId"])
        if st and st.get("isLive"):
            preferred = live_status["streamId"]
    if not preferred:
        preferred = next((sid for sid, st in stream_live_statuses.items() if st.get("isLive")), None)

    if preferred:
        st = stream_live_statuses[preferred]
        stream = get_stream(preferred)
        live_status.update(
            isLive=True,
            streamUrl=st.get("streamUrl") or (stream["url"] if stream else None),
            streamId=preferred,
            liveId=st.get("liveId"),
            startTime=st.get("startTime"),
        )
    else:
        live_status.update(isLive=False, streamUrl=None, streamId=None, liveId=None, startTime=None)
    return live_status


def live_status_dict(stream_id: str | None = None) -> dict[str, Any]:
    if stream_id:
        st = stream_live_statuses.get(stream_id, {})
        return {
            **_live_status_base(),
            "isLive": bool(st.get("isLive", False)),
            "streamUrl": st.get("streamUrl") if st.get("isLive") else None,
            "streamId": stream_id,
            "liveId": st.get("liveId"),
            "startTime": st.get("startTime"),
            "stopTime": st.get("stopTime"),
        }
    return dict(_sync_global_live_status())


def _seed_comment(user: str, text: str, avatar: str, likes: int) -> dict[str, Any]:
    return {"id": uid(), "user": user, "text": text, "time": "刚刚", "avatar": avatar, "likes": likes}


ai_contents: list[dict[str, Any]] = [
    {
        "id": uid(),
        "debate_id": debate_topic["id"],
        "streamId": "stream-default-001",
        "text": "正方观点：痛苦是人生成长的必要经历，消除痛苦会让我们失去学习和成长的机会。",
        "side": "left",
        "timestamp": now_ms() - 300000,
        "likes": 45,
        "comments": [
            _seed_comment("心理学家", "痛苦确实能促进心理成长，但过度的痛苦也可能造成创伤", "🧠", 15),
            _seed_comment("哲学家", "尼采说过，那些杀不死我们的，会让我们更强大", "🤔", 23),
        ],
    },
    {
        "id": uid(),
        "debate_id": debate_topic["id"],
        "streamId": "stream-default-001",
        "text": "反方观点：如果能够消除痛苦，为什么不呢？痛苦本身没有价值，消除痛苦可以让人更专注于积极的事情。",
        "side": "right",
        "timestamp": now_ms() - 240000,
        "likes": 52,
        "comments": [
            _seed_comment("医生", "作为医生，我见过太多不必要的痛苦，如果能消除，我支持", "👨‍⚕️", 18),
            _seed_comment("患者家属", "看着亲人痛苦，我多么希望有这样的按钮", "💝", 31),
        ],
    },
    {
        "id": uid(),
        "debate_id": debate_topic["id"],
        "streamId": "stream-default-001",
        "text": "正方回应：痛苦让我们学会同理心，如果所有人都没有痛苦经历，我们如何理解他人的苦难？",
        "side": "left",
        "timestamp": now_ms() - 180000,
        "likes": 38,
        "comments": [
            _seed_comment("社工", "同理心确实需要痛苦的经历来培养", "🤝", 12),
            _seed_comment("作家", "很多伟大的文学作品都源于作者的痛苦经历", "📚", 19),
        ],
    },
    {
        "id": uid(),
        "debate_id": debate_topic["id"],
        "streamId": "stream-default-001",
        "text": "反方回应：我们可以通过其他方式培养同理心，比如阅读、教育。消除痛苦不等于消除所有负面情绪。",
        "side": "right",
        "timestamp": now_ms() - 120000,
        "likes": 41,
        "comments": [
            _seed_comment("教育工作者", "教育确实可以培养同理心，不一定需要亲身经历痛苦", "👩‍🏫", 16),
            _seed_comment("心理咨询师", "区分痛苦和负面情绪很重要，这个按钮可能只针对真正的痛苦", "💭", 8),
        ],
    },
    {
        "id": uid(),
        "debate_id": debate_topic["id"],
        "streamId": "stream-default-001",
        "text": "正方总结：痛苦是人性的一部分，消除痛苦可能会让我们失去作为人的完整性。",
        "side": "left",
        "timestamp": now_ms() - 60000,
        "likes": 29,
        "comments": [_seed_comment("神学家", "痛苦在宗教和哲学中都有其深层意义", "⛪", 14)],
    },
]


# ---------------- 票数相关 ----------------
def _active_stream_id() -> str | None:
    active = get_active_stream()
    if active:
        return active["id"]
    return streams[0]["id"] if streams else None


def votes_dict(stream_id: str | None = None) -> dict[str, Any]:
    sid = stream_id or _active_stream_id()
    if sid and sid in stream_votes:
        v = stream_votes[sid]
    elif sid:
        stream_votes[sid] = {"leftVotes": 0, "rightVotes": 0}
        v = stream_votes[sid]
    else:
        v = {"leftVotes": 0, "rightVotes": 0}
    total = v["leftVotes"] + v["rightVotes"]
    lp = round(v["leftVotes"] / total * 100) if total > 0 else 50
    rp = round(v["rightVotes"] / total * 100) if total > 0 else 50
    return {
        "streamId": sid,
        "leftVotes": v["leftVotes"],
        "rightVotes": v["rightVotes"],
        "totalVotes": total,
        "leftPercentage": lp,
        "rightPercentage": rp,
    }


def apply_user_vote(p: dict[str, Any], stream_id: str | None = None) -> dict[str, Any]:
    sid = stream_id or _active_stream_id()
    if sid is None:
        sid = ""
    v = stream_votes.setdefault(sid, {"leftVotes": 0, "rightVotes": 0})
    if "leftVotes" in p and "rightVotes" in p:
        lv = int(p["leftVotes"])
        rv = int(p["rightVotes"])
        if lv + rv != 100:
            raise ValueError(f"票数分配错误: 正方{lv} + 反方{rv} = {lv + rv}，必须等于100")
        if not (0 <= lv <= 100 and 0 <= rv <= 100):
            raise ValueError("参数错误: 票数必须在 0-100 之间")
        v["leftVotes"] += lv
        v["rightVotes"] += rv
        return votes_dict(sid)
    elif p.get("side") and ("votes" in p):
        side = p["side"]
        vc = int(p.get("votes") or 10)
        if side not in ("left", "right"):
            raise ValueError("参数错误: side 必须为 'left' 或 'right'")
        if not (1 <= vc <= 1000):
            raise ValueError("参数错误: 投票数量必须在 1-1000 之间")
        if side == "left":
            v["leftVotes"] += vc
        else:
            v["rightVotes"] += vc
        return votes_dict(sid)
    else:
        raise ValueError("参数错误: 请提供 { leftVotes, rightVotes } 或 { side, votes }")


def update_votes_action(stream_id: str | None, action: str, lv: int, rv: int) -> dict[str, Any]:
    sid = stream_id or _active_stream_id()
    if sid is None:
        sid = ""
    v = stream_votes.setdefault(sid, {"leftVotes": 0, "rightVotes": 0})
    if action == "set":
        v["leftVotes"] = int(lv or 0)
        v["rightVotes"] = int(rv or 0)
    elif action == "add":
        v["leftVotes"] += int(lv or 0)
        v["rightVotes"] += int(rv or 0)
    elif action == "reset":
        v["leftVotes"] = 0
        v["rightVotes"] = 0
    return votes_dict(sid)


# ---------------- 用户 ----------------
def create_or_update_user(uid_: str, nickname: str, avatar: str) -> None:
    u = next((x for x in users if x["id"] == uid_), None)
    if u:
        u["nickname"] = nickname
        u["avatar"] = avatar
    else:
        users.append(
            {
                "id": uid_,
                "nickname": nickname,
                "avatar": avatar,
                "createdAt": iso_now(),
                "statistics": {"totalVotes": 0, "totalComments": 0, "totalLikes": 0, "currentPosition": "neutral"},
            }
        )


# ---------------- 直播流 ----------------
def get_active_stream() -> dict[str, Any] | None:
    for s in streams:
        if s.get("enabled"):
            return s
    return None


def get_stream(sid: str) -> dict[str, Any] | None:
    return next((s for s in streams if s["id"] == sid), None)


def generate_play_urls(stream: dict[str, Any]) -> dict[str, Any]:
    play_urls: dict[str, Any] = {"hls": None, "flv": None, "rtmp": None}
    url = stream.get("url", "")
    try:
        from urllib.parse import urlparse

        parts = [p for p in urlparse(url).path.split("/") if p]
        stream_name = parts[-1] if parts else "stream"
    except Exception:
        stream_name = "stream"
    t = stream.get("type")
    if t == "hls":
        play_urls["hls"] = url
        if ".m3u8" in url:
            play_urls["flv"] = url.replace(".m3u8", ".flv")
    elif t == "rtmp":
        play_urls["hls"] = f"http://localhost:8086/live/{stream_name}.m3u8"
        play_urls["flv"] = f"http://localhost:8086/live/{stream_name}.flv"
        play_urls["rtmp"] = url
    elif t == "flv":
        play_urls["flv"] = url
    if not play_urls["hls"] and url:
        play_urls["hls"] = url
    return play_urls


# ---------------- 直播控制 ----------------
def start_live(stream_id: str | None = None) -> dict[str, Any]:
    stream = get_stream(stream_id) if stream_id else get_active_stream()
    if not stream:
        raise ValueError("没有可用的直播流，请先在后台配置直播流")
    if not stream.get("enabled", True):
        raise ValueError("指定的直播流未启用")
    live_id = uid()
    start = iso_now()
    live_status.update(
        isLive=True, streamUrl=stream["url"], streamId=stream["id"], liveId=live_id, startTime=start
    )
    stream_live_statuses[stream["id"]] = {
        "isLive": True,
        "liveId": live_id,
        "startTime": start,
        "stopTime": None,
        "streamUrl": stream["url"],
        "streamName": stream["name"],
    }
    _sync_global_live_status(stream["id"])
    return {
        "liveId": live_id,
        "streamUrl": stream["url"],
        "streamId": stream["id"],
        "streamName": stream["name"],
        "startTime": start,
    }


def stop_live(stream_id: str | None = None) -> dict[str, Any]:
    target = stream_id or live_status.get("streamId")
    start_time = None
    duration = 0
    live_id = None
    if target and target in stream_live_statuses and stream_live_statuses[target]["isLive"]:
        st = stream_live_statuses[target]
        start_time = st.get("startTime")
        if start_time:
            duration = max(0, int((now_ms() - _parse_dt(start_time)) / 1000))
        live_id = st.get("liveId")
        stream_live_statuses[target]["isLive"] = False
        stream_live_statuses[target]["stopTime"] = iso_now()
    elif live_status["isLive"]:
        start_time = live_status.get("startTime")
        if start_time:
            duration = max(0, int((now_ms() - _parse_dt(start_time)) / 1000))
        live_id = live_status.get("liveId")
    stop = iso_now()
    _sync_global_live_status()
    total_v = 0
    if target and target in stream_votes:
        total_v = stream_votes[target]["leftVotes"] + stream_votes[target]["rightVotes"]
    summary: dict[str, int] = {
        "totalViewers": 0,
        "peakViewers": 0,
        "totalVotes": total_v,
        "totalComments": 0,
        "totalLikes": 0,
    }
    return {"streamId": target, "liveId": live_id, "status": "stopped", "stopTime": stop, "duration": duration, "summary": summary}


def set_schedule(st: Any, et: Any, sid: str | None) -> None:
    live_schedule.update(isScheduled=True, scheduledStartTime=st, scheduledEndTime=et, streamId=sid)
    live_status["isScheduled"] = True
    live_status["scheduledStartTime"] = st
    live_status["scheduledEndTime"] = et


def clear_schedule() -> None:
    live_schedule.update(isScheduled=False, scheduledStartTime=None, scheduledEndTime=None, streamId=None)
    live_status["isScheduled"] = False
    live_status["scheduledStartTime"] = None
    live_status["scheduledEndTime"] = None


# ---------------- AI 观点 ----------------
def find_ai_content(cid: str) -> dict[str, Any] | None:
    return next((c for c in ai_contents if c["id"] == cid), None)


# ---------------- 评委 / 辩论流程（多流） ----------------
def get_judges(stream_id: str) -> list[dict[str, Any]]:
    return judges.get(stream_id, [])


def save_judges(stream_id: str, judges_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    judges[stream_id] = judges_list
    return judges_list


def get_debate_flow(stream_id: str) -> list[dict[str, Any]]:
    return debate_flows.get(stream_id, list(DEFAULT_FLOW))


def save_debate_flow(stream_id: str, flow: list[dict[str, Any]]) -> list[dict[str, Any]]:
    debate_flows[stream_id] = flow
    return flow


def control_debate_flow(stream_id: str, action: str, segment_index: int = 0) -> dict[str, Any]:
    return {"streamId": stream_id, "action": action, "segmentIndex": segment_index}


# ---------------- 观看人数（多流） ----------------
def get_viewers(stream_id: str) -> int:
    return stream_viewers.get(stream_id, 0)


def set_viewers(stream_id: str, count: int) -> int:
    stream_viewers[stream_id] = count
    return count


# ---------------- 辩题（多流） ----------------
def get_stream_debate(stream_id: str) -> dict[str, Any] | None:
    did = stream_debates.get(stream_id)
    if not did:
        return None
    return get_debate(did)


def associate_stream_debate(stream_id: str, debate_id: str) -> dict[str, Any] | None:
    stream_debates[stream_id] = debate_id
    return get_debate(debate_id)


def disassociate_stream_debate(stream_id: str) -> None:
    _ = stream_debates.pop(stream_id, None)
    return None


def list_debates() -> list[dict[str, Any]]:
    return debates


def get_debate(did: str) -> dict[str, Any] | None:
    return next((d for d in debates if d["id"] == did), None)


def create_debate(data: dict[str, Any]) -> dict[str, Any]:
    d: dict[str, Any] = {
        "id": "debate-" + uid()[:8],
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "leftPosition": data.get("leftPosition", ""),
        "rightPosition": data.get("rightPosition", ""),
        "isActive": data.get("isActive", True),
        "createdAt": iso_now(),
        "updatedAt": iso_now(),
    }
    debates.append(d)
    return d


def update_debate(did: str, data: dict[str, Any]) -> dict[str, Any] | None:
    d = get_debate(did)
    if not d:
        return None
    for k in ("title", "description", "leftPosition", "rightPosition", "isActive"):
        if k in data:
            d[k] = data[k]
    d["updatedAt"] = iso_now()
    return d
