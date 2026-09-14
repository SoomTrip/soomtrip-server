from datetime import datetime, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    DiaryEntry,
    Friend,
    FriendStatus,
    RouteEntry,
    SavedRegion,
    SavedRegionShare,
    SavedRegionShareStatus,
    SavedRegionSpot,
    Stamp,
)
from app.schemas.saved_regions import SavedRegionCreateRequest
from app.services.upload_service import (
    create_profile_image_signed_url,
    delete_diary_images_from_supabase,
)
def create_saved_region(
    db: Session,
    user_id: int,
    request: SavedRegionCreateRequest,
) -> SavedRegion:
    saved_region = SavedRegion(
        user_id=user_id,
        region_name=request.region_name,
        score=request.score,
        mobility_choice=request.mobility_choice,
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
        .filter(
            SavedRegion.user_id == user_id,
            SavedRegion.deleted_at.is_(None),
        )
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
            SavedRegion.deleted_at.is_(None),
        )
        .first()
    )


def has_stamp(
    db: Session,
    saved_region_id: int,
) -> bool:
    return (
        db.query(Stamp.id)
        .filter(Stamp.saved_region_id == saved_region_id)
        .first()
        is not None
    )


def delete_saved_region(
    db: Session,
    user_id: int,
    saved_region_id: int,
    keep_stamp: bool = False,
) -> bool:
    saved_region = (
        db.query(SavedRegion)
        .filter(
            SavedRegion.id == saved_region_id,
            SavedRegion.user_id == user_id,
            SavedRegion.deleted_at.is_(None),
        )
        .first()
    )

    if saved_region is None:
        return False

    db.query(SavedRegionShare).filter(
        or_(
            SavedRegionShare.saved_region_id == saved_region_id,
            SavedRegionShare.cloned_saved_region_id == saved_region_id,
        )
    ).delete(synchronize_session=False)

    db.query(RouteEntry).filter(
        RouteEntry.saved_region_id == saved_region_id
    ).delete(synchronize_session=False)

    db.query(SavedRegionSpot).filter(
        SavedRegionSpot.saved_region_id == saved_region_id
    ).delete(synchronize_session=False)

    # 도장(그리고 그 도장의 근거인 그림일기)을 남기고 싶다면, 여행지 자체는 완전히
    # 지우지 않고 "저장 목록에서만 숨김" 처리한다(소프트 삭제). 도장/일기는
    # saved_region_id로 이 행을 계속 그대로 참조하므로 데이터가 살아있다.
    if keep_stamp and has_stamp(db, saved_region_id):
        saved_region.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True

    diary_image_paths = [
        image_url
        for (image_url,) in (
            db.query(DiaryEntry.image_url)
            .filter(
                DiaryEntry.saved_region_id == saved_region_id,
                DiaryEntry.image_url.isnot(None),
            )
            .all()
        )
    ]

    delete_diary_images_from_supabase(diary_image_paths)

    db.query(DiaryEntry).filter(
        DiaryEntry.saved_region_id == saved_region_id
    ).delete(synchronize_session=False)

    db.query(Stamp).filter(
        Stamp.saved_region_id == saved_region_id
    ).delete(synchronize_session=False)

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

def build_saved_region_response(
    db: Session,
    user_id: int,
    saved_region: SavedRegion,
) -> dict:
    shared_from = get_shared_from_info(
        db=db,
        user_id=user_id,
        saved_region_id=saved_region.id,
    )

    shared_to = get_shared_to_info(
        db=db,
        user_id=user_id,
        saved_region_id=saved_region.id,
    )

    return {
        "id": saved_region.id,
        "user_id": saved_region.user_id,
        "region_name": saved_region.region_name,
        "score": saved_region.score,
        "mobility_choice": saved_region.mobility_choice,
        "created_at": saved_region.created_at,
        "has_stamp": has_stamp(db, saved_region.id),
        "shared_from": shared_from,
        "shared_to": shared_to,
        "spots": saved_region.spots,
    }


def get_shared_from_info(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> dict | None:
    share = (
        db.query(SavedRegionShare)
        .options(joinedload(SavedRegionShare.sender))
        .filter(
            SavedRegionShare.receiver_id == user_id,
            SavedRegionShare.cloned_saved_region_id == saved_region_id,
            SavedRegionShare.status == SavedRegionShareStatus.ACCEPTED,
        )
        .first()
    )

    if share is None:
        return None

    return {
        "share_id": share.id,
        "user_id": share.sender.id,
        "nickname": share.sender.nickname,
        "profile_image": share.sender.profile_image,
        "signed_profile_image_url": create_profile_image_signed_url(
            share.sender.profile_image
        ),
    }


def get_shared_to_info(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> list[dict]:
    shares = (
        db.query(SavedRegionShare)
        .options(joinedload(SavedRegionShare.receiver))
        .filter(
            SavedRegionShare.sender_id == user_id,
            SavedRegionShare.saved_region_id == saved_region_id,
        )
        .order_by(SavedRegionShare.created_at.desc())
        .all()
    )

    return [
        {
            "share_id": share.id,
            "user_id": share.receiver.id,
            "nickname": share.receiver.nickname,
            "profile_image": share.receiver.profile_image,
            "signed_profile_image_url": create_profile_image_signed_url(
                share.receiver.profile_image
            ),
            "status": share.status,
        }
        for share in shares
    ]


def get_my_saved_region_responses(
    db: Session,
    user_id: int,
) -> list[dict]:
    saved_regions = get_my_saved_regions(db, user_id)

    return [
        build_saved_region_response(
            db=db,
            user_id=user_id,
            saved_region=saved_region,
        )
        for saved_region in saved_regions
    ]


def get_my_saved_region_response_by_id(
    db: Session,
    user_id: int,
    saved_region_id: int,
) -> dict | None:
    saved_region = get_my_saved_region_by_id(
        db=db,
        user_id=user_id,
        saved_region_id=saved_region_id,
    )

    if saved_region is None:
        return None

    return build_saved_region_response(
        db=db,
        user_id=user_id,
        saved_region=saved_region,
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
        mobility_choice=source_saved_region.mobility_choice,
    )

    db.add(copied_region)
    db.flush()

    spot_id_map = {}

    for spot in source_saved_region.spots:
        copied_spot = SavedRegionSpot(
            saved_region_id=copied_region.id,
            content_id=spot.content_id,
            name=spot.name,
            category_label=spot.category_label,
            latitude=spot.latitude,
            longitude=spot.longitude,
            is_anchor=spot.is_anchor,
        )

        db.add(copied_spot)
        db.flush()

        spot_id_map[spot.id] = copied_spot.id

    route_entries = (
        db.query(RouteEntry)
        .filter(RouteEntry.saved_region_id == source_saved_region.id)
        .all()
    )

    for route_entry in route_entries:
        new_spot_id = spot_id_map.get(route_entry.saved_region_spot_id)

        if new_spot_id is None:
            continue

        copied_route_entry = RouteEntry(
            saved_region_id=copied_region.id,
            saved_region_spot_id=new_spot_id,
            visit_day=route_entry.visit_day,
            visit_order=route_entry.visit_order,
            distance_from_prev_km=route_entry.distance_from_prev_km,
            duration_from_prev_minutes=route_entry.duration_from_prev_minutes,
            mobility_choice=route_entry.mobility_choice,
        )

        db.add(copied_route_entry)

    return copied_region


def already_has_pending_share(
    db: Session,
    saved_region_id: int,
    sender_id: int,
    receiver_id: int,
) -> bool:
    return (
        db.query(SavedRegionShare)
        .filter(
            SavedRegionShare.saved_region_id == saved_region_id,
            SavedRegionShare.sender_id == sender_id,
            SavedRegionShare.receiver_id == receiver_id,
            SavedRegionShare.status == SavedRegionShareStatus.PENDING,
        )
        .first()
        is not None
    )


def create_saved_region_share_requests(
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
            "created": [],
            "failed": [],
        }

    created = []
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

        if already_has_pending_share(
            db=db,
            saved_region_id=saved_region_id,
            sender_id=user_id,
            receiver_id=friend_user_id,
        ):
            failed.append({
                "friend_user_id": friend_user_id,
                "reason": "SHARE_ALREADY_PENDING",
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

        share = SavedRegionShare(
            saved_region_id=saved_region_id,
            sender_id=user_id,
            receiver_id=friend_user_id,
            status=SavedRegionShareStatus.PENDING,
        )

        db.add(share)
        db.flush()

        created.append({
            "friend_user_id": friend_user_id,
            "share_id": share.id,
        })

    db.commit()

    return {
        "error": None,
        "created": created,
        "failed": failed,
    }

def build_share_list_item(share: SavedRegionShare) -> dict:
    return {
        "share_id": share.id,
        "saved_region_id": share.saved_region_id,
        "region_name": share.saved_region.region_name,
        "status": share.status,
        "created_at": share.created_at,
        "responded_at": share.responded_at,

        "sender_id": share.sender.id,
        "sender_nickname": share.sender.nickname,
        "sender_profile_image": share.sender.profile_image,
        "sender_signed_profile_image_url": create_profile_image_signed_url(
            share.sender.profile_image
        ),

        "receiver_id": share.receiver.id,
        "receiver_nickname": share.receiver.nickname,
        "receiver_profile_image": share.receiver.profile_image,
        "receiver_signed_profile_image_url": create_profile_image_signed_url(
            share.receiver.profile_image
        ),
    }


def get_sent_saved_region_shares(
    db: Session,
    user_id: int,
) -> list[dict]:
    shares = (
        db.query(SavedRegionShare)
        .options(
            joinedload(SavedRegionShare.saved_region),
            joinedload(SavedRegionShare.sender),
            joinedload(SavedRegionShare.receiver),
        )
        .filter(SavedRegionShare.sender_id == user_id)
        .order_by(SavedRegionShare.created_at.desc())
        .all()
    )

    return [build_share_list_item(share) for share in shares]


def get_received_saved_region_shares(
    db: Session,
    user_id: int,
) -> list[dict]:
    shares = (
        db.query(SavedRegionShare)
        .options(
            joinedload(SavedRegionShare.saved_region),
            joinedload(SavedRegionShare.sender),
            joinedload(SavedRegionShare.receiver),
        )
        .filter(SavedRegionShare.receiver_id == user_id)
        .order_by(SavedRegionShare.created_at.desc())
        .all()
    )

    return [build_share_list_item(share) for share in shares]

def accept_saved_region_share(
    db: Session,
    user_id: int,
    share_id: int,
) -> dict | None:
    share = (
        db.query(SavedRegionShare)
        .options(
            joinedload(SavedRegionShare.saved_region).joinedload(SavedRegion.spots),
        )
        .filter(
            SavedRegionShare.id == share_id,
            SavedRegionShare.receiver_id == user_id,
            SavedRegionShare.status == SavedRegionShareStatus.PENDING,
        )
        .first()
    )

    if share is None:
        return None

    anchor_content_id = get_anchor_content_id(share.saved_region)

    if anchor_content_id and already_has_saved_region_with_anchor(
        db=db,
        user_id=user_id,
        anchor_content_id=anchor_content_id,
    ):
        raise ValueError("ALREADY_SAVED")

    copied_region = copy_saved_region_to_user(
        db=db,
        source_saved_region=share.saved_region,
        target_user_id=user_id,
    )

    share.status = SavedRegionShareStatus.ACCEPTED
    share.cloned_saved_region_id = copied_region.id
    share.responded_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "share_id": share.id,
        "status": share.status,
        "cloned_saved_region_id": copied_region.id,
    }


def reject_saved_region_share(
    db: Session,
    user_id: int,
    share_id: int,
) -> dict | None:
    share = (
        db.query(SavedRegionShare)
        .filter(
            SavedRegionShare.id == share_id,
            SavedRegionShare.receiver_id == user_id,
            SavedRegionShare.status == SavedRegionShareStatus.PENDING,
        )
        .first()
    )

    if share is None:
        return None

    share.status = SavedRegionShareStatus.REJECTED
    share.responded_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "share_id": share.id,
        "status": share.status,
    }