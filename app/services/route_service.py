from app.recommendation.route_optimizer import (
    ensure_food_per_day,
    get_real_route_info,
    interleave_food_evenly,
    optimize_route,
    split_route_by_days,
)
from app.schemas.routes import RouteOptimizeRequest, RouteOptimizeResponse


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

        result[day] = {
            "spots": ordered_spots,
            "total_distance_km": real_info["distance_km"],
            "total_duration_minutes": real_info["duration_minutes"],
            "segments": real_info["segments"],
        }

    return RouteOptimizeResponse(route_by_day=result)