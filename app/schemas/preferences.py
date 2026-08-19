from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Transport = Literal["CAR", "PUBLIC_TRANSIT"]
TravelCompanion = Literal["solo", "group"]


class PreferenceSaveRequest(BaseModel):
    nature_score: int = 0
    activity_score: int = 0
    healing_score: int = 0
    urban_score: int = 0
    ocean_score: int = 0

    budget_level: int | None = Field(default=None, ge=1, le=3)
    transport: Transport | None = None
    activity_intensity: int | None = Field(default=None, ge=1, le=5)
    travel_companion: TravelCompanion | None = None
    indoor_preference: bool | None = None


class PreferenceResponse(PreferenceSaveRequest):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True