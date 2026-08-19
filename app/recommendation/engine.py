import random
import concurrent.futures
from app.external.tour_api.client import get_area_based_list, get_location_based_list
from app.external.tour_api.schemas import normalize_tour_item
from app.external.demand_api.client import get_stay_intensity
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
    반경 내 연관 스팟이 너무 적은 후보를 제거.
    병렬로 API 호출해서 속도 개선.
    """
    def fetch_nearby(spot):
        if spot["latitude"] is None or spot["longitude"] is None:
            return None

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
            return spot
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_nearby, candidates)
        filtered = [r for r in results if r is not None]

    return filtered


def extract_region_name(address: str) -> str:
    """
    주소 문자열에서 "시/군 + 읍/면/동" 단위까지만 지역명을 추출.
    시/군은 접미사를 떼고("양양군"->"양양"), 구는 접미사를 유지("강서구"->"강서구").
    """
    parts = address.split()

    SKIP_SUFFIXES = ("특별시", "광역시", "특별자치시", "특별자치도", "도")

    sigungu = None
    eupmyeondong = None

    for part in parts:
        if any(part.endswith(suffix) for suffix in SKIP_SUFFIXES):
            continue

        if sigungu is None and part.endswith("구"):
            sigungu = part  # "구"는 그대로 유지 (예: "강서구")
            continue
        if sigungu is None and (part.endswith("시") or part.endswith("군")):
            sigungu = part[:-1]  # "시/군"만 떼기 (예: "양양군" -> "양양")
            continue
        if sigungu is not None and (part.endswith("읍") or part.endswith("면") or part.endswith("동")):
            eupmyeondong = part
            break

    if sigungu and eupmyeondong:
        return f"{sigungu} {eupmyeondong}"
    elif sigungu:
        return sigungu
    else:
        return parts[1] if len(parts) > 1 else address


def enrich_with_demand_score(candidates: list[dict], theme_weights: dict, budget_level: int) -> list[dict]:
    """
    각 후보에 혼잡도 API를 병렬로 조회해서 최종 점수까지 계산.
    """
    def score_one(c):
        val = get_stay_intensity(
            area_cd=c.get("stat_area_code"),
            signgu_cd=c.get("stat_sigungu_code"),
        )
        result = calculate_final_score(
            spot=c,
            theme_weights=theme_weights,
            budget_level=budget_level,
            stay_intensity_val=val,
        )
        c["score"] = result["final_score"]
        return c

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        candidates = list(executor.map(score_one, candidates))

    return candidates


def get_recommendations(preference: PreferenceInput) -> RecommendationResult:
    """
    ⭐ 메인 함수 (세영님이 호출하는 진입점)

    입력: PreferenceInput (취향 가중치, 지역코드, 예산, 액티비티 강도 등)
    출력: RecommendationResult
          - candidates: 상위 N개 중 랜덤으로 뽑힌 여행지(앵커스팟) 1개
          - 그 후보는 자기 정보 + 주변 추천 관광지 리스트(nearby_spots)를 함께 가짐

    ⭐ 랜덤 뽑기까지 이 함수 안에서 처리함. 재뽑기가 필요하면
       이 함수를 다시 호출하면 됨 (취향 계산부터 다시 하므로 결과가 새로 나옴).
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

    # 5. 스코어링 (혼잡도 실제 API 값 반영, 병렬 처리)
    candidates = enrich_with_demand_score(candidates, theme_weights, preference.budget_level)

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

    # 9. 상위 N개 중 랜덤으로 1개 최종 선택
    if not result_candidates:
        return RecommendationResult(candidates=[])

    selected = random.choice(result_candidates)
    return RecommendationResult(candidates=[selected])