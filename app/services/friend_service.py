from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Friend, FriendStatus, User
from app.services.upload_service import create_profile_image_signed_url


def attach_signed_profile_image_url_to_user(user: User) -> User:
    user.signed_profile_image_url = create_profile_image_signed_url(
        user.profile_image
    )
    return user


def attach_signed_profile_images_to_friend(friend: Friend) -> Friend:
    if friend.requester is not None:
        attach_signed_profile_image_url_to_user(friend.requester)

    if friend.receiver is not None:
        attach_signed_profile_image_url_to_user(friend.receiver)

    return friend

def create_friend_request(
    db: Session,
    requester_id: int,
    receiver_user_code: str,
) -> Friend:
    receiver = (
        db.query(User)
        .filter(User.user_code == receiver_user_code)
        .first()
    )

    if receiver is None:
        raise ValueError("USER_NOT_FOUND")

    if receiver.id == requester_id:
        raise ValueError("CANNOT_REQUEST_SELF")

    existing_friend = (
        db.query(Friend)
        .filter(
            or_(
                (Friend.requester_id == requester_id) & (Friend.receiver_id == receiver.id),
                (Friend.requester_id == receiver.id) & (Friend.receiver_id == requester_id),
            )
        )
        .first()
    )

    if existing_friend is not None:
        if existing_friend.status == FriendStatus.REJECTED:
            existing_friend.requester_id = requester_id
            existing_friend.receiver_id = receiver.id
            existing_friend.status = FriendStatus.PENDING
            existing_friend.accepted_at = None
            existing_friend.created_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(existing_friend)

            return attach_signed_profile_images_to_friend(existing_friend)

        raise ValueError("FRIEND_REQUEST_ALREADY_EXISTS")

    friend = Friend(
        requester_id=requester_id,
        receiver_id=receiver.id,
        status=FriendStatus.PENDING,
    )

    db.add(friend)
    db.commit()
    db.refresh(friend)

    return attach_signed_profile_images_to_friend(friend)

def get_my_friends(
    db: Session,
    user_id: int,
) -> list[Friend]:
    friends = (
        db.query(Friend)
        .filter(
            Friend.status == FriendStatus.ACCEPTED,
            or_(
                Friend.requester_id == user_id,
                Friend.receiver_id == user_id,
            ),
        )
        .all()
    )

    return [attach_signed_profile_images_to_friend(friend) for friend in friends]


def get_received_friend_requests(
    db: Session,
    user_id: int,
) -> list[Friend]:
    friends = (
        db.query(Friend)
        .filter(
            Friend.receiver_id == user_id,
            Friend.status == FriendStatus.PENDING,
        )
        .order_by(Friend.created_at.desc())
        .all()
    )

    return [attach_signed_profile_images_to_friend(friend) for friend in friends]


def accept_friend_request(
    db: Session,
    user_id: int,
    friend_id: int,
) -> Friend | None:
    friend = (
        db.query(Friend)
        .filter(
            Friend.id == friend_id,
            Friend.receiver_id == user_id,
            Friend.status == FriendStatus.PENDING,
        )
        .first()
    )

    if friend is None:
        return None

    friend.status = FriendStatus.ACCEPTED
    friend.accepted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(friend)

    return attach_signed_profile_images_to_friend(friend)


def reject_friend_request(
    db: Session,
    user_id: int,
    friend_id: int,
) -> Friend | None:
    friend = (
        db.query(Friend)
        .filter(
            Friend.id == friend_id,
            Friend.receiver_id == user_id,
            Friend.status == FriendStatus.PENDING,
        )
        .first()
    )

    if friend is None:
        return None

    friend.status = FriendStatus.REJECTED

    db.commit()
    db.refresh(friend)

    return attach_signed_profile_images_to_friend(friend)

def delete_friend(
    db: Session,
    user_id: int,
    friend_id: int,
) -> bool:
    friend = (
        db.query(Friend)
        .filter(
            Friend.id == friend_id,
            or_(
                Friend.requester_id == user_id,
                Friend.receiver_id == user_id,
            ),
        )
        .first()
    )

    if friend is None:
        return False

    db.delete(friend)
    db.commit()

    return True