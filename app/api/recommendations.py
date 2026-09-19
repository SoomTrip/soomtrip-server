from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from time import perf_counter

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.recommendation.schemas import RecommendationResult
from app.schemas.recommendations import RecommendationCreateRequest
from app.services.recommendation_service import create_recommendation_for_preference

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


@router.post("", response_model=RecommendationResult)
def create_recommendation(
    request: RecommendationCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):

    started_at = perf_counter()

    print(
        "[Recommendation API start] "
        f"user_id={current_user_id} "
        f"preference_id={request.preference_id}",
        flush=True,
    )

    recommendation = create_recommendation_for_preference(
        db=db,
        user_id=current_user_id,
        preference_id=request.preference_id,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 취향 결과를 찾을 수 없습니다.",
        )
    print(
        "[Recommendation API done] "
        f"user_id={current_user_id} "
        f"preference_id={request.preference_id} "
        f"candidate_count={len(recommendation.candidates)} "
        f"elapsed={perf_counter() - started_at:.2f}s",
        flush=True,
    )

    return recommendation