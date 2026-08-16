from app.external.tour_api.client import get_area_based_list, get_location_based_list
from app.external.tour_api.schemas import normalize_tour_item
from app.recommendation.mapping import THEME_TO_CAT1, THEME_TO_CONTENT_TYPE
from app.recommendation.scoring import (
    calculate_final_score,
    normalize_theme_weights,
    adjust_weights_by_activity_intensity,
)
from app.recommendation.geo import calculate_distance_km
from app.recommendation.schemas import (
    PreferenceInput,
    NearbySpot,
    AnchorSpotCandidate,
    RecommendationResult,
)


MIN_NEARBY_SPOTS = 5       # 최소 인프라 커트라인
NEARBY_RADIUS = 3000       # 주변 스팟 조회 반경(m)
NEARBY_FETCH_LIMIT = 100   # 주변 스팟 조회 시 최대 개수
TOP_N = 10                 # 최종 앵커스팟 후보 개수
MERGE_DISTANCE_KM = 5.0    # 같은 시군구일 때 병합 판단 거리(km)


def get_candidate_regions(area_code: str, theme_weights: dict, top_k: int = 3) -> list[dict]:
    """
    1단계: 상위 k개 선호 테마에 해당하는 관광지 후보(앵커스팟 후보)를 가져온다.
    테마마다 맞는 content_type_id(관광지/레포츠/음식점 등)를 사용.
    """
    sorted_themes = sorted(theme_weights.items(), key=lambda x: x[1], reverse=True)
    top_themes = [t[0] for t in sorted_themes[:top_k]]

    candidates = []
    seen_combinations = set()

    for theme in top_themes:
        cat1_list = THEME_TO_CAT1.get(theme, [])
        content_type_id = THEME_TO_CONTENT_TYPE.get(theme, "12")

        for cat1 in cat1_list:
            combo = (cat1, content_type_id)
            if combo in seen_combinations:
                continue  # 중복 호출 방지
            seen_combinations.add(combo)

            items = get_area_based_list(
                area_code=area_code,
                cat1=cat1,
                content_type_id=content_type_id,
                num_of_rows=50,
            )
            candidates.extend([normalize_tour_item(i) for i in items])

    return candidates


def apply_infra_cutoff(candidates: list[dict]) -> list[dict]:
    """
    2단계: 반경 내 연관 스팟이 너무 적은 후보를 제거하고,
    통과한 후보에는 주변 스팟 원본 리스트를 저장해둔다.
    (이 리스트가 나중에 '앵커스팟의 추천 관광지'가 됨)
    """
    filtered = []
    for spot in candidates:
        if spot["latitude"] is None or spot["longitude"] is None:
            continue

        nearby_raw = get_location_based_list(
            map_x=spot["longitude"],
            map_y=spot["latitude"],
            radius=NEARBY_RADIUS,
            num_of_rows=NEARBY_FETCH_LIMIT,
        )

        if len(nearby_raw) >= MIN_NEARBY_SPOTS:
            spot["nearby_count"] = len(nearby_raw)
            spot["nearby_spots"] = [
                normalize_tour_item(n) for n in nearby_raw
                if n.get("contentid") != spot["id"]
            ]
            filtered.append(spot)

    return filtered


def merge_nearby_duplicates(candidates: list[dict]) -> list[dict]:
    """
    3단계: 같은 시군구이면서 실제 거리도 가까운(MERGE_DISTANCE_KM 이내) 후보들 중
    점수가 가장 높은 것만 대표로 남기고 나머지는 제거.
    (예: '낙산도립공원'과 '낙산항'을 하나로 취급)
    """
    sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
    merged = []

    for spot in sorted_candidates:
        is_duplicate = False
        for kept in merged:
            same_sigungu = (
                spot.get("sigungu_code")
                and spot.get("sigungu_code") == kept.get("sigungu_code")
            )
            if same_sigungu:
                distance = calculate_distance_km(
                    spot["latitude"], spot["longitude"],
                    kept["latitude"], kept["longitude"]
                )
                if distance <= MERGE_DISTANCE_KM:
                    is_duplicate = True
                    break

        if not is_duplicate:
            merged.append(spot)

    return merged


def get_recommendations(preference: PreferenceInput) -> RecommendationResult:
    """
    ⭐ 메인 함수 (세영님이 호출하는 진입점)

    입력: PreferenceInput (취향 가중치, 지역코드, 예산, 액티비티 강도 등)
    출력: RecommendationResult
          - candidates: 여행지(앵커스팟) 후보 리스트 (상위 N개)
          - 각 후보는 자기 정보 + 그 주변 추천 관광지 리스트(nearby_spots)를 함께 가짐

    ⚠️ 랜덤 뽑기는 하지 않음 — 이 리스트를 세영님 쪽에서 DB에 저장하고
       랜덤 선택/재뽑기를 처리하는 구조.
    """
    # 1. 취향 가중치 정규화
    theme_weights = normalize_theme_weights(preference.theme_weights)

    # 2. 휴식/액티비티 선호도로 가중치 추가 보정
    theme_weights = adjust_weights_by_activity_intensity(
        theme_weights, preference.activity_intensity
    )

    # 3. 앵커스팟 후보 수집
    candidates = get_candidate_regions(preference.area_code, theme_weights)

    # 4. 인프라 컷오프 (+ 주변 관광지 리스트 확보)
    candidates = apply_infra_cutoff(candidates)

    if not candidates:
        return RecommendationResult(candidates=[])

    # 5. 스코어링
    for c in candidates:
        result = calculate_final_score(
            spot=c,
            theme_weights=theme_weights,
            budget_level=preference.budget_level,
        )
        c["score"] = result["final_score"]

    # 6. 근접 중복 제거 (같은 동네 후보 하나로 합치기)
    candidates = merge_nearby_duplicates(candidates)

    # 7. 점수 높은 순 정렬 후 상위 N개만 추리기
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = candidates[:TOP_N]

    # 8. 출력 스키마로 변환 (앵커스팟 + 주변 관광지 리스트)
    result_candidates = []
    for c in top_candidates:
        nearby_spots = [
            NearbySpot(
                content_id=n["id"],
                name=n["name"],
                address=n["address"],
                latitude=n["latitude"],
                longitude=n["longitude"],
                image_url=n.get("image_url"),
                cat1=n.get("cat1"),
            )
            for n in c.get("nearby_spots", [])
            if n["latitude"] is not None and n["longitude"] is not None
        ]

        anchor = AnchorSpotCandidate(
            content_id=c["id"],
            name=c["name"],
            address=c["address"],
            latitude=c["latitude"],
            longitude=c["longitude"],
            image_url=c.get("image_url"),
            cat1=c.get("cat1"),
            score=c["score"],
            nearby_count=c.get("nearby_count", 0),
            nearby_spots=nearby_spots,
        )
        result_candidates.append(anchor)

    return RecommendationResult(candidates=result_candidates)