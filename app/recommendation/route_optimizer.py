from app.recommendation.geo import calculate_distance_km
from app.recommendation.schemas import NearbySpot, RouteRequest, RouteResponse
from app.external.map_api.naver_client import get_driving_route_info
from app.external.map_api.tmap_client import get_walking_route_info
from app.db.models import PreferenceResult, SavedRegion
from app.db.session import SessionLocal


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
    날짜별 거리 기반 분할(split_route_by_days)의 결과를 유지하되,
    식당/카페를 포함한 모든 카테고리가 날짜 간 극단적으로 몰리지 않도록
    "가장 가까운 다른 날짜"와 교환하며 완화한다.
    완전한 균등 분배가 아니라, 거리를 해치지 않는 선에서의 보정.
    """
    days = list(route_by_day.keys())
    num_days = len(days)

    if num_days <= 1:
        return route_by_day

    # 카테고리별로 날짜마다 몇 개씩 있는지 집계
    from collections import defaultdict
    category_counts_by_day = {
        day: defaultdict(int) for day in days
    }
    for day in days:
        for spot in route_by_day[day]:
            category_counts_by_day[day][spot.get("category_label", "기타")] += 1

    all_categories = set()
    for day in days:
        all_categories.update(category_counts_by_day[day].keys())

    # 각 카테고리마다, 개수가 0인 날짜가 있고 다른 날짜엔 2개 이상 있으면 하나 옮김
    for category in all_categories:
        zero_days = [d for d in days if category_counts_by_day[d][category] == 0]
        for target_day in zero_days:
            # 가장 많이 가진 날짜에서 하나를 옮겨옴 (거리상 가장 가까운 스팟을 옮기는 게 이상적이나,
            # 단순화를 위해 해당 카테고리 중 하나를 이동)
            donor_day = max(days, key=lambda d: category_counts_by_day[d][category])
            if category_counts_by_day[donor_day][category] <= 1:
                continue  # 하나뿐이면 그 날짜의 유일한 카테고리이니 옮기지 않음

            # donor_day에서 해당 카테고리 스팟 하나 찾기
            spot_to_move = next(
                (s for s in route_by_day[donor_day] if s.get("category_label") == category),
                None
            )
            if spot_to_move:
                route_by_day[donor_day].remove(spot_to_move)
                route_by_day[target_day].append(spot_to_move)
                category_counts_by_day[donor_day][category] -= 1
                category_counts_by_day[target_day][category] += 1

    return route_by_day


def interleave_food_evenly(route: list[dict]) -> list[dict]:
    """
    관광지 전체 구간에 식당과 카페를 각각 독립적으로 고르게 분산 배치한다.
    식당끼리도, 카페끼리도 연속되지 않도록 처리.
    """
    non_food = [s for s in route if s.get("category_label") not in ["식당", "카페"]]
    restaurants = [s for s in route if s.get("category_label") == "식당"]
    cafes = [s for s in route if s.get("category_label") == "카페"]

    if not restaurants and not cafes:
        return non_food

    total_length = len(route)

    def calc_positions(count: int, total: int) -> list[int]:
        """count개의 항목을 total 길이 안에 균등한 간격으로 배치할 위치 계산."""
        if count == 0:
            return []
        return [round((i + 1) * total / (count + 1)) for i in range(count)]

    # 1. 식당 위치를 전체 길이에 고르게 분산
    restaurant_positions = calc_positions(len(restaurants), total_length)

    # 2. 카페 위치도 전체 길이에 고르게 분산
    cafe_positions = calc_positions(len(cafes), total_length)

    # 3. 위치가 겹치면 조정 (카페 위치를 살짝 밀어냄)
    used_positions = set(restaurant_positions)
    adjusted_cafe_positions = []
    for pos in cafe_positions:
        while pos in used_positions and pos < total_length - 1:
            pos += 1
        used_positions.add(pos)
        adjusted_cafe_positions.append(pos)

    # 4. 결과 배열 채우기
    result = [None] * total_length
    for idx, pos in enumerate(restaurant_positions):
        pos = min(pos, total_length - 1)
        result[pos] = restaurants[idx]
    for idx, pos in enumerate(adjusted_cafe_positions):
        pos = min(pos, total_length - 1)
        if result[pos] is None:
            result[pos] = cafes[idx]
        else:
            # 혹시 자리가 이미 찼으면 다음 빈 자리 찾기
            for j in range(total_length):
                if result[j] is None:
                    result[j] = cafes[idx]
                    break

    non_food_idx = 0
    for i in range(total_length):
        if result[i] is None and non_food_idx < len(non_food):
            result[i] = non_food[non_food_idx]
            non_food_idx += 1

    result = [s for s in result if s is not None]

    # 5. 최종 안전장치: 연속된 같은 카테고리가 있으면 뒤쪽 관광지와 자리 교환
    for i in range(len(result) - 1):
        curr = result[i].get("category_label")
        next_ = result[i + 1].get("category_label")
        if curr in ["식당", "카페"] and curr == next_:
            for j in range(i + 2, len(result)):
                if result[j].get("category_label") not in ["식당", "카페"]:
                    result[i + 1], result[j] = result[j], result[i + 1]
                    break

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


def get_latest_mobility_choice(user_id: int) -> str | None:
    """
    이 유저가 지금까지 한 월드컵(취향조사) 중 가장 최근 결과의 이동수단 선호값.
    없으면 None. SavedRegion을 새로 만들 때 그 시점의 선호값을 스냅샷으로 남기는 데 쓴다.
    """
    db = SessionLocal()
    try:
        latest = (
            db.query(PreferenceResult)
            .filter(
                PreferenceResult.user_id == user_id,
                PreferenceResult.mobility_choice.isnot(None),
            )
            .order_by(PreferenceResult.created_at.desc())
            .first()
        )
    finally:
        db.close()

    return latest.mobility_choice if latest is not None else None


def resolve_mobility_choice(mobility_choice: str, saved_region_id: int | None) -> str:
    """
    앱이 요청에 실어 보낸 mobility_choice를 그대로 믿지 않고,
    saved_region_id가 있으면 그 여행지를 찜할 당시 SavedRegion에 저장해둔
    이동수단 선호값을 우선 사용한다. (앱이 값을 잘못 보내는 경우를 서버에서 보정)
    """
    if saved_region_id is None:
        return mobility_choice

    db = SessionLocal()
    try:
        saved_region = (
            db.query(SavedRegion)
            .filter(SavedRegion.id == saved_region_id)
            .first()
        )
    finally:
        db.close()

    if saved_region is None or saved_region.mobility_choice is None:
        return mobility_choice
    return saved_region.mobility_choice


def get_real_route_info(
    route: list[dict],
    mobility_choice: str = "car",
    saved_region_id: int | None = None,
) -> dict:
    """
    이동수단에 따라 적절한 API로 실제 경로 정보(거리, 시간)를 구한다.
    - 자차: 네이버 Directions API
    - 뚜벅이: 티맵 보행자 경로 API
    """
    resolved_choice = resolve_mobility_choice(mobility_choice, saved_region_id)
    if resolved_choice == "walk_transit":
        return get_walking_route_info(route)
    return get_driving_route_info(route)