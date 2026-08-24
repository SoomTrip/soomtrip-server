from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


EntryType = Literal["photo", "drawing"]


class DiaryEntryCreateRequest(BaseModel):
    saved_region_id: int
    message: str | None = None
    image_url: str | None = None
    entry_type: EntryType = "photo"
    visit_start_date: date
    visit_end_date: date | None = None
    is_public: bool = True


class DiaryEntryUpdateRequest(BaseModel):
    message: str | None = None
    image_url: str | None = None
    entry_type: EntryType | None = None
    visit_start_date: date | None = None
    visit_end_date: date | None = None
    is_public: bool | None = None


class DiaryEntryResponse(BaseModel):
    id: int
    saved_region_id: int
    user_id: int
    message: str | None = None
    image_url: str | None = None
    entry_type: str
    visit_start_date: date
    visit_end_date: date | None = None
    is_public: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)