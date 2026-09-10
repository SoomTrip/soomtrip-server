from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.recommendation.schemas import NearbySpot


class RouteOptimizeRequest(BaseModel):
    saved_region_id: int
    selected_spots: list[NearbySpot]
    num_days: int = 1


class RouteMobilityOption(BaseModel):
    mobility_choice: str
    distance_from_prev_km: float | None = None
    duration_from_prev_minutes: int | None = None


class RouteSpotResponse(NearbySpot):
    distance_from_prev_km: float | None = None
    duration_from_prev_minutes: int | None = None
    car_alternative: RouteMobilityOption | None = None


class RouteDayResponse(BaseModel):
    spots: list[RouteSpotResponse]
    total_distance_km: float | None = None
    total_duration_minutes: int | None = None
    segments: list[dict]


class RouteOptimizeResponse(BaseModel):
    route_by_day: dict[str, RouteDayResponse]


class RouteEntrySaveRequest(BaseModel):
    saved_region_spot_id: int
    visit_day: int
    visit_order: int
    distance_from_prev_km: float | None = None
    duration_from_prev_minutes: int | None = None
    car_alternative: RouteMobilityOption | None = None


class RouteSaveRequest(BaseModel):
    saved_region_id: int
    entries: list[RouteEntrySaveRequest]


class RouteEntryResponse(BaseModel):
    id: int
    saved_region_id: int
    saved_region_spot_id: int
    visit_day: int
    visit_order: int
    distance_from_prev_km: float | None = None
    duration_from_prev_minutes: int | None = None
    mobility_choice: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RouteSaveResponse(BaseModel):
    saved_region_id: int
    entries: list[RouteEntryResponse]

class SavedRouteSpotResponse(BaseModel):
    route_entry_id: int | None = None
    saved_region_spot_id: int
    visit_day: int
    visit_order: int

    content_id: str
    name: str
    category_label: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_anchor: bool

    mobility_options: list[RouteMobilityOption]


class SavedRouteResponse(BaseModel):
    saved_region_id: int
    route_by_day: dict[str, list[SavedRouteSpotResponse]]