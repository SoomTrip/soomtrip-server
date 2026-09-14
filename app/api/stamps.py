from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.stamps import StampResponse
from app.services.stamp_service import delete_stamp, get_my_stamps


router = APIRouter(
    prefix="/stamps",
    tags=["stamps"],
)


@router.get("", response_model=list[StampResponse])
def get_stamps(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_my_stamps(
        db=db,
        user_id=current_user_id,
    )


@router.delete("/{stamp_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_stamp(
    stamp_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        deleted = delete_stamp(
            db=db,
            user_id=current_user_id,
            stamp_id=stamp_id,
        )
    except ValueError as exc:
        if str(exc) == "SAVED_REGION_STILL_ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="아직 저장 목록에 있는 여행지의 도장이라 삭제할 수 없습니다.",
            ) from exc
        raise

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도장을 찾을 수 없습니다.",
        )