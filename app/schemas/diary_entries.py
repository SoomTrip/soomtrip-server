from datetime import date as Date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


Weather = Literal["sunny", "cloudy", "rainy", "snowy"]


class DiaryEntryCreateRequest(BaseModel):
    saved_region_id: int
    title: str | None = None
    message: str | None = None
    image_url: str | None = None
    weather: Weather | None = None
    date: Date
    is_public: bool = True


class DiaryEntryUpdateRequest(BaseModel):
    title: str | None = None
    message: str | None = None
    image_url: str | None = None
    weather: Weather | None = None
    date: Date | None = None
    is_public: bool | None = None


class DiaryEntryResponse(BaseModel):
    id: int
    saved_region_id: int
    user_id: int
    title: str | None = None
    message: str | None = None

    image_url: str | None = None
    signed_image_url: str | None = None

    weather: str | None = None
    date: Date
    is_public: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)