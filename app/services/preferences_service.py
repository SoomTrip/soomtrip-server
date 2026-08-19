from sqlalchemy.orm import Session

from app.db.models import PreferenceResult
from app.schemas.preferences import PreferenceSaveRequest


def save_preference_result(
    db: Session,
    user_id: int,
    request: PreferenceSaveRequest,
) -> PreferenceResult:
    preference_result = PreferenceResult(
        user_id=user_id,
        ocean_score=request.ocean_score,
        nature_score=request.nature_score,
        theme_choice=request.theme_choice,
        walk_transit_score=request.walk_transit_score,
        car_score=request.car_score,
        mobility_choice=request.mobility_choice,
        solo_score=request.solo_score,
        group_score=request.group_score,
        companion_choice=request.companion_choice,
        rest_score=request.rest_score,
        dynamic_score=request.dynamic_score,
        activity_choice=request.activity_choice,
        outdoor_score=request.outdoor_score,
        indoor_score=request.indoor_score,
        indoor_choice=request.indoor_choice,
    )

    db.add(preference_result)
    db.commit()
    db.refresh(preference_result)

    return preference_result


def get_my_preference_results(
    db: Session,
    user_id: int,
) -> list[PreferenceResult]:
    return (
        db.query(PreferenceResult)
        .filter(PreferenceResult.user_id == user_id)
        .order_by(PreferenceResult.created_at.desc())
        .all()
    )


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