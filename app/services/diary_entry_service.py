from sqlalchemy.orm import Session

from app.db.models import DiaryEntry, SavedRegion
from app.schemas.diary_entries import DiaryEntryCreateRequest, DiaryEntryUpdateRequest


def create_diary_entry(
    db: Session,
    user_id: int,
    request: DiaryEntryCreateRequest,
) -> DiaryEntry | None:
    saved_region = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.id == request.saved_region_id,
            SavedRegion.user_id == user_id,
        )
        .first()
    )

    if saved_region is None:
        return None

    diary_entry = DiaryEntry(
        saved_region_id=request.saved_region_id,
        user_id=user_id,
        message=request.message,
        image_url=request.image_url,
        entry_type=request.entry_type,
        visit_start_date=request.visit_start_date,
        visit_end_date=request.visit_end_date,
        is_public=request.is_public,
    )

    db.add(diary_entry)
    db.commit()
    db.refresh(diary_entry)

    return diary_entry


def get_my_diary_entries(
    db: Session,
    user_id: int,
) -> list[DiaryEntry]:
    return (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == user_id)
        .order_by(DiaryEntry.created_at.desc())
        .all()
    )


def get_my_diary_entry_by_id(
    db: Session,
    user_id: int,
    diary_entry_id: int,
) -> DiaryEntry | None:
    return (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.id == diary_entry_id,
            DiaryEntry.user_id == user_id,
        )
        .first()
    )


def get_my_diary_entries_by_saved_region(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> list[DiaryEntry] | None:
    saved_region = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.id == saved_region_id,
            SavedRegion.user_id == user_id,
        )
        .first()
    )

    if saved_region is None:
        return None

    return (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.saved_region_id == saved_region_id,
            DiaryEntry.user_id == user_id,
        )
        .order_by(DiaryEntry.created_at.desc())
        .all()
    )


def update_my_diary_entry(
    db: Session,
    user_id: int,
    diary_entry_id: int,
    request: DiaryEntryUpdateRequest,
) -> DiaryEntry | None:
    diary_entry = get_my_diary_entry_by_id(db, user_id, diary_entry_id)

    if diary_entry is None:
        return None

    if request.message is not None:
        diary_entry.message = request.message
    if request.image_url is not None:
        diary_entry.image_url = request.image_url
    if request.entry_type is not None:
        diary_entry.entry_type = request.entry_type
    if request.visit_start_date is not None:
        diary_entry.visit_start_date = request.visit_start_date
    if request.visit_end_date is not None:
        diary_entry.visit_end_date = request.visit_end_date
    if request.is_public is not None:
        diary_entry.is_public = request.is_public

    db.commit()
    db.refresh(diary_entry)

    return diary_entry


def delete_my_diary_entry(
    db: Session,
    user_id: int,
    diary_entry_id: int,
) -> bool:
    diary_entry = get_my_diary_entry_by_id(db, user_id, diary_entry_id)

    if diary_entry is None:
        return False

    db.delete(diary_entry)
    db.commit()

    return True