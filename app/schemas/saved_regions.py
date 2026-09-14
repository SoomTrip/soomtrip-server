from datetime import datetime

from pydantic import BaseModel, ConfigDict

from typing import Literal

from app.db.models import SavedRegionShareStatus

MobilityChoice = Literal["walk_transit", "car"]


class SavedRegionSpotCreateRequest(BaseModel):
    content_id: str
    name: str
    category_label: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_anchor: bool = False


class SavedRegionCreateRequest(BaseModel):
    region_name: str
    score: int | None = None
    mobility_choice: MobilityChoice | None = None
    spots: list[SavedRegionSpotCreateRequest]


class SavedRegionSpotResponse(BaseModel):
    id: int
    content_id: str
    name: str
    category_label: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_anchor: bool

    model_config = ConfigDict(from_attributes=True)


class SavedRegionShareUserResponse(BaseModel):
    user_id: int
    nickname: str
    profile_image: str | None = None
    signed_profile_image_url: str | None = None


class SavedRegionSharedFromResponse(BaseModel):
    share_id: int
    user_id: int
    nickname: str
    profile_image: str | None = None
    signed_profile_image_url: str | None = None


class SavedRegionSharedToResponse(BaseModel):
    share_id: int
    user_id: int
    nickname: str
    profile_image: str | None = None
    signed_profile_image_url: str | None = None
    status: SavedRegionShareStatus


class SavedRegionResponse(BaseModel):
    id: int
    user_id: int
    region_name: str
    score: int | None = None
    mobility_choice: MobilityChoice | None = None
    created_at: datetime
    has_stamp: bool = False

    shared_from: SavedRegionSharedFromResponse | None = None
    shared_to: list[SavedRegionSharedToResponse] = []

    spots: list[SavedRegionSpotResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SavedRegionShareRequest(BaseModel):
    friend_user_ids: list[int]


class SavedRegionShareCreateSuccess(BaseModel):
    friend_user_id: int
    share_id: int


class SavedRegionShareFailure(BaseModel):
    friend_user_id: int
    reason: str


class SavedRegionShareCreateResponse(BaseModel):
    created: list[SavedRegionShareCreateSuccess]
    failed: list[SavedRegionShareFailure]


class SavedRegionShareListItem(BaseModel):
    share_id: int
    saved_region_id: int
    region_name: str
    status: SavedRegionShareStatus
    created_at: datetime
    responded_at: datetime | None = None

    sender_id: int
    sender_nickname: str
    sender_profile_image: str | None = None
    sender_signed_profile_image_url: str | None = None

    receiver_id: int
    receiver_nickname: str
    receiver_profile_image: str | None = None
    receiver_signed_profile_image_url: str | None = None


class SavedRegionShareAcceptResponse(BaseModel):
    share_id: int
    status: SavedRegionShareStatus
    cloned_saved_region_id: int


class SavedRegionShareRejectResponse(BaseModel):
    share_id: int
    status: SavedRegionShareStatus