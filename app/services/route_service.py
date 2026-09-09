from sqlalchemy.orm import Session

from app.db.models import RouteEntry, SavedRegion, SavedRegionSpot
from app.recommendation.route_optimizer import (
    ensure_food_per_day,
    get_real_route_info,
    interleave_food_evenly,
    optimize_route,
    split_route_by_days,
)
from app.schemas.routes import (
    RouteOptimizeRequest,
    RouteOptimizeResponse,
    RouteSpotResponse,
    RouteSaveRequest,
)


def attach_segment_info_to_spots(
    spots: list[dict],
    segments: list[dict],
) -> list[RouteSpotResponse]:
    route_spots = []

    for index, spot in enumerate(spots):
        segment = segments[index - 1] if index > 0 and index - 1 < len(segments) else {}

        route_spots.append(
            RouteSpotResponse(
                **spot,
                distance_from_prev_km=segment.get("distance_km"),
                duration_from_prev_minutes=segment.get("duration_minutes"),
            )
        )

    return route_spots


def create_optimized_route(
    request: RouteOptimizeRequest,
) -> RouteOptimizeResponse:
    spots_as_dict = [spot.model_dump() for spot in request.selected_spots]

    full_route = optimize_route(spots_as_dict)
    route_by_day = split_route_by_days(full_route, request.num_days)
    route_by_day = ensure_food_per_day(route_by_day)

    result = {}

    for day, spots in route_by_day.items():
        ordered_spots = interleave_food_evenly(spots)

        real_info = get_real_route_info(
            ordered_spots,
            mobility_choice=request.mobility_choice,
        )

        print("[Route Optimize real_info]", real_info)

        result[day] = {
            "spots": attach_segment_info_to_spots(
                ordered_spots,
                real_info["segments"],
            ),
            "total_distance_km": real_info["distance_km"],
            "total_duration_minutes": real_info["duration_minutes"],
            "segments": real_info["segments"],
        }

    return RouteOptimizeResponse(route_by_day=result)

def save_route_entries(
    db: Session,
    user_id: int,
    request: RouteSaveRequest,
) -> list[RouteEntry] | None:
    saved_region = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.id == request.saved_region_id,
            SavedRegion.user_id == user_id,
        )
        .first()
    )

    if saved_region is None:
        return None

    requested_spot_ids = {
        entry.saved_region_spot_id
        for entry in request.entries
    }

    valid_spot_count = (
        db.query(SavedRegionSpot)
        .filter(
            SavedRegionSpot.saved_region_id == request.saved_region_id,
            SavedRegionSpot.id.in_(requested_spot_ids),
        )
        .count()
    )

    if valid_spot_count != len(requested_spot_ids):
        raise ValueError("INVALID_SAVED_REGION_SPOT")

    db.query(RouteEntry).filter(
        RouteEntry.saved_region_id == request.saved_region_id,
    ).delete()

    saved_entries = []

    for entry in request.entries:
        route_entry = RouteEntry(
            saved_region_id=request.saved_region_id,
            saved_region_spot_id=entry.saved_region_spot_id,
            visit_day=entry.visit_day,
            visit_order=entry.visit_order,
            distance_from_prev_km=entry.distance_from_prev_km,
            duration_from_prev_minutes=entry.duration_from_prev_minutes,
            mobility_choice=request.mobility_choice,
        )

        db.add(route_entry)
        saved_entries.append(route_entry)

    db.commit()

    for entry in saved_entries:
        db.refresh(entry)

    return saved_entries

def get_saved_route_by_region(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> dict | None:
    saved_region = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.id == saved_region_id,
            SavedRegion.user_id == user_id,
        )
        .first()
    )

    if saved_region is None:
        return None

    route_entries = (
        db.query(RouteEntry)
        .join(SavedRegionSpot, RouteEntry.saved_region_spot_id == SavedRegionSpot.id)
        .filter(RouteEntry.saved_region_id == saved_region_id)
        .order_by(RouteEntry.visit_day.asc(), RouteEntry.visit_order.asc())
        .all()
    )

    route_by_day = {}

    for entry in route_entries:
        spot = entry.saved_region_spot
        day_key = f"day{entry.visit_day}"

        route_by_day.setdefault(day_key, []).append({
            "route_entry_id": entry.id,
            "saved_region_spot_id": entry.saved_region_spot_id,
            "visit_day": entry.visit_day,
            "visit_order": entry.visit_order,
            "content_id": spot.content_id,
            "name": spot.name,
            "category_label": spot.category_label,
            "latitude": spot.latitude,
            "longitude": spot.longitude,
            "is_anchor": spot.is_anchor,
            "distance_from_prev_km": entry.distance_from_prev_km,
            "duration_from_prev_minutes": entry.duration_from_prev_minutes,
            "mobility_choice": entry.mobility_choice,
        })

    return {
        "saved_region_id": saved_region_id,
        "route_by_day": route_by_day,
    }
