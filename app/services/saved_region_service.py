from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.db.models import Friend, FriendStatus, SavedRegion, SavedRegionSpot
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

def is_accepted_friend(
    db: Session,
    user_id: int,
    friend_user_id: int,
) -> bool:
    return (
        db.query(Friend)
        .filter(
            Friend.status == FriendStatus.ACCEPTED,
            or_(
                and_(
                    Friend.requester_id == user_id,
                    Friend.receiver_id == friend_user_id,
                ),
                and_(
                    Friend.requester_id == friend_user_id,
                    Friend.receiver_id == user_id,
                ),
            ),
        )
        .first()
        is not None
    )


def get_anchor_content_id(saved_region: SavedRegion) -> str | None:
    for spot in saved_region.spots:
        if spot.is_anchor:
            return spot.content_id

    return None


def already_has_saved_region_with_anchor(
    db: Session,
    user_id: int,
    anchor_content_id: str,
) -> bool:
    return (
        db.query(SavedRegionSpot)
        .join(SavedRegion)
        .filter(
            SavedRegion.user_id == user_id,
            SavedRegionSpot.content_id == anchor_content_id,
            SavedRegionSpot.is_anchor.is_(True),
        )
        .first()
        is not None
    )


def copy_saved_region_to_user(
    db: Session,
    source_saved_region: SavedRegion,
    target_user_id: int,
) -> SavedRegion:
    copied_region = SavedRegion(
        user_id=target_user_id,
        region_name=source_saved_region.region_name,
        score=source_saved_region.score,
    )

    for spot in source_saved_region.spots:
        copied_region.spots.append(
            SavedRegionSpot(
                content_id=spot.content_id,
                name=spot.name,
                category_label=spot.category_label,
                latitude=spot.latitude,
                longitude=spot.longitude,
                is_anchor=spot.is_anchor,
            )
        )

    db.add(copied_region)
    db.flush()

    return copied_region


def share_saved_region_with_friends(
    db: Session,
    user_id: int,
    saved_region_id: int,
    friend_user_ids: list[int],
) -> dict:
    source_saved_region = get_my_saved_region_by_id(
        db=db,
        user_id=user_id,
        saved_region_id=saved_region_id,
    )

    if source_saved_region is None:
        return {
            "error": "SAVED_REGION_NOT_FOUND",
            "shared": [],
            "failed": [],
        }

    shared = []
    failed = []
    anchor_content_id = get_anchor_content_id(source_saved_region)

    for friend_user_id in set(friend_user_ids):
        if friend_user_id == user_id:
            failed.append({
                "friend_user_id": friend_user_id,
                "reason": "CANNOT_SHARE_TO_SELF",
            })
            continue

        if not is_accepted_friend(db, user_id, friend_user_id):
            failed.append({
                "friend_user_id": friend_user_id,
                "reason": "NOT_ACCEPTED_FRIEND",
            })
            continue

        if anchor_content_id and already_has_saved_region_with_anchor(
            db=db,
            user_id=friend_user_id,
            anchor_content_id=anchor_content_id,
        ):
            failed.append({
                "friend_user_id": friend_user_id,
                "reason": "ALREADY_SAVED",
            })
            continue

        copied_region = copy_saved_region_to_user(
            db=db,
            source_saved_region=source_saved_region,
            target_user_id=friend_user_id,
        )

        shared.append({
            "friend_user_id": friend_user_id,
            "saved_region_id": copied_region.id,
        })

    db.commit()

    return {
        "error": None,
        "shared": shared,
        "failed": failed,
    }