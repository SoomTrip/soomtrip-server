from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.preferences import PreferenceResponse, PreferenceSaveRequest
from app.services.preferences_service import (
    delete_my_preference_result,
    get_my_preference_results,
    save_preference_result,
)

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
)


@router.post("", response_model=PreferenceResponse)
def save_preferences(
    request: PreferenceSaveRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return save_preference_result(
        db=db,
        user_id=current_user_id,
        request=request,
    )


@router.get("/me", response_model=list[PreferenceResponse])
def get_my_preferences(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    preference_result = get_my_preference_results(
        db=db,
        user_id=current_user_id,
    )

    return preference_result

@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preference(
    preference_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deleted = delete_my_preference_result(
        db=db,
        user_id=current_user_id,
        preference_id=preference_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="취향 결과를 찾을 수 없습니다.",
        )