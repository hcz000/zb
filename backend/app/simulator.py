import asyncio
import random

from app import store
from app.ws_manager import manager

NEW_CONTENTS = [
    {"text": "正方补充：痛苦让我们珍惜快乐，没有对比就没有真正的幸福。", "side": "left"},
    {"text": "反方补充：现代医学已经在消除很多痛苦，这个按钮只是技术的延伸。", "side": "right"},
    {"text": "正方质疑：如果所有人都按这个按钮，社会会变成什么样？", "side": "left"},
    {"text": "反方回应：每个人都有自己的选择权，不应该强迫别人承受痛苦。", "side": "right"},
]


async def vote_loop():
    """直播进行中每 3 秒随机增加票数并广播。"""
    while True:
        await asyncio.sleep(3)
        if store.live_status["isLive"]:
            sid = store.live_status.get("streamId") or store._active_stream_id()
            v = store.stream_votes.setdefault(sid, {"leftVotes": 0, "rightVotes": 0})
        v["leftVotes"] += random.randint(1, 5)
        v["rightVotes"] += random.randint(1, 5)
        await manager.broadcast("votes-updated", store.votes_dict(sid))
        # 观看人数模拟增长
        store.set_viewers(sid, store.get_viewers(sid) + random.randint(0, 3))


async def ai_loop():
    """直播进行中每 15 秒新增一条 AI 观点并广播。"""
    while True:
        await asyncio.sleep(15)
        if store.live_status["isLive"]:
            item = random.choice(NEW_CONTENTS)
            sid = store.live_status.get("streamId") or store._active_stream_id()
            content = {
                "id": store.uid(),
                "debate_id": store.debate_topic["id"],
                "streamId": sid,
                "text": item["text"],
                "side": item["side"],
                "timestamp": store.now_ms(),
                "likes": random.randint(10, 30),
                "comments": [],
            }
            store.ai_contents.append(content)
            await manager.broadcast("newAIContent", content)
