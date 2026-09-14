from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone
from app.db.models import (
    DiaryEntry,
    Friend,
    PreferenceResult,
    RefreshToken,
    RouteEntry,
    SavedRegion,
    SavedRegionShare,
    SavedRegionSpot,
    Stamp,
    User,
)
from app.services.upload_service import (
    create_profile_image_signed_url,
    delete_diary_images_from_supabase,
)
from app.schemas.users import UserUpdateRequest


def attach_signed_profile_image_url(user: User) -> User:
    user.signed_profile_image_url = create_profile_image_signed_url(
        user.profile_image
    )
    return user

def is_uploaded_profile_image(image_path: str | None) -> bool:
    return image_path is not None and image_path.startswith("profile/")

def get_user_by_id(db: Session, user_id: int) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        return None

    return attach_signed_profile_image_url(user)


def update_user(
    db: Session,
    user: User,
    request: UserUpdateRequest,
) -> User:
    old_profile_image = user.profile_image

    if request.nickname is not None:
        user.nickname = request.nickname

    if request.profile_image is not None:
        user.profile_image = request.profile_image

    db.commit()
    db.refresh(user)

    if (
        request.profile_image is not None
        and old_profile_image != user.profile_image
        and is_uploaded_profile_image(old_profile_image)
    ):
        delete_diary_images_from_supabase([old_profile_image])

    return attach_signed_profile_image_url(user)

def delete_user(
    db: Session,
    user_id: int,
) -> bool:
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        return False

    profile_image_path = user.profile_image

    saved_region_ids = [
        saved_region_id
        for (saved_region_id,) in (
            db.query(SavedRegion.id)
            .filter(SavedRegion.user_id == user_id)
            .all()
        )
    ]

    db.query(SavedRegionShare).filter(
        or_(
            SavedRegionShare.sender_id == user_id,
            SavedRegionShare.receiver_id == user_id,
        )
    ).delete(synchronize_session=False)

    if saved_region_ids:
        db.query(SavedRegionShare).filter(
            or_(
                SavedRegionShare.saved_region_id.in_(saved_region_ids),
                SavedRegionShare.cloned_saved_region_id.in_(saved_region_ids),
            )
        ).delete(synchronize_session=False)

        db.query(RouteEntry).filter(
            RouteEntry.saved_region_id.in_(saved_region_ids)
        ).delete(synchronize_session=False)

        diary_image_paths = [
            image_url
            for (image_url,) in (
                db.query(DiaryEntry.image_url)
                .filter(
                    DiaryEntry.saved_region_id.in_(saved_region_ids),
                    DiaryEntry.image_url.isnot(None),
                )
                .all()
            )
        ]

        delete_diary_images_from_supabase(diary_image_paths)

        db.query(DiaryEntry).filter(
            DiaryEntry.saved_region_id.in_(saved_region_ids)
        ).delete(synchronize_session=False)

        db.query(Stamp).filter(
            Stamp.saved_region_id.in_(saved_region_ids)
        ).delete(synchronize_session=False)

        db.query(SavedRegionSpot).filter(
            SavedRegionSpot.saved_region_id.in_(saved_region_ids)
        ).delete(synchronize_session=False)

        db.query(SavedRegion).filter(
            SavedRegion.id.in_(saved_region_ids)
        ).delete(synchronize_session=False)

    db.query(Friend).filter(
        (Friend.requester_id == user_id) | (Friend.receiver_id == user_id)
    ).delete(synchronize_session=False)

    db.query(PreferenceResult).filter(
        PreferenceResult.user_id == user_id
    ).delete(synchronize_session=False)

    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id
    ).delete(synchronize_session=False)

    if is_uploaded_profile_image(profile_image_path):
        delete_diary_images_from_supabase([profile_image_path])

    db.delete(user)
    db.commit()

    return True

def complete_onboarding(
    db: Session,
    user: User,
) -> User:
    user.onboarding_completed = True

    db.commit()
    db.refresh(user)

    return attach_signed_profile_image_url(user)

def agree_to_required_terms(
    db: Session,
    user: User,
) -> User:
    now = datetime.now(timezone.utc)

    if user.terms_agreed_at is None:
        user.terms_agreed_at = now

    if user.privacy_agreed_at is None:
        user.privacy_agreed_at = now

    db.commit()
    db.refresh(user)

    return attach_signed_profile_image_url(user)

