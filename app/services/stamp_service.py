import random

from sqlalchemy.orm import Session

from app.db.models import SavedRegion, Stamp


STAMP_ASSET_KEYS = [
    "stamp1",
    "stamp2",
    "stamp3",
    "stamp4",
    "stamp5",
    "stamp6",
]

def pick_stamp_asset_key(
    db: Session,
    user_id: int,
) -> str:
    used_stamp_keys = {
        stamp_asset_key
        for (stamp_asset_key,) in (
            db.query(Stamp.stamp_asset_key)
            .filter(Stamp.user_id == user_id)
            .all()
        )
    }

    unused_stamp_keys = [
        key for key in STAMP_ASSET_KEYS
        if key not in used_stamp_keys
    ]

    if unused_stamp_keys:
        return random.choice(unused_stamp_keys)

    return random.choice(STAMP_ASSET_KEYS)

def create_stamp_if_not_exists(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> Stamp:
    existing_stamp = (
        db.query(Stamp)
        .filter(
            Stamp.user_id == user_id,
            Stamp.saved_region_id == saved_region_id,
        )
        .first()
    )

    if existing_stamp is not None:
        return existing_stamp

    stamp = Stamp(
        user_id=user_id,
        saved_region_id=saved_region_id,
        stamp_asset_key=pick_stamp_asset_key(db, user_id),
    )

    db.add(stamp)

    return stamp


def get_my_stamps(
    db: Session,
    user_id: int,
) -> list[dict]:
    stamps = (
        db.query(Stamp, SavedRegion.region_name)
        .join(SavedRegion, Stamp.saved_region_id == SavedRegion.id)
        .filter(Stamp.user_id == user_id)
        .order_by(Stamp.created_at.desc())
        .all()
    )

    return [
        {
            "id": stamp.id,
            "user_id": stamp.user_id,
            "saved_region_id": stamp.saved_region_id,
            "region_name": region_name,
            "stamp_asset_key": stamp.stamp_asset_key,
            "created_at": stamp.created_at,
        }
        for stamp, region_name in stamps
    ]