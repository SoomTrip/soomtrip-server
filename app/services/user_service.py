from sqlalchemy.orm import Session

from app.db.models import User
from app.schemas.users import UserUpdateRequest


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def update_user(
    db: Session,
    user: User,
    request: UserUpdateRequest,
) -> User:
    if request.nickname is not None:
        user.nickname = request.nickname

    if request.profile_image is not None:
        user.profile_image = request.profile_image

    db.commit()
    db.refresh(user)

    return user