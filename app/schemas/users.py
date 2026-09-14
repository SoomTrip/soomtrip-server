from datetime import datetime

from pydantic import BaseModel


class UserMeResponse(BaseModel):
    id: int
    kakao_id: str
    nickname: str
    user_code: str
    profile_image: str | None = None
    signed_profile_image_url: str | None = None
    onboarding_completed: bool
    terms_agreed_at: datetime | None = None
    privacy_agreed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserAgreementRequest(BaseModel):
    terms_agreed: bool
    privacy_agreed: bool

class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    profile_image: str | None = None


class UserDeleteResponse(BaseModel):
    message: str