from sqlalchemy.orm import Session

from app.db.models import SavedRegion
from app.schemas.saved_regions import SavedRegionCreateRequest


def create_saved_region(
    db: Session,
    user_id: int,
    request: SavedRegionCreateRequest,
) -> SavedRegion:
    existing = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.user_id == user_id,
            SavedRegion.region_content_id == request.region_content_id,
        )
        .first()
    )

    if existing is not None:
        return existing

    saved_region = SavedRegion(
        user_id=user_id,
        region_content_id=request.region_content_id,
        region_name=request.region_name,
    )

    db.add(saved_region)
    db.commit()
    db.refresh(saved_region)

    return saved_region


def get_my_saved_regions(
    db: Session,
    user_id: int,
) -> list[SavedRegion]:
    return (
        db.query(SavedRegion)
        .filter(SavedRegion.user_id == user_id)
        .order_by(SavedRegion.created_at.desc())
        .all()
    )


def delete_saved_region(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> bool:
    saved_region = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.id == saved_region_id,
            SavedRegion.user_id == user_id,
        )
        .first()
    )

    if saved_region is None:
        return False

    db.delete(saved_region)
    db.commit()

    return True