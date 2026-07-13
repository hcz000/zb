from typing import Optional, Dict, Any, Literal, List
from pydantic import BaseModel


# ---------------- 鉴权 / 用户 ----------------
class WechatLoginReq(BaseModel):
    code: str
    userInfo: Optional[Dict[str, Any]] = None
    encryptedData: Optional[str] = None
    iv: Optional[str] = None


# ---------------- 投票 ----------------
class UserVoteReq(BaseModel):
    side: Optional[Literal["left", "right"]] = None
    votes: Optional[int] = None
    leftVotes: Optional[int] = None
    rightVotes: Optional[int] = None
    userId: Optional[str] = None
    streamId: Optional[str] = None


class UpdateVotesReq(BaseModel):
    action: Literal["set", "add", "reset"]
    leftVotes: Optional[int] = None
    rightVotes: Optional[int] = None
    reason: Optional[str] = None
    notifyUsers: Optional[bool] = True
    streamId: Optional[str] = None


class ResetVotesReq(BaseModel):
    resetTo: Optional[Dict[str, int]] = None
    saveBackup: Optional[bool] = True
    notifyUsers: Optional[bool] = True
    streamId: Optional[str] = None


# ---------------- 辩题 ----------------
class DebateUpdateReq(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    leftPosition: Optional[str] = None
    rightPosition: Optional[str] = None
    streamId: Optional[str] = None


# ---------------- AI 观点 ----------------
class AIContentCreate(BaseModel):
    text: str
    side: Literal["left", "right"]
    debate_id: Optional[str] = None
    streamId: Optional[str] = None


class AIContentUpdate(BaseModel):
    text: Optional[str] = None
    side: Optional[Literal["left", "right"]] = None
    debate_id: Optional[str] = None


# ---------------- 评论 / 点赞 ----------------
class CommentReq(BaseModel):
    contentId: str
    user: Optional[str] = None
    text: str
    avatar: Optional[str] = None


class LikeReq(BaseModel):
    contentId: str
    commentId: Optional[str] = None


# ---------------- 直播流 ----------------
class StreamCreate(BaseModel):
    name: str
    url: str
    type: Literal["hls", "rtmp", "flv"]
    description: Optional[str] = ""
    enabled: Optional[bool] = True


class StreamUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[Literal["hls", "rtmp", "flv"]] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


# ---------------- 直播控制 ----------------
class LiveControlReq(BaseModel):
    action: Literal["start", "stop"]
    streamId: Optional[str] = None


class LiveStartReq(BaseModel):
    streamId: Optional[str] = None
    autoStartAI: Optional[bool] = False
    notifyUsers: Optional[bool] = True


class LiveStopReq(BaseModel):
    streamId: Optional[str] = None
    saveStatistics: Optional[bool] = True
    notifyUsers: Optional[bool] = True


class ScheduleReq(BaseModel):
    scheduledStartTime: str
    scheduledEndTime: Optional[str] = None
    streamId: Optional[str] = None


# ---------------- AI 识别控制 ----------------
class AIStartReq(BaseModel):
    settings: Optional[Dict[str, Any]] = None
    notifyUsers: Optional[bool] = True
    streamId: Optional[str] = None


class AIToggleReq(BaseModel):
    action: Literal["pause", "resume"]
    notifyUsers: Optional[bool] = True


# ---------------- 评委（多流） ----------------
class JudgeItem(BaseModel):
    id: Optional[str] = None
    name: str
    role: Optional[str] = ""
    avatar: Optional[str] = None
    leftVotes: int = 0
    rightVotes: int = 0


class JudgesSaveReq(BaseModel):
    streamId: str
    judges: List[Dict[str, Any]]


# ---------------- 辩论流程（多流） ----------------
class DebateSegment(BaseModel):
    name: str
    duration: int
    side: Literal["left", "right", "both"]
    order: int


class DebateFlowSaveReq(BaseModel):
    streamId: str
    flow: List[Dict[str, Any]]


class DebateFlowControlReq(BaseModel):
    streamId: str
    action: Literal["start", "pause", "resume", "reset", "next", "prev"]
    segmentIndex: Optional[int] = 0
