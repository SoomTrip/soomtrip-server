import random

from sqlalchemy.orm import Session

from app.db.models import SavedRegion, Stamp


DEFAULT_STAMP_ASSET_KEYS = [
    "stamp1",
    "stamp2",
    "stamp3",
    "stamp4",
    "stamp5",
    "stamp6",
    "stamp7",
]

SHORT_NAME_STAMP_ASSET_KEYS = [
    "stamp8",
    "stamp9",
    "stamp10",
]

STAMP_ASSET_KEYS = DEFAULT_STAMP_ASSET_KEYS + SHORT_NAME_STAMP_ASSET_KEYS

def pick_stamp_asset_key(
    db: Session,
    user_id: int,
    region_name: str,
) -> str:
    available_stamp_keys = DEFAULT_STAMP_ASSET_KEYS.copy()

    if len(region_name) <= 5:
        available_stamp_keys += SHORT_NAME_STAMP_ASSET_KEYS

    used_stamp_keys = {
        stamp_asset_key
        for (stamp_asset_key,) in (
            db.query(Stamp.stamp_asset_key)
            .filter(Stamp.user_id == user_id)
            .all()
        )
    }

    unused_stamp_keys = [
        key for key in available_stamp_keys
        if key not in used_stamp_keys
    ]

    if unused_stamp_keys:
        return random.choice(unused_stamp_keys)

    return random.choice(available_stamp_keys)

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

    saved_region = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.id == saved_region_id,
            SavedRegion.user_id == user_id,
        )
        .first()
    )

    if saved_region is None:
        raise ValueError("SAVED_REGION_NOT_FOUND")

    stamp = Stamp(
        user_id=user_id,
        saved_region_id=saved_region_id,
        stamp_asset_key=pick_stamp_asset_key(
            db=db,
            user_id=user_id,
            region_name=saved_region.region_name,
        ),
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