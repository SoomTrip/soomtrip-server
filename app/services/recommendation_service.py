import random

from sqlalchemy.orm import Session

from app.db.models import PreferenceResult
from app.recommendation.converter import get_area_pool
from app.recommendation.engine import get_recommendations
from app.recommendation.schemas import PreferenceInput, RecommendationResult
from app.services.preferences_service import get_latest_preference_result


INDOOR_WEIGHT_RATIO = 0.3


def convert_preference_result_to_input(
    preference_result: PreferenceResult,
) -> PreferenceInput:
    theme_weights = {
        "ocean": float(preference_result.ocean_score or 0),
        "nature": float(preference_result.nature_score or 0),
        "activity": float(preference_result.dynamic_score or 0),
        "healing": float(preference_result.rest_score or 0),
        "urban": 0.0,
    }

    if preference_result.indoor_choice is True:
        theme_weights["urban"] += float(preference_result.indoor_score or 0) * INDOOR_WEIGHT_RATIO

    if preference_result.indoor_choice is False:
        theme_weights["nature"] += float(preference_result.outdoor_score or 0) * INDOOR_WEIGHT_RATIO

    transport = None
    if preference_result.mobility_choice == "car":
        transport = "CAR"
    elif preference_result.mobility_choice == "walk_transit":
        transport = "PUBLIC_TRANSIT"

    activity_intensity = 3
    if preference_result.activity_choice == "dynamic":
        dynamic_score = preference_result.dynamic_score or 0
        activity_intensity = round(3 + (dynamic_score / 50) * 2)
    elif preference_result.activity_choice == "rest":
        rest_score = preference_result.rest_score or 0
        activity_intensity = round(3 - (rest_score / 50) * 2)

    activity_intensity = max(1, min(5, activity_intensity))

    area_pool = get_area_pool(theme_weights)
    area_code = random.choice(area_pool)

    return PreferenceInput(
        theme_weights=theme_weights,
        budget_level=2,
        transport=transport,
        activity_intensity=activity_intensity,
        travel_companion=preference_result.companion_choice,
        area_code=area_code,
    )


def create_recommendation_for_user(
    db: Session,
    user_id: int,
) -> RecommendationResult | None:
    preference_result = get_latest_preference_result(
        db=db,
        user_id=user_id,
    )

    if preference_result is None:
        return None

    preference_input = convert_preference_result_to_input(preference_result)

    return get_recommendations(preference_input)