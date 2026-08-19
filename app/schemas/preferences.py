from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Transport = Literal["CAR", "PUBLIC_TRANSIT"]


class PreferenceSaveRequest(BaseModel):
    nature_score: int = 0
    activity_score: int = 0
    healing_score: int = 0
    urban_score: int = 0
    food_score: int = 0
    history_score: int = 0
    ocean_score: int = 0
    forest_score: int = 0

    budget_level: int | None = Field(default=None, ge=1, le=3)
    transport: Transport | None = None
    activity_intensity: int | None = Field(default=None, ge=1, le=5)
    departure_area_code: str | None = None

    pet_friendly: bool = False
    wellness_focus: bool = False


class PreferenceResponse(PreferenceSaveRequest):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True