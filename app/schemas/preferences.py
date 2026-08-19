from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ThemeChoice = Literal["ocean", "nature"]
MobilityChoice = Literal["walk_transit", "car"]
CompanionChoice = Literal["solo", "group"]
ActivityChoice = Literal["rest", "dynamic"]


class PreferenceSaveRequest(BaseModel):
    ocean_score: int = 0
    nature_score: int = 0
    theme_choice: ThemeChoice | None = None

    walk_transit_score: int = 0
    car_score: int = 0
    mobility_choice: MobilityChoice | None = None

    solo_score: int = 0
    group_score: int = 0
    companion_choice: CompanionChoice | None = None

    rest_score: int = 0
    dynamic_score: int = 0
    activity_choice: ActivityChoice | None = None

    outdoor_score: int = 0
    indoor_score: int = 0
    indoor_choice: bool | None = None


class PreferenceResponse(PreferenceSaveRequest):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)