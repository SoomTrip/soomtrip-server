import random
from app.recommendation.schemas import PreferenceInput
from app.recommendation.mapping import ALL_THEMES


INDOOR_WEIGHT_RATIO = 0.3

ALL_AREA_CODES = [
    "1", "2", "3", "4", "5", "6", "7", "8",
    "31", "32", "33", "34", "35", "36", "37", "38", "39",
]


def convert_worldcup_to_preference(
    raw: dict,
    area_code: str = None,
    budget_level: int = 2,
) -> PreferenceInput:
    """
    프론트 월드컵 결과(라운드별 tag + score)를
    추천 엔진이 쓰는 PreferenceInput으로 변환한다.
    선택하지 않은 쪽 값은 0으로 유지 (여백 채우기 없음).
    """
    theme_weights = {theme: 0.0 for theme in ALL_THEMES}

    # Round 1: 바다 vs 자연 — 선택한 쪽에만 점수 부여
    round1 = raw.get("Round 1", {})
    theme_choice = round1.get("tag", {}).get("theme")
    theme_score = round1.get("score", 25)

    if theme_choice == "ocean":
        theme_weights["ocean"] += theme_score
    else:  # "nature"
        theme_weights["nature"] += theme_score

    # Round 2: 이동수단
    round2 = raw.get("Round 2", {})
    mobility = round2.get("tag", {}).get("mobility")
    transport = "CAR" if mobility == "car" else "PUBLIC_TRANSIT"

    # Round 3: 동행자 — 스코어링 미반영, AI 문구 생성용으로만 보관
    round3 = raw.get("Round 3", {})
    companion = round3.get("tag", {}).get("companion")

    # Round 4: 휴식 vs 액티비티 (0~50 점수를 1~5 강도로 환산)
    round4 = raw.get("Round 4", {})
    activity_choice = round4.get("tag", {}).get("activity")
    activity_score = round4.get("score", 25)
    ratio = activity_score / 50

    if activity_choice == "dynamic":
        activity_intensity = round(3 + ratio * 2)
    else:
        activity_intensity = round(3 - ratio * 2)
    activity_intensity = max(1, min(5, activity_intensity))

    # Round 5: 실내 vs 실외 — 선택한 쪽에만 가중치 부여
    round5 = raw.get("Round 5", {})
    indoor = round5.get("tag", {}).get("indoor", False)
    indoor_score = round5.get("score", 25)
    boost = indoor_score * INDOOR_WEIGHT_RATIO

    if indoor:
        theme_weights["urban"] += boost
    else:
        theme_weights["nature"] += boost

    final_area_code = area_code or random.choice(ALL_AREA_CODES)

    return PreferenceInput(
        theme_weights=theme_weights,
        budget_level=budget_level,
        transport=transport,
        activity_intensity=activity_intensity,
        travel_companion=companion,
        area_code=final_area_code,
    )