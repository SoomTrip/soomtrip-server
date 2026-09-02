from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.saved_regions import (
    SavedRegionCreateRequest,
    SavedRegionResponse,
    SavedRegionShareRequest,
    SavedRegionShareResponse,
)

from app.services.saved_region_service import (
    create_saved_region,
    delete_saved_region,
    get_my_saved_region_by_id,
    get_my_saved_regions,
    share_saved_region_with_friends,
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


@router.get("/{saved_region_id}", response_model=SavedRegionResponse)
def get_saved_region(
    saved_region_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    saved_region = get_my_saved_region_by_id(
        db=db,
        user_id=current_user_id,
        saved_region_id=saved_region_id,
    )

    if saved_region is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 여행지를 찾을 수 없습니다.",
        )

    return saved_region


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

@router.post("/{saved_region_id}/share", response_model=SavedRegionShareResponse)
def share_saved_region(
    saved_region_id: int,
    request: SavedRegionShareRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    result = share_saved_region_with_friends(
        db=db,
        user_id=current_user_id,
        saved_region_id=saved_region_id,
        friend_user_ids=request.friend_user_ids,
    )

    if result["error"] == "SAVED_REGION_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved region not found.",
        )

    return {
        "shared": result["shared"],
        "failed": result["failed"],
    }