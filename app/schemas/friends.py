from datetime import datetime

from pydantic import BaseModel

from app.db.models import FriendStatus


class FriendRequestCreate(BaseModel):
    user_code: str


class FriendUserResponse(BaseModel):
    id: int
    nickname: str
    user_code: str
    profile_image: str | None = None

    class Config:
        from_attributes = True


class FriendResponse(BaseModel):
    id: int
    requester_id: int
    receiver_id: int
    status: FriendStatus
    created_at: datetime
    accepted_at: datetime | None = None

    requester: FriendUserResponse
    receiver: FriendUserResponse

    class Config:
        from_attributes = True