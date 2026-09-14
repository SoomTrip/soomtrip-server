from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StampResponse(BaseModel):
    id: int
    user_id: int
    saved_region_id: int
    region_name: str
    stamp_asset_key: str
    created_at: datetime
    is_region_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)