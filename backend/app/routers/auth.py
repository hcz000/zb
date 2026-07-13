import time

from fastapi import APIRouter

from .. import store
from ..config import WECHAT_USE_MOCK
from ..models import WechatLoginReq
from ..responses import ok, fail

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/wechat-login")
async def wechat_login(req: WechatLoginReq):
    if WECHAT_USE_MOCK:
        openid = "mock_openid_" + str(store.now_ms())
        session_key = "mock_session_key_" + str(store.now_ms())
    else:
        # 真实模式预留：调用微信 jscode2session（此处仍降级为 mock 以保证演示可用）
        openid = "mock_openid_" + str(store.now_ms())
        session_key = "mock_session_key"

    user = req.userInfo or {}
    store.create_or_update_user(openid, user.get("nickName", "微信用户"), user.get("avatarUrl", "👤"))
    return ok(
        {
            "openid": openid,
            "session_key": session_key,
            "unionid": None,
            "userInfo": user or {"nickName": "微信用户", "avatarUrl": "👤"},
            "loginTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "isMock": WECHAT_USE_MOCK,
        }
    )


@router.get("/admin/users")
async def list_users():
    return ok(store.users)


@router.get("/admin/users/{user_id}")
async def get_user(user_id: str):
    u = next((x for x in store.users if x["id"] == user_id), None)
    if not u:
        return fail("用户不存在", 404)
    return ok(u)


@router.get("/admin/miniprogram/users")
async def mp_users(page: int = 1, pageSize: int = 20, status: str = "all", orderBy: str = "joinTime"):
    us = list(store.users)
    if orderBy == "votes":
        us.sort(key=lambda u: u.get("statistics", {}).get("totalVotes", 0), reverse=True)
    else:
        us.sort(key=lambda u: u.get("createdAt", ""), reverse=True)
    total = len(us)
    start = (page - 1) * pageSize
    end = start + pageSize
    items = [
        {
            "userId": u["id"],
            "nickname": u.get("nickname"),
            "avatar": u.get("avatar"),
            "status": "online",
            "lastActiveTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "statistics": u.get(
                "statistics",
                {"totalVotes": 0, "totalComments": 0, "totalLikes": 0, "currentPosition": "neutral"},
            ),
            "joinTime": u.get("createdAt"),
        }
        for u in us[start:end]
    ]
    return ok({"total": total, "page": page, "pageSize": pageSize, "users": items})
