from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.stamps import StampResponse
from app.services.stamp_service import get_my_stamps


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