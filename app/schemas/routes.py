from pydantic import BaseModel

from app.recommendation.schemas import NearbySpot


class RouteOptimizeRequest(BaseModel):
    selected_spots: list[NearbySpot]
    num_days: int = 1
    mobility_choice: str = "car"


class RouteDayResponse(BaseModel):
    spots: list[NearbySpot]
    total_distance_km: float | None = None
    total_duration_minutes: int | None = None
    segments: list[dict]


class RouteOptimizeResponse(BaseModel):
    route_by_day: dict[str, RouteDayResponse]