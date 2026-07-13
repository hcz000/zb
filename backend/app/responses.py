from __future__ import annotations

import time
from typing import Any

from fastapi.responses import JSONResponse


def _ts() -> int:
    return int(time.time() * 1000)


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    """统一成功响应：{ success, code, data, message, timestamp }"""
    return {"success": True, "code": 0, "data": data, "message": message, "timestamp": _ts()}


def fail(message: str, code: int = 400) -> JSONResponse:
    """统一失败响应（HTTP 状态码与 code 一致）"""
    return JSONResponse(
        status_code=code,
        content={"success": False, "code": code, "message": message, "data": None, "timestamp": _ts()},
    )
