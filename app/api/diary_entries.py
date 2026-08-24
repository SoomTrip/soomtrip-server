from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.diary_entries import (
    DiaryEntryCreateRequest,
    DiaryEntryResponse,
    DiaryEntryUpdateRequest,
)
from app.services.diary_entry_service import (
    create_diary_entry,
    delete_my_diary_entry,
    get_my_diary_entries,
    get_my_diary_entries_by_saved_region,
    get_my_diary_entry_by_id,
    update_my_diary_entry,
)

router = APIRouter(
    prefix="/diary-entries",
    tags=["diary-entries"],
)


@router.post("", response_model=DiaryEntryResponse)
def create_entry(
    request: DiaryEntryCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    diary_entry = create_diary_entry(
        db=db,
        user_id=current_user_id,
        request=request,
    )

    if diary_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved region not found.",
        )

    return diary_entry


@router.get("/me", response_model=list[DiaryEntryResponse])
def get_my_entries(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_my_diary_entries(db, current_user_id)


@router.get("/saved-region/{saved_region_id}", response_model=list[DiaryEntryResponse])
def get_entries_by_saved_region(
    saved_region_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    diary_entries = get_my_diary_entries_by_saved_region(
        db=db,
        user_id=current_user_id,
        saved_region_id=saved_region_id,
    )

    if diary_entries is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved region not found.",
        )

    return diary_entries


@router.get("/{diary_entry_id}", response_model=DiaryEntryResponse)
def get_entry(
    diary_entry_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    diary_entry = get_my_diary_entry_by_id(
        db=db,
        user_id=current_user_id,
        diary_entry_id=diary_entry_id,
    )

    if diary_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary entry not found.",
        )

    return diary_entry


@router.patch("/{diary_entry_id}", response_model=DiaryEntryResponse)
def update_entry(
    diary_entry_id: int,
    request: DiaryEntryUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    diary_entry = update_my_diary_entry(
        db=db,
        user_id=current_user_id,
        diary_entry_id=diary_entry_id,
        request=request,
    )

    if diary_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary entry not found.",
        )

    return diary_entry


@router.delete("/{diary_entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    diary_entry_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deleted = delete_my_diary_entry(
        db=db,
        user_id=current_user_id,
        diary_entry_id=diary_entry_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary entry not found.",
        )