from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db

from app.schemas.users import UserDeleteResponse, UserMeResponse, UserUpdateRequest
from app.services.user_service import delete_user, get_user_by_id, update_user

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

    return update_user(db, user, request)

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