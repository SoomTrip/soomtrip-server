from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.recommendation.schemas import RecommendationResult
from app.services.recommendation_service import create_recommendation_for_user

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


@router.post("", response_model=RecommendationResult)
def create_recommendation(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    recommendation = create_recommendation_for_user(
        db=db,
        user_id=current_user_id,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 취향 결과가 없습니다.",
        )

    return recommendation