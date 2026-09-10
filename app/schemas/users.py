from datetime import datetime

from pydantic import BaseModel


class UserMeResponse(BaseModel):
    id: int
    kakao_id: str
    nickname: str
    user_code: str
    profile_image: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    profile_image: str | None = None


class UserDeleteResponse(BaseModel):
    message: str