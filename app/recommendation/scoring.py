from app.recommendation.mapping import get_theme_from_cat3


# ── 지표 1: 테마 매칭도 ──────────────────────────────

def calculate_theme_score(spot: dict, theme_weights: dict) -> float:
    """
    이 관광지가 사용자 취향과 얼마나 맞는지 (0~100).
    cat1뿐 아니라 cat3까지 활용해서 바다/숲처럼 세분화된 테마도 매칭.
    """
    spot_theme = get_theme_from_cat3(spot.get("cat1"), spot.get("cat3"))

    weight = theme_weights.get(spot_theme, 0.0)
    return round(weight * 100, 2)


# ── 지표 2: 다양성(인프라 풍부도) ──────────────────────

def calculate_diversity_score(nearby_count: int, max_reference: int = 100) -> float:
    """
    주변 스팟 개수를 0~100으로 정규화.
    max_reference개 이상이면 만점(100점), 그 이하는 비례해서 점수 부여.
    """
    if nearby_count <= 0:
        return 0.0
    normalized = min(nearby_count / max_reference, 1.0)
    return round(normalized * 100, 2)


# ── 지표 3: 혼잡도(수요강도) — 추후 API 연동 시 사용 ─────

def calculate_crowd_score(stay_intensity_val: float = None) -> float:
    """
    관광 체류 강도(1박 방문자수 관련 값)를 0~100 역점수로 변환.
    값이 낮을수록(외지인 체류 적을수록) 덜 붐비는 곳으로 보고 높은 점수 부여.

    ⚠️ 정확한 "혼잡도"는 아니고, 체류 강도를 붐빔의 근사치로 활용하는 것.
    데이터가 없으면(API 실패, 매칭 안 됨 등) 중립값(50) 반환.
    """
    if stay_intensity_val is None:
        return 50.0

    # 값의 실제 분포를 모르니, 우선 0~100 범위로 가정하고 역산
    # (실제 서비스 운영하며 관찰한 값 범위로 추후 보정 필요)
    normalized = min(max(stay_intensity_val, 0), 100)
    return round(100 - normalized, 2)


# ── 지표 4: 예산 매칭도 (단순 버전) ──────────────────────

def calculate_budget_score(spot: dict, budget_level: int) -> float:
    """
    TourAPI엔 정확한 가격 정보가 부족해서, 현재는 중립값 반환.
    """
    return 50.0


# ── 최종 스코어 계산 — 가중합 ─────────────────────────

DEFAULT_WEIGHTS = {
    "theme": 0.45,
    "diversity": 0.30,
    "crowd": 0.15,
    "budget": 0.10,
}


def calculate_final_score(
    spot: dict,
    theme_weights: dict,
    budget_level: int = 2,
    stay_intensity_val: float = None,
    score_weights: dict = None,
) -> dict:
    weights = score_weights or DEFAULT_WEIGHTS

    theme_score = calculate_theme_score(spot, theme_weights)
    diversity_score = calculate_diversity_score(spot.get("nearby_count", 0))
    crowd_score = calculate_crowd_score(stay_intensity_val)
    budget_score = calculate_budget_score(spot, budget_level)

    final_score = (
        theme_score * weights["theme"]
        + diversity_score * weights["diversity"]
        + crowd_score * weights["crowd"]
        + budget_score * weights["budget"]
    )

    return {
        "final_score": round(final_score, 2),
        "detail": {
            "theme_score": theme_score,
            "diversity_score": diversity_score,
            "crowd_score": crowd_score,
            "budget_score": budget_score,
        },
    }


# ── 취향 가중치 정규화 ─────────────────────────────

def normalize_theme_weights(raw_scores: dict) -> dict:
    """
    프론트에서 넘어온 누적 점수를 합이 1이 되는 가중치로 정규화.
    """
    total = sum(raw_scores.values())
    if total == 0:
        n = len(raw_scores)
        return {k: round(1 / n, 4) for k in raw_scores}

    return {k: round(v / total, 4) for k, v in raw_scores.items()}


def adjust_weights_by_activity_intensity(theme_weights: dict, activity_intensity: int) -> dict:
    """
    activity_intensity(1~5)에 따라 activity 테마 가중치를 보정.
    1(완전휴식)이면 activity 비중을 줄이고 healing 비중을 늘림.
    5(완전액티비티)면 반대로 activity 비중을 늘림.
    """
    adjusted = dict(theme_weights)

    # 1~5를 -1.0 ~ +1.0 스케일로 변환 (3이 중립)
    intensity_factor = (activity_intensity - 3) / 2.0  # -1.0(휴식) ~ +1.0(액티비티)

    ADJUSTMENT_STRENGTH = 0.15  # 보정 강도 (너무 세게 흔들리지 않도록)

    current_activity = adjusted.get("activity", 0.0)
    current_healing = adjusted.get("healing", 0.0)

    # activity와 healing을 서로 반대 방향으로 보정
    adjusted["activity"] = max(0.0, current_activity + intensity_factor * ADJUSTMENT_STRENGTH)
    adjusted["healing"] = max(0.0, current_healing - intensity_factor * ADJUSTMENT_STRENGTH)

    # 다시 정규화 (합이 1이 되도록)
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: round(v / total, 4) for k, v in adjusted.items()}

    return adjusted