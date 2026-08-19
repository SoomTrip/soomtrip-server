from datetime import datetime

from pydantic import BaseModel


class SavedRegionCreateRequest(BaseModel):
    region_content_id: str
    region_name: str


class SavedRegionResponse(BaseModel):
    id: int
    user_id: int
    region_content_id: str
    region_name: str
    created_at: datetime

    class Config:
        from_attributes = True