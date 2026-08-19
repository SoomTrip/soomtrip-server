import random
from app.recommendation.schemas import PreferenceInput
from app.recommendation.mapping import ALL_THEMES, COASTAL_AREA_CODES, INLAND_AREA_CODES


ALL_AREA_CODES = COASTAL_AREA_CODES + INLAND_AREA_CODES


def get_area_pool(theme_weights: dict) -> list[str]:
    if not theme_weights:
        return ALL_AREA_CODES

    sorted_themes = sorted(theme_weights.items(), key=lambda x: x[1], reverse=True)
    top_theme = sorted_themes[0][0] if sorted_themes else None

    if top_theme == "ocean":
        return COASTAL_AREA_CODES

    return ALL_AREA_CODES


def convert_worldcup_to_preference(
    raw: dict,
    area_code: str = None,
    budget_level: int = 2,
) -> PreferenceInput:
    """
    프론트 월드컵 결과(15개 필드: 라운드별 양쪽 점수 + 최종 선택)를
    추천 엔진이 쓰는 PreferenceInput으로 변환한다.
    """
    theme_weights = {theme: 0.0 for theme in ALL_THEMES}

    # Round 1: 바다 vs 자연
    round1 = raw.get("Round 1", {})
    theme_choice = round1.get("tag", {}).get("theme")
    theme_score = round1.get("score", 25)

    if theme_choice == "ocean":
        theme_weights["ocean"] += theme_score
    else:
        theme_weights["nature"] += theme_score

    # Round 2: 이동수단 (스코어링엔 미반영, 그대로 전달)
    round2 = raw.get("Round 2", {})
    mobility_choice = round2.get("tag", {}).get("mobility")

    # Round 3: 동행자 (스코어링엔 미반영, AI 문구용)
    round3 = raw.get("Round 3", {})
    companion_choice = round3.get("tag", {}).get("companion")

    # Round 4: 휴식 vs 액티비티
    round4 = raw.get("Round 4", {})
    activity_choice = round4.get("tag", {}).get("activity")
    activity_score = round4.get("score", 25)
    ratio = activity_score / 50

    if activity_choice == "dynamic":
        activity_intensity = round(3 + ratio * 2)
    else:
        activity_intensity = round(3 - ratio * 2)
    activity_intensity = max(1, min(5, activity_intensity))

    # Round 5: 실내 vs 실외 (테마 벡터엔 안 섞고, 별도 필드로만 전달)
    round5 = raw.get("Round 5", {})
    indoor_choice = round5.get("tag", {}).get("indoor", False)

    final_area_code = area_code if area_code else random.choice(get_area_pool(theme_weights))

    return PreferenceInput(
        theme_weights=theme_weights,
        mobility_choice=mobility_choice,
        companion_choice=companion_choice,
        activity_intensity=activity_intensity,
        indoor_choice=indoor_choice,
        budget_level=budget_level,
        area_code=final_area_code,
    )