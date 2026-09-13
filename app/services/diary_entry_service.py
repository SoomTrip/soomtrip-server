from sqlalchemy.orm import Session

from app.db.models import DiaryEntry, SavedRegion
from app.schemas.diary_entries import DiaryEntryCreateRequest, DiaryEntryUpdateRequest
from app.services.stamp_service import create_stamp_if_not_exists
from app.services.upload_service import delete_diary_images_from_supabase

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
        title=request.title,
        message=request.message,
        image_url=request.image_url,
        weather=request.weather,
        date=request.date,
        is_public=request.is_public,
    )

    db.add(diary_entry)

    create_stamp_if_not_exists(
        db=db,
        user_id=user_id,
        saved_region_id=request.saved_region_id,
    )

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

    if request.title is not None:
        diary_entry.title = request.title
    if request.message is not None:
        diary_entry.message = request.message
    if request.image_url is not None:
        diary_entry.image_url = request.image_url
    if request.weather is not None:
        diary_entry.weather = request.weather
    if request.date is not None:
        diary_entry.date = request.date
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

    image_path = diary_entry.image_url

    if image_path is not None:
        delete_diary_images_from_supabase([image_path])

    db.delete(diary_entry)
    db.commit()

    return True