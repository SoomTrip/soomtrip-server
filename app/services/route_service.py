from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.schemas.routes import RouteMobilityOption

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

ROUTE_CACHE_TTL = timedelta(hours=23)


def attach_segment_info_to_spots(
    spots: list[dict],
    segments: list[dict],
    car_segments: list[dict] | None = None,
) -> list[RouteSpotResponse]:
    route_spots = []

    for index, spot in enumerate(spots):
        segment = segments[index - 1] if index > 0 and index - 1 < len(segments) else {}
        car_segment = (
            car_segments[index - 1]
            if car_segments is not None and index > 0 and index - 1 < len(car_segments)
            else None
        )

        car_alternative = None
        mobility_used = segment.get("mobility_used")
        is_fallback = mobility_used == "fallback_car"
        duration = segment.get("duration_minutes")

        segment_car_alternative = segment.get("car_alternative")

        if duration is not None and duration >= 25:
            if segment_car_alternative is not None:
                car_alternative = RouteMobilityOption(
                    mobility_choice="car",
                    distance_from_prev_km=segment_car_alternative.get("distance_km"),
                    duration_from_prev_minutes=segment_car_alternative.get("duration_minutes"),
                    is_fallback=False,
                )
            elif car_segment is not None:
                car_alternative = RouteMobilityOption(
                    mobility_choice="car",
                    distance_from_prev_km=car_segment.get("distance_km"),
                    duration_from_prev_minutes=car_segment.get("duration_minutes"),
                    is_fallback=False,
                )

        route_spots.append(
            RouteSpotResponse(
                **spot,
                distance_from_prev_km=segment.get("distance_km"),
                duration_from_prev_minutes=segment.get("duration_minutes"),
                mobility_used=mobility_used,
                is_fallback=is_fallback,
                car_alternative=car_alternative,
            )
        )

    return route_spots


def create_optimized_route(
    db: Session,
    user_id: int,
    request: RouteOptimizeRequest,
) -> RouteOptimizeResponse | None:

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

    mobility_choice = saved_region.mobility_choice or "car"

    spots_as_dict = [spot.model_dump() for spot in request.selected_spots]

    full_route = optimize_route(spots_as_dict)
    route_by_day = split_route_by_days(full_route, request.num_days)
    route_by_day = ensure_food_per_day(route_by_day)

    result = {}

    for day, spots in route_by_day.items():
        ordered_spots = interleave_food_evenly(spots)

        real_info = get_real_route_info(
            ordered_spots,
            mobility_choice=mobility_choice,
        )

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

    mobility_choice = saved_region.mobility_choice or "car"

    for entry in request.entries:
        route_entry = RouteEntry(
            saved_region_id=request.saved_region_id,
            saved_region_spot_id=entry.saved_region_spot_id,
            visit_day=entry.visit_day,
            visit_order=entry.visit_order,
            distance_from_prev_km=entry.distance_from_prev_km,
            duration_from_prev_minutes=entry.duration_from_prev_minutes,
            mobility_choice=entry.mobility_used or mobility_choice,
        )

        db.add(route_entry)
        saved_entries.append(route_entry)

        if entry.car_alternative is not None:
            car_entry = RouteEntry(
                saved_region_id=request.saved_region_id,
                saved_region_spot_id=entry.saved_region_spot_id,
                visit_day=entry.visit_day,
                visit_order=entry.visit_order,
                distance_from_prev_km=entry.car_alternative.distance_from_prev_km,
                duration_from_prev_minutes=entry.car_alternative.duration_from_prev_minutes,
                mobility_choice="car",
            )

            db.add(car_entry)
            saved_entries.append(car_entry)

    db.commit()

    for entry in saved_entries:
        db.refresh(entry)

    return saved_entries

def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def is_route_cache_expired(route_entries: list[RouteEntry]) -> bool:
    if not route_entries:
        return False

    has_missing_walk_route_data = any(
        entry.visit_order > 1
        and entry.mobility_choice == "walk_transit"
        and (
            entry.distance_from_prev_km is None
            or entry.duration_from_prev_minutes is None
        )
        for entry in route_entries
    )

    if has_missing_walk_route_data:
        return True

    created_ats = [
        normalize_datetime(entry.created_at)
        for entry in route_entries
        if entry.created_at is not None
    ]

    if not created_ats:
        return True

    oldest_created_at = min(created_ats)

    return datetime.now(timezone.utc) - oldest_created_at >= ROUTE_CACHE_TTL

def saved_region_spot_to_route_spot(spot: SavedRegionSpot) -> dict:
    return {
        "content_id": spot.content_id,
        "name": spot.name,
        "address": "",
        "latitude": spot.latitude,
        "longitude": spot.longitude,
        "image_url": None,
        "cat1": None,
        "category_label": spot.category_label,
    }

def refresh_expired_route_entries(
    db: Session,
    saved_region: SavedRegion,
    route_entries: list[RouteEntry],
) -> list[RouteEntry]:
    route_groups = {}

    for entry in route_entries:
        group_key = (
            entry.visit_day,
            entry.visit_order,
            entry.saved_region_spot_id,
        )

        if group_key not in route_groups:
            route_groups[group_key] = {
                "visit_day": entry.visit_day,
                "visit_order": entry.visit_order,
                "saved_region_spot_id": entry.saved_region_spot_id,
                "spot": entry.saved_region_spot,
            }

    ordered_groups = sorted(
        route_groups.values(),
        key=lambda item: (item["visit_day"], item["visit_order"]),
    )

    db.query(RouteEntry).filter(
        RouteEntry.saved_region_id == saved_region.id
    ).delete(synchronize_session=False)

    mobility_choice = saved_region.mobility_choice or "car"
    refreshed_entries = []

    days = sorted({group["visit_day"] for group in ordered_groups})

    for day in days:
        day_groups = [
            group
            for group in ordered_groups
            if group["visit_day"] == day
        ]

        ordered_spots = [
            saved_region_spot_to_route_spot(group["spot"])
            for group in day_groups
        ]

        real_info = get_real_route_info(
            ordered_spots,
            mobility_choice=mobility_choice,
        )

        route_spots = attach_segment_info_to_spots(
            ordered_spots,
            real_info["segments"],
        )

        for index, route_spot in enumerate(route_spots):
            group = day_groups[index]

            route_mobility_choice = (
                "fallback_car"
                if route_spot.is_fallback
                else route_spot.mobility_used or mobility_choice
            )

            route_entry = RouteEntry(
                saved_region_id=saved_region.id,
                saved_region_spot_id=group["saved_region_spot_id"],
                visit_day=group["visit_day"],
                visit_order=group["visit_order"],
                distance_from_prev_km=route_spot.distance_from_prev_km,
                duration_from_prev_minutes=route_spot.duration_from_prev_minutes,
                mobility_choice=route_mobility_choice,
            )

            db.add(route_entry)
            refreshed_entries.append(route_entry)

            if route_spot.car_alternative is not None:
                car_entry = RouteEntry(
                    saved_region_id=saved_region.id,
                    saved_region_spot_id=group["saved_region_spot_id"],
                    visit_day=group["visit_day"],
                    visit_order=group["visit_order"],
                    distance_from_prev_km=route_spot.car_alternative.distance_from_prev_km,
                    duration_from_prev_minutes=route_spot.car_alternative.duration_from_prev_minutes,
                    mobility_choice=route_spot.car_alternative.mobility_choice,
                )

                db.add(car_entry)
                refreshed_entries.append(car_entry)

    db.commit()

    for entry in refreshed_entries:
        db.refresh(entry)

    return (
        db.query(RouteEntry)
        .join(SavedRegionSpot, RouteEntry.saved_region_spot_id == SavedRegionSpot.id)
        .filter(RouteEntry.saved_region_id == saved_region.id)
        .order_by(RouteEntry.visit_day.asc(), RouteEntry.visit_order.asc())
        .all()
    )

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

    if is_route_cache_expired(route_entries):
        route_entries = refresh_expired_route_entries(
            db=db,
            saved_region=saved_region,
            route_entries=route_entries,
        )

    route_by_day = {}

    for entry in route_entries:
        spot = entry.saved_region_spot
        day_key = f"day{entry.visit_day}"

        route_by_day.setdefault(day_key, {})

        group_key = (
            entry.saved_region_spot_id,
            entry.visit_day,
            entry.visit_order,
        )

        if group_key not in route_by_day[day_key]:
            route_by_day[day_key][group_key] = {
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
                "mobility_options": [],
            }

        route_by_day[day_key][group_key]["mobility_options"].append({
            "mobility_choice": entry.mobility_choice,
            "distance_from_prev_km": entry.distance_from_prev_km,
            "duration_from_prev_minutes": entry.duration_from_prev_minutes,
            "is_fallback": entry.mobility_choice == "fallback_car",
        })

    return {
        "saved_region_id": saved_region_id,
        "route_by_day": {
            day: list(spots_by_key.values())
            for day, spots_by_key in route_by_day.items()
        },
    }

    