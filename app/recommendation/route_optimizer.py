from app.recommendation.geo import calculate_distance_km
from app.recommendation.schemas import NearbySpot, RouteRequest, RouteResponse


FOOD_CATEGORIES = ["식당", "카페"]


def calculate_route_score(current: dict, candidate: dict, prev_category: str = None) -> float:
    """
    다음 방문지 후보의 점수를 계산.
    거리가 가까울수록, 직전 장소와 카테고리가 다를수록 높은 점수.
    """
    distance = calculate_distance_km(
        current["latitude"], current["longitude"],
        candidate["latitude"], candidate["longitude"]
    )
    distance_score = max(0, 100 - (distance / 5) * 100)
    candidate_category = candidate.get("category_label", "기타")
    diversity_bonus = 30 if candidate_category != prev_category else 0
    return distance_score + diversity_bonus


def optimize_route(selected_spots: list[dict]) -> list[dict]:
    """
    선택된 관광지들을 거리+카테고리 다양성 고려해 하나의 순서로 정렬.
    """
    if len(selected_spots) <= 1:
        return selected_spots

    remaining = selected_spots.copy()
    route = [remaining.pop(0)]

    while remaining:
        current = route[-1]
        prev_category = current.get("category_label")
        best_candidate = max(
            remaining,
            key=lambda c: calculate_route_score(current, c, prev_category)
        )
        route.append(best_candidate)
        remaining.remove(best_candidate)

    return route


def split_route_by_days(full_route: list[dict], num_days: int) -> dict[str, list[dict]]:
    """
    지리적으로 이어지는 순서로 정렬된 리스트를 일자 수만큼 균등하게 나눈다.
    """
    total = len(full_route)
    if num_days <= 0:
        num_days = 1
    if num_days > total:
        num_days = total

    per_day = total // num_days
    remainder = total % num_days

    result = {}
    idx = 0
    for day in range(1, num_days + 1):
        count = per_day + (1 if day <= remainder else 0)
        result[f"day{day}"] = full_route[idx: idx + count]
        idx += count

    return result


def ensure_food_per_day(route_by_day: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """
    각 날짜에 식당/카페가 최소 1개는 포함되도록 보정.
    다른 날짜에 식당이 2개 이상 있으면 하나를 옮겨온다.
    옮길 여분이 없으면 그대로 둔다(사용자가 애초에 식당을 충분히 선택 안 한 경우).
    """
    days_without_food = [
        day for day, spots in route_by_day.items()
        if not any(s.get("category_label") in FOOD_CATEGORIES for s in spots)
    ]

    for day_needing_food in days_without_food:
        for other_day, spots in route_by_day.items():
            if other_day == day_needing_food:
                continue
            food_spots = [s for s in spots if s.get("category_label") in FOOD_CATEGORIES]
            if len(food_spots) >= 2:
                spot_to_move = food_spots[0]
                route_by_day[other_day].remove(spot_to_move)
                route_by_day[day_needing_food].append(spot_to_move)
                break

    return route_by_day


def interleave_food_evenly(route: list[dict]) -> list[dict]:
    """
    관광지(비식당)를 먼저 순서 그대로 배치하고,
    그 사이사이에 식당/카페를 균등한 간격으로 끼워넣는다.
    예: 관광지 5개 + 식당 2개
        -> 관광지1, 관광지2, 식당1, 관광지3, 관광지4, 식당2, 관광지5
    """
    non_food = [s for s in route if s.get("category_label") not in FOOD_CATEGORIES]
    food = [s for s in route if s.get("category_label") in FOOD_CATEGORIES]

    if not food:
        return non_food
    if not non_food:
        return food

    result = []
    segment_count = len(food) + 1
    base_size = len(non_food) // segment_count
    remainder = len(non_food) % segment_count

    idx = 0
    for i in range(segment_count):
        size = base_size + (1 if i < remainder else 0)
        result.extend(non_food[idx: idx + size])
        idx += size
        if i < len(food):
            result.append(food[i])

    return result


def get_route_response(request: RouteRequest) -> RouteResponse:
    """
    ⭐ 세영님이 호출할 메인 함수.

    처리 순서:
    1) 전체 선택 장소를 거리+카테고리 다양성 고려해 하나의 순서로 정렬
    2) 여행 일수만큼 균등하게 날짜별로 분할 (지리적으로 자연스럽게 묶임)
    3) 각 날짜에 식당/카페가 최소 1개는 포함되도록 보정
    4) 각 날짜 안에서 식당/카페가 전체에 고르게 퍼지도록 재배치
       (식당끼리 연속되거나 한쪽에 몰리지 않도록)
    """
    spots_as_dict = [s.model_dump() for s in request.selected_spots]

    full_route = optimize_route(spots_as_dict)
    route_by_day_dict = split_route_by_days(full_route, request.num_days)
    route_by_day_dict = ensure_food_per_day(route_by_day_dict)

    for day in route_by_day_dict:
        route_by_day_dict[day] = interleave_food_evenly(route_by_day_dict[day])

    route_by_day = {
        day: [NearbySpot(**spot) for spot in spots]
        for day, spots in route_by_day_dict.items()
    }

    return RouteResponse(route_by_day=route_by_day)