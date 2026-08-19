import random

from sqlalchemy.orm import Session

from app.db.models import PreferenceResult
from app.recommendation.converter import get_area_pool
from app.recommendation.engine import get_recommendations
from app.recommendation.schemas import PreferenceInput, RecommendationResult


def get_latest_preference_result(
    db: Session,
    user_id: int,
) -> PreferenceResult | None:
    return (
        db.query(PreferenceResult)
        .filter(PreferenceResult.user_id == user_id)
        .order_by(PreferenceResult.created_at.desc())
        .first()
    )


def convert_preference_result_to_input(
    preference_result: PreferenceResult,
) -> PreferenceInput:
    theme_weights = {
        "nature": float(preference_result.nature_score or 0),
        "activity": float(preference_result.activity_score or 0),
        "healing": float(preference_result.healing_score or 0),
        "urban": float(preference_result.urban_score or 0),
        "ocean": float(preference_result.ocean_score or 0),
    }

    area_pool = get_area_pool(theme_weights)
    area_code = random.choice(area_pool)

    return PreferenceInput(
        theme_weights=theme_weights,
        budget_level=preference_result.budget_level or 2,
        transport=preference_result.transport,
        activity_intensity=preference_result.activity_intensity or 3,
        travel_companion=preference_result.travel_companion,
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