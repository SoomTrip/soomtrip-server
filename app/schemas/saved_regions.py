from datetime import datetime

from pydantic import BaseModel, ConfigDict

from typing import Literal

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


class SavedRegionResponse(BaseModel):
    id: int
    user_id: int
    region_name: str
    score: int | None = None
    mobility_choice: MobilityChoice | None = None
    created_at: datetime
    spots: list[SavedRegionSpotResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SavedRegionShareRequest(BaseModel):
    friend_user_ids: list[int]


class SavedRegionShareSuccess(BaseModel):
    friend_user_id: int
    saved_region_id: int


class SavedRegionShareFailure(BaseModel):
    friend_user_id: int
    reason: str


class SavedRegionShareResponse(BaseModel):
    shared: list[SavedRegionShareSuccess]
    failed: list[SavedRegionShareFailure]