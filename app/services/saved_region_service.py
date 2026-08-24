from sqlalchemy.orm import Session, joinedload

from app.db.models import SavedRegion, SavedRegionSpot
from app.schemas.saved_regions import SavedRegionCreateRequest


def create_saved_region(
    db: Session,
    user_id: int,
    request: SavedRegionCreateRequest,
) -> SavedRegion:
    saved_region = SavedRegion(
        user_id=user_id,
        region_name=request.region_name,
        score=request.score,
    )

    for spot in request.spots:
        saved_region.spots.append(
            SavedRegionSpot(
                content_id=spot.content_id,
                name=spot.name,
                category_label=spot.category_label,
                latitude=spot.latitude,
                longitude=spot.longitude,
                is_anchor=spot.is_anchor,
            )
        )

    db.add(saved_region)
    db.commit()
    db.refresh(saved_region)

    return (
        db.query(SavedRegion)
        .options(joinedload(SavedRegion.spots))
        .filter(SavedRegion.id == saved_region.id)
        .first()
    )


def get_my_saved_regions(
    db: Session,
    user_id: int,
) -> list[SavedRegion]:
    return (
        db.query(SavedRegion)
        .options(joinedload(SavedRegion.spots))
        .filter(SavedRegion.user_id == user_id)
        .order_by(SavedRegion.created_at.desc())
        .all()
    )


def get_my_saved_region_by_id(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> SavedRegion | None:
    return (
        db.query(SavedRegion)
        .options(joinedload(SavedRegion.spots))
        .filter(
            SavedRegion.id == saved_region_id,
            SavedRegion.user_id == user_id,
        )
        .first()
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