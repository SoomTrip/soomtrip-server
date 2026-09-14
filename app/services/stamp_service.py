import random

from sqlalchemy.orm import Session

from app.db.models import DiaryEntry, SavedRegion, Stamp
from app.services.upload_service import delete_diary_images_from_supabase


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
    # SavedRegion은 소프트 삭제(deleted_at)만 되고 실제로 지워지지는 않으므로,
    # 여행지를 지워도 그 여행지에 딸린 도장은 그대로 inner join으로 잘 나온다.
    stamps = (
        db.query(Stamp, SavedRegion.region_name, SavedRegion.deleted_at)
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
            "is_region_deleted": deleted_at is not None,
        }
        for stamp, region_name, deleted_at in stamps
    ]


def delete_stamp(
    db: Session,
    user_id: int,
    stamp_id: int,
) -> bool:
    stamp = (
        db.query(Stamp)
        .filter(Stamp.id == stamp_id, Stamp.user_id == user_id)
        .first()
    )

    if stamp is None:
        return False

    saved_region = (
        db.query(SavedRegion)
        .filter(SavedRegion.id == stamp.saved_region_id)
        .first()
    )

    # 아직 저장 목록에 남아있는(=지워지지 않은) 여행지의 도장은 이 방법으로
    # 지울 수 없다. 여행지 삭제 화면에서 "도장까지 삭제"를 선택하도록 유도한다.
    if saved_region is not None and saved_region.deleted_at is None:
        raise ValueError("SAVED_REGION_STILL_ACTIVE")

    diary_image_paths = [
        image_url
        for (image_url,) in (
            db.query(DiaryEntry.image_url)
            .filter(
                DiaryEntry.saved_region_id == stamp.saved_region_id,
                DiaryEntry.image_url.isnot(None),
            )
            .all()
        )
    ]

    delete_diary_images_from_supabase(diary_image_paths)

    db.query(DiaryEntry).filter(
        DiaryEntry.saved_region_id == stamp.saved_region_id
    ).delete(synchronize_session=False)

    db.delete(stamp)

    # user_id+saved_region_id는 유니크 제약이라 도장은 여행지당 최대 1개뿐이므로,
    # 이 도장을 지우면 소프트 삭제해뒀던 여행지 행도 완전히 정리한다.
    if saved_region is not None:
        db.delete(saved_region)

    db.commit()

    return True