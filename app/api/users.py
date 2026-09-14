from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db

from app.schemas.users import (
    UserAgreementRequest,
    UserDeleteResponse,
    UserMeResponse,
    UserUpdateRequest,
)
from app.services.user_service import (
    agree_to_required_terms,
    complete_onboarding,
    delete_user,
    get_user_by_id,
    update_user,
)
router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me", response_model=UserMeResponse)
def get_me(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, current_user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user


@router.patch("/me", response_model=UserMeResponse)
def update_me(
    request: UserUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, current_user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    try:
        return update_user(db, user, request)
    except ValueError as exc:
        if str(exc) == "INVALID_PROFILE_IMAGE_PATH":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid profile image path.",
            ) from exc

        raise

@router.patch("/me/onboarding-complete", response_model=UserMeResponse)
def complete_my_onboarding(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, current_user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return complete_onboarding(db, user)

@router.patch("/me/agreements", response_model=UserMeResponse)
def agree_my_required_terms(
    request: UserAgreementRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not request.terms_agreed or not request.privacy_agreed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Required agreements must be accepted.",
        )

    user = get_user_by_id(db, current_user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return agree_to_required_terms(db, user)

@router.delete("/me", response_model=UserDeleteResponse)
def delete_me(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deleted = delete_user(db, current_user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return {
        "message": "회원탈퇴가 완료되었습니다.",
    }