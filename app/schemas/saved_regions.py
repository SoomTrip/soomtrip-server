from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    created_at: datetime
    spots: list[SavedRegionSpotResponse] = []

    model_config = ConfigDict(from_attributes=True)