from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.saved_regions import SavedRegionCreateRequest, SavedRegionResponse
from app.services.saved_region_service import (
    create_saved_region,
    delete_saved_region,
    get_my_saved_regions,
)

router = APIRouter(
    prefix="/saved-regions",
    tags=["saved-regions"],
)


@router.post("", response_model=SavedRegionResponse)
def save_region(
    request: SavedRegionCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return create_saved_region(db, current_user_id, request)


@router.get("", response_model=list[SavedRegionResponse])
def get_saved_regions(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_my_saved_regions(db, current_user_id)


@router.delete("/{saved_region_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_region(
    saved_region_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deleted = delete_saved_region(db, current_user_id, saved_region_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 여행지를 찾을 수 없습니다.",
        )