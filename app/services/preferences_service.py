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
        nature_score=request.nature_score,
        activity_score=request.activity_score,
        healing_score=request.healing_score,
        urban_score=request.urban_score,
        ocean_score=request.ocean_score,
        budget_level=request.budget_level,
        transport=request.transport,
        activity_intensity=request.activity_intensity,
        travel_companion=request.travel_companion,
        indoor_preference=request.indoor_preference,
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